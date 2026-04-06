import os

from shared.crypto import sign_payload


DEFAULT_TTL = int(os.getenv("TOKEN_TTL_SECONDS", "30"))


def issue_token(payload: dict, ttl_seconds: int | None = None) -> dict:
    ttl = ttl_seconds if ttl_seconds is not None else DEFAULT_TTL
    return sign_payload(payload, ttl_seconds=ttl)
