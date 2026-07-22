# Checkpoint — `phase-01-a2-workload-target`

- Status: validated
- Updated at: 2026-07-22
- Related Phase: [Phase 1](../phases/phase-01-workload-implementation.md)
- Contract: [Data Plane API](../../contracts/openapi/mesh-benchmark-api.yaml)

## 목표

동일 seed/config에서 재현되며 자원 상한을 강제하는 `/api/v1/workloads/target`을 구현한다.

## 완료 조건

- [x] fixed/normal/exponential delay
- [x] deterministic error selection
- [x] bounded CPU/memory/blocking I/O
- [x] deterministic response checksum
- [x] 실제 작업량과 결과 metric
- [x] 경계값/재현성/오류 계약 테스트
- [x] Compose API E2E와 Evidence

## 다음 재개 지점

- A3 Sync Chain contract와 deadline 전파 구현

## 검증

- Workload Gradle test 통과
- 동일 seed/config checksum 일치, SHA-256 64자리
- fixed delay 1ms, memory 1024 byte 적용값 확인
- `meshperf_workload_executions_total` 노출
- Compose workload-service healthy
