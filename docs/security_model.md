# Security Model

The MVP follows an **assume breach** mindset.

That means the application-facing layer is treated as potentially compromiseable, and sensitive execution should still require a second authorization boundary.

## Security controls represented in the MVP

- short-lived signed execution tokens,
- endpoint-side token verification,
- token claim matching against the forwarded request,
- explicit policy checks before forwarding,
- audit logging of key stages.

## What this does well

- demonstrates service separation,
- makes execution conditional on more than a single API call,
- gives a clean foundation for explaining a future HSM adapter.

## What this does not solve yet

- relay impersonation at the network layer,
- token replay inside the TTL window,
- secret leakage from environment variables,
- operator abuse,
- real transaction signing security.
