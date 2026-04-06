# API Documentation

## Relay Server API

**Base URL**

```text
http://localhost:8000
```

### POST /request

Submit an execution request.

**Request**

```json
{
  "request_id": "req-001",
  "action": "sign_tx",
  "target": "wallet_A",
  "amount": 1000,
  "requester": "client_app"
}
```

**Successful response**

```json
{
  "request_id": "req-001",
  "status": "success",
  "detail": "Simulated signing completed for wallet_A"
}
```

**Policy denied**

```json
{
  "detail": "Target not whitelisted"
}
```

---

## Endpoint Server API

**Base URL**

```text
http://localhost:8001
```

### POST /execute

This endpoint is intended for internal relay-to-endpoint calls.

**Payload**

```json
{
  "request": {
    "request_id": "req-001",
    "action": "sign_tx",
    "target": "wallet_A",
    "requester": "client_app"
  },
  "execution_token": "token-value"
}
```

**Successful response**

```json
{
  "request_id": "req-001",
  "status": "success",
  "detail": "Simulated signing completed for wallet_A"
}
```

**Invalid token**

```json
{
  "detail": "invalid signature"
}
```
