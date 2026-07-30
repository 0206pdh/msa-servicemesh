# Service Mesh Performance Analysis

VMware 기반 온프레미스 Kubernetes 3노드 클러스터에서 No-Mesh, Istio Sidecar, Istio Ambient, Ambient +
Waypoint 네 가지 구성의 성능·자원·회복탄력성을 반복 측정하고, 통계적으로 유의한 차이만 결론으로 채택하는
정량 분석 프로젝트다. 측정 대상은 가상의 비즈니스 제품이 아니라, 동기 체인·병렬 fan-out·비동기 worker·
대용량 payload 등 실제 MSA에서 반복적으로 나타나는 통신 패턴을 재현하도록 설계한 통제 가능한 Java/Spring
Benchmark Workload다.

> 개요부터 결론까지 한 번에 보려면 [포트폴리오 요약(PORTFOLIO.md)](PORTFOLIO.md)을 참고한다.
> 무엇을, 왜 이렇게 테스트했는지 처음부터 끝까지 풀어 쓴 설명은
> [docs/testing-explained.md](docs/testing-explained.md)를 참고한다.

## 중심 질문

> No Mesh, Istio Sidecar, Ambient, Ambient + Waypoint는 워크로드 특성별로 어떤 성능·자원·관측성·회복탄력성
> 차이를 만들며, 측정된 병목을 어떤 설정과 아키텍처 변경으로 개선할 수 있는가?

## 지금까지의 정량 결론 (요약)

전체 근거와 신뢰구간은 [PORTFOLIO.md §6](PORTFOLIO.md), 원본 데이터는 [Evidence](docs/evidence/performance/)를
따른다. 아래는 정식 반복측정(bootstrap 95% CI, 조건당 10~15회)으로 확인된 핵심 수치만 요약한 것이다.

| 발견 | 수치 | 근거 |
|---|---|---|
| Sidecar의 요청당 network bytes 증가 | No-Mesh 대비 **+49%**, 3개 부하 조건(8/17/22 RPS) 모두 일관 | [Phase 8 비교](docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md) |
| Ambient의 요청당 network bytes 증가 | No-Mesh 대비 **+1~2%**만 (Sidecar의 1/20~1/40 수준) | 위와 동일 |
| Sidecar 오버헤드에서 mTLS가 차지하는 비중 | mTLS DISABLE 시 감소분은 전체 오버헤드의 **~3%뿐** | [Phase 9 실험 1](docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md) |
| Sidecar/Ambient가 애플리케이션 자체 CPU에 주는 영향 | 9개 profile 비교 전부 **유의한 차이 없음** | [Phase 8 비교](docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md) |
| Ambient + Waypoint (L7 selective proxy) | waypoint→backend 연결 실패, Istio 1.30.3/1.29.6 양쪽 재현 → **버전 독립적 비호환으로 최종 blocked** | [Waypoint 체크포인트](docs/checkpoints/phase-07-p1-waypoint-blocked.md) |

latency는 대부분의 비교에서 이 클러스터의 노이즈 하한(p95 ≈5ms/p99 ≈8ms)보다 작은 차이만 관측되어
"확인된 차이 없음"으로 보고했다 — 확인되지 않은 차이를 "없다"고 주장하는 것과는 다르다는 점을 모든 결론에
명시한다.

## 프로젝트가 답해야 하는 것

- Mesh profile별 p50/p95/p99, throughput, 오류율과 자원 비용은 얼마인가?
- Pod 수와 hop 수, payload, 동시성이 커질 때 비용 증가 형태는 어떻게 달라지는가?
- timeout/retry/circuit breaker의 소유 위치가 장애 전파와 회복에 미치는 영향은 무엇인가?
- Sidecar 또는 Waypoint의 L7 기능이 추가 비용만큼 실질적인 관측·제어 효과를 제공하는가?
- 병목을 개선했을 때 어떤 지표가 좋아지고 어떤 비용이나 기능 손실이 생기는가?
- 워크로드 유형별로 어떤 profile과 설정을 선택해야 하는가?

## 방법론

```text
기준선 측정 (조건당 10~15회, bootstrap 95% CI 정밀도 게이트)
→ profile 간 독립 2-표본 통계 비교로 병목 후보 선정
→ 원인 가설 수립
→ 단일 변수 개선안 적용
→ 동일 조건 반복 측정
→ 효과·부작용·신뢰구간 분석 (기각된 가설도 그대로 보존)
→ 적용 조건과 rollback 기준 기록
```

단순 profile 순위표가 아니라, 개선 전후 데이터와 조건부 의사결정 Matrix가 최종 산출물이다. 통계적으로
유의하지 않은 결과는 "차이 없음"으로, 유의하더라도 재현되지 않은 결과는 "확정 아님"으로 명시적으로
구분해 보고한다 — 방법론 세부사항(정밀도 게이트, config-fingerprint 기반 run 무효화, confound 처리 방식)은
[ADR](docs/decisions/README.md)에 결정 근거와 함께 기록되어 있다.

## Benchmark Workload

| 유형 | 구조 | 검증 대상 |
|---|---|---|
| Sync Chain | gateway → hop-a → hop-b → hop-c | hop 누적 지연, mTLS, timeout 전파 |
| Fan-out | orchestrator → target 4개 | 병렬 I/O, 부분 결과, retry 증폭 |
| Async | producer → Kafka → workers | backlog, consumer lag, worker scale |
| Payload | gateway → processor → storage | 크기·compression·proxy CPU |
| Mixed | CPU/Memory/I/O target | 자원 경합, throttling, HPA |

Workload는 지연, 오류율, 응답 크기, CPU, 메모리, fan-out 수와 hop 수를 설정으로 제어한다. 실험용 fault
설정은 인증된 실험 Runner에서만 변경할 수 있다.

## 기술 기준선

- Java 25, Spring Boot 4.1, Gradle 9 Wrapper
- React/TypeScript 실험 Console
- Docker Compose 로컬 검증
- VMware 3노드 Kubernetes
- Cilium, Hubble, MetalLB, Gateway API
- Istio Sidecar, Ambient, Waypoint
- Prometheus, Grafana, Loki, Tempo, OpenTelemetry
- k6, Chaos Mesh
- Helm 환경 profile

## Phase 진행 상태

| Phase | 내용 | 상태 |
|---:|---|---|
| 0 | 질문, 지표, Workload, 결과 schema와 공정성 기준 | 완료 |
| 1 | Java Benchmark Workload와 로컬 검증 | 완료 |
| 2 | k6, Experiment Runner, 자동 결과 수집 | 완료 |
| 3 | VMware Kubernetes, Cilium, 관측 스택 | 완료 |
| 4 | No Mesh 기준선 | 완료 |
| 5 | Sidecar 기준선 | 완료 |
| 6 | Ambient 기준선 (고정 replica) | 완료 |
| 7 | Ambient + Waypoint 기준선 | blocked 최종 확정 (버전 독립적 비호환) |
| 8 | profile 간 통계 비교와 병목 선정 | 완료 |
| 9 | 개선안별 단일 변수 실험 | 진행 중 (실험 1 완료·가설 기각, 실험 2 진행) |
| 10 | 회복탄력성·Chaos 재검증 | 예정 |
| 11 | 최종 Matrix, 재현성, 보고서 | 예정 |

세부 내용은 [전체 Phase](docs/phases/README.md), [Workload 개발 Phase](docs/phases/application-development.md),
[실험 계획](docs/experiments/README.md), 진행 중인 작업의 최신 상태는 [CURRENT.md](docs/CURRENT.md)를
따른다.

## 문서 지도

| 영역 | 문서 |
|---|---|
| 목표 | [프로젝트 개요](docs/00-project-overview.md), [범위와 성공 기준](docs/01-scope-and-success-criteria.md) |
| 구조 | [전체 아키텍처](docs/02-architecture.md), [Workload 설계](docs/application/README.md) |
| 인프라 | [플랫폼](docs/infrastructure/README.md), [Mesh](docs/infrastructure/network-and-mesh.md), [관측](docs/infrastructure/observability-and-operations.md) |
| 실행 | [전체 Phase](docs/phases/README.md), [Workload Phase](docs/phases/application-development.md) |
| 계약 | [계약 인덱스](contracts/README.md), [API와 데이터](docs/application/api-and-data.md) |
| 진행 상태 | [CURRENT](docs/CURRENT.md), [Phase 체크리스트](docs/checkpoints/phase-checklists.md) |
| 개념 | [핵심 개념과 용어](docs/03-concepts-and-glossary.md), [무엇을 왜 테스트했는가](docs/testing-explained.md) |
| 검증 | [실험 계획](docs/experiments/README.md), [Evidence](docs/evidence-management.md) |
| 결정 | [ADR](docs/decisions/README.md), [위험과 백로그](docs/risks-and-backlog.md) |

## 결론의 제한

결과는 사용한 하드웨어, VMware, Kubernetes/Istio/Cilium 버전, Workload와 부하 범위에만 적용한다.
"Ambient가 항상 빠르다" 같은 보편 결론을 주장하지 않는다. 모든 보고서에는 환경, 반복 횟수, 분포, 이상치,
무효화 조건, confound(예: 비교 대상 간 Istio 버전 차이)와 실패하거나 기각된 개선 가설도 그대로 포함한다.

## 현재 상태

- 완료: Phase 0~6, Phase 8 (설계 · Workload · Runner · 플랫폼 · No-Mesh/Sidecar/Ambient 기준선 · profile 간
  통계 비교)
- blocked: Phase 7 Waypoint — waypoint→backend 연결 실패가 Istio 1.30.3/1.29.6 양쪽에서 동일하게
  재현되어 버전 독립적 비호환으로 최종 확정
- 진행 중: Phase 9 개선 실험 — 실험 1(Sidecar mTLS DISABLE)은 완료되어 가설 기각(mTLS는 Sidecar network
  overhead의 ~3%만 설명), 실험 2(Ambient replica 확장에 따른 latency 저하 정식 확인) 진행 중
- 다음 Gate: 실험 2 결과 종합 후 Phase 9 결론 확정, Phase 10(회복탄력성) 착수
