# Phase 9 — 개선 실험

## 목적

선정한 병목을 실제 변경으로 개선하고 효과, 비용, 실패 조건을 같은 방식으로 재측정한다.

## 후보와 순서

1. retry 단일 소유와 retry budget
2. 계층별 timeout budget과 cancellation
3. 선택적 Waypoint
4. Sidecar/Waypoint resource와 concurrency
5. telemetry sampling/cardinality
6. HPA metric(CPU/RPS/Kafka lag)
7. MVC Virtual Threads와 WebFlux
8. compression, streaming과 Kafka batch 조정

## 실험 규칙

- 한 실험에서 독립 변수 하나만 바꾼다.
- before/after는 동일 baseline, 부하, fault schedule과 수집 설정을 사용한다.
- paired 유효 run 최소 10회와 정밀도 Gate의 절대/상대 변화 및 회귀 metric을 함께 보고한다.
- threshold를 통과하지 못한 개선도 `rejected` Evidence로 보존한다.
- 설정 flag와 rollback 절차로 before 상태를 재현 가능하게 유지한다.

## Gate

- 진입: Phase 8 개선 가설 승인
- 종료: 채택/기각/불확실 결론과 정량 근거, 적용 조건, rollback 기준 존재
