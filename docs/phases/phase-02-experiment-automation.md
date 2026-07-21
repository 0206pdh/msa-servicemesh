# Phase 2 — 실험 자동화

## 목적

동일한 ExperimentSpec을 한 명령으로 반복 실행하고 원본부터 요약까지 추적 가능하게 만든다.

## 작업

1. Runner에 `PLANNED → WARMING_UP → RUNNING → COLLECTING → COMPLETED` 상태 머신을 구현한다.
2. k6 smoke, baseline, load, stress, spike, soak profile을 버전 관리한다.
3. 시작 전 config snapshot, image digest, 배치, 시간 동기화와 headroom을 Ground Truth로 수집한다.
4. 실행 후 Prometheus/Tempo/Loki/Hubble/k6 원본을 run 디렉터리에 export한다.
5. cleanup과 fault disarm을 검증하고 실패 시 `INVALID` 처리한다.

## 검증과 Gate

- 같은 spec/seed를 최소 3회 실행해 동일 디렉터리와 schema 생성
- Runner 오류와 Workload 실패를 다른 code/status로 기록
- 부하 발생기 CPU 80% 초과, dropped iteration 또는 telemetry gap 발생 시 무효화
- 진입: Phase 1 완료
- 종료: unattended 반복 실행과 raw→summary 추적 성공
