import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict


def get_token_secret() -> bytes:
    return os.getenv("TOKEN_SECRET", "replace-this-with-a-long-random-secret").encode()


def timestamp_to_iso(timestamp: int) -> str:
    return (
        datetime.fromtimestamp(timestamp, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sign_payload(payload: Dict[str, Any], ttl_seconds: int = 30) -> Dict[str, Any]:
    payload = payload.copy()
    payload["exp"] = int(time.time()) + ttl_seconds

    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(get_token_secret(), raw, hashlib.sha256).digest()

    token = (
        base64.urlsafe_b64encode(raw).decode().rstrip("=")
        + "."
        + base64.urlsafe_b64encode(sig).decode().rstrip("=")
    )

    return {
        "token": token,
        "expires_at": payload["exp"],
        "expires_at_iso": timestamp_to_iso(payload["exp"]),
    }


def verify_signed_token(token: str) -> Dict[str, Any]:
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        raw = base64.urlsafe_b64decode(_pad(raw_b64))
        sig = base64.urlsafe_b64decode(_pad(sig_b64))

        expected = hmac.new(get_token_secret(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("invalid signature")

        payload = json.loads(raw.decode())
        if payload["exp"] < int(time.time()):
            raise ValueError("token expired")

        return payload
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"token verification failed: {exc}") from exc


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode()
