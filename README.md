# OT-OCN 실행 통제 웹 데모

**검증 로직 실제 동작 · NDN 전달 모의 구현 · HSM 모의 서명 · 실제 자산 이동 없음**

## 웹 데모 실행

Python 3.12와 venv를 준비한 뒤 저장소 루트에서 다음 한 가지 명령을 실행합니다.

```bash
bash scripts/run_web.sh
```

브라우저에서 `http://localhost:8080`을 엽니다. 최초 실행 시 의존성을 설치하고 `.demo-state/`에 역할별 Ed25519 데모 키와 SQLite DB를 생성합니다. 이후에도 이 디렉터리를 유지해야 키·승인·완료 이력을 복구할 수 있습니다. 서버 종료는 Ctrl+C입니다. 포트는 `PORT`로 변경할 수 있습니다.

Docker에서는 다음 명령을 사용합니다. 기존 두 서비스 Compose 구성은 유지했습니다.

```bash
docker compose -f compose.web.yml up --build
```

Docker의 `web-demo-state` 볼륨을 보존하세요. 서비스는 호스트 루프백에만 게시합니다. 공개 배포는 이 작업 범위에 포함하지 않습니다. 외부 공개 시 반드시 `DEMO_ACCESS_KEY`를 안전한 환경 변수로 지정하고 TLS 역방향 프록시를 사용하세요. HTTP Basic의 비밀번호로 사용되며 사용자명은 임의입니다. API는 클라이언트별 분당 30회 생성 제한과 교차 사이트 호출 차단을 적용합니다. 이 제한은 단일 프로세스 데모용이며 분산 운영용 제한기가 아닙니다. 요청자 드롭다운은 데모 권한 선택이며 인증된 신원이 아닙니다.

## 다른 노트북에서 시연하기

데스크톱이나 이 클라우드를 켜 둘 필요는 없습니다. 노트북에 Git과 Python 3.12를 설치하고 병합된 `main`을 받으면 노트북 자체에서 실행됩니다.

처음 받는 경우:

```bash
git clone https://github.com/OpenEntry921/OTOCN_HSM_mvp.git
cd OTOCN_HSM_mvp
```

이미 저장소가 있다면 작업 내용을 보존한 뒤 `git switch main`과 `git pull --ff-only origin main`으로 업데이트합니다.

macOS / Linux:

```bash
bash scripts/run_web.sh
```

Windows PowerShell (Bash 불필요):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn webdemo.app:app --host 127.0.0.1 --port 8080
```

노트북 브라우저에서 `http://localhost:8080`을 엽니다. Windows에서 다시 실행할 때는 마지막 서버 실행 명령만 사용하면 됩니다. 노트북 최초 설치에는 인터넷이 필요합니다. 발표 전에 설치와 10종 시나리오를 한 번 확인하세요. 설치가 끝난 뒤에는 외부 서비스 없이 실행할 수 있습니다. macOS / Linux에서도 이미 설치한 환경은 `.venv/bin/python -m uvicorn webdemo.app:app --host 127.0.0.1 --port 8080`으로 바로 실행할 수 있습니다.

각 컴퓨터는 별도의 데모 키와 이력을 생성합니다. GitHub에는 개인키·SQLite DB·실행 이력이 올라가지 않으므로 노트북의 시연 이력은 새로 시작합니다. 데스크톱의 데모 비밀키를 Git에 추가할 필요가 없습니다. 기존 시연 이력을 유지하려면 같은 컴퓨터의 `.demo-state/`를 보존하세요.

## 사용 방법과 확인 근거

거래를 입력하고 실행 시나리오를 선택합니다. DUSD는 소수점 2자리, DETH는 8자리까지 허용하며 수량은 Decimal로 검사한 뒤 최소 단위 정수로 서명 대상에 결합합니다. 허용 수신 주소는 `wallet_A`, `wallet_B`, 수량 상한은 100,000입니다. 조회 전용 역할은 독립 승인에서 차단됩니다.

- 정상 거래: HSM 모의 실행 1회.
- 금액·주소 변조: 서명된 실행 토큰과 전달 거래 불일치, 실행 0회.
- 동일 요청 재전송: 같은 실행 ID를 Endpoint에 재전달하고 저장된 결과를 반환, 총 1회.
- 토큰 만료: 서버가 이미 만료된 짧은 데모 토큰을 발급하고 정상 검증 경로에서 차단, 0회.
- 서명 없는 Data·비신뢰 서명자: 실제 서명 입력 제거 또는 다른 키의 유효 서명을 적용하여 차단, 0회.
- Relay 침해: **Relay 키 탈취·요청 변조 가정, 독립 승인 서비스와 Endpoint는 정상**. 변조 거래로 Relay 토큰을 다시 서명하므로 Relay 검증은 통과하지만 원래 독립 승인과 불일치하여 차단, 0회.
- 정책 위반: 비허용 주소에 대한 요청을 Relay 정책에서 차단, 0회. 직접 상한 초과 입력도 정책에서 차단됩니다.
- 캐시 응답 재사용: SQLite에서 기존 결과 Data를 조회하고 서명 검증 후 재표시, 추가 실행 없이 총 1회.

장비를 클릭하면 해당 단계의 실제 데이터가 열립니다. SSE 이벤트에 따라 상태가 바뀌며 타이머로 결과를 결정하지 않습니다. 화면 새로고침 시 마지막 요청 ID와 서버 기록을 복구하며 최근 실행 선택, 원본 JSON, 실행별 다운로드를 지원합니다. SSE 재접속은 `Last-Event-ID` 이후 이벤트를 복구합니다. 연결 오류는 별도로 표시하며 성공으로 처리하지 않습니다. 단계 시각화는 실제 기록 순서를 75ms 간격으로 재생하며 통신 성능 측정 자료가 아닙니다.

## 구현과 경계

`webdemo/core.py`의 독립 승인 서비스는 자신의 개인키를 보유합니다. Relay는 독립 승인 공개키만 받습니다. Endpoint는 승인·Relay·요청 Data의 신뢰 공개키를 검증합니다. NDN 요청 Data와 결과 Data, HSM 모의 서명에도 각각 다른 키를 사용하며 생성 키는 커밋하지 않습니다. 전체 실행 토큰·개인키는 API, SSE, 감사 다운로드에 포함하지 않습니다.

NDN은 `Transport` 인터페이스 뒤의 **애플리케이션 수준 모의 구현**입니다. 실제 NDN 패킷·포워더와 호환되지 않습니다. Endpoint의 요청 Interest → Relay의 요청 Data, Relay의 결과 Interest → Endpoint의 결과 Data를 서로 다른 `/otocn/demo/requests/…`, `/otocn/demo/results/…` 이름 공간으로 처리합니다. 이름·콘텐츠 해시·서명자·FreshnessPeriod와 콘텐츠의 요청 ID·거래 해시 결합을 검증합니다. 신뢰하지 않는 키의 수학적으로 유효한 서명도 거부합니다. Interest Nonce는 화면용 패킷 식별자이며 영속 실행 ID와 다릅니다. 캐시와 FreshnessPeriod는 거래 만료나 중복 방지 수단이 아닙니다.

SQLite의 실행 ID 고유 제약, 승인 ID 고유 제약, `BEGIN IMMEDIATE`로 하나의 실행 권한을 확보합니다. 완료된 요청은 서명·신뢰·거래 결합을 다시 확인한 후 만료된 재요청에도 저장 결과만 반환하고(새 실행 권한은 부여하지 않음), 처리 중 요청은 processing을 반환하며, 거래 충돌과 승인 재사용은 차단합니다. HSM 모의 부수효과 기록과 완료 결과는 한 DB 트랜잭션에서 저장됩니다. 실행 횟수는 `hsm_effects` 테이블에서 계산합니다. **실행기는 Endpoint만 호출**합니다. 처리 권한 획득 이후 장애로 남은 processing 기록은 자동 재실행하지 않으며 운영자 조사가 필요합니다. 실제 HSM·블록체인은 DB 트랜잭션에 포함할 수 없으므로 별도의 작업 저널·멱등성·상태 조정·장애 복구 설계가 필요합니다.

동일 호스트의 데모는 물리적 격리를 제공하지 않습니다. NDN 전달·HSM 자산 서명·자산 이동은 실제가 아닙니다. HSM 모의 서명값은 실제 거래 해시나 실제 자산 서명이 아닙니다. 일반 SQLite 감사 기록을 위변조 불가능한 증거로 취급하지 않습니다. 아래 기존 CLI/두 서비스 MVP는 비교·호환성용으로 유지했으며 웹 데모의 독립 승인·영속 실행 통제는 `webdemo` 경로에서 제공됩니다.

## 검증

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

Python 3.12에서 기존 12개를 포함한 54개 테스트 통과. 10종 시나리오, 잘못된 입력, 서명·대상 서비스·서버 만료 검사, 승인 누락, 순차·동시 중복, 실행 ID 충돌, 승인 재사용, 재시작, 캐시, 모의 부수효과 롤백, SSE 복구·다운로드·시스템 오류 구분·접근 보호를 검증합니다. Chromium 브라우저에서 10개 시나리오의 결과·단계 상태·감사 행을 백엔드 데이터와 대조했고, SSE 기록 수신, 새로고침 복구, 390px 모바일 가로 넘침 없음, 전송 실패·SSE 연결 실패 시 성공 표시 방지를 확인했습니다.

선택적 브라우저 회귀 검증은 웹 서버를 8080 포트에서 실행한 뒤 Playwright와 Chromium이 설치된 환경에서 `node tests/webdemo.browser.cjs`로 실행합니다. `CHROMIUM_PATH`로 Chromium 실행 파일을 지정할 수 있습니다. 이 검증은 실제 데모 실행 기록을 생성하며 스크린샷을 `/tmp/otocn-desktop.png`, `/tmp/otocn-mobile.png`에 저장합니다.

Docker Compose 구문 검증을 완료했습니다. 이 클라우드의 Docker 빌드 네트워크는 DNS/프록시 호스트를 해석하지 못해 일반 온라인 `pip install` 단계가 실패했습니다. 호스트에서 TLS 검증을 유지해 다운로드한 wheel을 사용한 임시 오프라인 빌드로 비루트 컨테이너 실행을 확인했습니다. 컨테이너 내부 HTTP 요청으로 정상·재전송·캐시·Relay 침해·무서명·비신뢰 서명자를 검증했고, 컨테이너 재시작 후 결과와 실행 횟수도 유지됐습니다. 일반 온라인 빌드는 Docker 빌드 환경에서 PyPI 접근이 가능해야 합니다. Python 3.9 호환성은 기존 MVP의 설명이며 새 웹 구성은 Python 3.12를 기준으로 검증합니다.

---

# Execution-Separated Custody MVP

A demo-focused **MVP prototype** that shows **execution authority separation**: application servers request critical actions, but they do not directly perform critical execution.

This repository demonstrates a simple Relay + Endpoint flow for **policy-based execution control**, **independent endpoint verification**, and **auditability**. It is intentionally small and direct so that the execution boundary is easy to understand in a demo.

> Status: MVP prototype. Not production-ready.
> Runtime: Python 3.9 compatible.
> Tested on Python 3.9.
> Typing: avoids Python 3.10+ only typing syntax such as `str | None`; use `Optional[...]` / `Union[...]` for Python 3.9 compatibility.

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

The token expiration time is displayed both as a Unix timestamp and as a human-readable ISO datetime for demo clarity.

Example token issuance output:

```text
EXECUTION TOKEN ISSUED: eyJh... (expires_at=1779979067, expires_at_iso=2026-05-28T14:45:00Z)
```

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
- audit event should be created,
- token issuance output should include `expires_at`,
- token issuance output should include `expires_at_iso`,
- token-issued audit events should include `expires_at_iso`.

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
