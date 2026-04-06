# API Documentation

## Relay Service

**Base URL**

```text
http://localhost:8000
```

### GET /health

Returns service liveness.

**Response**

```json
{
  "status": "ok",
  "service": "relay"
}
```

### POST /request

Submits an execution request to the relay.

**Request body**

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

**Possible error responses**

Policy denied:

```json
{
  "detail": "Target not whitelisted"
}
```

Endpoint failure:

```json
{
  "detail": "Endpoint request failed"
}
```

## Endpoint Service

**Base URL**

```text
http://localhost:8001
```

### GET /health

Returns service liveness.

**Response**

```json
{
  "status": "ok",
  "service": "endpoint"
}
```

### POST /execute

Internal relay-to-endpoint execution call.

**Request body**

```json
{
  "request": {
    "request_id": "req-001",
    "action": "sign_tx",
    "target": "wallet_A",
    "amount": 1000,
    "requester": "client_app",
    "timestamp": 1710000000.0
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

**Possible error responses**

Invalid token:

```json
{
  "detail": "invalid signature"
}
```

Token claim mismatch:

```json
{
  "detail": "Token claim mismatch: target"
}
```
