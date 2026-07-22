# 인프라 설계

## 목표

VMware 기반 재현 가능한 3노드 Kubernetes에서 네 Mesh profile과 개선 설정을 동일 조건으로 배포·측정한다.

## 후보 토폴로지

```text
Windows/VMware Host
├── control-plane-01  4 vCPU / 8 GB
├── worker-01         8 vCPU / 16 GB
├── worker-02         8 vCPU / 16 GB
└── load-generator    가능하면 별도 VM 또는 headroom 증명
```

실제 사양과 관측 스택 requests/limits는 노드 inventory와 idle headroom을 수집한 뒤 고정한다.

## Namespace

- `benchmark`: 측정 Workload
- `messaging`: Kafka와 결과 저장 후보
- `observability`: Prometheus/Loki/Tempo/OTel/Grafana
- `experiment`: Runner, k6, Chaos
- `istio-system`: Istio/ztunnel
- `gateway-system`: 선택한 Gateway controller

## 계층

1. OS, NTP, container runtime
2. Kubernetes
3. Cilium/Hubble
4. storage
5. MetalLB L2/Cilium Gateway API
6. observability
7. Benchmark Helm chart
8. Istio profile
9. k6/Chaos/Runner

## 환경 values

```text
deploy/environments/
├── no-mesh/
├── sidecar/
├── ambient/
├── waypoint-all/
└── waypoint-selected/
```

profile 적용 전후 manifest diff를 저장한다. 동일 목적의 Cilium/Istio 정책을 중복 적용하지 않는다.

배포는 GitOps controller 없이 저장소의 version-pinned Helm values와 manifest를 순서대로 직접 적용한다. 결정 근거는 ADR-0011을 따른다.

## 안전

- Chaos는 benchmark Namespace와 label allowlist만 대상으로 한다.
- control plane, storage 데이터, 호스트에는 적용하지 않는다.
- cleanup 검증 전 다음 run을 시작하지 않는다.
- Secret과 kubeconfig는 결과에 저장하지 않는다.
