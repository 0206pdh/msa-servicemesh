# Checkpoint — `phase-01-a4-fanout`

- Status: validated
- Updated at: 2026-07-22

## 목표

순차/Virtual Thread 병렬 Fan-out과 time-budget partial result를 구현한다.

## 완료 조건

- [x] target 1~64
- [x] sequential/Java 25 virtual-thread parallel
- [x] 전체 budget과 target outcome
- [x] partial/failed 판정과 pending task 취소
- [x] contract/Compose E2E

## 검증 결과

- parallel target 4개: `COMPLETED`, `completedTargets=4`
- workload 미지정 시 bounded no-op 기본값 적용
- retry는 baseline에 숨겨 넣지 않았으며 Mesh retry와 애플리케이션 retry는 후속 profile에서 분리한다.
- 동시 요청의 선언 memory 합계는 256MiB를 넘지 못한다.
