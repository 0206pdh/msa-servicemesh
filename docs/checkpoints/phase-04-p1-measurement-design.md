# Checkpoint — `phase-04-p1-measurement-design`

- Status: completed
- Owner: dohyun
- Started at: 2026-07-23
- Completed at: 2026-07-23
- Related Phase: [Phase 4](../phases/phase-04-no-mesh-baseline.md)
- Decision: [ADR-0014](../decisions/0014-measurement-repetition-and-load-policy.md)
- Config: [`phase4-measurement-policy.json`](../../experiments/design/phase4-measurement-policy.json)

## 완료 체크

- [x] 고정 50/200/500 RPS 폐기
- [x] geometric capacity search와 binary refinement
- [x] C* 기반 10/30/60/80% 부하 단계
- [x] core 조건 최소 10회·최대 15회
- [x] p95/p99/CPU bootstrap CI 정밀도 Gate
- [x] run당 최소 20,000 request와 600~1,800초
- [x] randomized complete block과 session drift 통제
- [x] k6 고정 VU 사전할당
- [x] 반복 집계와 자동 정지 판정 구현·unit test

## 다음 재개 지점

1. SYNC_CHAIN canonical condition의 capacity discovery를 실행한다.
2. 최초 실패점과 마지막 통과점 사이를 refine한다.
3. 승인된 C*로 10/30/60/80% 절대 RPS를 계산한다.
