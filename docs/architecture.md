# Architecture Overview

## Execution-Separated Custody Prototype Architecture

This prototype is designed to separate coordination logic from execution authority.

The objective is to reduce execution risk by ensuring that no single application component can independently trigger critical execution.

---

## Logical Flow

```text
Client
  ↓
Relay Layer
  ↓
Policy Evaluation
  ↓
Execution Token Issuance
  ↓
Endpoint Verification
  ↓
Execution
```

---

## Component Roles

### Client

Initiates a request.

Examples:

- transaction request
- operational request
- policy-controlled action

The client does not directly interact with the execution layer.

---

### Relay Layer

The Relay is responsible for:

- receiving requests  
- validating request structure  
- evaluating policy conditions  
- issuing execution tokens  
- generating audit events

The Relay coordinates requests.

It does not directly perform critical execution.

---

### Policy Evaluation

Policy logic determines whether a request satisfies predefined control conditions.

Examples:

- authorization checks  
- policy rules  
- risk conditions

Only approved requests proceed.

---

### Execution Token Issuance

If policy conditions are satisfied:

- an execution token is issued

The execution token is used as a required condition for downstream execution.

---

### Endpoint Verification

The Endpoint independently verifies:

- execution token validity  
- request integrity  
- execution conditions

Execution only proceeds if verification succeeds.

---

### Execution

Sensitive execution occurs only after:

- policy approval  
- token issuance  
- independent endpoint verification

---

## Core Principle

**Application-layer coordination and execution authority are separated.**

No single coordination component independently controls critical execution.

---

## Current Scope

This is an MVP prototype architecture.

Production features such as HSM integration, transport hardening, and replay protection are outside the current scope.
