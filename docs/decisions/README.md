# Architecture Decision Records

| ID | 상태 | 결정 |
|---|---|---|
| ADR-0003 | accepted | VMware 3노드 Kubernetes를 실험 환경으로 사용 |
| ADR-0004 | accepted | No Mesh/Sidecar/Ambient/Waypoint 비교 |
| ADR-0006 | proposed | Cilium, MetalLB, Gateway API 기준 |
| [ADR-0007](0007-java-and-frontend-baseline.md) | accepted | Java 25/Spring Boot/Gradle, React/TypeScript |
| ADR-0010 | proposed | Gateway API controller owner |
| ADR-0011 | proposed | GitOps 포함 여부 |
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
