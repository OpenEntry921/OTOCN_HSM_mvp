# Execution-Separated Custody MVP

A demo-focused **MVP prototype** that shows **execution authority separation**: application servers request critical actions, but they do not directly perform critical execution.

This repository demonstrates a simple Relay + Endpoint flow for **policy-based execution control**, **independent endpoint verification**, and **auditability**. It is intentionally small and direct so that the execution boundary is easy to understand in a demo.

> Status: MVP prototype. Not production-ready.
> Runtime: Python 3.9 compatible.
> Tested on Python 3.9.

## Why this exists

Many custody-style application flows place too much execution authority in the application server. If that server is misused, compromised, or incorrectly configured, critical execution may happen without a second boundary.

This prototype demonstrates a different pattern:

1. Client creates an execution request.
2. Relay validates the request and evaluates policy.
3. Relay issues a short-lived execution token bound to that exact request.
4. Endpoint independently verifies the token and request binding.
5. Endpoint executes only if verification succeeds.
6. Rejections and approvals are written to an audit log.

The core message is:

**Application servers do not directly perform critical execution.**

## Core architecture

```text
Client
  ↓
Relay
  - request validation
  - policy evaluation
  - execution token issuance
  - audit event creation
  ↓
Endpoint
  - independent endpoint verification
  - request/token binding check
  - execution approval or rejection
  - audit event creation
  ↓
Audit log
```

## Relay and Endpoint roles

### Relay

The Relay is the policy and coordination layer.

It performs:

- request receipt,
- simple policy checks,
- execution token issuance,
- audit logging.

It does **not** directly execute the sensitive action.

### Endpoint

The Endpoint is the execution boundary.

It performs:

- token signature and expiration verification,
- request field matching against token claims,
- final execution approval or rejection,
- audit logging.

This is the demo's **independent endpoint verification** step.

## Quick start

```bash
git clone https://github.com/OpenEntry921/OTOCN_HSM_mvp.git
cd OTOCN_HSM_mvp

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

./scripts/run_demo.sh
```

## Demo scenarios

`scripts/run_demo.sh` runs the complete local demo without requiring Docker or external services.

It prints:

- `REQUEST RECEIVED`
- `POLICY PASSED`
- `EXECUTION TOKEN ISSUED`
- `ENDPOINT VERIFICATION SUCCESS`
- `EXECUTION APPROVED`
- `TAMPERED REQUEST DETECTED`
- `ENDPOINT VERIFICATION FAILED`
- `EXECUTION REJECTED`
- `AUDIT EVENT CREATED`
- final audit log output

### Scenario A — 정상 요청 / Valid request

Conditions:

- allowed amount,
- allowed destination,
- valid token,
- policy conditions satisfied.

Expected result:

- Relay policy passes,
- execution token is issued,
- Endpoint verification succeeds,
- execution is approved as `EXECUTED`,
- audit events are created.

### Scenario B — 변조 / 비정상 요청

The demo includes rejection examples for:

- amount changed after token issuance,
- expired token.

The tests also cover destination tampering.

Expected result:

- Endpoint verification fails,
- rejection reason is printed,
- execution is rejected as `REJECTED`,
- audit events are created.

## Test execution

```bash
./scripts/test_demo.sh
```

The pytest suite covers:

- valid request should pass policy,
- token should be bound to original request,
- tampered amount should be rejected,
- tampered destination should be rejected,
- expired token should be rejected,
- audit event should be created.

## Repository structure

```text
endpoint/              Endpoint verification and simulated execution
relay/                 Policy evaluation, token issuance, audit writer
shared/                Shared request schemas and token signing helpers
docs/                  Architecture, demo, security, and operation notes
examples/              Demo request/flow examples
scripts/run_demo.sh    One-command demo runner
scripts/test_demo.sh   One-command test runner
tests/                 Pytest demo and policy tests
logs/                  Local demo audit output (created at runtime)
```

## Current MVP scope

Implemented in this MVP prototype:

- Relay / Endpoint separation,
- policy-based execution control,
- signed execution token issuance,
- token binding to request fields,
- independent endpoint verification,
- execution approval and rejection paths,
- local JSONL audit log,
- pytest coverage for the main demo flow.

## Not implemented yet

The following are intentionally outside the current MVP prototype:

- real blockchain transaction signing,
- real HSM-backed key custody,
- future HSM integration adapter,
- mTLS between Relay and Endpoint,
- durable nonce store for request replay prevention,
- operator identity and RBAC,
- tamper-resistant audit storage,
- high availability and failover,
- secure production secret management.

## Important limitation

This repository is a demo-oriented **MVP prototype** for explaining execution authority separation. It is not production-ready and should not be used to custody or execute real assets.
