# Checkpoint — `phase-04-p2-chain-capacity-discovery`

- Status: measured
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
- [x] geometric search 최초 실패점: 40 RPS
- [x] binary refinement interval ≤ 10%: 28~30 RPS, 7.14%
- [x] usable capacity `C*` 승인: 28 RPS
- [x] 10/30/60/80% 절대 RPS 확정: 3/8/17/22 RPS

## 결과

- low-load p99: 41.945 ms at 10 RPS
- 마지막 통과점: 28 RPS, 28.001 achieved RPS, error 0%, p99 69.087 ms
- 최초 성능 실패점: 30 RPS, p99 118.975 ms (`2 × low-load p99` 초과)
- 최종 interval: 28~30 RPS, relative width 7.14%
- 무효 27 RPS 실행 2건은 삭제하지 않고 보존했으며 용량 경계 계산에서 제외했다.
- Tempo OOM과 telemetry 누락을 수정한 뒤 clean source에서 27/28 RPS를 재측정했다.
- Evidence: [2026-07-23 canonical chain capacity](../evidence/performance/2026-07-23-canonical-chain-capacity.md)

## 다음 재개 지점

승인된 절대 부하 3/8/17/22 RPS를 사용해 canonical SYNC_CHAIN No Mesh 정식 반복 측정을 시작한다.
