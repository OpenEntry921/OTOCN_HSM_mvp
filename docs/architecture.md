# HSM_MVP Architecture

## Overview

HSM_MVP demonstrates a secure execution architecture that separates the “request layer” from the “execution layer”.

This design prevents compromised application servers from directly executing sensitive operations.

---

## Architecture Diagram


Client
↓
Relay Server
↓
Policy Engine
↓
Execution Token Issuer
↓
Secure Channel
↓
Endpoint Verifier
↓
Execution Engine

---

## Key Security Concepts

### Execution Path Isolation

Execution requests cannot reach the endpoint directly.

All requests must pass through:

1. Relay server
2. Policy engine
3. Token verification

---

### Token-Based Execution Authorization

Instead of allowing direct execution calls, the relay server issues a **short-lived execution token**.

The endpoint verifies this token before performing any action.

---

### Endpoint Autonomy

The endpoint independently verifies authorization.

This prevents the main server from becoming a single point of compromise.

---

### Assume Breach Model

The architecture assumes that the relay server or application layer could be compromised.

Security is enforced at the endpoint level.

---

## System Components

### Client

External application initiating requests.

---

### Relay Server

Functions:

- request intake
- policy validation
- execution token issuance
- request forwarding

---

### Policy Engine

Responsible for validating requests based on predefined rules.

Example rules:

- transaction limit
- target whitelist
- operation type validation

---

### Execution Token Service

Creates short-lived tokens representing approved operations.

Token properties:

- expiration timestamp
- request ID
- authorized action

---

### Endpoint Server

The endpoint verifies tokens and executes allowed operations.

It acts as the **execution authority boundary**.

---

### Execution Engine

Handles final execution logic such as:

- simulated transaction signing
- approval actions

---

## Audit Logging

All events are logged:

- request received
- policy decision
- token issued
- execution result

---

## Limitations

This MVP does not include:

- real blockchain integration
- HSM connection
- production cryptographic security

It demonstrates architectural concepts only.
