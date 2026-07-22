# ADR-0013 — Kubernetes run 유효성 Gate

- Status: accepted
- Date: 2026-07-23

## 결정

Kubernetes 성능 run은 다음 조건을 모두 통과해야 `COMPLETED`로 판정한다.

- Workload/Kafka Pod가 모두 Running/Ready이고 restart가 0이다.
- benchmark Prometheus target 7개가 전체 window에서 `up=1`이다.
- node NTP sync metric이 모두 1이고 가용 memory가 노드별 1 GiB 이상이다.
- node CPU peak가 85% 미만이다.
- OTel failed/refused span 증가가 없다.
- request counter 증가와 k6 sample이 존재한다.
- Tempo trace marker, Loki run marker와 Hubble flow artifact가 존재한다.
- 임시 Pod/Job과 fault schedule이 남지 않는다.
- Docker load-generator CPU peak가 80% 미만이다.
- source tree가 clean이다.

Prometheus의 15초 scrape 지연을 고려해 load 종료 후 기본 20초를 기다리고, warm-up/load/settle을 포함한 window query를 수행한다. 부하 발생기는 Windows Docker host에서 실행해 Kubernetes VM과 자원을 분리하고 Docker stats를 같은 run artifact로 기록한다.

## 근거

수치가 생성됐다는 사실만으로 비교 가능한 run이 되지 않는다. restart, telemetry gap, collector drop, node/load-generator 포화, cleanup 실패와 dirty source는 결과 해석을 바꾸므로 자동 무효화해야 한다.

## 결과

- runner가 Kubernetes snapshot과 raw telemetry를 반복별 디렉터리에 저장한다.
- Gate 실패는 결과 삭제가 아니라 `INVALID`와 원인 code로 보존한다.
- `kubectl top`은 Metrics API가 없어 사용하지 않고 Prometheus/node-exporter/cAdvisor를 기준으로 한다.
