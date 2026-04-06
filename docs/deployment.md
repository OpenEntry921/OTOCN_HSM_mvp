# Deployment Notes

## Purpose

This document outlines the gap between the local demo environment and a review-ready deployment target.

## Current local deployment model

The MVP runs as two FastAPI services behind Docker Compose:

- `relay` on port `8000`
- `endpoint` on port `8001`

The stack is intended for local review, internal demos, and architecture walkthroughs.

## What a more credible pre-production deployment would require

### Network controls

- private network segment between relay and endpoint,
- inbound filtering so endpoint is not publicly reachable,
- mutual TLS for service-to-service communication.

### Secret handling

- environment variables replaced by secret manager injection,
- signing key managed outside application containers,
- separate operational secret rotation policy.

### Audit and retention

- audit records written to append-only external storage,
- immutable retention policy,
- centralized search and alerting.

### Observability

- structured logs,
- request correlation IDs,
- metrics export,
- execution denial alerting.

### Runtime hardening

- non-root containers,
- pinned image versions,
- signed build artifacts,
- vulnerability scanning in CI.

## Suggested next deployment targets

1. Docker Compose for local demonstrations.
2. Single-node hardened VM for technical review.
3. Kubernetes or Nomad deployment only after transport and secrets controls are upgraded.
