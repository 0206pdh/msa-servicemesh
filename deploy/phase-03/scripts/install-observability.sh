#!/usr/bin/env bash
set -euo pipefail

readonly ROOT="${1:-.}"
readonly NAMESPACE="observability"

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 87.19.0 --namespace "${NAMESPACE}" \
  --values "${ROOT}/kube-prometheus-stack-values.yaml" \
  --rollback-on-failure --wait --timeout 10m

helm upgrade --install loki grafana/loki \
  --version 7.1.0 --namespace "${NAMESPACE}" \
  --values "${ROOT}/loki-values.yaml" \
  --rollback-on-failure --wait --timeout 10m

helm upgrade --install tempo grafana-community/tempo \
  --version 2.2.3 --namespace "${NAMESPACE}" \
  --values "${ROOT}/tempo-values.yaml" \
  --rollback-on-failure --wait --timeout 10m

helm upgrade --install otel open-telemetry/opentelemetry-collector \
  --version 0.165.0 --namespace "${NAMESPACE}" \
  --values "${ROOT}/otel-collector-values.yaml" \
  --rollback-on-failure --wait --timeout 10m

kubectl -n "${NAMESPACE}" get pods,pvc -o wide
