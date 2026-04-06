# HSM_MVP

HSM_MVP is a minimal but structured prototype for an **execution-path-isolated authorization flow** in a digital asset custody environment.

The repository demonstrates a simple separation between:

- a **relay service** that receives requests, applies policy, issues a short-lived execution token, and forwards approved requests, and
- an **endpoint service** that independently verifies the token before simulating a sensitive action.

This is **not** a production custody system. It is an MVP intended to show architectural intent, service boundaries, and a realistic repository structure.

---

## Why this exists

The project is designed to illustrate a core security idea:

> A compromised application server should not be able to directly trigger sensitive execution without passing an independent authorization boundary.

In this MVP, that boundary is represented by the endpoint service validating a signed, short-lived execution token.

---

## Repository structure

```text
HSM_mvp/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
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
│   ├── security_model.md
│   ├── sequence_flow.md
│   └── threat_model.md
├── examples/
│   └── sample_request.json
└── logs/
```

---

## Services

### Relay

The relay service is responsible for:

- accepting external execution requests,
- evaluating policy rules,
- issuing a short-lived execution token,
- forwarding approved requests to the endpoint service, and
- writing audit records.

### Endpoint

The endpoint service is responsible for:

- validating execution tokens independently,
- confirming that token claims match the request payload, and
- simulating the final execution action.

### Shared

The shared module contains:

- request/response schemas,
- token signing and verification helpers.

---

## Local run

### 1. Copy environment file

```bash
cp .env.example .env
```

### 2. Build and run

```bash
docker compose up --build
```

### 3. Test relay API

```bash
curl -X POST http://localhost:8000/request \
  -H "Content-Type: application/json" \
  -d @examples/sample_request.json
```

---

## Example flow

1. Client submits a request to the relay.
2. Relay validates the request against policy rules.
3. Relay issues a signed token with a short TTL.
4. Relay forwards the request and token to the endpoint.
5. Endpoint verifies the token independently.
6. Endpoint simulates the allowed action.
7. Relay records the forwarding and result status in the audit log.

---

## Current limitations

This MVP intentionally does **not** include:

- real HSM integration,
- hardware-backed key custody,
- mutual TLS or network segmentation controls,
- persistent token storage,
- replay cache,
- production-grade secret management,
- rate limiting, authentication, or RBAC.

Those items are future work, not hidden assumptions.

---

## Next realistic improvements

- move token secret to a secret manager,
- add replay protection with Redis,
- replace direct internal HTTP trust with mTLS,
- split audit logs from application logs,
- add structured monitoring and trace IDs,
- replace simulated executor logic with an HSM adapter interface.

---

## License

MIT License.
