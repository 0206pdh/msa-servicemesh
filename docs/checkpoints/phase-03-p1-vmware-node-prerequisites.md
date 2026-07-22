# Checkpoint — `phase-03-p1-vmware-node-prerequisites`

- Status: in-progress
- Owner: dohyun
- Started at: 2026-07-22
- Updated at: 2026-07-22
- Related Phase: [Phase 3](../phases/phase-03-platform-foundation.md)

## 목표

VMware의 Ubuntu 노드 3대를 고정 네트워크와 동일한 Kubernetes/containerd 사전 조건으로 준비한다.

## 확정된 토폴로지

| 역할 | hostname | IP |
|---|---|---|
| Control Plane | `mesh-cp-01` | `192.168.200.10/24` |
| Worker | `mesh-worker-01` | `192.168.200.11/24` |
| Worker | `mesh-worker-02` | `192.168.200.12/24` |

- VMware network: VMnet8 NAT
- Host/Gateway: `192.168.200.1` / `192.168.200.2`
- Guest OS: Ubuntu 26.04 LTS

## 완료 체크

- [x] VMware Workstation 26.0.0 설치 확인
- [x] VM 3대 hostname과 VMnet8 고정 IP 구성
- [x] SSH/Xshell 접속
- [x] 노드 간 이름 해석과 통신 구성
- [x] 공통 패키지와 chrony 설치
- [x] swap 비활성화
- [x] `overlay`, `br_netfilter`, IP forwarding 설정
- [x] containerd CRI 활성화와 `SystemdCgroup=true`
- [x] kubeadm/kubelet/kubectl 공통 설치
- [x] Control Plane Helm 설치
- [ ] 세 노드 최종 검사 출력과 정확한 버전 Evidence 저장
- [ ] UUID/MAC 고유성 Evidence 저장
- [ ] 재부팅 후 IP/containerd/chrony 설정 유지 검증

## 판정

사용자 확인 기준으로 공통 준비 명령은 완료됐다. 명령 출력 원본을 아직 저장하지 않았으므로 상태는 `in-progress`이며, `kubeadm init` 전에 최종 Evidence를 수집한다.

## 다음 재개 지점

1. 세 노드 inventory/버전/UUID/MAC/시간 동기화 출력을 수집한다.
2. Control Plane에서 kubeadm config를 생성하고 preflight를 통과한다.
3. kube-proxy를 설치하지 않고 cluster를 초기화한 뒤 Cilium을 설치한다.
