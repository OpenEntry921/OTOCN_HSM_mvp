# Threat Model

## Assumptions

- external clients may be malicious,
- the relay service may be probed or partially compromised,
- internal HTTP traffic should not be treated as inherently trusted,
- sensitive execution should require more than simple reachability.

## Threats considered

### 1. Unauthorized execution request
A caller attempts to trigger endpoint execution without relay authorization.

**Mitigation in MVP:** endpoint requires a valid signed token.

### 2. Request tampering after approval
A request body is modified between relay approval and endpoint execution.

**Mitigation in MVP:** endpoint compares token claims with request payload.

### 3. Expired token usage
A token is replayed after its intended lifetime.

**Mitigation in MVP:** token includes `exp` claim and endpoint enforces expiry.

## Threats not fully mitigated

### Replay within token TTL
A valid token reused within the active TTL can still pass.
This MVP does not maintain nonce or replay cache state.

### Shared secret compromise
If the token signing secret is leaked, token trust collapses.
This is why a real system needs proper secret storage and rotation.

### Network-layer spoofing
This MVP does not implement mTLS or service identity verification.
