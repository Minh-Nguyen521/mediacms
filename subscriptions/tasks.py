"""
Celery tasks for subscription lifecycle management.
"""
import logging
import uuid

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='expire_subscriptions')
def expire_subscriptions():
    """
    Runs daily. For each active subscription past its end_date:
      1. Attempt a server-initiated MoMo recurring charge to renew.
      2. If charge succeeds, extend the subscription by plan.duration_days.
      3. If charge fails or no agreementId exists, expire the subscription
         and remove the user from the associated RBAC group.
    """
    from .models import MoMoTransaction, Subscription
    from . import momo

    now = timezone.now()
    due = Subscription.objects.filter(
        status=Subscription.STATUS_ACTIVE,
        end_date__lte=now,
    ).select_related('plan', 'user')

    for sub in due:
        if sub.momo_agreement_id:
            order_id = f'RENEW-{sub.pk}-{uuid.uuid4().hex[:8]}'
            ipn_url = _build_ipn_url()

            try:
                result = momo.charge_recurring(
                    order_id=order_id,
                    amount=sub.plan.price,
                    agreement_id=sub.momo_agreement_id,
                    order_info=f'MediaCMS renewal — {sub.plan.name}',
                    ipn_url=ipn_url,
                )
            except Exception as exc:
                logger.error('Renewal charge failed for subscription %s: %s', sub.pk, exc)
                sub.expire()
                continue

            result_code = result.get('resultCode')
            MoMoTransaction.objects.create(
                subscription=sub,
                order_id=order_id,
                request_id=result.get('requestId', ''),
                amount=sub.plan.price,
                status=MoMoTransaction.STATUS_SUCCESS if result_code == 0 else MoMoTransaction.STATUS_FAILED,
                result_code=result_code,
                raw_response=result,
            )

            if result_code == 0:
                # Extend subscription from current end_date (not now) to avoid gaps.
                sub.end_date = sub.end_date + timezone.timedelta(days=sub.plan.duration_days)
                sub.save(update_fields=['end_date', 'updated_at'])
                logger.info('Subscription %s renewed until %s', sub.pk, sub.end_date)
            else:
                logger.info('Renewal failed for subscription %s (resultCode %s)', sub.pk, result_code)
                sub.expire()
        else:
            # No agreement token — cannot auto-renew, just expire.
            logger.info('Expiring subscription %s (no agreementId)', sub.pk)
            sub.expire()


def _build_ipn_url() -> str:
    """Build the absolute IPN URL from settings."""
    from django.conf import settings
    frontend_host = getattr(settings, 'FRONTEND_HOST', 'http://localhost').rstrip('/')
    return f'{frontend_host}/subscriptions/webhook/momo/'
