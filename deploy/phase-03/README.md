# Phase 3 배포

이 디렉터리는 VMware Kubernetes 플랫폼을 재현하는 version-pinned manifest, Helm values와 검증 스크립트를 저장한다. Secret, kubeconfig와 환경별 credential은 저장하지 않는다.

## 확정된 기준

- CNI/NetworkPolicy: Cilium
- flow evidence: Hubble
- LoadBalancer IP: MetalLB L2 mode
- ingress: Cilium Gateway API (`GatewayClass/cilium`)
- delivery: 저장소에서 Helm/manifest 직접 적용, GitOps controller 없음
- observability: kube-prometheus-stack, Loki single binary, Tempo monolithic, OTel Collector Deployment

관련 결정은 ADR-0006, ADR-0010, ADR-0011을 따른다.

## 적용 순서

1. `scripts/collect-vm-evidence.ps1`로 세 노드 원본과 재부팅 유지 상태를 수집한다.
2. VMnet8 DHCP 범위를 확인하고 후보 LoadBalancer 주소에 대해 충돌 검사를 수행한다.
3. chart/CRD 호환 버전을 고정한 뒤 MetalLB L2와 Cilium Gateway API를 적용한다.
4. 외부 호스트부터 `benchmark-gateway`까지의 진입 경로와 Hubble flow를 검증한다.
5. 관측 스택을 배포하고 metric/log/trace round trip과 headroom을 검증한다.
6. Benchmark Helm profile, NetworkPolicy와 Phase 2 Kubernetes adapter를 검증한다.

## 아직 관측 후 고정할 값

다음 값은 미결정 사항이 아니라 환경 관측이 선행되어야 하는 배포 입력이다.

- MetalLB address pool: VMnet8 DHCP 범위 밖, gateway/node IP와 겹치지 않고 ARP 충돌 검사를 통과한 연속 주소
- storage class와 용량: 노드별 disk inventory와 재부팅 유지 검증 후 선택
- 관측 stack requests/limits와 retention: VM memory/disk와 idle headroom 수집 후 선택
- load generator 위치: 별도 VM 사용을 우선하며, 불가능하면 호스트 실행과 CPU headroom Evidence를 필수화

관측 전 placeholder를 manifest에 넣지 않는다. 값이 확정되면 values와 Evidence를 같은 변경에 저장한다.
