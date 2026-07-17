"""
MoMo payment gateway client for subscriptions (recurring payments).

MoMo docs: https://developers.momo.vn/v3/docs/payment/api/wallet/
"""
import uuid

import requests
from django.conf import settings

from cms.momo_utils import sign, verify_ipn_signature  # noqa: re-exported for callers

MOMO_PARTNER_CODE = getattr(settings, 'MOMO_PARTNER_CODE', '')
MOMO_ACCESS_KEY = getattr(settings, 'MOMO_ACCESS_KEY', '')
MOMO_API_URL = getattr(settings, 'MOMO_API_URL', 'https://test-payment.momo.vn')

CREATE_ENDPOINT = f'{MOMO_API_URL}/v2/gateway/api/create'
RECURRING_ENDPOINT = f'{MOMO_API_URL}/v2/gateway/api/recurring'


def create_recurring_payment(order_id: str, amount: int, order_info: str, redirect_url: str, ipn_url: str) -> dict:
    """
    Initiate the first payment of a recurring subscription.
    Returns the raw MoMo API response dict (contains `payUrl` and later `agreementId` via IPN).
    """
    request_id = str(uuid.uuid4())
    extra_data = ''

    sig_params = {
        'accessKey': MOMO_ACCESS_KEY,
        'amount': str(amount),
        'extraData': extra_data,
        'ipnUrl': ipn_url,
        'orderId': order_id,
        'orderInfo': order_info,
        'partnerCode': MOMO_PARTNER_CODE,
        'redirectUrl': redirect_url,
        'requestId': request_id,
        'requestType': 'recurringPayment',
    }

    payload = {
        'partnerCode': MOMO_PARTNER_CODE,
        'requestId': request_id,
        'amount': amount,
        'orderId': order_id,
        'orderInfo': order_info,
        'redirectUrl': redirect_url,
        'ipnUrl': ipn_url,
        'requestType': 'recurringPayment',
        'extraData': extra_data,
        'lang': 'vi',
        'autoCapture': True,
        'signature': sign(sig_params),
    }

    response = requests.post(CREATE_ENDPOINT, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def charge_recurring(order_id: str, amount: int, agreement_id: str, order_info: str, ipn_url: str) -> dict:
    """
    Server-initiated charge against an existing MoMo recurring agreement.
    Used by the Celery renewal task.
    """
    request_id = str(uuid.uuid4())
    extra_data = ''

    sig_params = {
        'accessKey': MOMO_ACCESS_KEY,
        'agreementId': agreement_id,
        'amount': str(amount),
        'extraData': extra_data,
        'ipnUrl': ipn_url,
        'orderId': order_id,
        'orderInfo': order_info,
        'partnerCode': MOMO_PARTNER_CODE,
        'requestId': request_id,
        'requestType': 'payRecurring',
    }

    payload = {
        'partnerCode': MOMO_PARTNER_CODE,
        'requestId': request_id,
        'amount': amount,
        'orderId': order_id,
        'orderInfo': order_info,
        'ipnUrl': ipn_url,
        'agreementId': agreement_id,
        'requestType': 'payRecurring',
        'extraData': extra_data,
        'lang': 'vi',
        'signature': sign(sig_params),
    }

    response = requests.post(RECURRING_ENDPOINT, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
