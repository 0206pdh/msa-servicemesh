# 전체 Phase 로드맵

각 Phase는 다음 단계의 입력이 되는 검증 가능한 산출물을 만든다. 일정이 아니라 Exit criteria로 종료한다.

진행 상태는 [현재 체크포인트](../CURRENT.md)와 [전체 Phase 체크리스트](../checkpoints/phase-checklists.md)에서 관리한다. 모든 Phase는 시작·중간·종료 시 [체크포인트 템플릿](../checkpoints/checkpoint-template.md)을 사용한다.

| Phase | 목표 | 핵심 산출물 |
|---:|---|---|
| 0 | 질문·공정성·Workload·결과 계약 | 문서, ADR, schema |
| 1 | Java Benchmark Workload | 로컬 실행·테스트 |
| 2 | 자동 실험 제어 | k6, Runner, raw result |
| 3 | 온프레미스 플랫폼 | 3노드 K8s, Cilium, observability |
| 4 | No Mesh | 기준선과 포화점 |
| 5 | Sidecar | 동일 조건 profile 결과 |
| 6 | Ambient | 동일 조건 profile 결과 |
| 7 | Waypoint | 동일 조건 profile 결과 |
| 8 | 비교와 병목 | Evidence 기반 bottleneck backlog |
| 9 | 개선 실험 | before/after 결과 |
| 10 | 회복탄력성 | Chaos와 개선 재검증 |
| 11 | 최종화 | 선택 Matrix, 재현 보고서 |

## 상세 실행 문서

| Phase | 문서 |
|---:|---|
| 0 | [실험 설계](phase-00-experiment-design.md) |
| 1 | [Benchmark Workload 구현](phase-01-workload-implementation.md) |
| 2 | [실험 자동화](phase-02-experiment-automation.md) |
| 3 | [플랫폼 기반](phase-03-platform-foundation.md) |
| 4 | [No Mesh 기준선](phase-04-no-mesh-baseline.md) |
| 5 | [Istio Sidecar](phase-05-istio-sidecar.md) |
| 6 | [Istio Ambient](phase-06-istio-ambient.md) |
| 7 | [Ambient와 Waypoint](phase-07-waypoint.md) |
| 8 | [비교와 병목 선정](phase-08-bottleneck-analysis.md) |
| 9 | [개선 실험](phase-09-improvement-experiments.md) |
| 10 | [회복탄력성](phase-10-resilience.md) |
| 11 | [최종화와 재현](phase-11-finalization.md) |

## Phase 0 — 실험 설계

- 질문과 기각 가능한 가설
- Sync Chain, Fan-out, Async, Payload Workload 계약
- 변수, 고정 조건, invalidation rule
- 공통 result schema와 run manifest
- 앱/proxy/ztunnel/waypoint 자원 분리 규칙
- 개선 실험 템플릿

Exit: OpenAPI/schema lint, 문서 링크, legacy 방향 잔재 검사 통과.

## Phase 1 — Workload 구현

- benchmark-gateway, orchestrator, workload, producer, worker
- delay/error/payload/resource config
- correlation/trace/run ID와 deadline
- 부분 결과, 멱등 consumer
- Docker Compose와 최소 Console

Exit: Java 25 test/image build와 로컬 E2E, 결정론적 seed 재현.

## Phase 2 — Experiment Automation

- k6 smoke/baseline/load/stress/spike/soak
- Experiment Runner lifecycle
- config snapshot, Ground Truth, cleanup
- Prometheus query/export와 summary 생성
- 부하 발생기 포화 검사

Exit: 한 명령으로 같은 spec을 3회 실행하고 같은 구조의 결과 생성.

## Phase 3 — Platform Foundation

- VMware 노드와 시간 동기화
- Kubernetes 배포판 ADR
- Cilium/Hubble, MetalLB, Gateway API
- Prometheus/Grafana/Loki/Tempo/OTel
- Helm chart와 환경별 values

Exit: NetworkPolicy, telemetry completeness, node/collector headroom 검증.

## Phase 4 — No Mesh Baseline

- scenario별 포화점 탐색
- 정상/장애 기준 latency, throughput, resource
- workload 자체 병목 제거 또는 명시
- target RPS와 실험 시간 확정

Exit: 이후 profile과 개선 실험의 기준 데이터 승인.

## Phase 5 — Sidecar

- injection과 mTLS 검증
- proxy request/limit, concurrency, startup 기록
- 동일 부하·배치에서 비교
- retry/timeout은 기준선과 동일 소유 상태 유지

Exit: Sidecar 추가 비용과 L7 기능 Evidence 확보.

## Phase 6 — Ambient

- namespace enrollment와 ztunnel 경로 검증
- 노드 공유 자원 할당 방식 명시
- Pod 수 증가와 worker scale 실험
- Sidecar와 동일 기능 범위/차이 기록

Exit: 비용 증가 형태와 기능 차이 Evidence 확보.

## Phase 7 — Ambient + Waypoint

- 전체/선택 경로 Waypoint profile 분리
- replica, 통과 RPS, queue와 saturation 기록
- L7 routing/policy/telemetry 검증

Exit: Waypoint 비용과 제공 기능을 트래픽 범위와 연결.

## Phase 8 — 비교와 병목 선정

- 네 profile 통계와 절대 차이
- CPU throttling, connection, queue, GC, telemetry 상관관계
- 병목 주장마다 지지/반대 Evidence
- 최소 세 개선 가설과 예상 부작용

Exit: 개선 전 baseline run ID와 독립 변수가 승인됨.

## Phase 9 — 개선 실험

우선 후보:

1. retry 단일 소유와 retry budget
2. 계층별 timeout budget과 cancellation
3. 선택적 Waypoint
4. Sidecar resource/concurrency
5. telemetry sampling/cardinality
6. HPA metric(CPU/RPS/lag)
7. MVC Virtual Threads/WebFlux

각 개선은 한 변수만 바꾸고 최소 3회 재측정한다. 개선 실패도 결과다.

## Phase 10 — 회복탄력성

- delay/error, Pod kill, network fault, worker stop
- 장애 중 성공률, amplification, downtime, recovery
- 개선 전후 같은 fault schedule 비교
- cleanup과 정상화 검증

Exit: 정상 성능 개선이 장애 상황에서도 유지되는지 결론.

## Phase 11 — 최종화

- workload별 profile/설정 Matrix
- 적용 조건, 비용, 기능 손실, rollback 기준
- raw→summary→graph 자동 연결
- 새 환경 재현 시험
- 결론의 범위와 무효화 조건
