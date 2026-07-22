# Checkpoint — `phase-03-p2-kubernetes-cilium`

- Status: completed
- Owner: dohyun
- Started at: 2026-07-22
- Completed at: 2026-07-22
- Related Phase: [Phase 3](../phases/phase-03-platform-foundation.md)
- Evidence: [Kubernetes 3노드와 Cilium/Hubble](../evidence/infrastructure/2026-07-22-kubernetes-cilium-foundation.md)

## 목표

kube-proxy 없이 Kubernetes 3노드를 구성하고, 이후 Istio 비교 실험과 공존할 수 있는 Cilium/Hubble 네트워크 기반을 준비한다.

## 완료 체크

- [x] `mesh-cp-01` Control Plane 초기화
- [x] kube-proxy 미설치 구성
- [x] `mesh-worker-01`, `mesh-worker-02` join
- [x] 세 노드 내부 IP와 hostname 일치
- [x] 세 노드 Kubernetes `Ready`
- [x] Cilium Agent와 Envoy가 세 노드에서 `Running`
- [x] Cilium Operator 2개 `Running`
- [x] CoreDNS 2개 `Running`
- [x] Hubble Relay와 UI `Running` 및 Ready
- [x] Cilium Helm 릴리스 정상화
- [x] join token 값을 저장소에 기록하지 않음

## 설치 중 발생한 문제와 판정

초기 Cilium 설치의 `--wait`는 Control Plane 한 대만 존재할 때 시간 초과됐다. 당시 Hubble Relay/UI는 Control Plane taint를 허용하지 않아 스케줄링할 수 없었고 Cilium Operator도 목표 2개 중 1개만 Available이었다.

Worker 두 대를 join한 뒤 Cilium DaemonSet은 `3/3` Ready가 됐고, Hubble 이미지 다운로드와 컨테이너 시작이 끝나면서 Relay/UI가 자동 정상화됐다. 따라서 원인은 Cilium 설정 오류가 아니라 설치 순서상 일시적인 스케줄링 부족으로 판정한다.

## 다음 재개 지점

1. VM 원본 inventory와 재부팅 유지 Evidence를 보강한다.
2. MetalLB와 Gateway API를 설치한다.
3. 관측 스택을 배포하고 Phase 2 runner의 Kubernetes 검증을 수행한다.
