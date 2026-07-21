# ADR-0022: 개선 검증 루프

- 상태: accepted
- 날짜: 2026-07-22

Profile 비교만으로 프로젝트를 완료하지 않는다. 병목 주장에는 telemetry Evidence와 baseline run ID가 필요하다. 개선 실험은 독립 변수 하나, 예상 개선, 회귀 지표, rollback threshold를 사전 정의하고 동일 조건에서 최소 3회 재측정한다.

개선 실패와 악화도 최종 보고서에 포함한다.
