# Roadmap

This roadmap outlines the evolution from MVP to production-ready system.

---

## Phase 1 — MVP (Current)

Goal: Demonstrate architecture and execution separation

- Relay / Endpoint separation
- Token-based execution flow
- Basic validation and audit logging
- Dockerized local environment

---

## Phase 2 — Security Hardening

Goal: Introduce real security guarantees

- HSM integration for execution authority
- Mutual TLS (mTLS) between Relay and Endpoint
- Replay attack protection (nonce / timestamp validation)
- Append-only audit logging (tamper-resistant)
- Secure key management

---

## Phase 3 — Access Control

Goal: Control who can trigger execution

- Operator authentication
- Role-Based Access Control (RBAC)
- Policy engine for execution approval
- Multi-signature or approval workflow

---

## Phase 4 — Observability & Reliability

Goal: Make system production operable

- Structured logging
- Monitoring (Prometheus / Grafana)
- Alerting system
- Health checks and failover strategy

---

## Phase 5 — Production Deployment

Goal: Deploy in real environment

- Kubernetes deployment
- Secure network segmentation
- Secret management system
- CI/CD pipeline

---

## Phase 6 — Advanced Features

Goal: Expand system capability

- Multi-asset support
- Cross-chain execution
- Risk scoring / AI validation layer
- Integration with financial systems

---

## Summary

The MVP proves:

--> Execution can be separated from orchestration

Future phases focus on:

--> Making that separation secure, verifiable, and production-ready
