# 현재 작업 상태

이 파일은 세션 재개를 위한 단일 체크포인트다. 작업을 시작하거나 종료할 때 반드시 갱신한다. 완료 주장은 체크리스트와 Evidence가 일치할 때만 기록한다.

## 현재 위치

- Project: Mesh Performance Lab
- Overall Phase: Phase 5 — Istio Sidecar 설치·검증 완료, 정식 반복측정 진행 중
- Infrastructure Step: Istio 1.30.3 설치, sidecar 주입과 mTLS 검증 완료
- Status: phase-5-formal-measurement-in-progress
- Last updated: 2026-07-26

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

## 다음 작업

1. Phase 5 paired 정식 반복측정을 조건별 valid run이 `CONTINUE`가 아닐 때까지 세션을 이어서 실행한다.
2. 완료되면 Phase 5 Evidence 문서를 작성하고 checklist/CURRENT.md/PORTFOLIO.md를 갱신한다.
3. Phase 6(Ambient)에 착수한다.

## 현재 한계

- 로컬 Compose runner 결과는 자동으로 `INVALID` 처리되며 성능 Evidence로 사용할 수 없다.
- 이 클러스터(노드당 allocatable 2 vCPU)는 p95 ≈5ms/p99 ≈8ms보다 작은 latency 차이를 통계적으로 구분하지 못한다. Phase 5 이후 Mesh profile 오버헤드가 이보다 작게 나오면 `확인된 차이 없음`으로만 보고해야 한다.
- nominal(8 RPS) 조건은 15회까지도 p99 정밀도 기준에 수렴하지 않았다. cross-profile 비교에서 nominal의 p99는 다른 조건보다 넓은 CI를 감안해 해석한다.
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
- Python 전체 unittest: 21 passed
- Git: 스케줄러 버그 수정 `2e8faf4`, ADR-0023 `0a78a3b`, Phase 4 최종 Evidence 커밋 예정

## 재개 절차

1. 이 파일과 [전체 체크리스트](checkpoints/phase-checklists.md)를 읽는다.
2. `git status -sb`와 현재 브랜치를 확인한다.
3. 진행 중 체크포인트의 미완료 항목부터 시작한다.
4. 변경 근거, 검증 결과와 다음 작업을 이 파일에 갱신한다.
