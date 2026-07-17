"""
MoMo payment client for one-time donation payments (captureWallet).
"""
import uuid

import requests
from django.conf import settings

from cms.momo_utils import sign

MOMO_PARTNER_CODE = getattr(settings, 'MOMO_PARTNER_CODE', '')
MOMO_ACCESS_KEY = getattr(settings, 'MOMO_ACCESS_KEY', '')
MOMO_API_URL = getattr(settings, 'MOMO_API_URL', 'https://test-payment.momo.vn')

CREATE_ENDPOINT = f'{MOMO_API_URL}/v2/gateway/api/create'


def create_donation_payment(order_id: str, amount: int, order_info: str, redirect_url: str, ipn_url: str) -> dict:
    """
    Create a one-time MoMo wallet payment for a donation.
    Returns the raw MoMo API response dict (contains `payUrl`).
    Raises requests.HTTPError on non-2xx responses.
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
        'requestType': 'captureWallet',
    }

    payload = {
        'partnerCode': MOMO_PARTNER_CODE,
        'requestId': request_id,
        'amount': amount,
        'orderId': order_id,
        'orderInfo': order_info,
        'redirectUrl': redirect_url,
        'ipnUrl': ipn_url,
        'requestType': 'captureWallet',
        'extraData': extra_data,
        'lang': 'vi',
        'signature': sign(sig_params),
    }

    response = requests.post(CREATE_ENDPOINT, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
