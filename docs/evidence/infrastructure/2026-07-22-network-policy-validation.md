# Workload NetworkPolicy 검증

- Status: validated
- Date: 2026-07-22
- Helm release: `meshperf` revision 3
- Namespace: `benchmark`

## 적용 범위

- Kubernetes NetworkPolicy 11개
- CiliumNetworkPolicy 1개
- 기본 ingress/egress deny
- DNS, Gateway, 서비스 체인, Kafka, Prometheus와 OTel 최소 허용

## 발견 및 수정

첫 적용 revision 2에서 Pod는 모두 Ready였지만 외부 Gateway 요청이 `upstream connect ... connection timeout`으로 실패했다. Hubble drop flow는 다음 실제 경로를 확인했다.

- source IP: `10.244.1.30`
- source identity: `8`
- source label: `reserved:ingress`
- destination: benchmark-gateway Pod port 8080
- verdict: `DROPPED`
- reason: `POLICY_DENIED`

Gateway namespaceSelector 규칙을 제거하고 CiliumNetworkPolicy `fromEntities: ingress`를 적용했다. revision 3에서 정책은 `VALID=True`가 됐고 외부 경로가 복구됐다.

## 허용 경로 검증

- `/api/v1/system/ping`: `UP`
- 3-hop chain: `COMPLETED`
- parallel fan-out 3개: `COMPLETED`
- STREAMING/GZIP 4096-byte payload: checksum 반환
- async task 3개: accepted `3`
- 모든 애플리케이션/Kafka Pod: Ready
- Prometheus benchmark Java job 7개: 각각 `up=1`
- worker completed 누계: `6`

검증 correlation ID는 `phase3-netpol`, experiment run ID는 `phase3-no-mesh-netpol`이다.

## 차단 경로 검증

임시 `curlimages/curl:8.12.1` Pod에서 `workload-a:8080/actuator/health`를 직접 호출했다. 연결은 3초 후 curl exit 28로 timeout됐고 임시 Pod는 자동 삭제됐다. 즉 Gateway/Orchestrator를 우회하는 임의 Pod 직접 접근은 차단된다.

## 재현 검증

- `helm lint`: 0 failed
- `helm template | kubectl apply --dry-run=server`: passed
- Helm upgrade: revision 3 `deployed`

이 검증은 네트워크 격리 기능 검증이며 성능 Evidence가 아니다.
