# ADR-0006: 플랫폼 네트워크 기준선

- 상태: accepted
- 날짜: 2026-07-22

## Context

No Mesh, Istio Sidecar, Ambient, Waypoint를 비교할 때 Pod 네트워크와 외부 진입 경로가 바뀌면 Mesh 비용과 플랫폼 네트워크 비용을 분리할 수 없다. 현재 클러스터는 kube-proxy 없이 Cilium 1.19.6과 Hubble을 사용한다.

## Decision

- Cilium을 모든 profile의 CNI, kube-proxy replacement, NetworkPolicy 구현으로 유지한다.
- Hubble을 모든 profile의 L3/L4 flow와 drop Evidence 원본으로 사용한다.
- MetalLB는 VMnet8의 LoadBalancer 주소를 L2 mode로 광고하는 역할만 맡긴다.
- 공통 인바운드는 Gateway API를 사용하며 controller 선택은 ADR-0010을 따른다.
- Cilium과 Istio가 동일한 정책, retry 또는 timeout을 동시에 소유하지 않게 한다.
- 설치 chart, CRD, image 버전과 실제 Helm values를 저장소에 고정한다.

## Alternatives

- Cilium LB IPAM: 구성 요소는 줄지만 MetalLB를 기술 기준선으로 정한 기존 범위와 달라진다.
- NodePort: 단순하지만 실제 LoadBalancer 진입 경로를 검증하지 못한다.
- profile별 Gateway 변경: 각 Mesh의 기능은 드러나지만 공정한 데이터면 비용 비교가 불가능하다.

## Consequences

- 네 profile에서 CNI, LoadBalancer, Gateway 경로가 동일하다.
- Cilium Gateway의 Envoy 비용은 공통 플랫폼 비용으로 취급하고 모든 run에서 별도로 기록한다.
- Gateway controller 자체 비교는 별도 experiment ID로만 수행한다.

## Validation and rollback

- MetalLB 주소 할당, ARP 광고, 외부 호스트 접근, Gateway/HTTPRoute 상태와 Hubble flow를 검증한다.
- 주소 충돌이나 VMnet8 L2 광고 문제가 있으면 설치를 중단하고 IP pool을 재선정한다. NodePort를 측정 기준선으로 대체하지 않는다.
