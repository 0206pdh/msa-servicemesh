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
- [x] replica 확장에 따른 공유 비용 측정 — 방향성 확인 연구 완료 (ADR-0027, 정식 통계 아님). Sidecar 메모리는 replica 수에 선형 비례(120→173MiB), Ambient/ztunnel 메모리는 거의 불변(15.8→16.1MiB) — 가설 1 방향과 일치. Ambient latency는 replica 증가 시 뚜렷이 악화(p99 51→99.5ms, 3회 반복 기준 방향성)
- [x] 기본 Ambient 기능 범위(L7 없음)를 Sidecar와 구분 기록
- [x] Phase 6 Evidence measured (고정 replica baseline 한정 — 확장 측정은 별도)

## Phase 7 — Waypoint

- [x] 선택 경로(단일 hop) 배포 범위 결정 (ADR-0026)
- [x] **Waypoint 통과 검증 — 2026-07-30 해결**: 원인은 `orchestrator-service` NetworkPolicy의 waypoint
      ingress 규칙이 HBONE 포트(15008)를 빠뜨린 템플릿 버그였다(`cilium monitor --type drop`으로 확인).
      한때 "버전 독립적 비호환"으로 오판했던 것은 잘못된 추론이었음을 확인·정정했다
      (`phase-07-p1-waypoint-blocked`의 "최종 해결" 절 참고). 20/20·50/50 soak 테스트와 Waypoint 자체
      rq_total 증가로 실제 트래픽 통과를 검증했다
- [x] replica/queue/saturation 측정 — nominal/high/near-saturation 정식 15회씩 완료(전부
      `INCONCLUSIVE_MAX_RUNS`, Sidecar와 같은 패턴)
- [x] 적용 범위별 비용 Evidence — Waypoint 자원 실측 완료(request당 CPU 0.0014~0.0016 core-s, 메모리
      peak ~45MB)
- [x] Phase 7 Evidence — **완료** (`2026-08-01-canonical-waypoint-baseline-final.md`). 핵심 발견:
      network bytes/request는 세 조건 모두 Ambient와 Sidecar 사이(No-Mesh 대비 +16~18%, Ambient
      +1~2%/Sidecar +49%와 대비). latency는 nominal/high에서 세 profile 대비 일관되게 유의하게 느리지만
      near-saturation에서는 차이가 사라짐(원인 미규명, Phase 9 후보)

## Phase 8 — 병목 분석

- [x] profile 분포와 절대/상대 차이 비교 — No-Mesh/Sidecar/Ambient 3개 profile × 3개 부하 조건 × 6개 지표,
      독립 2-표본 bootstrap 차이 검정(`experiments/compare_profiles.py`)으로 36개 비교 완료. 핵심 발견:
      network bytes/request는 Sidecar가 세 부하 조건 모두에서 일관되게 ~49% 증가(고신뢰), Ambient는
      No-Mesh 대비 ~1-2%만 증가. p95/p99 latency는 27개 비교 중 단 1건(high 조건 No-Mesh vs Ambient)만
      유의했고 다음 부하 단계에서 재현되지 않음 — 확정 결론 아님. app 자체 CPU-per-request는 9개 비교
      전부 유의한 차이 없음 (`docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md`)
- [x] 시간축 metric/trace/resource 상관 분석 — **metric/trace는 재구성 불가, 로그는 남아있으나 내용 없음으로
      확정**: Prometheus(자체 TSDB retention)와 Tempo(살아있는 compactor)는 24h retention이 실제로
      강제되어 Phase 4~7 run(2026-07-23~29) 시점 데이터가 진짜로 사라졌음을 직접 확인(Tempo는 실제 trace
      ID 조회로 재검증). Loki는 `retention_period: 24h`가 설정만 있고 강제하는 compactor가 없어 그 시점
      로그가 실제로는 남아있음을 확인했으나(최초 점검은 잘못된 라벨 이름으로 "없다"고 오판했었음), 가장
      latency가 높았던 run 구간을 직접 열어보니 WARN/ERROR 0건·전체 로그 2줄뿐이라 상관 분석에 쓸 내용이
      없었다(애플리케이션이 요청 단위 로그를 남기지 않음). 조작 없이 이 정확한 한계로 기록하고 종료
      (comparison Evidence 문서의 "Time-axis correlation" 절)
- [x] 지지/반대 Evidence가 있는 병목 주장 — 위 비교 결과의 "Reading the two clean signals" 절 참고
- [x] 최소 3개 개선 가설 승인 — comparison Evidence 문서의 "Candidate bottleneck hypotheses" 절 (Sidecar
      mTLS/HTTP framing 오버헤드, ztunnel 공유 프록시의 미확정 latency 저하, mesh 비용이 proxy/network
      계층에 국한되고 application 계층에는 없다는 부정 결과)
- [x] Phase 8 Evidence validated — 통계 비교 완료, 시간축 상관 분석은 재구성 불가로 한계 기록 후 종료

## Phase 9 — 개선 실험

- [x] baseline과 독립 변수 고정 — 실험 1(ADR-0028): Sidecar mTLS PERMISSIVE vs DISABLE, nominal 고정.
      Istio 버전 confound(1.30.3 vs 1.29.6) 발견했으나 사용자 판단으로 수용하고 명시적으로 기록
- [x] 후보별 paired before/after 최소 10회와 CI 정밀도 Gate — 실험 1: DISABLE 10회 `STOP_PRECISION_REACHED`
      (기존 PERMISSIVE 15회 `INCONCLUSIVE_MAX_RUNS`보다 빠르게 수렴)
- [x] 회귀 지표와 rollback 판정 — 실험 1: latency는 DISABLE이 오히려 유의하게 악화(p95 +12.4ms, p99
      +18.9ms, 단 버전 confound로 확정 불가). mTLS DISABLE은 실험 종료 후 즉시 PERMISSIVE로 rollback함
- [x] 실패한 개선도 Evidence 보존 — 실험 1의 핵심 가설("mTLS가 Sidecar network-bytes 오버헤드의 주 원인")은
      기각됨(전체 오버헤드의 ~3%만 mTLS 기여). 조작 없이 기각 결과 그대로 보존
      (`docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md`)
- [x] 실험 2(ADR-0029) 완료: Ambient replica 1 vs 4, nominal 고정, replica=4 10회
      `STOP_PRECISION_REACHED`. p99 latency 저하는 방향 확인(유의, +20%)됐지만 ADR-0027 방향성 연구가
      시사한 크기(+95%)는 재현 안 됨. ztunnel 메모리는 오히려 방향성 연구와 반대로 유의하게 증가(+79%,
      "확정 결론 아님, 추가 조사 필요"로 기록). ztunnel CPU 증가는 재현 안 됨. Istio 버전 confound
      있음(사전에 ADR-0029에서 수용) (`docs/evidence/performance/2026-08-02-phase9-ambient-replica-scaling-formal.md`)
- [x] 실험 3은 Phase 8에서 이미 9/9 비교로 확인된 부정 결과(mesh 비용이 proxy/network 계층에 국한)라
      신규 실험 불필요로 결론
- [x] Phase 9 결론 validated — 실험 1(가설 기각) + 실험 2(방향 부분 확인, 크기 불일치) + 실험 3(Phase 8
      재확인으로 충분)으로 Phase 9 종료

## Phase 10 — 회복탄력성

- [x] bounded fault와 자동 cleanup — pod kill(kubectl delete, Deployment 자동 재생성)과 chain-wide
      delay(work.delayMs, 실험 종료 후 정상값 1ms로 원복 확인) 둘 다 별도 인프라 없이 bounded, 자동 정리
- [x] 동일 fault schedule before/after — pod-kill은 run 내 kill 전/후 구간 비교, chain-delay는 Phase 6
      canonical nominal baseline(delay=1ms) 대비 정식 10+회 비교
- [x] 성공률/amplification/recovery 측정 — pod-kill: recovery 29.9~39.9초, peak error rate 37.5~73.3%.
      chain-delay: errorRate 0(둘 다), latency +160~167ms(injected 150ms와 근접)
- [x] 정상화와 잔여 영향 검사 — pod-kill 자동 복구 확인, chain-delay 종료 후 정상 파라미터 SYNC_CHAIN
      재확인
- [x] Phase 10 Evidence measured
      (`docs/evidence/performance/2026-08-03-phase10-resilience-results.md`) — Network delay/loss,
      Kafka worker stop/restart, hop 단위 격리 fault(`armFault` API)는 ADR-0030에서 사전에 범위 밖으로
      명시, cross-profile 비교 안 함(Ambient만), Istio 버전 confound(chain-delay before 1.30.3/after
      1.29.6) 발견해 명시

## Phase 11 — 최종화

- [ ] workload별 선택 Matrix
- [ ] raw→summary→graph→claim 연결
- [ ] 새 환경 대표 재현
- [ ] 적용 범위와 외삽 금지 조건
- [ ] 최종 Evidence와 보고서 validated
