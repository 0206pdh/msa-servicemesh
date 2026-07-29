# 전체 Phase 체크리스트

세부 작업은 각 Phase 문서를 따르고, 여기서는 진입과 종료 Gate만 추적한다.

## Phase 0 — 실험 설계

- [x] 질문, profile과 scenario 범위 확정
- [x] 공정성·무효화·Evidence 규칙 확정
- [x] API/Event/Result 계약 lint 및 compile
- [x] Phase 0 Evidence validated

## Phase 1 — Benchmark Workload

- [x] A1 Java 25 공통 런타임, 관측 기능과 Compose E2E
- [x] A2 bounded Workload Target
- [x] A3 Sync Chain과 deadline/cancellation
- [x] A4 Fan-out과 partial result
- [x] A5 Kafka Async Pipeline과 멱등성
- [x] A6 Payload와 checksum
- [x] 전체 계약/통합/E2E 검증
- [x] Phase 1 Evidence validated

## Phase 2 — 실험 자동화

- [x] Runner 상태 머신과 ExperimentSpec
- [x] k6 profile과 반복 실행
- [x] Ground Truth와 config snapshot
- [x] raw export와 summary 생성
- [x] 로컬 adapter invalidation과 overwrite 방지
- [x] Kubernetes telemetry/headroom/fault cleanup 검증
- [x] Phase 2 Evidence validated

## Phase 3 — 플랫폼 기반

- [x] VMware 3노드, 고정 IP와 OS/containerd/Kubernetes 사전 준비
- [x] 노드 inventory/버전/시간 동기화 Evidence
- [x] kubeadm Control Plane과 Worker join
- [x] Kubernetes/Ubuntu/containerd/Cilium 확인 버전 기록
- [x] VMware 자원과 UUID/MAC 원본 Evidence 수집
- [x] Cilium/Hubble
- [x] MetalLB와 Gateway API
- [x] Prometheus/Grafana/Loki/Tempo/OTel
- [x] Helm profile과 NetworkPolicy
- [x] telemetry completeness와 headroom
- [x] Phase 3 Evidence validated

## Phase 4 — No Mesh

- [x] Scenario별 포화점과 목표 부하 (C\*=28 RPS, 3/8/17/22 RPS)
- [x] core 조건 유효 run 최소 10회와 bootstrap CI 정밀도 Gate (high/near-saturation `STOP_PRECISION_REACHED`, nominal `INCONCLUSIVE_MAX_RUNS`)
- [x] Workload/부하 발생기 자체 병목 판정 (28 RPS에서 node CPU peak 36%, 부하발생기 CPU peak 5% — 자체 병목 아님)
- [x] baseline run ID 승인
- [x] Phase 4 Evidence measured

## Phase 5 — Sidecar

- [x] injection/mTLS/traffic path 검증
- [x] app/proxy 자원 분리
- [x] paired core 조건 10~15회와 CI 정밀도 Gate (세 조건 모두 15회 `INCONCLUSIVE_MAX_RUNS`)
- [x] 기능과 비용 Evidence (proxy CPU/메모리 실측, No-Mesh 대비 예비 비교는 Phase 8 정식 비교 전까지 잠정)
- [x] Phase 5 Evidence measured

## Phase 6 — Ambient

- [x] enrollment/HBONE/ztunnel 경로 검증
- [x] ztunnel 공유 자원 귀속 (노드 단위 절대값, per-request 정규화 안 함 — ADR-0025)
- [x] 고정 replica(1개)에서 paired core 조건 10~15회 (nominal 10회/near-saturation 14회 `STOP_PRECISION_REACHED`, high 15회 `INCONCLUSIVE_MAX_RUNS`)
- [ ] **replica/node 확장에 따른 공유 비용 측정 — 미완료, Phase 8 전에 별도로 수행 필요** (가설 1의 핵심 근거)
- [x] 기본 Ambient 기능 범위(L7 없음)를 Sidecar와 구분 기록
- [x] Phase 6 Evidence measured (고정 replica baseline 한정 — 확장 측정은 별도)

## Phase 7 — Waypoint

- [x] 선택 경로(단일 hop) 배포 범위 결정 (ADR-0026)
- [ ] **Waypoint 통과 검증 — 차단됨**: gateway→waypoint 홉은 성공하지만 waypoint→실제 backend pod 홉이
      항상 TCP 연결 후 HTTP 즉시 리셋으로 실패한다. 노드 분리로도 재현되어 원인 불명 (`phase-07-p1-waypoint-blocked` 참고)
- [ ] replica/queue/saturation 측정 — 위 차단으로 미착수
- [ ] 적용 범위별 비용 Evidence — 미착수
- [ ] Phase 7 Evidence — **blocked**, Phase 8은 No-Mesh/Sidecar/Ambient 세 profile로 진행

## Phase 8 — 병목 분석

- [ ] profile 분포와 절대/상대 차이 비교
- [ ] 시간축 metric/trace/resource 상관 분석
- [ ] 지지/반대 Evidence가 있는 병목 주장
- [ ] 최소 3개 개선 가설 승인
- [ ] Phase 8 Evidence validated

## Phase 9 — 개선 실험

- [ ] baseline과 독립 변수 고정
- [ ] 후보별 paired before/after 최소 10회와 CI 정밀도 Gate
- [ ] 회귀 지표와 rollback 판정
- [ ] 실패한 개선도 Evidence 보존
- [ ] Phase 9 결론 validated/rejected

## Phase 10 — 회복탄력성

- [ ] bounded fault와 자동 cleanup
- [ ] 동일 fault schedule before/after
- [ ] 성공률/amplification/recovery 측정
- [ ] 정상화와 잔여 영향 검사
- [ ] Phase 10 Evidence measured

## Phase 11 — 최종화

- [ ] workload별 선택 Matrix
- [ ] raw→summary→graph→claim 연결
- [ ] 새 환경 대표 재현
- [ ] 적용 범위와 외삽 금지 조건
- [ ] 최종 Evidence와 보고서 validated
