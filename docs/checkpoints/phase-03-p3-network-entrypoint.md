# Checkpoint — `phase-03-p3-network-entrypoint`

- Status: completed
- Owner: dohyun
- Started at: 2026-07-22
- Completed at: 2026-07-22
- Related Phase: [Phase 3](../phases/phase-03-platform-foundation.md)
- Evidence: [VM inventory와 네트워크 진입 기반](../evidence/infrastructure/2026-07-22-vm-inventory-and-network-entrypoint.md)

## 완료 체크

- [x] VMnet8 DHCP와 사용 중인 주소 확인
- [x] MetalLB pool `192.168.200.100-192.168.200.110` 고정
- [x] Gateway API 1.4.1 CRD 설치
- [x] Cilium 1.19.6 Gateway API controller 활성화
- [x] MetalLB 0.16.1 L2 설치와 speaker 3/3 Ready
- [x] `GatewayClass/cilium` Accepted
- [x] Gateway Programmed와 HTTPRoute Accepted/ResolvedRefs
- [x] Windows host → MetalLB → Cilium Gateway → backend 요청 성공
- [x] L2 announcer와 interface 확인
- [x] smoke 리소스 cleanup

## 다음 재개 지점

1. P1의 UUID와 재부팅 유지 Evidence를 보완한다.
2. Phase 3 P4 관측 스택을 노드 headroom에 맞춰 배포한다.
