# Phase 2 Experiment Runner

- Status: validated-local
- Date: 2026-07-22

## 구현

- Python 표준 라이브러리 기반 lifecycle runner
- Docker k6 0.49.0 고정 실행
- 6개 load profile과 scenario 공통 script
- manifest/Ground Truth/state/raw/summary/report 연결
- 오류 시 `RUNNER_ERROR`, 기존 run overwrite 거부

## 검증

- `python -m unittest experiments.runner.test_runner -v`: 2 tests passed
- Compose chain smoke를 같은 spec/seed로 3회 실행
- 세 반복에 동일 artifact 구조와 완료 상태 이력 생성
- Compose adapter 결과는 의도대로 `INVALID` 및 `NON_MEASUREMENT_COMPOSE_ADAPTER`

## 다음 환경 Gate

Phase 3에서 VMware Kubernetes, Prometheus/Tempo/Loki/Hubble가 준비된 뒤 telemetry completeness, load generator CPU와 cleanup을 실측한다. 그 전에는 성능 수치로 인용하지 않는다.
