import hmac
import hashlib
import base64
import json
import time

SECRET_KEY = b"replace-this-with-strong-secret"


def verify_token(token: str) -> dict:
    try:
        raw_b64, sig_b64 = token.split(".")
        raw = base64.urlsafe_b64decode(raw_b64.encode())
        sig = base64.urlsafe_b64decode(sig_b64.encode())

        expected = hmac.new(SECRET_KEY, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("Invalid signature")

        payload = json.loads(raw.decode())
        if payload["exp"] < int(time.time()):
            raise ValueError("Token expired")

        return payload
    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")
