# ADR-0024: Istio Sidecar 설치 버전과 자원 크기

- 상태: accepted
- 날짜: 2026-07-25

## Context

Phase 5는 Istio Sidecar profile을 No Mesh baseline과 동일 조건으로 비교해야 한다. 이 클러스터는
`mesh-worker-01`/`mesh-worker-02` 각각 allocatable 2 vCPU, 5,386,900Ki(~5.14Gi) 메모리이며, 측정 시작
시점 기준 이미 다음을 요청 중이다.

| 노드 | CPU 요청 | 메모리 요청 |
|---|---:|---:|
| mesh-worker-01 | 520m (26%) | 938Mi (17%) |
| mesh-worker-02 | 770m (38%) | 1,706Mi (32%) |

Istio 공식 Helm chart(`istio/istiod` 1.30.3)의 기본값은 istiod(pilot) 요청 500m CPU/2,048Mi 메모리(제한
없음), Envoy sidecar(`global.proxy`) 요청 100m CPU/128Mi 메모리·제한 2000m CPU/1,024Mi 메모리다. `benchmark`
namespace의 애플리케이션 Pod 8개(gateway/orchestrator/workload-a·b·c/producer/worker/kafka) 전부에 sidecar가
주입되므로, worst-case(istiod와 다수 sidecar가 한 노드에 몰릴 경우) 요청 합이 노드 CPU headroom을 초과할 수
있다(계산: istiod 500m + sidecar 8×100m = 1,300m vs `mesh-worker-02`의 CPU headroom 1,230m).

## Decision

### 버전

`istio/istiod`와 `istio/base` Helm chart 1.30.3(App Version 1.30.3)을 사용한다. Kubernetes 1.36.2와
함께 동작을 확인한 뒤 진행한다. Istio ingress gateway chart는 설치하지 않는다 —
[network-and-mesh.md](../infrastructure/network-and-mesh.md)에 따라 모든 profile은 `GatewayClass/cilium`을
공통 진입점으로 유지하고 Istio ingress gateway는 기본 비교 경로에서 제외한다.

### 자원 크기 (기본값 대비 축소, 근거와 함께)

| 컴포넌트 | 항목 | Istio 기본값 | 이 클러스터 설정 |
|---|---|---:|---:|
| istiod | CPU 요청 | 500m | 200m |
| istiod | 메모리 요청 | 2,048Mi | 512Mi |
| istiod | CPU/메모리 제한 | 없음 | 1000m / 1,024Mi |
| Envoy sidecar | CPU 요청 | 100m | 20m |
| Envoy sidecar | 메모리 요청 | 128Mi | 64Mi |
| Envoy sidecar | CPU/메모리 제한 | 2000m / 1,024Mi | **변경 없음 (2000m / 1,024Mi 유지)** |

**요청(request)만 낮추고 제한(limit)은 Istio 기본값을 그대로 유지한다.** 요청은 스케줄링 시 노드가
확보해주는 최소값일 뿐 실제 사용량 상한이 아니며, 제한은 실제 cgroup 사용량을 강제로 억누른다. Phase 5의
목적 자체가 "Envoy sidecar의 실제 CPU/메모리 비용"을 측정하는 것이므로, 제한을 낮게 잡아 인위적으로
throttling을 유발하면 측정하려는 값 자체를 왜곡하는 confounding variable이 된다. 반면 8~22 RPS, 1ms
hop delay, 1 KiB payload 수준의 부하에서 Envoy 하나가 기본 제한(2 vCPU)에 근접할 가능성은 낮으므로, 요청만
줄여 스케줄링 여유를 확보하고 실측값은 왜곡 없이 그대로 수집한다.

축소된 요청 기준 worst-case 합산(istiod + sidecar 8개가 한 노드에 몰리는 경우): CPU 200m + 8×20m = 360m,
메모리 512Mi + 8×64Mi ≈ 1,024Mi. 두 워커 노드 모두 현재 headroom(최소 1,230m CPU / 3,680Mi 메모리) 안에
여유 있게 들어간다.

### mTLS

먼저 sidecar 주입만 적용하고 PERMISSIVE(Istio mesh 기본값)로 E2E 트래픽이 정상 통과하는지 확인한 뒤,
`benchmark` namespace에 STRICT `PeerAuthentication`을 적용하고 다시 검증한다. 이 단계적 순서는 문제
발생 시 mTLS 강제와 sidecar 주입 중 어느 쪽이 원인인지 구분하기 위함이다.

### NetworkPolicy

기존 `meshperf-default-deny`는 `benchmark` namespace Pod의 모든 egress를 기본 차단한다. Envoy sidecar가
istiod(`istiod.istio-system.svc:15012`)로 xDS discovery 트래픽을 보내려면 egress 허용이 추가로 필요하다.
`sidecar.enabled=true`일 때만 적용되는 `meshperf-istiod-egress` NetworkPolicy를 chart에 추가한다
(No Mesh values는 영향받지 않는다).

## Alternatives

- **Istio 기본값 그대로 설치**: worst-case 스케줄링 실패 위험이 있고, 이미 알려진 이 클러스터의
  자원 제약(Phase 4에서 tail latency 노이즈의 원인으로 지목된 2 vCPU 노드) 위에 추가 압박을 준다. 기각.
- **`istioctl`로 minimal/demo profile 설치**: `istioctl`이 로컬에 없고 별도 설치가 필요하며, Helm 기반
  배포로 통일하는 기존 프로젝트 관례(No Mesh도 Helm)와 어긋난다. Helm chart 값 직접 조정이 동일한
  결과를 더 적은 도구로 달성한다. 기각.
- **제한(limit)도 함께 축소**: 스케줄링 여유는 더 커지지만 실측 CPU/메모리 값 자체가 인위적으로
  눌릴 위험이 있어 Phase 5의 측정 목적과 상충한다. 기각.

## Consequences

- `deploy/charts/meshperf`에 `sidecar.*` values 블록과 조건부 sidecar injection annotation, 조건부
  NetworkPolicy가 추가된다. `deploy/environments/no-mesh/values.yaml`은 변경하지 않는다(기본 `sidecar.enabled: false`).
- `deploy/environments/sidecar/values.yaml` 신규 파일이 이 자원 크기와 mTLS 순서를 값으로 반영한다.
- 이후 Phase 5 Evidence에 이 축소된 요청값을 명시해, Sidecar 자원 비용 수치를 다른(기본값) Istio
  배치와 비교할 때 요청/제한 차이를 감안하도록 한다.

## Validation and rollback

- `helm show values istio/istiod --version 1.30.3`로 기본값을 확인 후 이 문서의 표와 대조했다.
- 설치 후 `kubectl top`/`kubectl describe node`로 실제 스케줄링과 여유를 재확인한다.
- 자원 부족으로 Pod가 `Pending`/`OOMKilled` 상태가 반복되면 요청값을 이 문서를 갱신하며 조정한다.
