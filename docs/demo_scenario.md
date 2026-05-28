# Demo Scenario — Execution-Separated Custody MVP

## Objective

Show an **MVP prototype** where application servers do not directly perform critical execution. The demo highlights:

- **execution authority separation**,
- **policy-based execution control**,
- **independent endpoint verification**,
- **auditability**,
- a clear path toward **future HSM integration**.

## Scenario A — 정상 요청 / Valid request

### Input

- action: `approve_transfer`
- amount: `1000.0`
- destination: `wallet_A`
- requester: `client_app`

### Expected flow

1. Client creates the execution request.
2. Relay prints `REQUEST RECEIVED`.
3. Relay evaluates policy and prints `POLICY PASSED`.
4. Relay issues a request-bound execution token and prints `EXECUTION TOKEN ISSUED`.
5. Endpoint independently verifies token signature, expiration, and request binding.
6. Endpoint prints `ENDPOINT VERIFICATION SUCCESS`.
7. Endpoint simulates execution and prints `EXECUTION APPROVED`.
8. Audit events are written and `AUDIT EVENT CREATED` is printed.

### Expected result

`EXECUTED`

## Scenario B — 변조 / 비정상 요청

### B-1: Amount tampering

The Relay issues a token for amount `1000.0`. Before the request reaches the Endpoint, the amount is changed to `90000.0`.

Expected flow:

1. Relay policy passes for the original request.
2. Relay issues a token bound to the original request.
3. Demo prints `TAMPERED REQUEST DETECTED`.
4. Endpoint compares the token claims with the modified request.
5. Endpoint prints `ENDPOINT VERIFICATION FAILED`.
6. Endpoint prints `EXECUTION REJECTED` with the mismatch reason.
7. Audit event is created.

Expected result:

`REJECTED`

### B-2: Expired token

The Relay issues an already-expired token for demo purposes.

Expected flow:

1. Relay policy passes.
2. Relay issues an expired token.
3. Endpoint checks expiration during independent verification.
4. Endpoint prints `ENDPOINT VERIFICATION FAILED`.
5. Endpoint prints `EXECUTION REJECTED` with `token expired`.
6. Audit event is created.

Expected result:

`REJECTED`

## Run

```bash
./scripts/run_demo.sh
```

## Audit log

The demo writes JSON lines to:

```text
logs/demo_audit.log
```

The final section of the demo prints the audit log so reviewers can see request receipt, policy decisions, token issuance, endpoint verification, and execution or rejection outcomes.

## Current boundary

This demo does not implement real asset signing or real HSM operations. It focuses on the control pattern: request → policy → token → independent endpoint verification → execute/reject → audit log.
