# VM inventory와 네트워크 진입 기반

- Status: validated-foundation
- Date: 2026-07-22
- Raw inventory: `raw/2026-07-22-vm-inventory/`
- Post-reboot inventory: `raw/2026-07-22-vm-inventory-post-reboot/`

## VM inventory 판정

| 노드 | vCPU | Memory | Disk | IP | MAC |
|---|---:|---:|---:|---|---|
| `mesh-cp-01` | 2 | 5.2 GiB | 55 GB | `192.168.200.10/24` | `00:0c:29:d7:6a:78` |
| `mesh-worker-01` | 2 | 5.2 GiB | 55 GB | `192.168.200.11/24` | `00:0c:29:23:33:f8` |
| `mesh-worker-02` | 2 | 5.2 GiB | 55 GB | `192.168.200.12/24` | `00:0c:29:3d:5c:69` |

- 세 MAC은 고유하다.
- 세 VM product UUID는 각각 `D3DB4D56-BAF7-B7CA-8AF3-41E764D76A78`, `7F1E4D56-4C0A-D8AA-AB37-E788372333F8`, `55344D56-3F8C-D55A-8AC1-4FDF8D3D5C69`이며 모두 고유하다.
- 세 노드 모두 swap 0, IP forwarding과 bridge netfilter 1이다.
- `containerd`, `kubelet`, `chrony`는 enabled/active다.
- system clock은 synchronized이며 동일한 Canonical NTP source와 정상 leap status를 보고했다.
- Kubernetes 1.36.2 세 노드, Cilium Agent/Envoy 3개, Operator 2개와 Hubble Relay/UI가 Ready다.
- DMI product UUID는 sudo를 사용해 별도로 수집했다.

## 순차 재부팅 검증

`mesh-worker-01`, `mesh-worker-02`, `mesh-cp-01` 순서로 재부팅했다. 각 노드 복구 후 다음 노드로 진행했다.

- 세 노드의 고정 IP와 MAC이 유지됐다.
- `containerd`, `kubelet`, `chrony`가 자동 시작됐고 시간 동기화가 정상화됐다.
- Kubernetes 세 노드가 모두 `Ready`로 복구됐다.
- Control Plane의 etcd, API server, controller manager, scheduler와 CoreDNS 2개가 Ready로 복구됐다.
- Cilium Agent/Envoy `3/3`, Operator `2/2`, Hubble Relay/UI가 Ready로 복구됐다.
- MetalLB Controller `1/1`, Speaker `3/3`과 `GatewayClass/cilium` Accepted 상태가 유지됐다.

## MetalLB 주소 선정

- VMnet8 subnet: `192.168.200.0/24`
- host/NAT gateway: `192.168.200.1`, `192.168.200.2`
- VMware DHCP range: `192.168.200.128-192.168.200.254`
- 고정 node range: `192.168.200.10-192.168.200.12`
- 선정 pool: `192.168.200.100-192.168.200.110`

선정 pool은 DHCP와 고정 node 주소 밖에 있고 설치 직전 Windows host의 ping과 ARP 검사에서 사용 중인 주소가 없었다.

## 설치 기준

- Gateway API CRD: 1.4.1 standard channel
- Cilium: 1.19.6, `gatewayAPI.enabled=true`
- MetalLB chart/app: 0.16.1, L2 only, FRR/FRR-K8s disabled
- MetalLB speaker: 세 노드 `3/3 Ready`
- `GatewayClass/cilium`: Accepted

## 외부 진입 smoke

임시 `gateway-smoke` Namespace에 HTTP backend, Gateway와 HTTPRoute를 배포했다.

- MetalLB assigned IP: `192.168.200.100`
- Gateway Programmed: `True`
- HTTPRoute Accepted: `True`
- HTTPRoute ResolvedRefs: `True`
- L2 announcer: `mesh-worker-01`, interface `ens32`
- Windows host `curl http://192.168.200.100/`: HTTP request 성공 및 backend UTC 응답 확인

검증 후 임시 Namespace와 관련 리소스를 제거했다. 주소는 pool로 반환됐다.

## 남은 Gate

- Benchmark Gateway를 동일 경로에 배포한 영구 진입 검증

## Hubble export

- Hubble CLI: `v1.19.4`
- Relay healthcheck: `Ok`
- Connected nodes: `3/3`
- Flow buffer: `4,699/12,285`
- Export: `raw/2026-07-22-hubble/flows.jsonl` 150 JSON lines

`kubectl port-forward service/hubble-relay 4245:80`을 통해 cluster-wide Relay API를 조회했다. status와 flow 원본을 저장한 뒤 port-forward 프로세스를 종료했다.
