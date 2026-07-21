# Phase 10 — 회복탄력성

## 목적

정상 상태의 개선이 장애 중 성공률과 복구 특성을 악화시키지 않는지 검증한다.

## Fault Matrix

- target delay/HTTP 5xx/reset
- Pod kill와 graceful termination
- network delay/loss 후보
- Kafka worker stop/restart와 backlog drain

## 작업과 지표

1. seed 기반 fault schedule을 before/after에 동일하게 적용한다.
2. 장애 중 성공률, p99, retry amplification, duplicate와 partial response를 측정한다.
3. detection time, downtime, recovery time, queue drain과 정상화 이후 지표를 측정한다.
4. fault disarm, Pod/route/config 복구와 잔여 영향이 없음을 확인한다.

## Gate

- safety limit와 자동 cleanup 없는 fault 실행 금지
- 진입: Phase 9의 개선 후보
- 종료: 개선별 정상/장애 trade-off와 rollback 판단 완료
