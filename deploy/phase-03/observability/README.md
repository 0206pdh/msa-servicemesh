# Observability baseline

Pinned charts:

- kube-prometheus-stack `87.19.0`
- Loki `7.1.0`, single binary
- Grafana Community Tempo `2.2.3` (Tempo `2.10.7`), monolithic
- OpenTelemetry Collector `0.165.0`, contrib image

Stateful components are scheduled on `mesh-cp-01` to keep benchmark workers free from direct storage and query load. Retention is 24 hours and PVCs are intentionally small. Control Plane saturation, telemetry drop or disk pressure invalidates a benchmark run.
