# MVC Virtual Threads vs WebFlux

Fan-out scenario에서 두 동시성 모델의 효과와 복잡도를 비교한다.

## 고정 조건

- Java 25/Spring Boot, payload와 결과 계약
- target 수, delay/error distribution
- connection timeout과 전체 budget
- image resource, replica, Mesh profile
- warm-up, k6 load, seed

## 시나리오

- target 4/16/64개
- 모두 20ms
- 한 target 1초 지연
- 30% 5xx
- timeout과 cancellation
- connection pool saturation
- 30분 soak

## 지표

- TTFI/TTCR p50/p95/p99
- throughput, partial/error rate
- platform/virtual thread, event-loop saturation
- connection pending/acquire
- CPU, heap, RSS, GC
- 구현·디버깅·관측 복잡도

## 결정

MVC+Virtual Threads가 목표 범위에서 안정적이면 단순성을 우선한다. WebFlux는 반복 가능한 성능 또는 자원 이점이 운영 복잡도보다 클 때만 채택한다.
