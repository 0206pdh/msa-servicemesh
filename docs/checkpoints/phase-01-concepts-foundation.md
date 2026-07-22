# Checkpoint — `phase-01-concepts-foundation`

- Status: validated
- Updated at: 2026-07-22
- Related Phase: [Phase 1](../phases/phase-01-workload-implementation.md)
- Related ADR: [ADR-0020](../decisions/0020-performance-engineering-project.md), [ADR-0021](../decisions/0021-benchmark-workload-boundaries.md)

## 목표

구현과 결과 해석에 사용하는 Mesh, Workload, 호출 구조, 지표와 실험 용어의 의미를 통일한다.

## 완료 조건

- [x] Service Mesh와 네 Profile 설명
- [x] Benchmark/Scenario/Profile/Baseline 설명
- [x] Hop/Chain/Fan-out/Async/Payload 설명
- [x] resilience, 성능 지표, 실험 설계와 관측 용어 설명
- [x] Kubernetes 구성 요소와 프로젝트 서비스 연결
- [x] 문서 인덱스와 현재 상태 연결

## 변경 근거

- 문제: 같은 용어를 애플리케이션, Mesh와 실험 문맥에서 다르게 해석할 수 있음
- 선택: 프로젝트 문맥과 측정 주의점을 포함하는 단일 용어 문서 사용
- 대안: 외부 링크만 제공하면 프로젝트 고유 규칙과 비교 범위를 설명하기 어려움
- Trade-off: 문서가 길어지지만 구현·분석 단계의 용어 불일치를 줄임

## 검증 기록

| 검증 | 방법 | 결과 | Evidence |
|---|---|---|---|
| coverage | Phase/architecture/contract 용어 대조 | passed | [용어 문서](../03-concepts-and-glossary.md) |
| links | Markdown 상대 링크 검사 | passed | 전체 Markdown 링크 검사 |

## 다음 재개 지점

- 첫 작업: A1 공통 metrics/tracing, run ID와 immutable config snapshot
- 필요한 파일: `services/*`, Data Plane OpenAPI, A1 체크리스트
- 주의: 용어 의미가 달라지는 구현은 같은 commit에서 이 문서도 갱신
