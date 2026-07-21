# Mesh Performance Lab

Mesh Performance Lab은 VMware 기반 온프레미스 Kubernetes에서 Service Mesh 구성의 성능·자원·회복탄력성을 반복 측정하고, 관측된 병목에 개선안을 적용해 효과와 부작용을 정량 검증하는 Performance Engineering 프로젝트다.

이 프로젝트는 비즈니스 제품을 가장하지 않는다. Java/Spring MSA는 동기 체인, 병렬 fan-out, 비동기 worker, 대용량 payload 등 현실적인 통신 패턴을 재현하는 제어 가능한 Benchmark Workload다.

## 중심 질문

> No Mesh, Istio Sidecar, Ambient, Ambient + Waypoint는 워크로드 특성별로 어떤 성능·자원·관측성·회복탄력성 차이를 만들며, 측정된 병목을 어떤 설정과 아키텍처 변경으로 개선할 수 있는가?

## 프로젝트가 답해야 하는 것

- Mesh profile별 p50/p95/p99, throughput, 오류율과 자원 비용은 얼마인가?
- Pod 수와 hop 수, payload, 동시성이 커질 때 비용 증가 형태는 어떻게 달라지는가?
- timeout/retry/circuit breaker의 소유 위치가 장애 전파와 회복에 미치는 영향은 무엇인가?
- Sidecar 또는 Waypoint의 L7 기능이 추가 비용만큼 실질적인 관측·제어 효과를 제공하는가?
- 병목을 개선했을 때 어떤 지표가 좋아지고 어떤 비용이나 기능 손실이 생기는가?
- 워크로드 유형별로 어떤 profile과 설정을 선택해야 하는가?

## 검증 루프

```text
기준선 측정
→ 병목과 Evidence 확인
→ 원인 가설 작성
→ 한 가지 개선 적용
→ 동일 조건 반복 측정
→ 효과·부작용·신뢰구간 분석
→ 적용 조건과 rollback 기준 기록
```

단순 profile 순위표가 아니라 개선 전후 데이터와 조건부 의사결정 Matrix가 최종 산출물이다.

## Benchmark Workload

| 유형 | 구조 | 검증 대상 |
|---|---|---|
| Sync Chain | gateway → hop-a → hop-b → hop-c | hop 누적 지연, mTLS, timeout 전파 |
| Fan-out | orchestrator → target 4개 | 병렬 I/O, 부분 결과, retry 증폭 |
| Async | producer → Kafka → workers | backlog, consumer lag, worker scale |
| Payload | gateway → processor → storage | 크기·compression·proxy CPU |
| Mixed | CPU/Memory/I/O target | 자원 경합, throttling, HPA |

Workload는 지연, 오류율, 응답 크기, CPU, 메모리, fan-out 수와 hop 수를 설정으로 제어한다. 실험용 fault 설정은 인증된 실험 Runner에서만 변경할 수 있다.

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

## Phase

| Phase | 결과 |
|---:|---|
| 0 | 질문, 지표, Workload, 결과 schema와 공정성 기준 |
| 1 | Java Benchmark Workload와 로컬 검증 |
| 2 | k6, Experiment Runner, 자동 결과 수집 |
| 3 | VMware Kubernetes, Cilium, 관측 스택 |
| 4 | No Mesh 기준선 |
| 5 | Sidecar 기준선 |
| 6 | Ambient 기준선 |
| 7 | Ambient + Waypoint 기준선 |
| 8 | profile 비교와 병목 선정 |
| 9 | 개선안별 단일 변수 실험 |
| 10 | 회복탄력성·Chaos 재검증 |
| 11 | 최종 Matrix, 재현성, 보고서 |

세부 내용은 [전체 Phase](docs/phases/README.md), [Workload 개발 Phase](docs/phases/application-development.md), [실험 계획](docs/experiments/README.md)을 따른다.

## 문서 지도

| 영역 | 문서 |
|---|---|
| 목표 | [프로젝트 개요](docs/00-project-overview.md), [범위와 성공 기준](docs/01-scope-and-success-criteria.md) |
| 구조 | [전체 아키텍처](docs/02-architecture.md), [Workload 설계](docs/application/README.md) |
| 인프라 | [플랫폼](docs/infrastructure/README.md), [Mesh](docs/infrastructure/network-and-mesh.md), [관측](docs/infrastructure/observability-and-operations.md) |
| 실행 | [전체 Phase](docs/phases/README.md), [Workload Phase](docs/phases/application-development.md) |
| 계약 | [계약 인덱스](contracts/README.md), [API와 데이터](docs/application/api-and-data.md) |
| 검증 | [실험 계획](docs/experiments/README.md), [Evidence](docs/evidence-management.md) |
| 결정 | [ADR](docs/decisions/README.md), [위험과 백로그](docs/risks-and-backlog.md) |

## 결론의 제한

결과는 사용한 하드웨어, VMware, Kubernetes/Istio/Cilium 버전, Workload와 부하 범위에만 적용한다. “Ambient가 항상 빠르다” 같은 보편 결론을 주장하지 않는다. 모든 보고서에는 환경, 반복 횟수, 분포, 이상치, 무효화 조건과 실패한 개선도 포함한다.

## 현재 상태

- 방향: Service Mesh Performance Engineering으로 확정
- 현재 Phase: Phase 0 완료, Phase 1 시작 준비
- Git 저장소: 아직 생성되지 않음
- 기존 코드: Java/Docker 런타임 골격만 재사용
