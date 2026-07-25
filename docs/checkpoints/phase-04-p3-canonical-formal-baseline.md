# Checkpoint — `phase-04-p3-canonical-formal-baseline`

- Status: measured
- Owner: dohyun
- Started at: 2026-07-23
- Related Phase: [Phase 4](../phases/phase-04-no-mesh-baseline.md)
- Policy: [ADR-0014](../decisions/0014-measurement-repetition-and-load-policy.md)

## 조건

- NO_MESH
- SYNC_CHAIN 3 hop, payload 1 KiB, fixed hop delay 1 ms
- nominal/high/near-saturation: 8/17/22 RPS
- warm-up 180초
- 최소 20,000 request와 1% 일정 여유: 2,525/1,189/919초
- pre-allocated/max VUs: 모든 정식 조건에서 128 고정
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
- [x] 22 RPS에서 관측된 2.61초 tail과 조건 간 공정성을 위해 모든 정식 조건에 128 VU 고정
- [x] 최종 128 VU fingerprint만 통계에 포함하고 이전 설정은 `SUPERSEDED_CONFIG_FINGERPRINT`로 보존
- [x] session 1 첫 유효 block 수집
- [x] session 2 이상에서 조건별 유효 run 10회 확보
- [x] 세션 재시작 시 valid run 회계가 0으로 리셋되는 스케줄러 버그 수정 (commit `2e8faf4`)
- [x] 상대 half-width 단일 기준으로는 15회에도 수렴 불가함을 확인하고 절대 기준 병행 정책 도입 (ADR-0023)
- [x] bootstrap 95% CI 정밀도 판정 — high/near-saturation `STOP_PRECISION_REACHED`, nominal `INCONCLUSIVE_MAX_RUNS`(p99만 미달)
- [x] canonical No Mesh baseline 승인 — 결과와 한계는 Evidence에 명시

## 최종 결과

| 조건 | valid run | 판정 | p95 median | p99 median |
|---|---:|---|---:|---:|
| nominal (8 RPS) | 15/15 | `INCONCLUSIVE_MAX_RUNS` | 28.21 ms | 36.56 ms |
| high (17 RPS) | 10/15 | `STOP_PRECISION_REACHED` | 25.20 ms | 30.77 ms |
| near-saturation (22 RPS) | 13/15 | `STOP_PRECISION_REACHED` | 33.79 ms | 46.40 ms |

nominal은 p99 절대 half-width(9.08ms)가 8ms 기준을 8.9% 초과해 상한까지 반복했지만 미달로 종료했다.
이는 실패가 아니라 ADR-0014가 정의한 정식 결과이며, 이후 Mesh profile 비교에서 nominal 조건의 p99는
더 넓은 신뢰구간을 감안해 해석해야 한다.

## 다음 재개 지점

Phase 4는 완료됐다. 다음은 Phase 5(Istio Sidecar)로, 승인된 No Mesh baseline(이 체크포인트)을 진입
조건으로 사용한다.

최종 Evidence: [2026-07-25 canonical baseline final](../evidence/performance/2026-07-25-canonical-baseline-final.md)
첫 유효 block Evidence: [2026-07-24 session 1 block 1](../evidence/performance/2026-07-24-canonical-baseline-session-01-block-01.md)
