# Checkpoint — `phase-02-experiment-runner`

- Status: validated-local
- Updated at: 2026-07-22
- Related Phase: [Phase 2](../phases/phase-02-experiment-automation.md)

## 완료 조건

- [x] immutable JSON ExperimentSpec 검증
- [x] PLANNED → WARMING_UP → RUNNING → COLLECTING → COMPLETED/FAILED
- [x] k6 smoke/baseline/load/stress/spike/soak profile
- [x] config fingerprint, Git, adapter와 실행 환경 Ground Truth
- [x] 원본 k6/Prometheus snapshot, summary, report 생성
- [x] 동일 spec 3회 동일 artifact 구조
- [x] 기존 Evidence 디렉터리 overwrite 거부
- [x] Compose 실행을 측정 부적격 `INVALID`로 자동 표기
- [ ] VMware Kubernetes에서 telemetry/headroom/fault cleanup gate 실측 — Phase 3 환경 구축 후 수행

## 판정

Phase 2 자동화 코드는 로컬에서 검증됐다. 생성된 로컬 수치는 Mesh 성능 Evidence가 아니며 `NON_MEASUREMENT_COMPOSE_ADAPTER`로 무효화된다. Phase 3 이후 `kubernetes` adapter의 실환경 Ground Truth가 채워져야 측정 적격이다.
