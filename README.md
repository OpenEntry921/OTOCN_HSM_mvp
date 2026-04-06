# HSM_MVP

Prototype repository for an **execution-path-isolated authorization model** in a digital asset custody environment.

This project is designed to look and behave like a credible early-stage engineering repo rather than a slide-only concept. It demonstrates how an external request can be accepted by a policy relay, translated into a short-lived execution token, and then independently verified by a separate endpoint before a sensitive action is simulated.

## What this repository shows

- **Service separation** between request intake and execution approval.
- **Short-lived signed token flow** instead of direct server-to-executor trust.
- **Independent verification boundary** at the endpoint.
- **Audit-friendly request lifecycle** with structured log events.
- **Containerized local environment** for quick review and demo.

## Why the design matters

The security claim behind this repository is simple:

> Even if the upstream application path is compromised, sensitive execution should still require an independently verifiable authorization artifact.

In this MVP, that artifact is a signed execution token validated by the endpoint service.

## Demo architecture

```text
Client
  │
  ▼
Relay Service
  ├─ validates policy
  ├─ issues short-lived execution token
  ├─ writes audit trail
  └─ forwards approved request
        │
        ▼
Endpoint Service
  ├─ verifies token signature and expiry
  ├─ checks claim-to-request match
  └─ simulates execution
```

## Repository structure

```text
HSM_mvp/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── README.md
├── requirements-dev.txt
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── relay/
│   ├── Dockerfile
│   ├── __init__.py
│   ├── audit.py
│   ├── main.py
│   ├── policy.py
│   ├── requirements.txt
│   └── token_service.py
├── endpoint/
│   ├── Dockerfile
│   ├── __init__.py
│   ├── executor.py
│   ├── main.py
│   ├── requirements.txt
│   └── verifier.py
├── shared/
│   ├── __init__.py
│   ├── crypto.py
│   └── schemas.py
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── deployment.md
│   ├── roadmap.md
│   ├── security_model.md
│   ├── sequence_flow.md
│   └── threat_model.md
├── examples/
│   └── sample_request.json
├── tests/
│   ├── test_endpoint.py
│   └── test_relay_policy.py
└── logs/
```

## Core services

### Relay service

The relay service is the intake and authorization layer.

Responsibilities:
- accept execution requests,
- evaluate policy rules,
- issue short-lived signed tokens,
- forward approved requests to the endpoint,
- record audit events.

### Endpoint service

The endpoint service is the independent execution boundary.

Responsibilities:
- verify token authenticity and expiry,
- validate that token claims match the request payload,
- simulate the final privileged action.

### Shared module

The shared package contains reusable models and cryptographic helpers used by both services.

## Local quick start

### 1. Copy environment file

```bash
cp .env.example .env
```

### 2. Build and start the stack

```bash
docker compose up --build
```

### 3. Verify health endpoints

- Relay: `http://localhost:8000/health`
- Endpoint: `http://localhost:8001/health`

### 4. Send a sample request

```bash
curl -X POST http://localhost:8000/request \
  -H "Content-Type: application/json" \
  -d @examples/sample_request.json
```

Expected successful response:

```json
{
  "request_id": "req-001",
  "status": "success",
  "detail": "Simulated signing completed for wallet_A"
}
```

## Demo APIs

Once the containers are running, FastAPI docs are available at:

- Relay Swagger UI: `http://localhost:8000/docs`
- Endpoint Swagger UI: `http://localhost:8001/docs`

## Current limitations

This MVP intentionally does **not** include:

- real HSM hardware integration,
- mutual TLS,
- hardware-backed key custody,
- replay cache,
- RBAC,
- secret manager integration,
- persistent audit backends,
- production observability.

That is not a flaw in documentation. It is the boundary of the prototype.

## What makes the next version more credible

1. Replace the in-memory shared secret with KMS or HSM-backed signing.
2. Add replay protection using Redis or a durable nonce store.
3. Add mTLS between relay and endpoint.
4. Move audit logs to append-only external storage.
5. Introduce role-based approval policy and operator identity.
6. Replace the simulated executor with a hardware adapter interface.

## Intended audience

This repo is useful for:

- internal architecture review,
- investor or partner technical diligence,
- security model discussion,
- early engineering validation before hardware integration.

## License

MIT License.
