# 관측 스택 기반

- Status: validated-foundation
- Date: 2026-07-22
- Raw: `raw/2026-07-22-observability/`

## 배포 버전

| 구성 요소 | Chart | App |
|---|---:|---:|
| kube-prometheus-stack | 87.19.0 | prometheus-operator 0.92.1 |
| Loki single binary | 7.1.0 | 3.6.8 |
| Grafana Community Tempo monolithic | 2.2.3 | 2.10.7 |
| OpenTelemetry Collector | 0.165.0 | contrib 0.156.0 |

모든 stateful 관측 Pod는 `mesh-cp-01`에 고정했다. Worker에는 Prometheus node exporter만 배치한다. retention은 24시간이며 Local Path PVC는 Grafana 1 GiB, Prometheus 3 GiB, Loki 2 GiB, Tempo 2 GiB다.

## 검증

- 모든 Helm release `deployed`
- 모든 관측 Pod Ready, restart 0
- 모든 PVC `Bound`
- Prometheus API `count(up == 1)` query 성공
- Prometheus target에 세 node exporter, OTel Collector와 Tempo 포함
- Loki push 후 `{job="phase3-smoke"}` query 성공
- telemetrygen → OTel Collector → Tempo trace round trip 성공
- 최종 검증 trace ID: `319dfa37587dd338c4202661631ebf23`
- Grafana datasource: Prometheus, Loki `:3100`, Tempo `:3200`
- OTel 로그에서 error/refused/dropped 없음

## 설치 직후 headroom

Prometheus `node_memory_MemAvailable_bytes` 기준:

| 노드 | Available memory |
|---|---:|
| `mesh-cp-01` | 2.37 GiB |
| `mesh-worker-01` | 4.13 GiB |
| `mesh-worker-02` | 4.09 GiB |

Control Plane root disk는 약 11 GiB가 남았다. Local Path Provisioner는 PVC 용량을 실제 filesystem quota로 강제하지 않으므로 disk pressure와 retention size를 지속 감시한다.

## 제한

- node-local storage이므로 node failure에 대한 HA를 제공하지 않는다.
- 현재 값은 idle foundation 검증이며 Benchmark 부하 중 headroom Gate를 대신하지 않는다.
- Loki에는 cluster Pod log 수집 agent를 아직 배포하지 않았다. 현재 검증은 OTel log pipeline과 Loki API round trip 범위다.
