import hmac
import hashlib
import base64
import json
import time

SECRET_KEY = b"replace-this-with-strong-secret"


def issue_token(payload: dict, ttl_seconds: int = 30) -> dict:
    payload = payload.copy()
    payload["exp"] = int(time.time()) + ttl_seconds

    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(SECRET_KEY, raw, hashlib.sha256).digest()

    token = base64.urlsafe_b64encode(raw).decode() + "." + \
            base64.urlsafe_b64encode(sig).decode()

    return {
        "token": token,
        "expires_at": payload["exp"]
    }
