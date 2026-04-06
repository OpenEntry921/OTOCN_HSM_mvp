# HSM_MVP Architecture

## Overview

HSM_MVP demonstrates a two-stage authorization and execution flow:

1. **Relay** receives and approves requests.
2. **Endpoint** independently verifies authorization before execution.

The design goal is not “perfect security.”
The design goal is to reduce the blast radius of a compromised application tier.

---

## Logical flow

```text
Client
  |
  v
Relay API
  |
  +--> Policy validation
  |
  +--> Token issuance
  |
  v
Endpoint API
  |
  +--> Token verification
  |
  v
Execution engine
```

---

## Security boundary

The endpoint represents the **execution authority boundary**.

A caller reaching the relay does not automatically gain execution rights.
The relay must first create a valid short-lived token, and the endpoint must still verify that token independently.

---

## Design choices in this MVP

- relay and endpoint are separated services,
- token signing and verification are centralized in shared helpers,
- the endpoint verifies token claims against the request body,
- audit logs are persisted to a mounted logs directory,
- environment variables are used for secret and endpoint configuration.

---

## Non-goals

This repository does not yet model:

- network-level trust boundaries,
- hardware-backed key use,
- certificate management,
- secret rotation,
- replay cache,
- operational failover.
