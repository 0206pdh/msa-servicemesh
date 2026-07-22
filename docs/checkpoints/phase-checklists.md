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
- [ ] Kubernetes telemetry/headroom/fault cleanup 검증(Phase 3 환경 필요)
- [ ] Phase 2 Evidence validated

## Phase 3 — 플랫폼 기반

- [x] VMware 3노드, 고정 IP와 OS/containerd/Kubernetes 사전 준비
- [ ] 노드 inventory/버전/시간 동기화 Evidence
- [ ] kubeadm Control Plane과 Worker join
- [ ] VMware/Kubernetes 버전과 자원 기록
- [ ] Cilium/Hubble, MetalLB, Gateway API
- [ ] Prometheus/Grafana/Loki/Tempo/OTel
- [ ] Helm profile과 NetworkPolicy
- [ ] telemetry completeness와 headroom
- [ ] Phase 3 Evidence validated

## Phase 4 — No Mesh

- [ ] Scenario별 포화점과 목표 부하
- [ ] 유효 반복 run 최소 3회
- [ ] Workload/부하 발생기 자체 병목 판정
- [ ] baseline run ID 승인
- [ ] Phase 4 Evidence measured

## Phase 5 — Sidecar

- [ ] injection/mTLS/traffic path 검증
- [ ] app/proxy 자원 분리
- [ ] 동일 조건 반복 run 최소 3회
- [ ] 기능과 비용 Evidence
- [ ] Phase 5 Evidence measured

## Phase 6 — Ambient

- [ ] enrollment/HBONE/ztunnel 경로 검증
- [ ] ztunnel 공유 자원 귀속
- [ ] replica/node 확장 반복 측정
- [ ] 기능 범위 차이 기록
- [ ] Phase 6 Evidence measured

## Phase 7 — Waypoint

- [ ] 전체/선택 경로 profile 분리
- [ ] Waypoint 통과와 L7 기능 검증
- [ ] replica/queue/saturation 측정
- [ ] 적용 범위별 비용 Evidence
- [ ] Phase 7 Evidence measured

## Phase 8 — 병목 분석

- [ ] profile 분포와 절대/상대 차이 비교
- [ ] 시간축 metric/trace/resource 상관 분석
- [ ] 지지/반대 Evidence가 있는 병목 주장
- [ ] 최소 3개 개선 가설 승인
- [ ] Phase 8 Evidence validated

## Phase 9 — 개선 실험

- [ ] baseline과 독립 변수 고정
- [ ] 후보별 before/after 최소 3회
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
