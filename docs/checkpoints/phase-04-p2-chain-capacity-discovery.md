# Checkpoint — `phase-04-p2-chain-capacity-discovery`

- Status: in-progress
- Owner: dohyun
- Started at: 2026-07-23
- Related Phase: [Phase 4](../phases/phase-04-no-mesh-baseline.md)
- Policy: [ADR-0014](../decisions/0014-measurement-repetition-and-load-policy.md)

## 조건

- NO_MESH
- SYNC_CHAIN 3 hop
- payload 1 KiB
- hop delay 1 ms
- target RPS: 10부터 2배 증가
- point별 warm-up 120초, 측정 180초
- 최초 실패 후 최대 4회 binary refinement

## 완료 체크

- [x] resume 가능한 capacity discovery 실행기
- [x] point별 runner artifact와 Gate 보존
- [x] p99 2× low-load 추가 판정
- [ ] geometric search 최초 실패점
- [ ] binary refinement interval ≤ 10%
- [ ] usable capacity `C*` 승인
- [ ] 10/30/60/80% 절대 RPS 확정

## 다음 재개 지점

`results/phase4-chain-capacity/discovery.json`을 읽고 마지막 미실행 RPS부터 자동 재개한다.
