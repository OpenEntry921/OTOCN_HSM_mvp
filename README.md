# HSM_mvp
HSM_MVP is a minimal prototype demonstrating an **execution-path-isolated secure channel architecture** for digital asset custody systems.

This project shows how an execution request can be separated from the main server layer and securely delivered to a protected execution endpoint using a relay-based authorization flow.

---

## Purpose

The goal of this project is to demonstrate the following security concepts:

- Execution path isolation
- Policy-based authorization
- Opaque token execution control
- Relay-to-endpoint secure channel
- Independent endpoint verification
- Audit logging for execution flow

This repository provides a **proof-of-concept architecture prototype**, not a production-ready custody system.

---

## System Overview

The system separates external service logic from secure execution endpoints.


Client
↓
Relay Server
↓
Policy Engine
↓
Execution Token
↓
Secure Execution Channel
↓
Endpoint Server
↓
Execution Engine

The endpoint verifies the execution token independently before performing any action.

---

## Components

### Relay Server

Responsible for:

- receiving external requests
- evaluating security policy
- issuing execution tokens
- forwarding approved requests to endpoint

### Policy Engine

Validates whether a request is allowed.

Examples:

- whitelist validation
- transaction limits
- action validation

### Execution Token

Short-lived opaque authorization token issued by relay.

Used to verify execution permission at endpoint.

### Endpoint Server

Responsible for:

- verifying execution tokens
- executing approved operations
- preventing direct server-triggered execution

### Audit Module

Logs the entire execution process.

---

## Security Concept

The architecture follows an **Assume Breach model**.

Even if the main server is compromised, the attacker cannot directly execute operations on the secure endpoint without a valid execution token.

This reduces the attack surface for high-value operations such as:

- digital asset signing
- transaction approval
- custody operations

---

## Disclaimer

This project is a prototype architecture demonstration.

It does not implement:

- production-grade custody security
- real HSM integration
- cryptographic key management

---

## Project Structure


HSM_-mvp/
├── relay/
├── endpoint/
├── shared/
├── docs/
├── docker-compose.yml

---

## Future Improvements

Possible extensions:

- Redis-backed opaque token storage
- device identity authentication
- multi-relay architecture
- HSM adapter integration
- MPC compatibility

---

## License

MIT License
