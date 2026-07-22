# Checkpoint — `phase-03-p5-no-mesh-workload`

- Status: completed
- Owner: dohyun
- Started at: 2026-07-22
- Completed at: 2026-07-22
- Related Phase: [Phase 3](../phases/phase-03-platform-foundation.md)
- Evidence: [No-mesh Workload 배포](../evidence/infrastructure/2026-07-22-no-mesh-workload-deployment.md)

## 완료 체크

- [x] GHCR 이미지 5개 Public 전환과 anonymous Kubernetes pull
- [x] digest-pinned 공통 Helm chart와 no-mesh values
- [x] Gateway/Orchestrator/Workload/Producer/Worker/Kafka 배포
- [x] Cilium Gateway와 MetalLB 영구 주소
- [x] chain/fan-out/payload/async 외부 E2E
- [x] ServiceMonitor 7개 Java target `up=1`
- [x] Kafka async worker completed metric
- [x] Kafka bootstrap DNS 설정과 numeric non-root UID/GID 차트 반영

## 다음 재개 지점

1. NetworkPolicy 기본 거부와 최소 허용 규칙을 적용한다.
2. Phase 2 Kubernetes adapter의 telemetry/headroom/cleanup Gate를 검증한다.
3. no-mesh 반복 측정 전 log/trace completeness를 검증한다.
