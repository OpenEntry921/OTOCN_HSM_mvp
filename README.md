# HSM MVP (Relay–Endpoint Architecture Prototype)

This project demonstrates a **secure transaction execution architecture**
based on the separation of responsibilities between a **relay layer**
and an **execution endpoint layer**.

The goal is to show how execution authority can be isolated from
request orchestration, reducing systemic risk in financial or
sensitive transaction systems.

---

## Core Idea

Traditional systems allow application servers to directly execute
sensitive operations.

This architecture enforces:

- Relay = request validation + orchestration
- Endpoint = execution authority (isolated)

The server **never directly executes critical actions

---

## Architecture Overview

Client → Relay → Endpoint → Execution  
             ↓  
         Audit Log  

### Components

- **Relay**
  - Validates request
  - Applies policy checks
  - Signs execution token
  - Records audit log

- **Endpoint**
  - Verifies token
  - Executes request
  - No external exposure

- **Shared**
  - Common schemas
  - Crypto utilities

---

## Tech Stack

- Python 3.10
- FastAPI
- Docker / Docker Compose

---

## Getting Started

### 1. Clone repository

```bash
git clone <your-repo-url>
cd HSM_mvp
```

### 2. Environment setup

```bash
cp .env.example .env
```

### 3. Run services

```bash
docker compose up --build
```

### 4. Verify services

- Relay: http://localhost:8000/health
- Endpoint: http://localhost:8001/health

---

## Example Flow

1. Client sends request to Relay
2. Relay validates and signs token
3. Relay forwards to Endpoint
4. Endpoint verifies token and executes
5. Result returned to client

---

## Project Structure

HSM_mvp/
├── relay/
├── endpoint/
├── shared/
├── docs/
├── docker-compose.yml

---

## Limitations (Current MVP Scope)

This project is a **functional MVP prototype** designed to demonstrate
architectural separation.

The following production-grade features are intentionally not implemented:

- No real HSM integration (execution is simulated)
- No mutual TLS (mTLS) between services
- No replay attack protection
- No append-only or tamper-proof audit storage
- No operator authentication or RBAC

These features are planned for future development.

---

## Roadmap

See: `docs/roadmap.md`

---

## Documentation

- Architecture: `docs/architecture.md`
- Flow: `docs/flow.md`
- API: `docs/api.md`

---

## Design Philosophy

This project focuses on:

- Execution isolation
- Minimal trust assumptions
- Clear separation of responsibilities

---

## Status

- MVP prototype (development stage)
- Not production-ready
