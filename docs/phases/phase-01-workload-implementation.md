# Phase 1 — Benchmark Workload 구현

## 목적

Mesh 구성과 무관하게 동일하게 배포할 결정론적 Java MSA 측정 대상을 만든다. 세부 순서는 [Workload 개발 Phase](application-development.md)를 따른다.

## 작업

1. Gateway, Orchestrator, Workload Target, Producer, Worker를 Java 25/Spring Boot로 구현한다.
2. Chain hop, Fan-out 병렬도, delay/error, CPU/memory/I/O, payload 크기를 bounded parameter로 제공한다.
3. Kafka 발행·소비, 멱등키, duplicate, lag와 drain time을 구현한다.
4. run/correlation/trace ID, 남은 deadline, config fingerprint와 image 정보를 전파한다.
5. health/readiness/startup, Prometheus metric과 OpenTelemetry span을 추가한다.
6. 선택적 Web Console은 API 상태와 저장된 결과만 다루며 부하를 생성하지 않는다.

## 검증

- 계약/경계/오류 단위 테스트와 Testcontainers 통합 테스트
- 동일 seed payload checksum 및 fault schedule 재현
- Compose 전체 healthy와 각 데이터 경로 E2E
- 무제한 메모리, thread, label, retry가 없음을 확인

## 산출물과 Gate

- 서비스 이미지, 테스트 결과, Compose smoke Evidence
- 진입: Phase 0 계약 `validated`
- 종료: 모든 Scenario가 Mesh 없이 계약대로 실행되고 A1~A6 Evidence가 존재
