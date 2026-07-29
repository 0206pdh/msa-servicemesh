# 현재 작업 상태

이 파일은 세션 재개를 위한 단일 체크포인트다. 작업을 시작하거나 종료할 때 반드시 갱신한다. 완료 주장은 체크리스트와 Evidence가 일치할 때만 기록한다.

## 현재 위치

- Project: Mesh Performance Lab
- Overall Phase: Phase 7 — Waypoint blocked. Replica-scaling 방향성 연구 완료. Phase 8 착수 준비 완료
- Infrastructure Step: 클러스터는 순수 Ambient 상태(orchestrator-service 1 replica)로 복구됨
- Status: phase-8-ready-waypoint-retry-pending
- Last updated: 2026-07-29

## 완료된 기준점

- [x] Phase 0 실험 방향, 공정성, Workload 경계 확정
- [x] Phase 0~11 상세 실행 문서 작성
- [x] Data/Control Plane OpenAPI lint 통과
- [x] Event/Result JSON Schema compile 통과
- [x] Java 25 설치 및 서비스 5개 Gradle test 통과
- [x] Compose 6개 서비스 healthy와 Gateway → Orchestrator smoke 확인
- [x] GitHub `0206pdh/msa-servicemesh` main 동기화
- [x] Mesh, Benchmark, Workload와 측정 용어 기준 문서화
- [x] A2~A6 bounded workload와 Compose 7-container E2E
- [x] Phase 2 runner, k6 profile, Ground Truth/raw/summary 구현
- [x] 같은 Compose smoke spec 3회 반복과 무효화 판정
- [x] VMware Workstation 26.0.0과 Ubuntu 26.04 LTS VM 3대 구성
- [x] `192.168.200.10~12` 고정 IP, SSH와 VMnet8 통신 구성
- [x] swap/kernel/sysctl/containerd/Kubernetes CLI 공통 사전 준비
- [x] kube-proxy를 제외한 Kubernetes 1.36 Control Plane 초기화
- [x] Worker 2대 join 및 Kubernetes 3노드 `Ready`
- [x] Cilium 1.19.6 Agent/Envoy 3노드 배포
- [x] Cilium Operator 2개와 Hubble Relay/UI 정상화
- [x] VM inventory, 고유 MAC, 시간 동기화와 서비스 상태 원본 수집
- [x] Gateway API 1.4.1과 Cilium Gateway controller 활성화
- [x] MetalLB 0.16.1 L2 및 `192.168.200.100~110` pool 구성
- [x] Windows host → MetalLB → Cilium Gateway → 임시 backend smoke 검증
- [x] 세 VM 순차 재부팅 후 IP/서비스/NTP/Kubernetes/Cilium/MetalLB 복구 검증
- [x] Hubble Relay cluster-wide `3/3` 연결과 JSON flow export 검증
- [x] Local Path StorageClass와 Pod 재생성 persistence 검증
- [x] Prometheus/Grafana/Loki/Tempo/OTel Collector 배포
- [x] Prometheus query, Loki push/query, OTel → Tempo trace round trip 검증
- [x] Java Workload 이미지 5개 GHCR build/push와 linux/amd64 digest lock
- [x] GHCR Public 전환과 Kubernetes anonymous pull smoke
- [x] digest-pinned 공통 Helm chart와 no-mesh values 배포
- [x] Cilium Gateway를 통한 chain/fan-out/payload/async 외부 E2E
- [x] benchmark Java target 7개 Prometheus 수집과 async worker 완료 metric
- [x] 기본 deny NetworkPolicy와 서비스별 최소 허용 규칙
- [x] Cilium `reserved:ingress` Gateway 경로와 임의 Pod 직접 접근 차단 검증
- [x] Kubernetes runner telemetry/headroom/cleanup 자동 Gate
- [x] OTel DaemonSet Pod log 수집과 Loki native OTLP ingest
- [x] run ID Loki/Tempo marker와 Hubble flow artifact
- [x] Docker load-generator CPU sampling과 Kubernetes node 자원 분리
- [x] Java startupProbe와 전체 Workload restart 0 기준점
- [x] clean source commit `3848517` 기반 final dry-run `COMPLETED`
- [x] Phase 2/3 Evidence와 exit Gate 완료
- [x] Phase 4 capacity 기반 부하와 10~15회 통계 정밀도 정책
- [x] bootstrap CI 집계와 자동 정지 판정 구현
- [x] canonical SYNC_CHAIN usable capacity `C*` 28 RPS 승인
- [x] canonical 절대 부하 low/nominal/high/near-saturation 3/8/17/22 RPS 확정
- [x] Tempo OOM 복구: ballast 128 MiB, memory limit 1536 MiB, trace round trip 통과
- [x] 세션 재시작 시 valid run 회계가 0으로 리셋되는 스케줄러 버그 수정 (commit `2e8faf4`)
- [x] 상대 half-width 단일 정밀도 기준이 15회 상한에도 수렴 불가함을 확인
- [x] 절대(ms/core-s)·상대(%) 혼합 정밀도 기준 도입 (ADR-0023)
- [x] SYNC_CHAIN canonical No Mesh 정식 반복측정 완료: high(10회)/near-saturation(13회) `STOP_PRECISION_REACHED`, nominal(15회) `INCONCLUSIVE_MAX_RUNS`
- [x] Phase 4 Evidence와 exit Gate 완료
- [x] Istio 1.30.3 버전/자원 크기 결정과 Helm 설치 (ADR-0024)
- [x] Helm chart Sidecar profile 지원 (No Mesh 회귀 없음, lint/render 확인)
- [x] 7개 SYNC_CHAIN 서비스 sidecar 주입과 `2/2 Running` 확인
- [x] 실제 mTLS 적용을 Envoy config dump로 직접 확인 (STRICT 시도 중 Prometheus 스크레이프 붕괴 발견 → PERMISSIVE로 정정)
- [x] app/proxy(Envoy) 자원 분리 수집과 throttling 감지 gate 추가
- [x] 스케줄러의 No Mesh/Sidecar profile 공용화 (기존 Phase 4 fingerprint 불변 검증)
- [x] 스케줄러가 단일 run 실패로 전체 세션이 죽지 않도록 견고성 개선 (commit `8afe58c`)
- [x] Phase 5 Sidecar 정식 반복측정 완료: 세 조건 모두 15회 `INCONCLUSIVE_MAX_RUNS`
- [x] Phase 5 Evidence와 exit Gate 완료
- [x] ztunnel/istio-cni 1.30.3 설치와 노드 단위 공유 자원 귀속 모델 결정 (ADR-0025)
- [x] Ambient enrollment 실제 검증: kubelet probe가 ambient 캡처에 걸려 crash-loop하는 문제와 HBONE 포트 15008이 NetworkPolicy에서 막혀있던 문제를 실측으로 발견·수정
- [x] ztunnel CPU/메모리를 노드 단위 절대값으로 수집(Pod당 정규화 안 함), throttling 게이트 추가
- [x] Ambient 고정 replica(1개) 정식 반복측정 완료: nominal 10회/near-saturation 14회 `STOP_PRECISION_REACHED`, high 15회 `INCONCLUSIVE_MAX_RUNS`
- [x] Phase 6 고정 replica baseline Evidence 완료
- [x] Waypoint 배포 범위 결정 (ADR-0026, 선택 경로/단일 hop)
- [x] `istio-waypoint` GatewayClass 자동 생성과 Gateway 리소스로 Waypoint Pod 프로비저닝 확인
- [x] gateway→waypoint 홉 NetworkPolicy 수정(HBONE 15008)과 정상 동작 확인
- [ ] **waypoint→실제 backend pod 홉이 원인 불명으로 항상 실패 — Phase 7 blocked** (`phase-07-p1-waypoint-blocked` 참고, 같은 노드 가설은 patch로 재현·기각함)
- [x] 클러스터를 순수 Ambient 상태로 복구 (Waypoint 리소스 제거, SYNC_CHAIN 정상 동작 재확인)
- [x] Replica 확장 방향성 연구 완료 (ADR-0027): orchestrator-service 1/2/4 replica × Sidecar/Ambient × 3회 = 18 run, 전부 성공
- [x] 발견: Sidecar 메모리는 replica 수에 선형 비례(120→173MiB), Ambient/ztunnel 메모리는 거의 불변(15.8→16.1MiB) — 가설 1 방향과 일치
- [x] 발견: Ambient latency가 replica 증가에 따라 뚜렷이 악화(p99 51→99.5ms, 방향성 데이터). Sidecar는 오히려 소폭 개선(부하분산 효과로 추정)

## 다음 작업

1. Istio 버전을 바꿔(1.29.x 계열 시도) Waypoint를 재설치하고 같은 진단 절차로 재시도한다 (사용자 요청,
   Phase 7 재개 시도). 실패해도 여러 버전에서 재현되는 근본 비호환으로 최종 확정하고 넘어간다.
2. Phase 8(병목 분석) 착수: No-Mesh/Sidecar/Ambient 세 profile의 정식 데이터 + replica-scaling 방향성
   데이터로 진행한다(Waypoint는 재시도 결과에 따라 포함 여부 결정).
3. Phase 8에서 profile 간 정식 통계 비교 도구(paired difference, 결합 불확실성)를 구현한다 — 지금까지
   Evidence 문서들의 "예비 비교"를 정식 결론으로 승격하려면 이 도구가 필요하다.

## 현재 한계

- 로컬 Compose runner 결과는 자동으로 `INVALID` 처리되며 성능 Evidence로 사용할 수 없다.
- 이 클러스터(노드당 allocatable 2 vCPU)는 p95 ≈5ms/p99 ≈8ms보다 작은 latency 차이를 통계적으로 구분하지 못한다. Mesh profile 오버헤드가 이보다 작게 나오면 `확인된 차이 없음`으로만 보고해야 한다.
- nominal(8 RPS) 조건은 No Mesh에서 15회까지도 p99 정밀도 기준에 수렴하지 않았다. cross-profile 비교에서 nominal의 p99는 다른 조건보다 넓은 CI를 감안해 해석한다.
- Sidecar profile은 세 조건 모두 15회 상한에도 latency 정밀도가 수렴하지 않았다(No Mesh보다 CI가 넓음). No-Mesh 대비 예비 비교(Evidence 문서 참고)는 방향성 참고용일 뿐이며, 정식 profile 간 통계 비교 도구는 아직 없다(Phase 8에서 구현 예정).
- Ambient는 high 조건만 15회 상한에도 p99가 수렴하지 않았다(세 profile 중 가장 넓은 단일 미달 폭, 10.00ms).
- Sidecar/Ambient 도입 후 메모리 여유가 더 빠듯해졌다(`NODE_MEMORY_HEADROOM_LOW`가 Phase 5/6에서 가장 흔한 무효 요인). Phase 7(Waypoint)도 같은 제약을 받을 것으로 예상한다.
- **Phase 6의 replica/node 확장 측정은 아직 하지 않았다** — 지금 Evidence는 고정 replica(서비스당 1개) 조건에서만 유효하다.
- kafka/producer/worker의 Ambient HBONE 연결이 여전히 타임아웃된다(SYNC_CHAIN 범위 밖이라 이번 Evidence에는 영향 없음, Phase 9 비동기 파이프라인 작업 시 재확인 필요).
- **Phase 7(Waypoint)은 blocked 상태다** — orchestrator-service 단일 hop 구성에서 gateway→waypoint 홉은 성공하지만 waypoint→실제 backend pod 홉이 항상 TCP 연결 후 HTTP 즉시 리셋으로 실패한다. 같은 노드 배치 가설은 podAntiAffinity로 재현·기각했다. `istioctl` 없이는 근본 원인을 더 파기 어려워 보류했다. Phase 8은 Waypoint 없이 3개 profile로 진행한다.
- VM inventory, MAC과 DMI UUID 원본 및 고유성을 확인했다.
- dirty-tree dry-run은 telemetry completeness를 통과했지만 성능 Evidence로 사용하지 않는다.
- 운영 credential은 저장하지 않고 SSH key와 로컬 kubeconfig를 사용한다.

## 마지막 검증

- `java -version`: Temurin 25.0.3
- Java 서비스 5개 `gradlew test`: passed
- Compose 7개 healthy, chain/fanout/payload/async E2E: passed
- Python runner unit test: passed
- Docker k6 동일 spec 3회: artifact 생성, Compose adapter 무효화 passed
- Kubernetes: `mesh-cp-01`, `mesh-worker-01`, `mesh-worker-02` 모두 `Ready`
- Cilium DaemonSet: Desired/Current/Ready `3/3/3`
- Cilium Operator `2/2`, Hubble Relay `1/1`, Hubble UI `1/1` Available
- MetalLB Controller `1/1`, Speaker `3/3`, `GatewayClass/cilium` Accepted
- Gateway smoke: `192.168.200.100`, Programmed/Accepted/ResolvedRefs, Windows HTTP passed
- Helm `meshperf` revision 1: `deployed`, 애플리케이션/Kafka Pod 모두 Ready
- No-mesh E2E: ping/3-hop chain/3-target fan-out/4 KiB payload/3-task async passed
- Prometheus: benchmark Java job 7개 `up=1`, async completed `3`
- NetworkPolicy: Helm revision 3, KNP 11개와 CNP 1개, 허용/차단 smoke passed
- Prometheus: NetworkPolicy 적용 후 Java job 7개 `up=1`, async completed 누계 `6`
- Runner dry-run v2: 환경 Gate passed, `DIRTY_SOURCE_TREE`만으로 `INVALID`
- Runner final dry-run: commit `3848517`, status `COMPLETED`, invalidating factor 없음
- Git: Phase 3 구현 `3848517`, final Evidence `2d9fa1a`
- Phase 4 policy: core 조건 10~15회, run당 최소 20,000 request, precision stop rule
- Formal duration: nominal/high/near-saturation 8/17/22 RPS에서 2,525/1,189/919초
- Formal VUs: 8/17/22 RPS 모두 128 pre-allocated/max VUs로 고정
- Canonical capacity: C*=28 RPS, first failing=30 RPS, interval width 7.14%
- Canonical operating points: 3/8/17/22 RPS
- Low 3 RPS는 sanity/linearity 전용이며 정식 cross-profile 반복에서 제외
- Capacity retry: 27/28 RPS `COMPLETED`, telemetry factor 없음, Tempo restart 0
- Formal baseline session 1 block 1: 8/17/22 RPS 각각 유효 run 1/10
- Formal baseline 최종: nominal 15회(`INCONCLUSIVE_MAX_RUNS`), high 10회(`STOP_PRECISION_REACHED`), near-saturation 13회(`STOP_PRECISION_REACHED`)
- Python 전체 unittest: 24 passed
- Git: 스케줄러 버그 수정 `2e8faf4`, ADR-0023 `0a78a3b`, Phase 4 최종 Evidence `d697ec1`
- Istio 설치: `istio-base`/`istiod` 1.30.3, istiod 요청 200m CPU/512Mi 메모리(ADR-0024), 노드 스케줄링 확인
- Sidecar 주입: 7개 SYNC_CHAIN 서비스 `2/2 Running`, mTLS PERMISSIVE(Envoy config dump로 TLS+client cert 확인)
- Sidecar formal baseline 최종: nominal/high/near-saturation 모두 15회 `INCONCLUSIVE_MAX_RUNS`
- Sidecar 실측 proxy CPU: 0.0072~0.0086 core-s/req, 메모리 peak 약 294~306MiB (조건 간 거의 일정)
- Git: ADR-0024 `829077b`, 스케줄러 일반화 `34f69b8`, throttle metric 수정 `20981cc`, 견고성 개선 `8afe58c`, Phase 5 최종 Evidence `fb7d5e1`
- ztunnel 설치: istio-cni + ztunnel 1.30.3, istiod에 `PILOT_ENABLE_AMBIENT=true` 추가 필요했음
- Ambient 호환성 수정 2건: probe를 httpGet(pod IP)→exec wget(127.0.0.1)로 전환, NetworkPolicy에 HBONE 포트 15008 추가(ambient.enabled 게이트)
- Ambient formal baseline 최종: nominal 10회(`STOP_PRECISION_REACHED`)/high 15회(`INCONCLUSIVE_MAX_RUNS`)/near-saturation 14회(`STOP_PRECISION_REACHED`)
- ztunnel 실측: 누적 CPU 72.9~82.4 core-s/run window(클러스터 전체, per-request 아님), 메모리 peak 약 16.7~16.9MiB (Envoy 대비 훨씬 가벼움)
- Git: ADR-0025 `39cf266`, Ambient 지원과 호환성 수정 `b63c386`, ztunnel 자원 수집 `e35d391`, Phase 6 최종 Evidence `a8b9fd6`
- Waypoint: `istio-waypoint` GatewayClass 자동 생성 확인, Gateway 리소스로 Pod 자동 프로비저닝 확인
- Waypoint 진단: Envoy `/clusters`에서 `cx_total=1,cx_connect_fail=0,rq_error=1,rq_success=0` — TCP는 연결되지만 HTTP 요청이 즉시 리셋. ztunnel access log에 해당 연결 기록 없음
- Waypoint 재현 시도: podAntiAffinity로 다른 노드 강제 배치 후에도 동일 실패 — 같은 노드 가설 기각
- Waypoint 심화 진단: `istioctl` 설치 후 xDS 설정 확인(정상), Waypoint 내부→실제 backend 평문 curl 성공(네트워킹 정상), `cilium-dbg endpoint list`에 Waypoint IP 미노출(원인 불명)
- Waypoint 거짓 양성 발견: 클린 재배포 직후 5연속 성공했으나 Waypoint 자체 rq_total은 무변화 → 20연속 재시도 시 0/20 성공. 최초 성공은 연결 풀 재사용에 의한 우회로 판정
- 클러스터 복구: Waypoint 라우팅 완전 제거 후 SYNC_CHAIN HTTP 200/3-hop 완료 재확인
- Git: ADR-0026 `af0d10c`, Phase 7 blocked 체크포인트 `58736f1`
- Replica-scaling: ADR-0027, `experiments/replica_scaling.py`, 18/18 run `COMPLETED` (Sidecar/Ambient × 1/2/4 replica × 3회)
- Python 전체 unittest: 27 passed
- Git: ADR-0027 `30abbef`/`6f90e72`, replica_scaling.py `b702871`, replica-scaling Evidence 커밋 예정

## 재개 절차

1. 이 파일과 [전체 체크리스트](checkpoints/phase-checklists.md)를 읽는다.
2. `git status -sb`와 현재 브랜치를 확인한다.
3. 진행 중 체크포인트의 미완료 항목부터 시작한다.
4. 변경 근거, 검증 결과와 다음 작업을 이 파일에 갱신한다.
