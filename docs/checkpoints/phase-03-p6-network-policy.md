# Checkpoint — `phase-03-p6-network-policy`

- Status: completed
- Owner: dohyun
- Started at: 2026-07-22
- Completed at: 2026-07-22
- Related Phase: [Phase 3](../phases/phase-03-platform-foundation.md)
- Decision: [ADR-0012](../decisions/0012-workload-network-isolation.md)
- Evidence: [NetworkPolicy 검증](../evidence/infrastructure/2026-07-22-network-policy-validation.md)

## 완료 체크

- [x] 기본 ingress/egress deny
- [x] DNS, 서비스 체인, Kafka 최소 허용
- [x] Prometheus scrape와 OTel export 허용
- [x] Cilium Gateway `reserved:ingress` 허용
- [x] 외부 E2E 전체 재검증
- [x] 임의 Pod 직접 접근 차단 검증
- [x] Helm lint와 server dry-run
- [x] 실패 원인과 Hubble identity 기록

## 다음 재개 지점

1. Phase 2 Kubernetes adapter를 현재 Helm profile에 연결한다.
2. telemetry/headroom/cleanup Gate를 검증한다.
3. 로그와 trace의 experiment run ID completeness를 검증한다.
