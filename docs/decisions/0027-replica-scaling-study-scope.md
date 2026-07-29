# ADR-0027: Replica 확장 비용 연구 범위

- 상태: accepted
- 날짜: 2026-07-29

## Context

Phase 6 문서(`docs/phases/phase-06-istio-ambient.md`)와 프로젝트 가설 1("Sidecar의 Pod별 비용과
Ambient의 노드 공유 비용은 Pod 수 증가 시 다른 형태로 확장된다")은 Pod replica 수 증가에 따른 Sidecar와
Ambient의 비용 확장 특성을 직접 비교할 것을 요구한다. 이 데이터 없이는 Phase 8 병목 분석이 Sidecar vs
Ambient의 핵심 트레이드오프(Pod당 비용 vs 노드 공유 비용)를 근거 없이 서술하게 된다.

Phase 4~6에서 쓴 조건당 10~15회 반복·bootstrap 95% CI 정밀도 게이트를 replica 수만큼(예: 3개 replica
지점) 곱하면 측정 시간이 또 한 번 크게 늘어난다. 이미 Phase 4~7에 상당한 시간을 썼고, 이 연구의 목적은
"확정적인 통계 결론"이 아니라 "두 profile의 확장 형태가 실제로 다른가"라는 방향성 확인이다.

## Decision

### 범위 축소: 방향성 확인 연구로 설계

- 대상 서비스: `orchestrator-service` 1개만 확장한다(SYNC_CHAIN 중간 hop, 대표성 있음). 다른 서비스는
  전부 1 replica로 고정한다.
- Replica 수: 1 / 2 / 4 세 지점.
- 부하 조건: nominal(8 RPS) 하나만 사용한다. high/near-saturation은 확인하지 않는다.
- Profile: Sidecar와 Ambient만 비교한다(핵심 가설이 이 둘의 비용 모델 차이에 관한 것이므로 No-Mesh는
  이 연구에서 제외).
- 반복 횟수: 지점당 3회로 줄인다(정식 10~15회 반복과 정밀도 게이트를 적용하지 않는다). 이 데이터는
  **방향성 확인용**이며 정식 통계적 결론(Phase 4~6과 같은 급의 신뢰구간)을 주장하지 않는다.
- 측정 시간: run당 warm-up 60초·측정 180초로 축소한다(capacity discovery와 동일 수준). 정식 baseline의
  20,000 request 최소 기준은 적용하지 않는다 — 이 연구의 목적은 개별 run의 tail latency 정밀도가 아니라
  replica 수에 따른 자원 총량의 상대적 변화이므로, 표본이 더 적어도 목적에 부합한다.

### 측정 지표

- Sidecar: `orchestrator-service`에 붙은 모든 replica의 sidecar CPU-초 **합계**(Pod당이 아니라 조건당
  전체 프록시 비용의 총합 — replica가 늘면 이 합계가 어떻게 느는지가 핵심 질문).
- Ambient: 클러스터 전체 ztunnel CPU-초(ADR-0025의 기존 정의 그대로) — replica 수와 무관하게 거의
  일정한지 확인하는 것이 핵심 질문.
- 참고용: p95/p99, app CPU/request(맥락 파악용, 이 연구의 주 결론 대상 아님).

## Alternatives

- **정식 10~15회 반복을 모든 replica 지점에 적용**: 통계적으로 더 견고하지만 이미 상당한 시간을 쓴
  프로젝트 일정에서 비합리적으로 크다. 기각.
- **replica 확장 연구를 완전히 생략**: 가설 1을 검증할 근거가 전혀 없어진다. 기각.
- **모든 5개 서비스를 동시에 확장**: 변수가 너무 많아져 "확장에 따른 비용"이라는 단일 질문에 집중하기
  어렵다. 기각.

## Consequences

- Phase 8 병목 분석은 이 연구 결과를 "방향성 있는 참고 자료"로 인용하되, Phase 4~6 수준의 통계적
  확실성을 갖는 것으로 서술하지 않는다.
- 향후 이 결론을 더 견고히 하려면 별도 정식 반복 연구가 필요하며, 이는 알려진 잔여 작업으로 남긴다.

## Validation and rollback

- 각 replica 지점 배포 후 모든 Pod가 `Running`/`Ready`인지 확인한다.
- 클러스터 메모리 헤드룸이 4 replica 지점에서도 `NODE_MEMORY_HEADROOM_LOW`를 상시로 유발하지 않는지
  확인한다. 자원 부족이 확인되면 3보다 낮은 최대 replica 수로 축소한다.
