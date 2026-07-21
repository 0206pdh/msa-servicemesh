# ADR-0007: Java와 Console 기준선

- 상태: accepted
- 날짜: 2026-07-21

Java 25, Spring Boot 4.1, Gradle 9 Wrapper와 React/TypeScript/Vite를 사용한다. Workload 서비스는 독립 이미지로 빌드한다.

Fan-out 동시성 모델은 MVC+Virtual Threads를 기준으로 구현한 뒤 WebFlux와 TTFI/TTCR, p95/p99, throughput, thread/connection, CPU/memory와 운영 복잡도를 비교한다.
