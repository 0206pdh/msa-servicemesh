# Benchmark Workload 개발 Phase

## A0 — 계약

- Scenario와 config model
- 데이터면/제어면 API
- run ID, correlation, trace, deadline
- fault 안전 경계
- metric naming과 cardinality budget
- 결과 schema

## A1 — 공통 런타임 골격

- Java 25/Spring Boot 서비스
- 공통 health, metrics, tracing
- immutable config snapshot
- benchmark-gateway → orchestrator ping
- React run/result shell
- Docker Compose

Exit: 전체 이미지 build/test, 6개 컨테이너 healthy, ID 전파.

## A2 — Workload Target

- 고정/정규/지수 지연 후보
- 설정 오류율과 status distribution
- 결정론적 payload와 checksum
- bounded CPU/memory/I/O 작업
- role/instance metadata
- fault off 기본값과 cleanup

Exit: 동일 seed와 config의 분포 허용 오차 검증.

## A3 — Sync Chain

- hop count와 route
- 남은 deadline 전파
- cancellation 확인
- hop별 span과 latency
- app/Mesh retry owner 표시

측정: hop 증가당 p95/p99, 호출 수, timeout, proxy 비용.

## A4 — Fan-out

- 순차/parallel
- 전체 대기/부분 결과
- source별 timeout
- MVC Virtual Threads 기준 구현
- WebFlux 비교 branch 또는 profile

측정: TTFI, TTCR, p95/p99, throughput, thread/connection, partial rate.

## A5 — Async Pipeline

- Kafka topic/partition 계약
- producer rate와 message size
- worker concurrency와 processing cost
- idempotency와 duplicate metric
- retry/DLQ 정책

측정: publish/consume rate, lag, oldest age, drain time, duplicates.

## A6 — Payload

- 1KB/100KB/1MB/10MB fixture
- buffered/streaming 후보
- compression on/off
- checksum과 byte accounting

측정: throughput, p99, app/proxy CPU, memory, network bytes.

## A7 — Experiment Runner

- ExperimentSpec validation
- warm-up/run/collect/cleanup state machine
- Kubernetes/Helm profile 적용 adapter
- k6 invocation
- Ground Truth와 invalidation
- raw export와 summary

Runner 오류는 workload 결과와 분리한다.

## A8 — Resilience Controls

- timeout budget
- retry policy/budget
- circuit breaker
- bulkhead/concurrency limit
- partial response
- graceful shutdown

기능을 한꺼번에 켜지 않고 baseline과 개선 profile로 분리한다.

## A9 — 개선 구현

- bottleneck Evidence가 있는 항목만 구현
- feature/config flag로 before/after 보존
- rollback threshold
- regression metric
- 설정 변경 이력

## A10 — 재현성과 마감

- contract/integration/load test
- seed와 fixture version
- image digest와 config endpoint
- 결과 schema compatibility
- Console에서 run 비교
- 문서와 자동 실행 경로

## 공통 완료 증거

- 요구사항/ADR
- 변경 파일/commit/image
- test와 raw output
- 환경·자원·seed
- 실패/누락/무효화 요인
- 다음 Phase 진입 조건
