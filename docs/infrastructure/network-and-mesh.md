# 네트워크와 Service Mesh

## 책임 분리

| 기능 | 기본 소유자 |
|---|---|
| Pod 네트워크와 NetworkPolicy | Cilium |
| Flow 관측과 L3/L4 drop | Hubble |
| LoadBalancer IP | MetalLB |
| 인바운드 API | 선택한 단일 Gateway API controller |
| 서비스 간 mTLS와 Mesh profile | Istio |
| L7 retry/timeout | 앱 우선, 실험 시 Istio와 명시 비교 |

Cilium과 Istio가 같은 정책을 중복 소유하지 않게 한다. Gateway controller는 호환성 검증 후 하나만 선택한다.

## 기본 흐름

```text
Load Generator → MetalLB IP → Gateway → benchmark-gateway
gateway → orchestrator → workload targets
producer → Kafka → workers
Experiment Runner → control endpoints/Chaos
```

## NetworkPolicy

- 모든 애플리케이션 Namespace는 default-deny로 시작한다.
- Gateway만 외부 인바운드를 받는다.
- 데이터면 서비스는 필요한 downstream/Kafka 흐름만 허용한다.
- 제어 endpoint는 experiment Namespace에서만 접근한다.
- Experiment Runner는 benchmark Namespace의 allowlist 자원만 변경한다.

## 비교 Profile

| Profile | Data plane | L7 | 주요 비용 |
|---|---|---|---|
| No Mesh | Cilium | 앱 telemetry | 기준선 |
| Sidecar | Pod별 Envoy | 지원 | Pod별 CPU/메모리, 시작시간 |
| Ambient | 노드별 ztunnel | 제한 | 공유 노드 비용, 경로 지연 |
| Ambient + Waypoint | ztunnel + 선택 Envoy | 선택 경로 | Waypoint 병목과 비용 |

## 실험 질문

- Mesh가 정상 p95/p99와 최대 처리량에 주는 비용은 얼마인가?
- 장애 중 retry amplification과 cascade 범위가 달라지는가?
- Sidecar/Waypoint의 L7 telemetry가 진단 정확도나 MTTD를 개선하는가?
- 워크로드가 10/50/100 Pod로 증가할 때 비용 증가 형태는 어떤가?
- Waypoint는 어떤 서비스 경로에만 둘 때 비용 대비 효과가 좋은가?

모든 profile은 동일 이미지, replica, resource limit, node placement, 부하, Chaos 정의를 사용한다.
