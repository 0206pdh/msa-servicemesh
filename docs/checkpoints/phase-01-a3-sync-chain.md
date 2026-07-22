# Checkpoint — `phase-01-a3-sync-chain`

- Status: validated
- Updated at: 2026-07-22
- Related Phase: [Phase 1](../phases/phase-01-workload-implementation.md)

## 목표

각 hop이 HTTP 경계를 통과하고 절대 deadline, ID와 trace를 다음 hop으로 전파하는 Sync Chain을 구현한다.

## 완료 조건

- [x] 0~16 hop
- [x] 절대 deadline 전파와 hop 전후 검사
- [x] 504 deadline 결과와 진행 중 virtual task 취소 경계
- [x] hop별 HTTP/trace 경계
- [x] checksum과 completed hop
- [x] Gradle/Compose E2E

## 검증 결과

- Gateway → Orchestrator → Workload 내부 HTTP 3 hop: `COMPLETED`, `completedHops=3`
- deadline 만료 요청: HTTP 504와 `DEADLINE_EXCEEDED`
- 최종 Kubernetes 측정에서는 동일 workload 이미지를 role별 Deployment로 분리한다. Compose의 self-hop은 개발 E2E 전용이다.
