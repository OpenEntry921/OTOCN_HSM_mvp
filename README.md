# HSM MVP — Execution-Separated Custody Prototype

## Overview

This repository contains an MVP prototype for an execution-separated digital asset custody model.

The prototype explores a control architecture where application-layer coordination and execution authority are separated through independent policy evaluation and execution validation.

The design objective is to reduce execution risk in digital asset operations.

---

## Core Architecture

### Components

### 1. Relay Layer
Responsible for:

- Request validation
- Policy evaluation
- Execution token issuance
- Audit event generation

The Relay coordinates requests but does not directly perform sensitive execution.

---

### 2. Endpoint Layer
Responsible for:

- Independent execution token verification
- Execution request validation
- Final action execution

The Endpoint only executes when policy and token conditions are satisfied.

---

### 3. Audit Layer

Captures:

- Request events
- Policy decisions
- Execution events

Designed to support auditability and operational traceability.

---

## Design Principle

Core principle:

**Application servers do not directly perform critical execution.**

Execution requires:

- Policy validation
- Execution token issuance
- Independent endpoint verification

This creates an execution authority boundary between orchestration and execution.

---

## Threat Model (Current Scope)

This MVP is designed to help mitigate:

- Unauthorized execution attempts
- Server-side logic abuse
- Single-layer execution authority risk

---

## Current MVP Scope

Implemented:

- Relay–Endpoint prototype flow
- Policy evaluation logic
- Execution token validation
- Audit logging

---

## Planned Scope (Not Yet Implemented)

Planned for future development:

- HSM integration
- mTLS transport hardening
- Replay protection
- Failover handling
- Production-grade key isolation

---

## Explicit Non-Goals (Current MVP)

This repository does NOT currently provide:

- Production custody system
- Complete HSM implementation
- Certified security module
- Production deployment architecture

This is an MVP / prototype only.

---

## Repository Structure

```text
/docs
  architecture.md
  threat-model.md

/tests
  policy-tests

/examples
  demo-flow.md
```

---

## Roadmap

Phase 1
- MVP prototype
- Policy flow validation

Phase 2
- HSM integration
- Transport hardening

Phase 3
- Production-grade architecture

---

## Status

Prototype / Experimental

Not production ready.
