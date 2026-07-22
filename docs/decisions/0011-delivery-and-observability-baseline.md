# ADR-0011: 배포 및 관측 기준선

- 상태: accepted
- 날짜: 2026-07-22

## Context

3노드 VMware 실험실에서 재현성은 필요하지만 GitOps controller 자체의 자원 비용과 운영 범위는 핵심 연구 질문이 아니다. 관측 스택도 측정 장비로서 충분해야 하며 워크로드를 포화시키면 안 된다.

## Decision

- Phase 3~11에서는 GitOps controller를 도입하지 않는다.
- 저장소의 version-pinned Helm values와 manifest를 순서가 명시된 스크립트로 적용한다.
- Prometheus/Grafana는 `kube-prometheus-stack`, Loki와 Tempo는 single-binary/monolithic, OpenTelemetry Collector는 Deployment mode로 시작한다.
- 영속 저장소는 Rancher Local Path Provisioner의 node-local `local-path` StorageClass를 사용한다.
- 관측 데이터는 짧은 보존기간의 실험용 저장소에 두고 장기 보존 대상은 run별 export 원본과 summary로 제한한다.
- 관측 구성 요소에는 requests/limits를 설정하고 collector drop, Prometheus scrape 실패, node와 load generator headroom을 run 유효성 조건에 포함한다.
- Secret, kubeconfig, join token과 Grafana credential은 저장소나 Evidence에 저장하지 않는다.

## Alternatives

- Argo CD/Flux: drift 관리에는 유리하지만 현재 실험 질문과 무관한 상시 자원과 장애 지점을 추가한다.
- 분산 Loki/Tempo: 확장성은 높지만 3노드 실험실 기준으로 과도하다.
- 분산 storage 또는 NFS: node failure 복구에는 유리하지만 현재 단일 호스트 실험실의 범위를 넘고 추가 측정 변수를 만든다.
- 관측 데이터 전체 장기 보존: 분석에는 편하지만 디스크와 compaction 비용이 측정에 영향을 준다.

## Consequences

- Git commit, chart version, values와 적용 순서로 재현성을 확보한다.
- 실제 부하에서 관측 스택 headroom이 부족하면 retention이나 sampling을 먼저 조정하지 않고 run을 invalid 처리한 뒤 별도 변경으로 검증한다.
- GitOps 도입 여부는 프로젝트 규모가 커질 때 새 ADR로 재검토한다.

## Validation and rollback

- 모든 Pod readiness, scrape target, log ingest, trace round trip, telemetry drop과 자원 headroom을 검증한다.
- 관측 스택이 포화되면 측정을 시작하지 않고 resources 또는 배치를 조정한 뒤 동일 검증을 반복한다.
