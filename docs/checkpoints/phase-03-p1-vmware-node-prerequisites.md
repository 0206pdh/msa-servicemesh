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
- [x] 세 노드 inventory 파일 생성(`/tmp/<hostname>-inventory.txt`)
- [ ] UUID/MAC 고유성 Evidence 저장
- [ ] 재부팅 후 IP/containerd/chrony 설정 유지 검증
- [x] kubeadm Control Plane 초기화(`kube-proxy` 미설치)
- [x] Cilium 설치와 Control Plane `Ready`
- [x] Worker 2대 join과 3노드 `Ready`

## 판정

VM과 Kubernetes 공통 준비, Control Plane 초기화, Worker join 및 Cilium/Hubble 정상화까지 완료됐다. 노드별 inventory 파일은 VM 내부에 있으며, UUID/MAC 및 재부팅 유지 검증과 원본의 저장소 수집이 남아 있어 체크포인트는 `in-progress`를 유지한다.

## 다음 재개 지점

1. 세 노드 inventory 파일을 저장소 Evidence로 수집한다.
2. UUID/MAC 고유성과 재부팅 후 IP/containerd/chrony 유지 상태를 검증한다.
3. Phase 3 P3인 MetalLB/Gateway API 설치로 이동한다.
