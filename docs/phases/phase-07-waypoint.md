# Phase 7 — Ambient와 Waypoint

## 목적

L7 기능이 필요한 경로에 Waypoint를 적용할 때의 비용과 선택적 배치 효과를 측정한다.

## 작업

1. 전체 경로와 선택 경로 profile을 분리한다.
2. Waypoint replica, requests/limits, 통과 RPS, queue와 saturation을 기록한다.
3. routing, policy, retry/timeout과 L7 telemetry 제공 여부를 검증한다.
4. Waypoint를 통과하지 않는 traffic과 결과를 섞지 않는다.

## 검증과 Gate

- intended route의 Waypoint 통과와 정책 적용 증거 확보
- 동일 기능 범위 비교와 비용만 비교하는 실험을 구분
- 유효 run 최소 3회
- 진입: Ambient baseline 완료
- 종료: 적용 범위별 비용/기능 Evidence `measured`
