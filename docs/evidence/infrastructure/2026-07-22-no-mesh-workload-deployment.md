# No-mesh Workload 배포 검증

- Status: validated
- Date: 2026-07-22
- Namespace: `benchmark`
- Helm release: `meshperf` revision 1

## 배포 기준

- GHCR 이미지 5개를 source tag `9cf3285756d2`와 linux/amd64 digest로 고정했다.
- GHCR package를 Public으로 전환한 뒤 Kubernetes anonymous pull smoke를 모두 통과했다.
- Gateway, Orchestrator, Producer, Worker와 Workload a/b/c를 배포했다.
- Kafka 4.0.0 KRaft single broker와 Local Path 3 GiB PVC를 사용했다.
- Cilium Gateway API와 MetalLB 주소 `192.168.200.100`을 영구 진입점으로 사용했다.
- ServiceMonitor로 모든 Java 서비스의 Prometheus endpoint를 수집했다.

Kafka bootstrap 중 headless Service가 Ready endpoint만 게시해 `kafka-0.kafka` DNS와 readiness 사이에 순환 의존성이 발생했다. Service에 `publishNotReadyAddresses: true`를 추가하고 Kafka Pod를 재생성해 해결했으며, 이 설정을 Helm chart에도 반영했다. Java 이미지의 non-root 사용자도 숫자 UID/GID `100:101`로 명시했다.

## 검증 결과

- Helm release: `deployed`
- 애플리케이션 Pod 7개와 Kafka Pod 모두 `Ready`
- Gateway: `Programmed=True`, address `192.168.200.100`
- 외부 `/api/v1/system/ping`: gateway와 orchestrator `UP`
- chain: 3 hops, status `COMPLETED`, completedHops `3`
- parallel fan-out: 3 targets, completed `3`, failed `0`
- payload: 4096 bytes, STREAMING/GZIP checksum 반환
- async: 3 tasks accepted, Kafka consumer group 안정화
- Prometheus: benchmark namespace의 7개 Java job 모두 `up=1`
- Prometheus: `meshperf_worker_tasks_total{outcome="completed"}=3`

최종 smoke에는 correlation ID `phase3-smoke`, experiment run ID `phase3-no-mesh`를 사용했다. 이 결과는 기능 배포 검증이며 성능 비교 결과로 사용하지 않는다.

## 다음 Gate

1. 기본 거부 NetworkPolicy와 필요한 통신 allow-list를 적용한다.
2. Phase 2 runner의 Kubernetes adapter와 telemetry/headroom/cleanup Gate를 검증한다.
3. no-mesh 반복 실행을 시작하기 전에 로그 수집과 run ID 기반 telemetry completeness를 확인한다.
