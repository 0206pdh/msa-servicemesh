# Phase 1 Workload A3~A6

- Status: validated
- Date: 2026-07-22

## 구현 근거

Mesh profile의 차이를 hop 수, fan-out, Kafka message 크기와 payload 크기별로 분리하려면 모든 부하가 bounded parameter와 결정론 seed를 가져야 한다. baseline에는 암묵적 retry를 넣지 않았다.

## 검증

- Java 5개 서비스 Gradle test
- Compose 7개 컨테이너 healthy
- Sync Chain: 3 hop 완료
- Fan-out: parallel 4 target 완료
- Payload: 1KiB gzip과 checksum 완료
- Async: 5 task 발행/소비 metric 증가

## 제한

- Compose self-hop과 로컬 자원값은 개발 검증일 뿐 최종 성능 자료가 아니다.
- 진짜 binary streaming, retry/circuit breaker와 fault recovery는 별도 profile/후속 Phase에서 다룬다.
