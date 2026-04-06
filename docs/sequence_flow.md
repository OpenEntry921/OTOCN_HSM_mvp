# Execution Sequence Flow

```text
1. Client sends POST /request to relay.
2. Relay records request_received in audit log.
3. Relay evaluates whitelist, amount, and supported action policy.
4. Relay issues a short-lived signed token.
5. Relay forwards request + token to endpoint.
6. Endpoint verifies token signature and expiration.
7. Endpoint checks token claims against request fields.
8. Endpoint simulates the approved action.
9. Relay records forwarding result in audit log.
10. Client receives execution result.
```
