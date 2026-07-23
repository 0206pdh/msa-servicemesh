# Checkpoint — `phase-04-p3-canonical-formal-baseline`

- Status: in-progress
- Owner: dohyun
- Started at: 2026-07-23
- Related Phase: [Phase 4](../phases/phase-04-no-mesh-baseline.md)
- Policy: [ADR-0014](../decisions/0014-measurement-repetition-and-load-policy.md)

## 조건

- NO_MESH
- SYNC_CHAIN 3 hop, payload 1 KiB, fixed hop delay 1 ms
- nominal/high/near-saturation: 8/17/22 RPS
- warm-up 180초
- 최소 20,000 request: 2,500/1,177/910초
- seeded randomized complete block, seed 42
- 조건별 최소 10회, 최대 15회
- session당 최대 5 block, 최소 2 session
- run 사이 cooldown 120초

3 RPS low point는 sanity/linearity 전용이며 정식 cross-profile 반복에서 제외한다.

## 완료 체크

- [x] 재부팅 후 Kubernetes/Cilium/MetalLB/observability/workload 복구 Gate
- [x] Prometheus target 7, Tempo trace, Hubble 3/3 검증
- [x] resume 가능한 randomized-block 실행기
- [x] 8 RPS에서 20,000 request를 만족하도록 최대 측정 시간을 2,700초로 조정
- [x] VM 재부팅 이전 restart count는 허용하고 측정 중 증가분만 무효화하도록 Gate 수정
- [ ] session 1 유효 block 수집
- [ ] session 2 이상에서 조건별 유효 run 10회 확보
- [ ] bootstrap 95% CI 정밀도 판정
- [ ] canonical No Mesh baseline 승인

## 다음 재개 지점

`results/phase4-chain-baseline/state.json`과 조건별 `repeat-*`를 읽고 다음 미실행 repeat부터 재개한다.
