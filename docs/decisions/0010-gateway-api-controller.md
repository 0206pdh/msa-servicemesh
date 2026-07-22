# ADR-0010: 공통 Gateway API controller

- 상태: accepted
- 날짜: 2026-07-22

## Context

Gateway controller가 profile마다 달라지면 ingress proxy와 control plane 비용이 Mesh profile 차이에 섞인다. No Mesh에서도 사용할 수 있고 현재 CNI와 함께 운영할 단일 controller가 필요하다.

## Decision

- Cilium Gateway API controller와 `GatewayClass/cilium`을 네 profile의 공통 인바운드로 사용한다.
- Istio ingress gateway는 기본 비교 경로에 배포하지 않는다.
- Gateway, HTTPRoute, backend Service와 요청/제한값은 profile 간 동일하게 유지한다.
- Gateway Envoy의 CPU, memory, request metric을 측정 대상과 분리하여 Ground Truth에 기록한다.
- 내부 서비스 간 통신만 Istio Sidecar, Ambient, Waypoint profile에 따라 변경한다.

## Alternatives

- Istio Gateway: Istio 기능 검증에는 자연스럽지만 No Mesh 기준선에도 Istio control plane과 gateway 비용이 들어간다.
- Envoy Gateway 또는 NGINX Gateway Fabric: 독립성은 높지만 별도 controller 운영과 telemetry 정합 작업이 추가된다.

## Consequences

- 외부 진입 경로가 모든 profile에서 동일해진다.
- 결과는 Cilium Gateway가 포함된 플랫폼 위에서의 Mesh 내부 경로 비교로 한정한다.
- Cilium Gateway 자체 병목은 headroom 검증에서 run 무효화 조건으로 검사한다.

## Validation and rollback

- `GatewayClass` 수락, Gateway programmed, HTTPRoute accepted/resolvedRefs, LoadBalancer IP와 외부 요청 성공을 확인한다.
- 호환성 문제가 있으면 버전과 증상을 Evidence로 남기고 controller 변경은 새 ADR과 별도 기준선으로 수행한다.
