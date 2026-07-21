# Phase 4 — No Mesh 기준선

## 목적

Mesh 비용이 없는 Workload 자체 성능과 포화점을 이후 모든 비교의 기준으로 확정한다.

## 작업

1. Scenario별 낮은 부하부터 포화까지 단계적으로 탐색한다.
2. 정상 상태와 합의된 fault 상태의 latency, throughput, error, CPU, memory, network를 수집한다.
3. GC, thread/connection pool, Kafka, DB 없는 target 자체 병목을 구분한다.
4. 목표 RPS, warm-up, 측정 시간과 Pod 배치를 고정한다.

## 검증과 Gate

- 각 조건 유효 run 최소 3회, p50/p95/p99와 분산 보고
- 부하 발생기가 target보다 먼저 포화되지 않았음을 증명
- profile별 동일 조건에 사용할 baseline run ID 승인
- 진입: Phase 3 완료
- 종료: Scenario별 비교 부하와 기준선 Evidence `measured`
