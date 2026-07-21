# Phase 8 — 비교와 병목 선정

## 목적

단순 순위가 아니라 관측 근거로 병목을 특정하고 개선 가능한 가설로 바꾼다.

## 작업

1. 네 profile의 절대값, baseline 대비 변화, 반복 분포와 신뢰구간을 비교한다.
2. app/proxy/ztunnel/waypoint CPU, throttling, GC, connection, queue와 latency를 시간축으로 정렬한다.
3. 병목 주장마다 지지 Evidence, 반대 Evidence와 대안 설명을 기록한다.
4. 영향도, 구현 비용, 위험과 검증 가능성으로 개선 후보를 정렬한다.

## Gate

- 데이터가 없는 원인 추정과 단일 metric 기반 결론 금지
- 최소 3개 개선 가설에 baseline run, 독립 변수, 기대/회귀 지표, rollback 기준 존재
- 진입: Phase 4~7 유효 결과
- 종료: bottleneck backlog 승인
