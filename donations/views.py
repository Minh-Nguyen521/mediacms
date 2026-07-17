import json
import logging
import uuid

from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from cms.momo_utils import verify_ipn_signature
from .models import Donation
from . import momo

logger = logging.getLogger(__name__)
User = get_user_model()

DONATION_MIN_AMOUNT = 10_000   # VND
DONATION_MAX_AMOUNT = 10_000_000  # VND


@require_POST
def initiate_donation(request, username):
    """
    Create a MoMo one-time payment for a donation to a creator.
    Donor must be authenticated.
    Request body (JSON): { "amount": 50000, "message": "Keep it up!" }
    Returns: { "payUrl": "..." }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    creator = get_object_or_404(User, username=username)

    if creator == request.user:
        return JsonResponse({'error': 'You cannot donate to yourself.'}, status=400)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    try:
        amount = int(body.get('amount', 0))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'amount must be an integer.'}, status=400)

    if not (DONATION_MIN_AMOUNT <= amount <= DONATION_MAX_AMOUNT):
        return JsonResponse(
            {'error': f'Amount must be between {DONATION_MIN_AMOUNT:,} and {DONATION_MAX_AMOUNT:,} VND.'},
            status=400,
        )

    message = str(body.get('message', ''))[:500]
    order_id = f'DON-{uuid.uuid4().hex[:16]}'

    donation = Donation.objects.create(
        donor=request.user,
        donor_name=request.user.get_full_name() or request.user.username,
        creator=creator,
        amount=amount,
        message=message,
        order_id=order_id,
    )

    frontend_host = request.build_absolute_uri('/').rstrip('/')
    redirect_url = f'{frontend_host}/donations/return/'
    ipn_url = f'{frontend_host}/donations/webhook/momo/'

    try:
        result = momo.create_donation_payment(
            order_id=order_id,
            amount=amount,
            order_info=f'Donation to {creator.username} on MediaCMS',
            redirect_url=redirect_url,
            ipn_url=ipn_url,
        )
    except Exception as exc:
        logger.error('MoMo create_donation_payment failed: %s', exc)
        donation.delete()
        return JsonResponse({'error': 'Payment gateway error. Please try again.'}, status=502)

    pay_url = result.get('payUrl')
    if not pay_url:
        logger.error('MoMo did not return payUrl for donation: %s', result)
        donation.delete()
        return JsonResponse({'error': 'No payment URL returned by MoMo.'}, status=502)

    return JsonResponse({'payUrl': pay_url})


@csrf_exempt
def momo_donation_webhook(request):
    """
    IPN endpoint called by MoMo after donation payment is processed.
    Marks the donation as success/failed. Returns HTTP 204 to acknowledge.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if not verify_ipn_signature(data):
        logger.warning('Donation IPN: invalid signature. Data: %s', data)
        return HttpResponse(status=400)

    order_id = data.get('orderId', '')
    result_code = data.get('resultCode')
    trans_id = str(data.get('transId', ''))

    try:
        donation = Donation.objects.get(order_id=order_id)
    except Donation.DoesNotExist:
        logger.error('Donation IPN: unknown orderId %s', order_id)
        return HttpResponse(status=204)

    if donation.status != Donation.STATUS_PENDING:
        # Already processed (MoMo may retry IPN).
        return HttpResponse(status=204)

    donation.raw_ipn = data
    donation.momo_trans_id = trans_id

    if result_code == 0:
        donation.status = Donation.STATUS_SUCCESS
        logger.info('Donation %s succeeded: %s VND from %s to %s', order_id, donation.amount, donation.donor_id, donation.creator_id)
    else:
        donation.status = Donation.STATUS_FAILED
        logger.info('Donation %s failed (resultCode %s)', order_id, result_code)

    donation.save(update_fields=['status', 'momo_trans_id', 'raw_ipn', 'updated_at'])
    return HttpResponse(status=204)


@require_GET
def momo_donation_return(request):
    """Redirect landing page after donor completes payment on MoMo."""
    result_code = request.GET.get('resultCode', '')
    if result_code == '0':
        return redirect('/?donation=success')
    return redirect('/?donation=failed')


@require_GET
def creator_donation_summary(request, username):
    """
    Returns a summary of successful donations received by a creator.
    Accessible by: the creator themselves, or any site admin.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    creator = get_object_or_404(User, username=username)

    if request.user != creator and not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    donations = (
        Donation.objects.filter(creator=creator, status=Donation.STATUS_SUCCESS)
        .values('id', 'donor_name', 'amount', 'message', 'payout_status', 'created_at')
        .order_by('-created_at')
    )

    total_received = sum(d['amount'] for d in donations)
    total_pending_payout = sum(d['amount'] for d in donations if d['payout_status'] == Donation.PAYOUT_PENDING)

    return JsonResponse({
        'creator': username,
        'total_received_vnd': total_received,
        'total_pending_payout_vnd': total_pending_payout,
        'donations': list(donations),
    })
