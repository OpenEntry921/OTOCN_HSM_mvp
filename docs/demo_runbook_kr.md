# 데모 실행 Runbook — Execution-Separated Custody MVP

## 목적

이 데모는 애플리케이션 서버가 민감한 실행 권한을 직접 갖지 않고, Relay와 Endpoint를 분리해 실행을 통제하는 구조를 보여준다.

핵심 메시지:

- **execution authority separation**: 실행 권한 분리
- **policy-based execution control**: 정책 기반 실행 통제
- **independent endpoint verification**: Endpoint 독립 검증
- **auditability**: 감사 가능성
- **future HSM integration**: 향후 HSM 연동 가능 구조

## 실행 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 데모 실행

```bash
./scripts/run_demo.sh
```

## 확인할 출력

정상 요청에서는 아래 흐름을 확인한다.

```text
REQUEST RECEIVED
POLICY PASSED
EXECUTION TOKEN ISSUED
ENDPOINT VERIFICATION SUCCESS
EXECUTION APPROVED
AUDIT EVENT CREATED
```

변조 또는 비정상 요청에서는 아래 흐름을 확인한다.

```text
TAMPERED REQUEST DETECTED
ENDPOINT VERIFICATION FAILED
EXECUTION REJECTED
AUDIT EVENT CREATED
```

## 감사 로그 확인

데모 마지막에 `logs/demo_audit.log` 내용이 출력된다.

확인 포인트:

- 요청 수신 기록
- 정책 판단 기록
- 토큰 발급 기록
- Endpoint 검증 성공/실패 기록
- 실행 승인 또는 거부 기록

## 테스트 실행

```bash
./scripts/test_demo.sh
```

테스트는 정상 정책 통과, 토큰-요청 바인딩, amount 변조, destination 변조, 만료 토큰, 감사 로그 생성을 검증한다.

## 현재 구현 범위

- Relay / Endpoint 분리
- 정책 평가
- 요청 바인딩된 실행 토큰
- Endpoint 독립 검증
- 실행 승인/거부
- JSONL 감사 로그

## 아직 구현하지 않은 범위

- 실제 블록체인 서명
- 실제 HSM 연동
- mTLS
- replay 방지용 영속 nonce 저장소
- 운영자 인증/RBAC
- 변조 방지 감사 저장소

이 저장소는 데모 중심 **MVP prototype**이며 실제 자산 실행에 사용하면 안 된다.
