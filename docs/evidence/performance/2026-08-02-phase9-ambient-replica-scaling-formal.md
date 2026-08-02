# Phase 9 개선 실험 2 — Ambient replica 확장 latency 저하 정식 확인 (ADR-0029)

- Completed: 2026-08-02 (Asia/Seoul)
- Scope: [ADR-0029](../../decisions/0029-phase9-ambient-replica-scaling-formal-experiment.md)
- Hypothesis under test: ADR-0027의 방향성 관찰("Ambient/ztunnel latency가 replica 수 증가에 따라
  나빠진다", 3회 반복, 신뢰구간 없음)이 정식 반복측정에서도 재현되는가
- 독립 변수: orchestrator-service replica 수 — 1(재사용) vs 4(신규 측정)
- 조건: nominal(8 RPS) 하나, SYNC_CHAIN 3-hop, Ambient profile
- replica=1: Phase 6 canonical(`results/phase6-ambient-baseline-nominal`, Istio 1.30.3, 10회
  `STOP_PRECISION_REACHED`) 재사용
- replica=4: 신규 측정(Istio 1.29.6), 10회 `STOP_PRECISION_REACHED`

## 알려진 제약: Istio 버전 confound (ADR-0029에서 사전에 수용하기로 결정)

Phase 6 canonical(replica=1)은 Istio 1.30.3에서, 이번 replica=4 측정은 Phase 7 Waypoint 버전 재시도로
재설치된 Istio 1.29.6에서 진행됐다. ADR-0029 자체가 이 confound를 사전에 인지하고 "재현이 필요할 만큼
버전 차이가 결론을 뒤집을 가능성은 낮다"는 판단으로 감수하기로 결정한 상태였다(ADR-0028과 동일한 원칙).
아래 결과, 특히 예상 밖으로 크게 나온 ztunnel 메모리 차이는 이 confound의 영향을 받았을 가능성을 배제할
수 없다.

## Result

| Metric | replica=1 (Phase 6, before) | replica=4 (신규, after) | Diff (after−before) | 95% CI | Significant |
|---|---:|---:|---:|---|---|
| throughputRps | 8.0006 | 8.0006 | -0.0000 | [-0.0003, 0.0003] | No |
| p95Ms | 30.08 ms | 32.63 ms | +2.55 ms | [-0.63, 5.50] | No |
| p99Ms | 39.50 ms | 47.40 ms | **+7.90 ms (+20%)** | [1.31, 14.60] | **Yes** |
| cpuCoreSecondsPerRequest (app) | 0.0751 | 0.0792 | +0.0040 | [-0.0094, 0.0199] | No |
| ztunnelCpuCoreSecondsAbsolute | 82.44 | 83.16 | +0.71 | [-1.65, 2.48] | No |
| ztunnelMemoryPeakBytes | 16.9 MB | 30.25 MB | **+13.3 MB (+79%)** | [11.4M, 14.2M] | **Yes** |
| networkBytesPerRequest | 21,653 B | 22,415 B | **+761 B (+3.5%)** | [715, 813] | **Yes** |

## 해석: 방향은 확인됐지만 크기는 다르게 나왔다

**p99 latency 저하는 정식으로 확인됐다.** replica 1→4에서 p99가 39.5ms→47.4ms로 유의하게(+20%)
나빠졌다 — ADR-0027의 방향성 관찰과 같은 방향이다. 다만 **크기는 크게 다르다**: ADR-0027의 3회 반복
방향성 데이터는 p99가 51.0ms→99.5ms로 거의 2배(+95%) 나빠지는 것으로 관찰됐는데, 이번 정식 10회
측정에서는 +20%에 그쳤다. p95는 이번에 아예 유의하지 않았다(diff +2.55ms, CI가 0을 포함) — ADR-0027의
방향성 데이터에서는 p95도 34.3→68.4ms로 크게 나빠지는 것으로 관찰됐던 것과 다르다.

이 크기 차이는 다음 요인들의 조합일 수 있다: (1) ADR-0027은 180초 짧은 창(capacity-discovery 수준)을
썼고 이번은 정식 2,525초 전체 창을 썼다 — 측정 방법 자체가 다르다. (2) Istio 버전이 다르다(1.30.3 vs
1.29.6). (3) ADR-0027은 3회 반복이라 우연히 큰 값이 뽑혔을 수 있다(신뢰구간이 없으니 이 가능성을 배제할
수 없었다). **결론: "replica가 늘면 ztunnel을 통한 p99 latency가 나빠진다"는 방향 자체는 이제 정식
신뢰구간을 갖춘 결론이지만, "거의 2배"라는 초기 관찰의 크기는 재현되지 않았다 — 방향성 연구 특유의
과대추정 위험을 그대로 보여주는 사례로 기록한다.**

**ztunnel 메모리가 유의하게 늘어난 것은 ADR-0027의 핵심 관찰("메모리는 거의 불변")과 정면으로 배치된다.**
ADR-0027은 15.8MB→16.1MB(+2%)로 거의 안 변한다고 봤는데, 이번 정식 측정은 16.9MB→30.25MB(+79%)로
크게 늘었다. 두 결과가 이렇게까지 다른 것은 방향성 연구의 표본 부족만으로는 설명하기 어렵다 — Istio
버전 차이(위 confound)나 측정 창 길이 차이(180초 vs 2,525초, ztunnel의 연결 상태 추적이 오래 쌓일수록
늘어나는 것일 가능성)가 더 유력한 후보로 보이지만, 이 데이터만으로는 어느 쪽인지 확정할 수 없다.
**이 결과는 "확정된 결론"이 아니라 "추가 조사가 필요한 신호"로 기록한다** — 같은 Istio 버전에서
짧은/긴 측정 창을 둘 다 시도해보는 것이 다음 단계로 적절하다.

**ztunnel CPU와 app CPU-per-request는 이번엔 유의하지 않았다** — ADR-0027이 관찰한 "ztunnel CPU
+32%"는 정식 측정에서 재현되지 않았다(diff +0.71 core-s, CI가 0을 포함). Network bytes/request는
작지만(+3.5%) 유의하게 늘었다 — 방향성 연구에서는 확인하지 않았던 지표다.

## 종합 판단

Hypothesis 2(ztunnel latency가 replica 확장에 취약할 수 있다)는 **부분적으로만 확인됐다** — p99
latency 저하 방향은 정식 신뢰구간으로 확인됐지만, 그 크기는 방향성 연구가 시사했던 것보다 훨씬 작았고
(2배 → 20%), ztunnel CPU 증가는 재현되지 않았으며, ztunnel 메모리는 오히려 방향성 연구의 결론과
반대로 유의하게 증가했다. **방향성 연구(ADR-0027)의 역할과 한계를 정확히 보여주는 사례다** — 빠른
3회 반복이 "무언가 있다"는 신호는 정확히 잡아냈지만("p99가 나빠진다"), 그 신호의 정확한 크기나 다른
지표(메모리)에 대한 결론은 정식 반복 없이는 신뢰할 수 없었다.

## Evidence integrity

- replica=4 canonical run: `results/phase9-ambient-replica4-nominal/repeat-{05,06,07,09,10,11,...}`
  (10개 유효 run, `STOP_PRECISION_REACHED`)
- 비교 산출물: `results/phase9-comparison/nominal-replica1-vs-replica4.json` — SHA-256
  `942563c15f23909ad59a2ec6a2856151cff0fc193dcfa8144f6525d404bd3caa`
- replica=1(before): 기존 Phase 6 canonical Evidence 재사용, 새 측정 없음

## Limits recorded for downstream use

- Istio 버전 confound(1.30.3 vs 1.29.6)를 배제하지 못했다 — 이 프로젝트 안에서 이미 두 번째로 나온
  같은 종류의 confound다(ADR-0028도 동일). Phase 11 최종 보고서에서 이 클러스터의 측정 이력 전반에
  버전 변경이 있었다는 것을 명시해야 한다.
- 측정 창 길이(180초 vs 2,525초)가 결과에 미치는 영향을 분리하지 못했다 — 같은 조건에서 창 길이만
  다르게 한 대조 실험은 하지 않았다.
- 이 실험은 nominal(8 RPS) 부하 하나, replica 1과 4 양 극단만 다룬다 — replica 2에서의 거동이나
  다른 부하 조건에서의 재현성은 확인하지 않았다.

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 43 passed
- replica=4: 10/10 valid runs `COMPLETED`, `STOP_PRECISION_REACHED`
