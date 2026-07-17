import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import momo
from .models import MoMoTransaction, Subscription, SubscriptionPlan

logger = logging.getLogger(__name__)


@require_GET
@login_required
def plan_list(request):
    """Return all active subscription plans as JSON."""
    plans = SubscriptionPlan.objects.filter(is_active=True).values(
        'id', 'name', 'description', 'price', 'duration_days'
    )
    return JsonResponse({'plans': list(plans)})


@require_POST
@login_required
def initiate_subscription(request, plan_id):
    """
    Create a MoMo recurring payment request for the given plan.
    Returns the MoMo payUrl to redirect the user to.
    """
    plan = get_object_or_404(SubscriptionPlan, pk=plan_id, is_active=True)

    subscription = Subscription.objects.create(user=request.user, plan=plan)
    order_id = f'SUB-{subscription.pk}-{uuid.uuid4().hex[:8]}'

    frontend_host = request.build_absolute_uri('/').rstrip('/')
    redirect_url = f'{frontend_host}/subscriptions/return/'
    ipn_url = f'{frontend_host}/subscriptions/webhook/momo/'

    try:
        result = momo.create_recurring_payment(
            order_id=order_id,
            amount=plan.price,
            order_info=f'MediaCMS — {plan.name}',
            redirect_url=redirect_url,
            ipn_url=ipn_url,
        )
    except Exception as exc:
        logger.error('MoMo create_recurring_payment failed: %s', exc)
        subscription.delete()
        return JsonResponse({'error': 'Payment gateway error. Please try again.'}, status=502)

    MoMoTransaction.objects.create(
        subscription=subscription,
        order_id=order_id,
        request_id=result.get('requestId', ''),
        amount=plan.price,
        status=MoMoTransaction.STATUS_PENDING,
        raw_response=result,
    )

    pay_url = result.get('payUrl')
    if not pay_url:
        logger.error('MoMo did not return payUrl: %s', result)
        subscription.delete()
        return JsonResponse({'error': 'No payment URL returned by MoMo.'}, status=502)

    return JsonResponse({'payUrl': pay_url})


@csrf_exempt
def momo_webhook(request):
    """
    IPN endpoint called by MoMo after payment is processed.
    Must return HTTP 204 to acknowledge receipt.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if not momo.verify_ipn_signature(data):
        logger.warning('MoMo IPN: invalid signature. Data: %s', data)
        return HttpResponse(status=400)

    order_id = data.get('orderId', '')
    result_code = data.get('resultCode')
    agreement_id = data.get('agreementId', '')

    try:
        transaction = MoMoTransaction.objects.select_related('subscription__plan').get(order_id=order_id)
    except MoMoTransaction.DoesNotExist:
        logger.error('MoMo IPN: unknown orderId %s', order_id)
        return HttpResponse(status=204)

    transaction.result_code = result_code
    transaction.raw_response = data
    transaction.status = MoMoTransaction.STATUS_SUCCESS if result_code == 0 else MoMoTransaction.STATUS_FAILED
    transaction.save(update_fields=['result_code', 'raw_response', 'status'])

    if result_code == 0:
        sub = transaction.subscription
        if agreement_id:
            sub.momo_agreement_id = agreement_id
            sub.save(update_fields=['momo_agreement_id', 'updated_at'])
        sub.activate()
        logger.info('Subscription %s activated for user %s', sub.pk, sub.user_id)
    else:
        logger.info('MoMo IPN: payment failed for orderId %s, resultCode %s', order_id, result_code)

    return HttpResponse(status=204)


@require_GET
@login_required
def momo_return(request):
    """
    Redirect landing page after user completes payment on MoMo.
    MoMo sends query params here; actual activation happens via IPN.
    """
    result_code = request.GET.get('resultCode', '')
    if result_code == '0':
        return redirect('/?subscription=success')
    return redirect('/?subscription=failed')


@require_GET
def subscriptions_page(request):
    """Render the React-powered subscriptions/plans page."""
    return render(request, 'cms/subscriptions.html')


@require_GET
@login_required
def subscription_status(request):
    """Return the current user's active subscription, if any."""
    sub = (
        Subscription.objects.filter(user=request.user, status=Subscription.STATUS_ACTIVE)
        .select_related('plan')
        .order_by('-end_date')
        .first()
    )
    if not sub or not sub.is_active:
        return JsonResponse({'active': False})

    return JsonResponse({
        'active': True,
        'plan': sub.plan.name,
        'end_date': sub.end_date.isoformat(),
    })
