# Checkpoint — `phase-01-a1-common-runtime`

- Status: validated
- Updated at: 2026-07-22
- Related Phase: [Phase 1](../phases/phase-01-workload-implementation.md)
- Related Contract: [Data Plane API](../../contracts/openapi/mesh-benchmark-api.yaml)

## 목표

다섯 Java 서비스에 동일한 요청 식별자, tracing, Prometheus와 변경 불가능한 startup config snapshot을 제공한다.

## 완료 조건

- [x] Correlation ID 생성/검증/응답 및 downstream 전파
- [x] Experiment Run ID 검증/응답 및 downstream 전파
- [x] W3C trace context 자동 전파
- [x] bounded-cardinality 공통 request metric
- [x] health/readiness/prometheus endpoint
- [x] secret 없는 immutable config snapshot과 fingerprint
- [x] 서비스별 test와 Compose E2E
- [x] A1 Evidence와 CURRENT/checklist 갱신

## 초기 진단

- Gateway만 tracing bridge가 있고 Prometheus registry가 없음
- 나머지 서비스는 Prometheus registry만 있고 tracing bridge가 없음
- Gateway의 수동 `RestClient.builder()` bean은 Spring 자동 observation builder를 우회함
- Micrometer bridge만으로 `Tracer` bean이 생성되지 않아 Spring Boot OpenTelemetry starter로 교체
- Correlation ID는 있으나 길이 검증과 Run ID가 없음
- startup config snapshot과 fingerprint가 없음

## 다음 재개 지점

- A2 `/workloads/target` 계약 테스트부터 시작

## 실패와 해결

- Docker Desktop Linux engine 미기동: engine 시작 후 재검증
- Micrometer bridge만 사용해 `Tracer` bean 없음: Spring Boot OpenTelemetry starter로 교체
- Boot 4 server starter에 `RestClient.Builder` 없음: Gateway에 restclient starter 추가
- 로컬 collector 없음: Compose에서 OTLP exporter를 `none`으로 두고 trace 생성/전파만 검증

## 최종 검증

- Java 서비스 5개 Gradle test 통과
- 이미지 6개 build 성공, Compose 6개 healthy
- Correlation/Run ID Gateway → Orchestrator 일치
- Gateway/Orchestrator 32자리 trace ID 일치
- 서비스 5개 config fingerprint 64자리, Prometheus endpoint 응답
- 잘못된 Run ID 응답 400
