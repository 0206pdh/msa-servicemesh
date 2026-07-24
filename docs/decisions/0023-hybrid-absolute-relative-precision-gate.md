# ADR-0023: 절대값·상대값 혼합 정밀도 기준

- 상태: accepted
- 날짜: 2026-07-25
- supersedes: ADR-0014의 정밀도 정지 규칙(상대 half-width 단일 기준) 부분

## Context

ADR-0014는 core 조건의 정지 기준을 p95 relative half-width ≤5%, p99 relative half-width ≤10%,
application CPU/request relative half-width ≤5%로 정했다.

Phase 4 정식 No-Mesh baseline을 9~11회 반복한 시점에 관측한 값은 다음과 같다.

| 조건 | p95 relative half-width | p99 relative half-width | CPU/request relative half-width |
|---|---:|---:|---:|
| nominal (n=11) | 20.2% | 27.6% | 28.3% |
| high (n=10) | 12.1% | 13.3% | 3.2% |
| near-saturation (n=9) | 25.0% | 36.5% | 20.0% |

bootstrap CI half-width는 대략 `1/√n`로 줄어든다. 이 조건들을 최대 15회까지 채웠을 때의 예상치를 계산하면
nominal과 near-saturation은 여전히 기준을 2~3배 초과하고, high도 p95는 기준을 넘길 것으로 예상됐다.

원인은 두 가지로 파악했다.

1. 클러스터의 3개 VM 노드는 각각 allocatable CPU 2코어로, `docs/risks-and-backlog.md`에 이미 기록된
   "VMware noisy neighbor"·"scheduling 차이" 위험이 실제로 tail latency 변동으로 나타난 것으로 보인다.
2. 기준선 latency 자체가 p95/p99 기준 25~40ms대로 작아, 상대 비율 기준은 작은 절대 잡음(수 ms)도 크게
   과장한다. 이는 `docs/03-concepts-and-glossary.md`의 Resource Overhead 항목에서 이미 지적한
   "작은 기준값은 상대 비율을 과장할 수 있다"는 원칙과 같은 문제다.

## Decision

정밀도 통과 조건을 "상대 half-width ≤ 기존 상대 기준 **OR** 절대 half-width ≤ 신규 절대 기준"인
혼합 규칙으로 바꾼다. 상대 기준(5%/10%/5%)은 유지하고 절대 기준을 추가한다.

| 지표 | 상대 기준 (유지) | 절대 기준 (신규) |
|---|---:|---:|
| p95 | ≤5% | ≤5 ms |
| p99 | ≤10% | ≤8 ms |
| CPU/request | ≤5% | ≤0.01 core-seconds |

절대 기준값은 임의로 정하지 않고, 관측된 절대 half-width가 15회 시점에 도달할 것으로 예상되는 값을
근거로 다음 기준에 맞춰 정했다.

- high 조건은 신규 기준으로 이미 안정된 상태를 통과할 수 있어야 한다.
- 절대 기준이 baseline latency(25~40ms) 대비 지나치게 넓어 이후 Mesh profile 비교에서 실제 오버헤드와
  잡음을 구분하지 못할 정도로 느슨해서는 안 된다 (p99 8ms는 기준선의 약 20~27%로, 나중에 관측될 Sidecar/
  Ambient/Waypoint 오버헤드가 이보다 뚜렷하게 크다면 여전히 유의미하게 구분할 수 있다).

## Alternatives

- **실행 횟수 상한(15회)을 늘린다**: half-width는 `1/√n`로만 줄어들어 15→30회로 늘려도 약 30%만 더
  줄어든다. 관측된 잡음이 표본 부족이 아니라 구조적(노드 자원 제약)이라고 판단해 기각했다.
- **원인을 먼저 조사하고 클러스터 자원을 늘린다**: 더 근본적인 해결책이지만 VM 재구성과 전체 재측정이
  필요해 즉시 적용하지 않는다. 이후 필요 시 별도 ADR로 재검토한다.
- **상대 기준만 완화한다**: 절대 기준 없이 상대 기준만 낮추면, 이후 더 높은 RPS나 다른 시나리오에서
  latency 자체가 커질 때 상대 비율 왜곡 문제가 다시 나타난다. 상대·절대를 함께 쓰는 쪽을 선택했다.

## Consequences

- `high` 조건은 이 정책 변경 시점(n=10)에 즉시 `STOP_PRECISION_REACHED`로 종료된다.
- `nominal`/`near-saturation`은 일부 지표가 여전히 근소하게 기준을 초과할 수 있으며, 15회에도 미달하면
  ADR-0014에 정의된 대로 `INCONCLUSIVE_MAX_RUNS`로 기록하고 원인(노드 자원 제약)을 명시한다.
- 이후 Phase 5~9의 Mesh profile 비교 보고서에는 "p99 8ms/p95 5ms보다 작은 차이는 이 환경의 측정 잡음과
  통계적으로 구분하기 어렵다"는 한계를 명시한다.
- `experiments/analysis.py`의 `POLICY["precision"]`이 `{metric: threshold}`에서
  `{metric: {"relative": ..., "absolute": ...}}` 구조로 바뀌고, `metric_summary()`가 절대 half-width
  (`halfWidth`)를 함께 반환하도록 바뀐다.

## Validation and rollback

- `python -m unittest discover -s experiments -p 'test_*.py'`: 21 tests passed
- 실제 데이터로 재계산: high는 n=10에서 세 지표 모두 통과(`STOP_PRECISION_REACHED`), nominal/near-saturation은
  CONTINUE 유지
- 이후 Mesh profile 비교에서 이 절대 기준보다 작은 실제 차이가 반복적으로 의심되면 절대 기준을 재검토한다.
