# utils/paytm_utils.py
import json
from paytmchecksum import PaytmChecksum

PAYTM_MID = "Resell00448805757124"
PAYTM_MERCHANT_KEY = "KXHUJH&Ywq9pUkkr"
PAYTM_INITIATE_URL = "https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction"


def generate_checksum(body: dict) -> str:
    """
    Generate Paytm checksum for initiateTransaction using official library.
    """
    data_str = json.dumps(body)
    return PaytmChecksum.generateSignature(data_str, PAYTM_MERCHANT_KEY)


def verify_checksum(body: dict, checksum: str) -> bool:
    """
    Verify Paytm checksum for response/callback using official library.
    """
    data_str = json.dumps(body)
    return PaytmChecksum.verifySignature(body, PAYTM_MERCHANT_KEY, checksum)
