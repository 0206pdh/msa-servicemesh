# Checkpoint — `phase-03-p7-kubernetes-runner-gates`

- Status: in-progress
- Owner: dohyun
- Started at: 2026-07-23
- Related Phase: [Phase 3](../phases/phase-03-platform-foundation.md)
- Decision: [ADR-0013](../decisions/0013-kubernetes-run-validity-gates.md)
- Evidence: [Kubernetes runner dry-run](../evidence/infrastructure/2026-07-23-kubernetes-runner-dry-run.md)

## 완료 체크

- [x] k6 values parser 결함 수정과 unit test
- [x] Kubernetes pre/post snapshot과 restart 0 Gate
- [x] Prometheus resource/headroom/window Gate
- [x] Loki Pod log collection과 run marker
- [x] Tempo trace marker와 Hubble flow export
- [x] load-generator 분리와 Docker CPU sampling
- [x] cleanup/fault/dirty tree 자동 무효화
- [x] startupProbe와 깨끗한 Pod restart 0 기준점
- [x] dirty-tree dry-run에서 모든 환경 Gate 통과
- [ ] 검증 스냅샷 commit
- [ ] clean-tree final dry-run `COMPLETED`

## 다음 재개 지점

1. 전체 검증 후 변경을 commit한다.
2. 새 run ID로 clean-tree final dry-run을 실행한다.
3. Phase 3 exit Gate를 판정한다.
