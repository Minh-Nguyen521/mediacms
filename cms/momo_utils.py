"""
Shared MoMo payment utility functions used by subscriptions and donations.
"""
import hashlib
import hmac

from django.conf import settings


def get_secret_key() -> str:
    return getattr(settings, 'MOMO_SECRET_KEY', '')


def get_access_key() -> str:
    return getattr(settings, 'MOMO_ACCESS_KEY', '')


def sign(params: dict) -> str:
    """Generate HMAC-SHA256 signature from a dict of parameters (sorted alphabetically)."""
    raw = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    return hmac.new(
        get_secret_key().encode('utf-8'),
        raw.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def verify_ipn_signature(data: dict) -> bool:
    """
    Verify the HMAC-SHA256 signature on an IPN callback from MoMo.

    MoMo signs these fields (alphabetical order):
      accessKey, amount, extraData, message, orderId, orderInfo,
      orderType, partnerCode, payType, requestId, responseTime,
      resultCode, transId
    """
    sig_params = {
        'accessKey': get_access_key(),
        'amount': str(data.get('amount', '')),
        'extraData': data.get('extraData', ''),
        'message': data.get('message', ''),
        'orderId': data.get('orderId', ''),
        'orderInfo': data.get('orderInfo', ''),
        'orderType': data.get('orderType', ''),
        'partnerCode': data.get('partnerCode', ''),
        'payType': data.get('payType', ''),
        'requestId': data.get('requestId', ''),
        'responseTime': str(data.get('responseTime', '')),
        'resultCode': str(data.get('resultCode', '')),
        'transId': str(data.get('transId', '')),
    }
    expected = sign(sig_params)
    received = data.get('signature', '')
    return hmac.compare_digest(expected, received)
