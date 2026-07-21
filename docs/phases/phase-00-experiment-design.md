# Phase 0 — 실험 설계

## 목적

측정 전에 질문, 비교 대상, 고정 조건, 지표와 무효화 규칙을 동결한다. 결과를 본 뒤 성공 기준을 바꾸지 않는다.

## 입력과 범위

- Profile: `NO_MESH`, `SIDECAR`, `AMBIENT`, `WAYPOINT`
- Scenario: `SYNC_CHAIN`, `FAN_OUT`, `ASYNC_PIPELINE`, `PAYLOAD`, `MIXED_RESOURCE`
- Java 25 Benchmark Workload와 온프레미스 VMware Kubernetes
- 측정 경로 밖의 Experiment Runner, k6, 선택적 Web Console

## 작업

1. 가설마다 독립 변수 하나, 기대 지표, 회귀 지표와 기각 조건을 기록한다.
2. 노드, Pod 배치, 이미지 digest, JVM, requests/limits, 부하와 수집 설정의 고정 조건을 정의한다.
3. warm-up, 측정 시간, 반복 횟수, 실행 순서 무작위화와 cooldown을 정한다.
4. 부하 발생기/수집기 포화, 시간 동기화, 재시작, 설정 drift를 무효화 조건으로 정한다.
5. OpenAPI, 이벤트, run manifest와 result schema를 lint한다.

## 산출물과 Evidence

- 프로젝트 질문, ADR-0020~0022, API와 Schema
- A0 체크리스트와 foundation Evidence
- 단위·분위수·결측값 처리·반복 비교 규칙

## Gate

- 진입: 없음
- 종료: 계약 lint, 문서 링크, 현재 소스의 legacy 도메인 검사 통과
- 금지: 실제 결과가 없는 상태에서 특정 Mesh가 우월하다고 주장
