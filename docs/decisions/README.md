# Architecture Decision Records

| ID | 상태 | 결정 |
|---|---|---|
| ADR-0003 | accepted | VMware 3노드 Kubernetes를 실험 환경으로 사용 |
| ADR-0004 | accepted | No Mesh/Sidecar/Ambient/Waypoint 비교 |
| [ADR-0006](0006-platform-network-baseline.md) | accepted | Cilium, MetalLB, Gateway API 기준 |
| [ADR-0007](0007-java-and-frontend-baseline.md) | accepted | Java 25/Spring Boot/Gradle, React/TypeScript |
| [ADR-0010](0010-gateway-api-controller.md) | accepted | Cilium Gateway API를 공통 인바운드로 사용 |
| [ADR-0012](0012-workload-network-isolation.md) | accepted | 기본 deny와 Workload 최소 허용 통신 경계 |
| [ADR-0013](0013-kubernetes-run-validity-gates.md) | accepted | Kubernetes telemetry/headroom/cleanup 자동 무효화 Gate |
| [ADR-0014](0014-measurement-repetition-and-load-policy.md) | accepted | capacity 기반 부하와 10~15회 정밀도 기반 반복 |
| [ADR-0011](0011-delivery-and-observability-baseline.md) | accepted | 직접 배포와 경량 관측 스택 기준 |
| [ADR-0017](0017-pivot-to-sre-response-platform.md) | superseded | SRE 제품 전환안 폐기 |
| [ADR-0020](0020-performance-engineering-project.md) | accepted | Service Mesh Performance Engineering으로 확정 |
| [ADR-0021](0021-benchmark-workload-boundaries.md) | accepted | 통신 패턴 기반 Benchmark Workload |
| [ADR-0022](0022-improvement-validation-loop.md) | accepted | 비교 후 병목 개선과 재측정을 필수화 |
| [ADR-0023](0023-hybrid-absolute-relative-precision-gate.md) | accepted | 정밀도 정지 기준에 절대값(ms) 기준 추가 |
| [ADR-0024](0024-istio-sidecar-install.md) | accepted | Istio 1.30.3 Helm 설치와 클러스터 맞춤 자원 크기 |
| [ADR-0025](0025-ambient-mesh-install.md) | accepted | ztunnel 설치와 노드 단위 공유 자원 귀속 모델 |
| [ADR-0026](0026-waypoint-deployment-scope.md) | accepted | Waypoint 선택 경로(단일 hop) 우선 배치와 자원 모델 |
| [ADR-0027](0027-replica-scaling-study-scope.md) | accepted | Replica 확장 비용 연구를 방향성 확인 범위로 축소 |
| [ADR-0028](0028-phase9-sidecar-mtls-disable-experiment.md) | accepted | Phase 9 개선 실험 1 — Sidecar mTLS DISABLE 단일 변수 실험 |
| [ADR-0029](0029-phase9-ambient-replica-scaling-formal-experiment.md) | accepted | Phase 9 개선 실험 2 — Ambient replica 확장 latency 저하 정식 확인 |

## 템플릿

```markdown
# ADR-NNNN: 제목
- 상태: proposed | accepted | superseded | rejected
- 날짜:
- supersedes/superseded by:
## Context
## Decision
## Alternatives
## Consequences
## Validation and rollback
```
