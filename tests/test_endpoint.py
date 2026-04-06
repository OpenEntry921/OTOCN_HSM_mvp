from endpoint.verifier import verify_token
from relay.token_service import issue_token


TOKEN_PAYLOAD = {
    "request_id": "req-001",
    "action": "sign_tx",
    "target": "wallet_A",
    "requester": "client_app",
}


def test_issue_and_verify_token_roundtrip() -> None:
    token_info = issue_token(TOKEN_PAYLOAD)
    token_data = verify_token(token_info["token"])

    assert token_data["request_id"] == TOKEN_PAYLOAD["request_id"]
    assert token_data["target"] == TOKEN_PAYLOAD["target"]
    assert "exp" in token_data
