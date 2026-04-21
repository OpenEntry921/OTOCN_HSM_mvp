# Threat Model

## Scope

This MVP considers risks related to execution control and authority separation.

The model focuses on reducing structural execution risks rather than providing a complete production security model.

---

## Threats Considered

## 1. Unauthorized Execution Attempts

Risk:

A request attempts to trigger execution without satisfying control conditions.

Mitigation:

- policy validation required  
- execution token required  
- independent endpoint verification required

---

## 2. Server-Side Logic Abuse

Risk:

A coordination component is misused or compromised.

Mitigation:

- Relay does not directly perform execution  
- Endpoint performs independent verification  
- execution requires multiple conditions

---

## 3. Single-Layer Execution Authority Risk

Risk:

One component alone can trigger sensitive execution.

Mitigation:

- coordination and execution authority are separated  
- execution requires layered approval path

---

## Out of Scope (Current MVP)

The following are not fully addressed in the current prototype:

- HSM compromise scenarios  
- transport-layer attacks  
- replay attacks  
- distributed failover scenarios  
- production-grade insider threat models

These are planned for future phases.

---

## Security Goal

Primary goal:

Reduce structural execution risk through authority separation.

This is the core security objective of the current MVP.
