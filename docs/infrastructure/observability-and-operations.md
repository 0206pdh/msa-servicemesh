# 관측성과 측정 운영

## 목적

관측 스택은 제품 기능이 아니라 결과와 병목을 설명하는 측정 장비다. 관측 자체의 비용과 drop도 측정 대상이다.

## 구성

- Prometheus: app/JVM/container/node/Istio/Cilium metrics
- Grafana: run별 dashboard와 annotation
- Loki: 제한된 구조화 로그
- Tempo: trace와 hop/fan-out 경로
- OpenTelemetry Collector: trace/metric 처리
- Hubble: flow, drop, policy evidence

## 필수 Metrics

- request rate, duration histogram, error
- downstream calls와 retry count
- active/pending connections
- JVM heap, GC, thread
- CPU usage/throttling, RSS, network
- Envoy CPU/memory/concurrency/pending
- ztunnel node CPU/memory/traffic
- Waypoint replica/RPS/queue/resource
- Kafka publish/consume/lag/backlog age
- OTel accepted/dropped/exported spans

## Cardinality

- run ID는 제한된 실험 환경에서만 label 후보로 사용하고 종료 후 series 수를 확인한다.
- raw URL, correlation ID, payload ID는 metric label로 금지한다.
- route template과 bounded scenario/profile을 사용한다.

## Headroom

- 부하 발생기, Prometheus, Collector와 대상 node의 포화를 별도 감시한다.
- 측정 장비 포화 시 run을 invalid로 처리한다.
- telemetry on/off 비교를 별도 실험으로 하며 기본 비교에서는 동일 설정을 유지한다.

## 시간

- 모든 VM은 동일 NTP source를 사용한다.
- k6, fault, Kubernetes Event와 telemetry 시간을 UTC로 저장한다.
- 시간 drift가 허용 범위를 넘으면 MTTD/복구 지표를 사용하지 않는다.
