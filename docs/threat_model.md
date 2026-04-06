# Threat Model

The system assumes the possibility of application server compromise.

## Threats Considered

- server compromise
- unauthorized execution requests
- replay attacks
- lateral movement inside network

## Mitigation

- execution path isolation
- short-lived execution tokens
- endpoint-side verification
- audit logging
