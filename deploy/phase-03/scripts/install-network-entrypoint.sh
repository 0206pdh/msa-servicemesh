#!/usr/bin/env bash
set -euo pipefail

readonly GATEWAY_API_VERSION="v1.4.1"
readonly CILIUM_VERSION="1.19.6"
readonly METALLB_CHART_VERSION="0.16.1"
readonly ROOT="${1:-.}"

for resource in gatewayclasses gateways httproutes referencegrants grpcroutes; do
  kubectl apply -f "https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/${GATEWAY_API_VERSION}/config/crd/standard/gateway.networking.k8s.io_${resource}.yaml"
done

helm upgrade cilium oci://quay.io/cilium/charts/cilium \
  --version "${CILIUM_VERSION}" \
  --namespace kube-system \
  --reuse-values \
  --values "${ROOT}/cilium/gateway-api-values.yaml" \
  --wait --timeout 10m

kubectl -n kube-system rollout restart deployment/cilium-operator
kubectl -n kube-system rollout restart daemonset/cilium
kubectl -n kube-system rollout status deployment/cilium-operator --timeout=5m
kubectl -n kube-system rollout status daemonset/cilium --timeout=5m

helm repo add metallb https://metallb.github.io/metallb
helm repo update metallb
helm upgrade --install metallb metallb/metallb \
  --version "${METALLB_CHART_VERSION}" \
  --namespace metallb-system \
  --create-namespace \
  --values "${ROOT}/metallb/values.yaml" \
  --wait --timeout 10m

kubectl apply -f "${ROOT}/metallb/l2-pool.yaml"
kubectl wait --for=condition=Established crd/gateways.gateway.networking.k8s.io --timeout=60s
kubectl wait --for=condition=Established crd/ipaddresspools.metallb.io --timeout=60s
kubectl get gatewayclass cilium
kubectl -n metallb-system get pods,ipaddresspool,l2advertisement -o wide
