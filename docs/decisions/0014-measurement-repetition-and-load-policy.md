# ADR-0014 — 반복 횟수와 부하 단계 결정 정책

- Status: accepted
- Date: 2026-07-23

## 문제

고정된 50/200/500 RPS와 조건당 3회 반복은 현재 3노드 환경과 시나리오별 처리 능력을 반영하지 않는다. 3개 run은 이상 변동을 발견하거나 run-level p95/p99와 자원 비용의 불확실성을 정량화하기에 부족하다.

## 결정

### 1. 탐색과 본 측정을 분리한다

Capacity discovery는 10 RPS에서 시작해 2배씩 증가하며 각 점을 warm-up 120초, 측정 180초로 한 번 실행한다. 최초 실패점이 나오면 마지막 통과점과 실패점 사이를 최대 4회 이분 탐색해 interval 폭을 10% 이내로 줄인다.

`usable capacity (C*)`는 다음 조건을 모두 만족하는 가장 높은 RPS다.

- achieved/target throughput ≥ 98%
- dropped iteration 0
- error rate ≤ 1%
- p99 ≤ low-load p99의 2배
- node CPU < 85%, load-generator CPU < 80%
- 모든 node available memory ≥ 1 GiB
- 기존 telemetry/cleanup Gate 통과

본 측정 부하는 C*의 10%, 30%, 60%, 80%로 계산한다. 모든 Mesh profile은 No Mesh에서 승인한 절대 RPS를 그대로 사용하며 profile별 capacity에 맞춰 다시 낮추지 않는다.

### 2. 독립 run은 최소 10회다

각 core condition은 최소 10개, 최대 15개의 유효 run을 수집한다. 10회 이후 다음 세 기준의 run-level median 95% percentile-bootstrap CI를 계산한다.

- p95 relative half-width ≤ 5%
- p99 relative half-width ≤ 10%
- application CPU/request relative half-width ≤ 5%

세 기준을 모두 만족하면 종료한다. 15회에도 만족하지 못하면 `INCONCLUSIVE_MAX_RUNS`로 판정하고 부하·환경 drift나 metric 정의를 조사한다. 유효 run의 이상치는 삭제하지 않는다. 무효 run은 통계에서 제외하지만 원인과 원본은 보존하고 대체 실행한다.

### 3. run 내부 표본 수도 고정한다

각 run은 warm-up 180초 후 최소 600초 측정하며 요청 수가 20,000개 미만이면 최대 1,800초까지 늘린다. 측정 시간은 `max(600, ceil(20000 / targetRps))`로 계산하고 1,800초로 제한한다. 이는 p99 영역에 기대 표본 약 200개 이상을 확보하기 위한 프로젝트 기준이다.

### 4. 시간 drift를 block으로 통제한다

조건 실행 순서는 고정하지 않고 seed가 기록된 randomized complete block으로 배치한다. 세션당 같은 조건은 최대 5회만 실행하고 최소 2개 세션에 나눠 시간대 drift를 관찰한다. run 사이 cooldown은 120초다.

## Core cross-profile matrix

- SYNC_CHAIN: 3 hop, 1 KiB, hop delay 1 ms
- FAN_OUT: parallel 16 targets, target delay 20 ms
- PAYLOAD: 64 KiB, identity, streaming
- ASYNC_PIPELINE: batch 10, processing 10 ms, payload 1 KiB

각 core scenario는 nominal/high/near-saturation 30/60/80% C*를 정식 비교점으로 사용한다. 10% low는 sanity/linearity 기준으로 수집하되 cross-profile 핵심 결론에는 필요할 때만 포함한다.

## 결과

- 과거 profile JSON의 고정 RPS와 3회 반복을 폐기한다.
- discovery 결과 없이 baseline/load/stress profile을 실행할 수 없다.
- 정식 core matrix는 4 scenario × 3 load × 조건당 10~15 run으로 120~180개의 유효 run이다.
- spike는 5~10회, 4시간 soak는 leak/drift 전용으로 3~5회 수행하며 steady-state 비교와 분리한다.
