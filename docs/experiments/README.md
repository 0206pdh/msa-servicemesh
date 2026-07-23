# 실험 계획

## 비교 Profile

- P0 No Mesh
- P1 Istio Sidecar
- P2 Ambient
- P3 Ambient + Waypoint

## 공정성

- 동일 commit과 image digest
- 동일 VM/node, CPU pinning 후보, scheduling/placement
- 동일 replica, request/limit, HPA 상태
- 동일 dataset, seed, cache와 JVM warm-up
- 동일 k6 실행 위치와 네트워크
- 동일 fault schedule
- profile 외 설정 차이는 manifest diff로 검출

## 실험 Matrix

| ID | 질문 | 독립 변수 | 지표 |
|---|---|---|---|
| PERF-01 | 정상 비용 | Mesh profile | throughput, p95/p99, CPU/memory |
| PERF-02 | hop 누적 | 0/1/3/5 hop | hop당 latency, proxy CPU |
| PERF-03 | scale 비용 | 10/50/100 Pods | node cost, packing density |
| FAN-01 | I/O 모델 | sequential/VT/WebFlux | TTFI/TTCR, threads, CPU |
| FAN-02 | 부분 결과 | full wait/time budget | p99, partial rate |
| ASYNC-01 | worker 확장 | replica/concurrency | lag, drain time, memory |
| PAY-01 | 전송 비용 | payload/compression | throughput, CPU, network |
| RES-01 | timeout | 계층별 budget | tail latency, cancellation |
| RES-02 | retry | app/mesh/both | amplification, success, recovery |
| RES-03 | circuit breaker | on/off/settings | isolation, open/recovery time |
| OBS-01 | telemetry | sample/log/cardinality | coverage, ingest, p99, storage |
| WAY-01 | Waypoint 범위 | all/selected | L7 coverage, CPU, p99 |
| HPA-01 | scale metric | CPU/RPS/queue lag | convergence, backlog, waste |
| CHAOS-01 | delay/5xx | profile/policy | error spread, recovery |
| CHAOS-02 | Pod kill | app/proxy/worker | downtime, convergence |
| CHAOS-03 | network fault | loss/deny | timeout, Hubble evidence |

## 개선 실험 계약

각 개선은 다음을 사전에 작성한다.

```text
Bottleneck claim
Supporting and contradicting evidence
Baseline run IDs
One independent variable
Expected improvement
Regression metrics
Rollback threshold
After run count
Decision rule
```

## 주요 개선 후보

### Retry 단일화

- 호출 증폭률 = 실제 downstream calls / 최초 client calls
- 성공률 개선과 장애 대상 부하를 함께 본다.

### Timeout Budget

- 전체 deadline과 hop별 남은 예산을 기록한다.
- timeout 감소 대신 부분 실패가 증가하는지 본다.

### 선택적 Waypoint

- L7 기능이 필요한 경로만 통과시킨다.
- 비용 절감과 telemetry/policy 손실을 함께 측정한다.

### Proxy Resource

- CPU request/limit, concurrency, throttling을 조정한다.
- latency 개선과 node packing 손실을 같이 본다.

### Telemetry

- sampling, access log, cardinality, collector batch를 조정한다.
- 저장 비용 감소와 장애 분석 가능성 감소를 함께 본다.

## 부하 Profile

- Smoke: 기능과 telemetry 확인
- Baseline: 낮고 일정한 RPS
- Load: 목표 RPS
- Stress: 포화점 탐색
- Spike: 급증과 HPA
- Soak: 누수, connection, queue, 저장 증가

고정 RPS는 사용하지 않는다. 먼저 scenario별 usable capacity `C*`를 탐색한 뒤 baseline/load/near-saturation을 각각 C*의 30/60/80% 절대 RPS로 해석한다. 반복과 정지 규칙은 [ADR-0014](../decisions/0014-measurement-repetition-and-load-policy.md)와 `experiments/design/phase4-measurement-policy.json`을 따른다.

## 반복과 통계

- 탐색점: 1회, geometric search 후 binary refinement
- core steady-state: 최소 10회, 최대 15회
- 종료: p95/CPU 5%, p99 10% relative CI half-width
- run 내부: 최소 20,000 request와 600~2,700초 측정
- 유효 이상치 삭제 금지, 무효 run 원본 보존
- 조건 순서는 seeded randomized complete block으로 배치

## Run 무효화 조건

- 부하 발생기 CPU/네트워크 포화
- 관측 collector drop이 허용 범위 초과
- node pressure 또는 예상치 못한 scheduling 차이
- image/config/profile mismatch
- warm-up 미완료
- fault cleanup 실패
- 시간 동기화 오류

## 결과 해석

- 백분율과 절대값을 같이 표시한다.
- 중앙값뿐 아니라 run별 값과 분포를 제공한다.
- 통계적 차이와 운영상 의미를 구분한다.
- 보편 결론 대신 환경과 부하 범위를 명시한다.
- 개선 실패와 회귀를 숨기지 않는다.
