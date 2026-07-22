#!/usr/bin/env bash
set -euo pipefail

pids=()
cleanup() {
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  kubectl -n observability delete pod telemetrygen --ignore-not-found --wait=true >/dev/null
}
trap cleanup EXIT

kubectl -n observability port-forward service/monitoring-kube-prometheus-prometheus 9090:9090 >/tmp/prometheus-pf.log 2>&1 & pids+=("$!")
kubectl -n observability port-forward service/loki 3100:3100 >/tmp/loki-pf.log 2>&1 & pids+=("$!")
kubectl -n observability port-forward service/tempo 3200:3200 >/tmp/tempo-pf.log 2>&1 & pids+=("$!")

for attempt in {1..20}; do
  curl -fsS http://127.0.0.1:9090/-/ready >/dev/null \
    && curl -fsS http://127.0.0.1:3100/ready >/dev/null \
    && curl -fsS http://127.0.0.1:3200/ready >/dev/null \
    && break
  sleep 1
done

curl -fsSG http://127.0.0.1:9090/api/v1/query \
  --data-urlencode 'query=count(up == 1)' >/tmp/prometheus-smoke.json
curl -fsSG http://127.0.0.1:9090/api/v1/query \
  --data-urlencode 'query=count by (job) (up == 1)' >/tmp/prometheus-targets.json
curl -fsSG http://127.0.0.1:9090/api/v1/query \
  --data-urlencode 'query=node_memory_MemAvailable_bytes' >/tmp/node-memory-headroom.json

timestamp="$(date +%s%N)"
curl -fsS -H 'Content-Type: application/json' -X POST http://127.0.0.1:3100/loki/api/v1/push \
  --data-raw "{\"streams\":[{\"stream\":{\"job\":\"phase3-smoke\"},\"values\":[[\"${timestamp}\",\"loki-round-trip\"]]}]}"
sleep 2
curl -fsSG http://127.0.0.1:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="phase3-smoke"}' >/tmp/loki-smoke.json

kubectl -n observability run telemetrygen --restart=Never \
  --image=ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:v0.134.0 \
  --command -- /telemetrygen traces \
  --otlp-endpoint otel-opentelemetry-collector:4317 --otlp-insecure --traces 1
kubectl -n observability wait --for=jsonpath='{.status.phase}'=Succeeded pod/telemetrygen --timeout=60s
sleep 5
curl -fsSG http://127.0.0.1:3200/api/search \
  --data-urlencode 'tags=service.name=telemetrygen' >/tmp/tempo-smoke.json

python3 - <<'PY'
import json
from pathlib import Path

prometheus = json.loads(Path('/tmp/prometheus-smoke.json').read_text())
loki = json.loads(Path('/tmp/loki-smoke.json').read_text())
tempo = json.loads(Path('/tmp/tempo-smoke.json').read_text())

assert prometheus['status'] == 'success' and prometheus['data']['result'], 'Prometheus query returned no result'
assert loki['status'] == 'success' and loki['data']['result'], 'Loki query returned no result'
assert tempo.get('traces'), 'Tempo search returned no trace'

print('prometheus=passed')
print('loki=passed')
print('tempo_via_otel=passed')
print('tempo_trace_id=' + tempo['traces'][0]['traceID'])
PY
