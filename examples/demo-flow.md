# Example Demo Flow

## Valid request

```json
{
  "request_id": "demo-valid-001",
  "action": "approve_transfer",
  "target": "wallet_A",
  "amount": 1000.0,
  "requester": "client_app"
}
```

Expected output highlights:

```text
REQUEST RECEIVED
POLICY PASSED
EXECUTION TOKEN ISSUED: eyJh... (expires_at=1779979067, expires_at_iso=2026-05-28T14:45:00Z)
ENDPOINT VERIFICATION SUCCESS
EXECUTION APPROVED
AUDIT EVENT CREATED
```

## Tampered request

Original token is issued for:

```json
{
  "amount": 1000.0,
  "target": "wallet_A"
}
```

The forwarded request is changed to:

```json
{
  "amount": 90000.0,
  "target": "wallet_A"
}
```

Expected output highlights:

```text
TAMPERED REQUEST DETECTED
ENDPOINT VERIFICATION FAILED
EXECUTION REJECTED
AUDIT EVENT CREATED
```

The Endpoint rejects the request because the execution token is bound to the original request fields.
