# Kubernetes 3노드와 Cilium/Hubble 기반

- Status: validated-foundation
- Date: 2026-07-22
- Source: 사용자 제공 Control Plane 명령 출력

## 구성

| 노드 | 역할 | 내부 IP | 상태 |
|---|---|---|---|
| `mesh-cp-01` | control-plane | `192.168.200.10` | Ready |
| `mesh-worker-01` | worker | `192.168.200.11` | Ready |
| `mesh-worker-02` | worker | `192.168.200.12` | Ready |

확인된 버전과 환경은 다음과 같다.

- Kubernetes: `v1.36.2`
- containerd: `2.2.2`
- Cilium: `1.19.6`
- OS: Ubuntu 26.04 LTS
- Kernel: `7.0.0-28-generic (amd64)`
- CNI: Cilium, kube-proxy replacement 활성화

## 검증 결과

- `kubectl get nodes -o wide --watch`: 세 노드가 최종적으로 모두 `Ready`
- Cilium DaemonSet: Desired 3, Current 3, Ready 3, Available 3
- Cilium Agent: 세 노드 모두 `1/1 Running`, restart 0
- Cilium Envoy: 세 노드 모두 `1/1 Running`, restart 0
- Cilium Operator: 2개 모두 `1/1 Running`
- CoreDNS: 2개 모두 `1/1 Running`
- Hubble Relay: `1/1 Running`, readiness true
- Hubble UI: frontend/backend `2/2 Running`, readiness true

## 설치 시간 초과 분석

첫 `helm install --wait`와 Worker join 직후의 `helm upgrade --wait`는 Hubble Deployment의 progress deadline 때문에 실패했다. Pod 이벤트에는 Control Plane 한 대뿐일 때 `untolerated taint`로 스케줄링할 수 없었다는 기록이 있다.

Worker가 추가된 뒤 Relay와 UI는 `mesh-worker-01`에 배치됐다. 이미지를 정상적으로 pull하고 컨테이너를 시작했으며 readiness도 통과했다. Cilium을 제거하거나 재설치하지 않고 기존 리소스가 정상화됐으므로, 이 실패는 구성 결함이 아닌 일시적인 배치 조건 부족으로 분류한다.

## 보안과 재현성

- kubeadm join token과 discovery hash는 임시 Secret이므로 이 Evidence에 저장하지 않는다.
- 새 Worker가 필요하면 `kubeadm token create --print-join-command`로 새 명령을 발급한다.
- Helm values와 정확한 설치 명령은 Phase 3 인프라 코드에 고정해야 한다.

## 남은 Evidence

- VM별 vCPU, memory, disk와 VMware 버전 원본
- UUID/MAC 고유성
- 재부팅 후 고정 IP, containerd, chrony 유지 상태
- Cilium connectivity test와 Hubble flow 관측
- MetalLB/Gateway API 및 관측 스택 검증

이 문서는 플랫폼 기반 설치가 동작한다는 근거이며 성능 측정 Evidence는 아니다.
