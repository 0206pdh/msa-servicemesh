# A1 공통 런타임 검증

- Status: validated
- Date: 2026-07-22
- Scope: Java services common runtime
- Checkpoint: [A1 common runtime](../../checkpoints/phase-01-a1-common-runtime.md)

## 변경 근거

Mesh profile 비교 전에 모든 서비스가 같은 요청 식별, trace 전파, metric과 startup config 식별 방식을 가져야 한다. Run ID 원문을 metric label로 사용하지 않아 cardinality를 제한한다.

## 구현

- bounded Correlation ID와 Experiment Run ID 검증, MDC와 응답 헤더
- Gateway downstream ID 전파
- Spring Boot OpenTelemetry와 observation-enabled RestClient
- `meshperf.request.context` bounded-cardinality counter
- allowlist startup config와 SHA-256 fingerprint
- health/readiness/prometheus

## 검증 결과

- Java 25 서비스 5개 Gradle test 통과
- Java 서비스 5개와 Web image build 성공
- Compose 6개 모두 healthy
- Correlation ID `a1-e2e-correlation` downstream 일치
- Run ID `a1-e2e-run` downstream 일치
- Gateway와 Orchestrator trace ID 일치
- 5개 config fingerprint 길이 64
- 5개 Prometheus endpoint 응답
- 공통 context metric 노출
- 잘못된 Run ID 400

## 한계

- 로컬 Compose에는 OTel Collector가 없어 exporter는 `none`이며 trace 생성과 hop 전파까지만 검증했다.
- 실제 Tempo export와 trace completeness는 Phase 3에서 검증한다.
- 현재 공통 런타임 코드는 서비스별로 존재하며 공통 모듈 추출은 코드 변경 빈도와 build context를 평가한 뒤 결정한다.
