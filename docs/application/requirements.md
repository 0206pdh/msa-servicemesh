# Benchmark Workload 요구사항

## 기능 요구사항

### BW-01 동기 Chain

- 0~N hop을 구성할 수 있다.
- 각 hop은 고정/분포 지연, 오류율, payload 크기를 설정할 수 있다.
- correlationId, traceparent, experimentRunId와 남은 deadline을 전파한다.

### BW-02 Fan-out

- target 수와 순차/병렬 방식을 선택한다.
- 전체 대기와 time-budget 부분 결과 모드를 지원한다.
- target별 성공, timeout, 오류와 완료 시각을 반환한다.
- MVC Virtual Threads와 WebFlux 구현을 같은 계약으로 비교할 수 있다.

### BW-03 Async Pipeline

- producer가 설정한 크기와 rate로 메시지를 발행한다.
- worker concurrency와 처리 비용을 설정한다.
- idempotency key로 중복을 식별한다.
- queue lag, oldest age, 처리율과 backlog drain을 측정한다.

### BW-04 Payload

- 1KB~10MB 범위의 결정론적 payload를 생성한다.
- compression on/off와 streaming/buffered 후보를 비교한다.
- payload checksum으로 손상 여부를 검증한다.

### BW-05 Resource Target

- 제한된 시간 동안 CPU, memory, blocking I/O 부하를 생성한다.
- 목표량을 벗어나는 할당과 무제한 누수를 금지한다.
- 실제 소비량과 요청 파라미터를 metric으로 노출한다.

### BW-06 Fault

- delay, HTTP 5xx, reset, process exit 후보를 제공한다.
- fault는 run ID, 시작/종료, 대상과 강도를 갖는다.
- 운영 기본값은 fault off다.
- 실험 Namespace와 인증된 Runner만 제어할 수 있다.

### BW-07 Run Lifecycle

- `PLANNED → WARMING_UP → RUNNING → COLLECTING → COMPLETED` 상태를 갖는다.
- 설정 변경, 부하 포화, cleanup 실패 시 `INVALID` 또는 `FAILED`로 종료한다.
- run 완료 후 manifest와 raw result 위치를 제공한다.

## 비기능 요구사항

- Java 25/Spring Boot, 서비스별 독립 이미지
- UTC와 시간 동기화 상태 기록
- liveness/readiness/startup/prometheus
- W3C Trace Context와 run ID
- 설정 snapshot과 image digest 노출
- unbounded metric label 금지
- 측정 경로 로그는 sampling 가능하며 적용 상태 기록
- 동일 seed는 동일 payload와 fault schedule 생성
