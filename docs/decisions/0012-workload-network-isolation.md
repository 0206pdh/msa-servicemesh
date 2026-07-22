# ADR-0012 — Workload NetworkPolicy 최소 허용 기준

- Status: accepted
- Date: 2026-07-22

## 결정

`benchmark` namespace의 Mesh Performance Workload는 Cilium이 집행하는 기본 ingress/egress deny 정책을 사용한다. 다음 흐름만 명시적으로 허용한다.

- Cilium Gateway `reserved:ingress` → benchmark-gateway:8080
- benchmark-gateway → orchestrator-service, producer-service:8080
- orchestrator-service → workload-a → workload-b → workload-c:8080
- workload-c → workload-c:8080
- producer-service, worker-service ↔ Kafka:9092
- Kafka self controller/broker:9092,9093
- 모든 Workload → CoreDNS:53
- Java 서비스 → OTel Collector:4318
- Prometheus → Java actuator:8080

Kubernetes NetworkPolicy로 Pod와 namespace 기반 흐름을 정의하고, Cilium Gateway의 source가 일반 Pod가 아닌 `reserved:ingress` identity로 전달되는 진입 경로만 CiliumNetworkPolicy `fromEntities: ingress`를 사용한다.

## 근거

Gateway 구현 namespace를 기준으로 허용하면 실제 datapath identity와 일치하지 않았다. Hubble에서 source identity `8`, label `reserved:ingress`가 `benchmark-gateway:8080`에서 `POLICY_DENIED`되는 것을 확인했다. Cilium identity를 직접 허용하면 외부 진입을 복구하면서 임의 Pod의 직접 호출은 계속 차단된다.

## 결과

- no-mesh와 이후 mesh profile이 동일한 L3/L4 경계를 공유한다.
- 서비스 간 우회 호출은 실험 경로에 포함되지 않는다.
- 정책 변경은 Helm revision과 Evidence로 추적한다.
- 새 dependency를 추가할 때 해당 통신 규칙과 차단/허용 검증을 함께 갱신해야 한다.
