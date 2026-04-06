# API Documentation

## Relay Server API

Base URL


http://localhost:8000

---

## Request Execution

### POST /request

Submit an execution request.

Request:

```json
{
  "request_id": "req-001",
  "action": "sign_tx",
  "target": "wallet_A",
  "amount": 1000,
  "requester": "client_app"
}

Response:
{
  "request_id": "req-001",
  "status": "success",
  "detail": "Simulated signing completed"
}
Endpoint Server API
Base URL

http://localhost:8001
POST /execute
Called internally by the relay server.
Payload:
{
  "request": {
    "request_id": "req-001",
    "action": "sign_tx",
    "target": "wallet_A",
    "requester": "client_app"
  },
  "execution_token": "token-value"
}

Response:
{
  "request_id": "req-001",
  "status": "success",
  "detail": "Execution completed"
}
Error Responses
403 Policy Denied
{
  "detail": "Target not whitelisted"
}
401 Invalid Token
{
  "detail": "Token verification failed"
}
