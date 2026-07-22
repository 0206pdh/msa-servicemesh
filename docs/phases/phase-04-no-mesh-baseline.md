# Phase 4 — No Mesh 기준선

## 목적

Mesh 비용이 없는 Workload 자체 성능과 포화점을 이후 모든 비교의 기준으로 확정한다.

## 작업

1. Scenario별 10 RPS geometric search와 binary refinement로 usable capacity `C*`를 찾는다.
2. 정상 상태와 합의된 fault 상태의 latency, throughput, error, CPU, memory, network를 수집한다.
3. GC, thread/connection pool, Kafka, DB 없는 target 자체 병목을 구분한다.
4. `C*`의 10/30/60/80%에서 목표 RPS, warm-up, 측정 시간과 Pod 배치를 고정한다.

## 검증과 Gate

- core 조건 유효 run 최소 10회, 최대 15회와 bootstrap 95% CI 정밀도 Gate
- run당 최소 20,000 request, warm-up 180초와 측정 600~1,800초
- 부하 발생기가 target보다 먼저 포화되지 않았음을 증명
- seeded randomized complete block, 세션당 최대 5회와 최소 2개 세션
- profile별 동일 조건에 사용할 baseline run ID 승인
- 진입: Phase 3 완료
- 종료: Scenario별 비교 부하와 기준선 Evidence `measured`
