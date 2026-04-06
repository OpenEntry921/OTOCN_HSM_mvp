# Security Model

The architecture follows the Assume Breach model.

Security is enforced through:

- execution authority isolation
- token-based authorization
- endpoint verification
- audit logging

Sensitive operations are executed only after endpoint-side authorization.
