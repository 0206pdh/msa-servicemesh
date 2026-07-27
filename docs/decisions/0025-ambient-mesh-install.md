# ADR-0025: Ambient mesh (ztunnel) 설치와 자원 귀속 모델

- 상태: accepted
- 날짜: 2026-07-27

## Context

Phase 6은 Istio Ambient mode(ztunnel)를 No Mesh/Sidecar와 동일한 SYNC_CHAIN 조건(8/17/22 RPS)으로
측정해야 한다. 이 클러스터는 이미 Cilium 1.19.6을 `kube-proxy-replacement: true`, `routing-mode: tunnel`
(VXLAN overlay)로 CNI/서비스 라우팅에 사용 중이고(Phase 3), Istio 1.30.3 istiod가 Sidecar profile용으로
이미 설치돼 있다(Phase 5, ADR-0024). Ambient mode는 Sidecar와 근본적으로 다른 자원 모델을 가진다 —
Envoy sidecar는 Pod마다 하나씩 붙지만, ztunnel은 **노드마다 하나씩** DaemonSet으로 떠서 그 노드의 모든
enrolled Pod trafic을 처리한다. 따라서 "Pod당 proxy 비용"이라는 Phase 5의 귀속 방식을 그대로 쓸 수 없다.

## Decision

### 버전과 설치 방식

`istio/cni`와 `istio/ztunnel` Helm chart 1.30.3(기존 istiod와 동일 버전)을 설치한다. `istio-cni`는
`kube-system`에, `ztunnel`은 `istio-system`에 DaemonSet으로 배포한다. Sidecar와 마찬가지로 Helm 기반
설치로 통일한다.

### Cilium과의 공존 확인 절차

Cilium이 kube-proxy-replacement + VXLAN tunnel mode인 조합은 Istio ambient의 iptables 기반 리다이렉션과
알려진 상호작용 이슈가 있을 수 있는 조합이다. 사전 문서 조사만으로 안전을 단정하지 않고, Phase 5와 동일한
방식으로 설치 직후 실제 트래픽과 mTLS를 직접 검증한다(Envoy 대신 ztunnel 로그/HBONE 연결 상태 확인).
호환성 문제가 실제로 발생하면 그 증상과 원인을 그대로 기록하고 국소적으로 해결한다. **단, Cilium의
kube-proxy-replacement 자체를 끄거나 CNI 근본 설정을 바꾸는 조치는 이미 완료된 Phase 4/5 Evidence의
네트워킹 전제를 흔드는 큰 변경이므로, 그 수준의 변경이 필요하면 진행 전에 사용자에게 확인한다.**

### Namespace 전환

`benchmark` namespace를 Sidecar에서 Ambient로 전환할 때 두 dataplane mode가 동시에 적용되지 않도록
한다. Sidecar 주입에 썼던 `istio.io/rev=default` 라벨을 제거하고 `istio.io/dataplane-mode=ambient`
라벨을 추가한다. Helm `sidecar.enabled`는 `false`로 되돌려 pod annotation 주입을 끈다. 전환 후
애플리케이션 Pod는 다시 `1/1`(주입된 proxy 컨테이너 없음)이어야 한다.

### 자원 귀속 모델

ztunnel의 CPU/메모리는 `resources.sidecar`가 아니라 **새 `resources.ztunnel` 슬롯**에 기록하고, Pod당
정규화(request 당 나누기)하지 않는다. 대신 노드 단위 절대값(해당 노드의 ztunnel DaemonSet Pod 1개의
CPU-seconds/메모리 peak)과, 그 노드가 처리한 실험 traffic 비율을 함께 기록해 "이 실험이 유발한 몫"을
추정할 수 있게 한다. 여러 Pod가 공유하는 자원이므로 Sidecar처럼 "1 Pod = 1 proxy 비용"으로 단순화하면
과소평가하거나(다른 워크로드와 공유) 과대평가한다(이 실험 전용이 아닌 배경 비용까지 포함).

## Alternatives

- **Pod당 정규화(Sidecar와 동일 계산)**: ztunnel이 실제로 Pod 단위가 아니므로 통계적으로 오해를 유발한다.
  기각.
- **ztunnel 자원을 아예 측정하지 않고 앱 자원만 비교**: Ambient의 핵심 트레이드오프(공유 tunnel 비용)를
  누락하게 되어 프로젝트 목적(§ concepts-and-glossary.md의 ztunnel 항목)과 어긋난다. 기각.

## Consequences

- `experiments/runner/kubernetes.py`에 `ztunnel*` 쿼리(DaemonSet 전체가 아니라 실험이 도는 노드의 ztunnel
  Pod로 한정)와 `resources.ztunnel` summary 필드가 추가된다.
- Ambient Evidence는 Sidecar Evidence와 "Pod당 비용" 대 "노드당 공유 비용"이라는 다른 단위로 보고되며,
  1:1 직접 비교 시 이 차이를 반드시 명시한다.
- `deploy/environments/ambient/values.yaml`이 `sidecar.enabled: false`로 추가된다.

## Validation and rollback

- 설치 후 ztunnel DaemonSet이 3노드 모두 `Ready`인지 확인한다.
- SYNC_CHAIN E2E가 정상 동작하고 ztunnel을 통한 mTLS(HBONE)가 적용됨을 직접 확인한 뒤에만 정식 측정을
  시작한다.
- Cilium 설정 변경이 필요할 정도의 비호환이 발견되면 설치를 중단하고 사용자에게 보고한다.
