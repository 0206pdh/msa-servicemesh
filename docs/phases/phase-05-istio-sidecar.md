# Phase 5 — Istio Sidecar

## 목적

Sidecar가 제공하는 기능과 Pod별 proxy 비용을 No Mesh 기준선과 동일 조건에서 측정한다.

## 작업

1. Istio/control plane 버전, injection, mTLS mode와 Envoy 설정을 snapshot한다.
2. proxy request/limit, concurrency, startup과 readiness 영향을 기록한다.
3. Workload retry/timeout 소유권을 baseline과 동일하게 유지한다.
4. Scenario와 replica 증가에 따른 app/proxy CPU·memory·latency를 분리한다.

## 검증과 Gate

- 실제 traffic이 Sidecar를 통과하고 mTLS가 적용됐음을 확인
- No Mesh와 paired block으로 core 조건 10~15회, CI와 절대/상대 overhead 보고
- 기능 차이가 있는 비교는 별도 실험으로 표시
- 진입: 승인된 No Mesh baseline
- 종료: Sidecar 비용과 기능 Evidence `measured`
