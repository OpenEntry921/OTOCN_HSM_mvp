from shared.crypto import verify_signed_token


def verify_token(token: str) -> dict:
    return verify_signed_token(token)
