# Checkpoint — `phase-01-a5-async-pipeline`

- Status: validated
- Updated at: 2026-07-22

## 목표

Kafka task 발행, Worker 처리와 멱등성 metric을 구현한다.

## 완료 조건

- [x] task/result event schema 기반 발행
- [x] batch 기반 deterministic idempotency key
- [x] bounded idempotency cache와 duplicate 구분
- [x] 실제 payload 크기, checksum, age/processing/Kafka lag metric
- [x] 10MiB payload를 위한 명시적 15MB broker/client 상한
- [x] batch 전체 payload 64MiB 조합 상한
- [x] Compose publish-consume E2E

## 검증 결과

- task 5개 발행 후 `meshperf_worker_tasks_total{outcome="completed"}=5`
- worker 단위 테스트에서 같은 멱등키의 두 번째 이벤트를 duplicate로 판정
- 무제한 key 저장 대신 최대 100,000건 Caffeine cache 사용
