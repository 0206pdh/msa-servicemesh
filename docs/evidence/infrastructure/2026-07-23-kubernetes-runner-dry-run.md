# Kubernetes runner와 telemetry Gate 검증

- Status: validated-dry-run
- Date: 2026-07-23
- Profile: NO_MESH
- Scenario: 3-hop SYNC_CHAIN

## 구현

- 로컬 kubeconfig: 사용자 홈 `.kube/meshperf-config`에 저장하고 저장소에서는 제외
- Kubernetes pre/post Pod, image digest, placement와 restart snapshot
- Prometheus scrape/NTP/node memory/application resource/network window query
- OTel failed/refused span Gate
- run ID Loki marker와 임시 marker Pod cleanup
- run ID ping trace ID와 Tempo exact trace 조회
- Hubble Relay port-forward와 benchmark namespace flow export
- Windows Docker stats 기반 load-generator CPU/memory sampling
- dirty tree, dropped iteration, temporary resource와 fault cleanup 무효화

Pod 로그는 OTel Collector chart 0.165.0 DaemonSet 3개로 수집한다. 공식 `logsCollection`과 Kubernetes attributes preset을 사용하고 Loki 3.6.8 native OTLP endpoint로 전송한다. collector 자체 로그는 재수집하지 않는다.

## 발견한 결함과 수정

1. 기존 runner가 k6 JSON의 `metrics.*.values`를 읽지 않아 과거 Compose summary가 sample 0이었다. parser와 회귀 테스트를 수정했다. 과거 Compose 결과는 이미 `INVALID`였으므로 성능 결론에는 사용되지 않았다.
2. 첫 Kubernetes dry-run은 Prometheus scrape 직후 query해 request delta를 놓쳤다. 20초 settle과 확장 window를 추가했다.
3. Java Pod 동시 rolling restart에서 시작 시간이 약 52초까지 증가해 기존 liveness가 프로세스를 종료했다. 최대 180초 startupProbe를 차트에 추가했다.

## dry-run 결과

### `phase3-no-mesh-dry-run`

- sample: 11
- load-generator CPU peak: 2.63%
- 결과: `INVALID`
- 원인: `PROMETHEUS_REQUEST_DELTA_MISSING`, `DIRTY_SOURCE_TREE`

이 실행은 실패 Evidence로 보존했고 성능 수치로 사용하지 않는다.

### `phase3-no-mesh-dry-run-v2`

- sample: 10, error rate 0
- preflight/cleanup/telemetry Gate: passed
- application CPU: 41.11 core-seconds, peak 0.82 cores
- application memory peak: 1,852,248,064 bytes
- node CPU peak: 27.33%
- node minimum available memory: 1,824,956,416 / 3,590,066,176 / 2,965,790,720 bytes
- load-generator CPU peak: 2.10%, 4 samples
- 결과: `INVALID`
- 유일한 원인: `DIRTY_SOURCE_TREE`

따라서 구현과 환경 Gate는 통과했으며 검증 스냅샷을 커밋한 뒤 clean-tree final dry-run이 필요하다. 위 수치는 runner 검증용이고 Phase 4 baseline으로 인용하지 않는다.

### `phase3-no-mesh-final-dry-run`

- source commit: `3848517`
- source tree: clean
- status: `COMPLETED`
- invalidating factors: 없음
- sample: 11, error rate 0
- preflight/telemetry/headroom/cleanup Gate: 모두 passed
- application CPU: 45.16 core-seconds, peak 0.75 cores
- application memory peak: 1,897,852,928 bytes
- node CPU peak: 29.78%
- node minimum available memory: 2,174,005,248 / 3,587,432,448 / 2,942,390,272 bytes
- load-generator CPU peak: 0.71%, 4 samples

Phase 3 exit dry-run은 유효하다. 이 실행 역시 저부하 기능/Gate 검증용이며 Phase 4 성능 baseline으로 사용하지 않는다.
