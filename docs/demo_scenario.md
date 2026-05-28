# Demo Scenario — Execution-Separated Custody MVP

## Demo Objective

Demonstrate that:

1. Application systems cannot directly execute sensitive asset operations.
2. Policy evaluation and execution authority are separated.
3. Execution only occurs after independent verification.
4. All critical events are auditable.

---

# Core Story

Traditional systems often allow application servers to directly execute asset operations once credentials or internal authority are compromised.

This MVP demonstrates a different architecture:

- The application requests execution.
- The Relay validates policy.
- The Relay issues a constrained execution token.
- The Endpoint independently verifies the token.
- The Endpoint decides whether execution is allowed.

Execution authority is separated from orchestration.

---

# Demo Participants

## 1. Client Application
Simulates:
- Trading platform
- Treasury system
- Automation workflow
- AI agent

The client initiates a withdrawal request.

---

## 2. Relay Layer
Responsible for:
- Request validation
- Policy evaluation
- Risk checks
- Execution token issuance
- Audit event creation

The Relay DOES NOT directly execute the transfer.

---

## 3. Endpoint Layer
Responsible for:
- Independent token verification
- Validation of execution conditions
- Final execution approval

The Endpoint only executes when all conditions pass.

---

## 4. Audit Layer
Captures:
- Request logs
- Policy decisions
- Token issuance events
- Execution outcomes

Provides operational traceability.

---

# Demo Flow

## Scenario A — Valid Execution

### Step 1
Client submits withdrawal request.

Example:
- Amount: 1 ETH
- Destination: Approved wallet
- Time: Within policy window

Expected Result:
- Relay accepts request.

---

### Step 2
Relay evaluates policy.

Checks:
- Amount limit
- Allowed destination
- Time restrictions
- Request validity

Expected Result:
- Policy passes.

---

### Step 3
Relay issues execution token.

Token properties:
- Short-lived
- Request-bound
- Non-transferable
- Policy-scoped

Expected Result:
- Token generated.

---

### Step 4
Endpoint independently verifies token.

Checks:
- Signature validity
- Expiration
- Request binding
- Policy scope

Expected Result:
- Verification succeeds.

---

### Step 5
Endpoint executes operation.

Expected Result:
- Execution approved.
- Audit event generated.

---

# Scenario B — Invalid Execution Attempt

## Attack Simulation

Simulate:
- Modified amount
- Expired token
- Unauthorized destination
- Replay attempt

Expected Result:
- Endpoint rejects execution.
- Audit event generated.

Critical Point:
Even if the application layer attempts unauthorized execution, the Endpoint still independently validates execution authority.

---

# Key Message During Demo

"The application server itself does not possess direct execution authority."

This architecture reduces:
- Single-layer compromise risk
- Blind execution risk
- Unauthorized automated execution
- Centralized execution authority exposure

---

# Recommended Live Demo Sequence

1. Show architecture diagram
2. Start Relay service
3. Start Endpoint service
4. Submit valid request
5. Show token issuance
6. Show independent verification
7. Show successful execution
8. Run tampered request
9. Show rejection
10. Show audit logs

Total recommended runtime:
5–7 minutes.

---

# Suggested Closing Statement

"This MVP demonstrates a separation model between orchestration authority and execution authority.

The objective is not simply key storage.
The objective is reducing execution risk through independent validation boundaries."
