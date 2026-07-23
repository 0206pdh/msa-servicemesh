# 현재 작업 상태

이 파일은 세션 재개를 위한 단일 체크포인트다. 작업을 시작하거나 종료할 때 반드시 갱신한다. 완료 주장은 체크리스트와 Evidence가 일치할 때만 기록한다.

## 현재 위치

- Project: Mesh Performance Lab
- Overall Phase: Phase 4 — No Mesh baseline 준비
- Infrastructure Step: Phase 3 exit Gate 완료
- Status: phase-4-canonical-baseline-measurement
- Last updated: 2026-07-23

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

## 다음 작업

1. SYNC_CHAIN canonical condition을 8/17/22 RPS에서 seeded randomized block으로 정식 측정한다.
2. 조건별 유효 run을 최소 10회 수집하고 bootstrap 95% CI 정밀도 Gate를 평가한다.
3. 최대 15회에도 정밀도 기준 미달이면 `INCONCLUSIVE_MAX_RUNS`로 기록한다.

## 현재 한계

- 로컬 Compose runner 결과는 자동으로 `INVALID` 처리되며 성능 Evidence로 사용할 수 없다.
- capacity discovery 값은 부하점 결정 Evidence이며 정식 profile 비교값은 아직 없다.
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
- Formal VUs: 관측된 2.61초 tail을 수용하도록 24/51/66 pre-allocated VUs
- Canonical capacity: C*=28 RPS, first failing=30 RPS, interval width 7.14%
- Canonical operating points: 3/8/17/22 RPS
- Low 3 RPS는 sanity/linearity 전용이며 정식 cross-profile 반복에서 제외
- Capacity retry: 27/28 RPS `COMPLETED`, telemetry factor 없음, Tempo restart 0

## 재개 절차

1. 이 파일과 [전체 체크리스트](checkpoints/phase-checklists.md)를 읽는다.
2. `git status -sb`와 현재 브랜치를 확인한다.
3. 진행 중 체크포인트의 미완료 항목부터 시작한다.
4. 변경 근거, 검증 결과와 다음 작업을 이 파일에 갱신한다.
