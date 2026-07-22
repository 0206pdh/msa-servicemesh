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
| [ADR-0011](0011-delivery-and-observability-baseline.md) | accepted | 직접 배포와 경량 관측 스택 기준 |
| [ADR-0017](0017-pivot-to-sre-response-platform.md) | superseded | SRE 제품 전환안 폐기 |
| [ADR-0020](0020-performance-engineering-project.md) | accepted | Service Mesh Performance Engineering으로 확정 |
| [ADR-0021](0021-benchmark-workload-boundaries.md) | accepted | 통신 패턴 기반 Benchmark Workload |
| [ADR-0022](0022-improvement-validation-loop.md) | accepted | 비교 후 병목 개선과 재측정을 필수화 |

과거 항공 및 SRE 제품 서비스 경계 ADR은 현재 구조에 적용하지 않는다.

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
