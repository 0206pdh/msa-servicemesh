# ADR-0021: 통신 패턴 기반 Workload 경계

- 상태: accepted
- 날짜: 2026-07-22

Benchmark Workload는 benchmark-gateway, orchestrator, configurable workload, producer, worker로 나눈다. 동일 workload 이미지를 role/config로 여러 hop과 target에 사용한다. 서비스 개수를 늘리기 위한 복제 구현은 금지한다.

Sync Chain, Fan-out, Async, Payload를 독립 scenario로 제공해 특정 workload 하나의 결과를 전체 MSA에 일반화하지 않는다.
