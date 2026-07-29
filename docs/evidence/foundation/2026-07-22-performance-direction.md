# Performance Engineering 방향 전환

- Status: validated
- Date: 2026-07-22
- ADR: ADR-0020, ADR-0021, ADR-0022

## 결정

비즈니스 제품 또는 SRE 제품을 위한 MSA 대신 통신 패턴 기반 Benchmark Workload와 Service Mesh 개선 검증을 프로젝트 목적으로 확정했다.

## 재사용

- Java 25/Spring Boot/Gradle/Docker 골격
- VMware/Cilium/MetalLB/Gateway/Istio 계획
- Prometheus/Loki/Tempo/OpenTelemetry
- k6/Chaos와 Evidence 원칙

## 검증 결과

- Markdown 로컬 링크 검사 통과
- Redocly OpenAPI lint 통과
- 이벤트 및 실험 결과 JSON Schema 구문 검사 통과
- 런타임 코드의 이전 방향 도메인 잔재 검사 통과
- Web production build 통과
- Java 25 기반 5개 서비스 Gradle test 통과
- Java 서비스 5개와 Web 이미지 build 통과
- Compose 서비스 6개 모두 healthy
- Gateway → Orchestrator 호출 성공
- 요청 `X-Correlation-ID`가 응답 헤더와 Orchestrator 응답에 동일하게 전파됨
- Web `http://localhost:3000` 응답 200

최초 E2E 스크립트는 상관관계 ID를 최상위 JSON 필드에서 읽어 `null`을 반환했다. 원문 확인 결과 실제 값은 응답 헤더와 `downstream.correlationId`에 있었으며, 이는 구현 장애가 아닌 검증식 오류였다.

## 현재 한계

- 현재 구현은 이름이 전환된 ping 런타임 골격이다.
- A1의 Sync Chain, Fan-out, Async, Payload workload API는 아직 구현하지 않았다.
- 실제 Service Mesh 성능 측정값은 아직 생성하지 않았다.
- Git 저장소는 아직 생성하지 않았다.
