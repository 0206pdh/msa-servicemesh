# 현재 작업 상태

이 파일은 세션 재개를 위한 단일 체크포인트다. 작업을 시작하거나 종료할 때 반드시 갱신한다. 완료 주장은 체크리스트와 Evidence가 일치할 때만 기록한다.

## 현재 위치

- Project: Mesh Performance Lab
- Overall Phase: Phase 9 완료. **Phase 10 데이터 수집 완료, Evidence 작성 전 단계**:
  - pod-kill(`experiments/resilience.py`, orchestrator-service): 10/10회 완료(2026-08-02) —
    `results/phase10-pod-kill-orchestrator/repeat-01~10`, recovery 29.9~39.9초, peakErrorRate 38~73%
  - chain-wide delay(`hop_delay_ms=50`, nominal 8 RPS): 3세션×5블록=15/15회 완료(2026-08-03) —
    `results/phase10-chain-delay-50ms*`, state.json 최종 `SESSION_COMPLETED`이나 `cpuCoreSecondsPerRequest`
    정밀도는 15회 상한에도 미수렴(`observedRelative` 10.6% vs 기준 5%/절대 0.01) — 기존 phase들의
    `INCONCLUSIVE_MAX_RUNS`와 같은 패턴, 재측정 불필요하고 이 한계를 명시한 채 Evidence로 보고
  - 둘 다 정전 **이전에** 완료됨 — 아래 인시던트와 무관하게 데이터 자체는 유효함
- **2026-08-03 인시던트**: 호스트 전원 손실로 VM 3대 비정상 종료 → `mesh-cp-01`의 etcd 데이터
  손상(bbolt backend consistent-index 손실, snapshot 복구용 `.snap.db` 부재로 panic). 사용자 승인 하에
  `/var/lib/etcd` 백업(`mesh-cp-01:/tmp/etcd-backup-20260803T015518Z.tar.gz`) 후 kubeadm
  reset+init으로 클러스터 전체 재부트스트랩, Cilium 1.19.6부터 Ambient(Istio 1.29.6)까지 전체 스택
  재설치 완료(2026-08-03). 측정 결과(`results/`, git 커밋)는 클러스터와 독립적으로 보존되어 영향 없음.
  재구축 상세는 아래 "마지막 검증" 참고
- Infrastructure Step: 클러스터는 순수 Ambient 상태(Istio 1.29.6, 재설치본). orchestrator-service
  1 replica
- Status: phase-10-data-collected-evidence-pending
- Last updated: 2026-08-03

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
- [x] **waypoint→실제 backend pod 홉 연결 — 2026-07-30 해결**: `orchestrator-service` NetworkPolicy의
      waypoint ingress 규칙이 HBONE 15008 포트를 빠뜨려 Cilium이 SYN을 drop하고 있었다(`cilium monitor
      --type drop`으로 확인). 포트 추가 후 20/20·50/50 성공, rq_total 증가로 실제 트래픽 통과 검증
      (`phase-07-p1-waypoint-blocked`의 "최종 해결" 절 참고)
- [x] 클러스터를 순수 Ambient 상태로 복구했다가, NetworkPolicy 수정 후 Waypoint를 다시 활성화(현재 상태)
- [x] Replica 확장 방향성 연구 완료 (ADR-0027): orchestrator-service 1/2/4 replica × Sidecar/Ambient × 3회 = 18 run, 전부 성공
- [x] 발견: Sidecar 메모리는 replica 수에 선형 비례(120→173MiB), Ambient/ztunnel 메모리는 거의 불변(15.8→16.1MiB) — 가설 1 방향과 일치
- [x] 발견: Ambient latency가 replica 증가에 따라 뚜렷이 악화(p99 51→99.5ms, 방향성 데이터). Sidecar는 오히려 소폭 개선(부하분산 효과로 추정)
- [x] Istio 1.30.3 → 1.29.6 완전 재설치 후 Waypoint 재시도: 순수 Ambient는 정상, Waypoint 경유는 동일하게
      0/20 재현 → 당시 "버전 독립적 근본 비호환"으로 판단했으나, 이는 **틀린 결론이었음이 2026-07-30에
      밝혀짐** (실제 원인은 NetworkPolicy 템플릿 버그, Istio 재설치로는 바뀌지 않는 리소스였음)
- [x] 클러스터를 순수 Ambient 상태(Istio 1.29.6)로 재복구, SYNC_CHAIN 정상 동작(HTTP 200, 3/3) 재확인
- [x] `experiments/compare_profiles.py` 구현: 독립 2-표본 bootstrap 차이 검정(medium(B)-median(A), 95% CI).
      `analysis.py`의 valid-run 필터링 로직을 `collect_valid_runs()`로 분리해 재사용(기존 24개 테스트 회귀 없음 확인)
- [x] No-Mesh/Sidecar/Ambient 3개 profile × 3개 부하 조건(nominal/high/near-saturation) × 6개 지표 = 36개
      비교 완료. 핵심 발견: network bytes/request는 Sidecar가 세 조건 모두에서 일관되게 ~49% 증가(고신뢰,
      CI가 0에서 크게 벗어남), Ambient는 No-Mesh 대비 ~1-2%만 증가. p95/p99 latency는 27개 비교 중 단
      1건(high 조건, No-Mesh vs Ambient)만 유의했고 다음 부하 단계(near-saturation)에서 방향이 뒤집혀
      재현되지 않음 — 확정 결론으로 보지 않음. app 자체 CPU-per-request는 9개 비교 전부 유의한 차이 없음
      (`docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md`)
- [x] 시간축 metric/trace/resource 상관 분석 시도 → **metric/trace는 재구성 불가, 로그는 남아있지만
      쓸모 없음으로 확정**: Prometheus/Tempo는 24h retention이 실제로 강제돼(각각 자체 TSDB retention과
      살아있는 compactor로 확인) Phase 4~7 시점 데이터가 진짜로 사라졌다. 반면 Loki는 `retention_period:
      24h`가 설정만 있고 강제하는 compactor가 없어 2026-07-23 로그도 실제로는 남아있음을 직접 확인했다
      (최초 조회는 `namespace` 라벨을 잘못 써서 "없다"고 오판했었음 — `k8s_namespace_name`이 맞는 라벨).
      다만 가장 latency가 높았던 run 구간의 로그를 실제로 열어보니 WARN/ERROR 0건, 전체 로그도 2줄뿐이라
      (애플리케이션이 lifecycle/error만 기록하고 요청 단위 로그를 안 남김) 상관 분석에 쓸 내용이 없었다.
      조작 없이 이 정확한 한계로 기록하고 Phase 8 Evidence 종료
- [x] Phase 8 Evidence validated (통계 비교 완료 + 시간축 분석 한계 기록)
- [x] Runner에 `window_timeseries()` 추가 — run마다 15초 간격 실제 시계열(`raw/prometheus-timeseries.json`)을
      집계 스냅샷과 함께 저장 (Phase 8에서 겪은 "재구성 불가" 한계 재발 방지, 게이트에는 영향 없음)
- [x] Phase 9 실험 1(ADR-0028) 완료: Sidecar mTLS PERMISSIVE vs DISABLE, nominal 8 RPS, DISABLE 10회
      `STOP_PRECISION_REACHED`. 핵심 가설("mTLS가 Sidecar network-bytes 오버헤드의 주 원인") 기각 —
      DISABLE은 network bytes/request를 341B(~1%)만 줄임, Phase 8에서 확인한 Sidecar 전체 오버헤드
      10,469B(~49%)의 극히 일부. p95/p99 latency는 DISABLE에서 오히려 유의하게 악화(+12.4ms/+18.9ms)했으나,
      측정 도중 Phase 5 baseline(Istio 1.30.3)과 이번 측정(1.29.6) 사이 버전이 다르다는 confound를 발견함.
      같은 버전 대조군 측정을 시작했으나 사용자 지시로 중단하고, confound를 명시한 채 기존 비교를 그대로
      보고하기로 함 (`docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md`)
- [x] mTLS DISABLE 실험 종료 후 클러스터를 순수 Ambient 상태로 복구
- [x] Phase 7 Waypoint 정식 반복측정 완료(2026-08-01): nominal/high/near-saturation 각 15회
      `INCONCLUSIVE_MAX_RUNS`(Sidecar와 같은 패턴). 무효율 30~45%(`NODE_MEMORY_HEADROOM_LOW`)였으나
      VM 자원은 바꾸지 않고 반복 횟수만 늘려 극복
- [x] Waypoint cross-profile 비교(9건) 완료: network bytes/request는 세 조건 모두 Ambient와 Sidecar
      사이(No-Mesh 대비 +16~18%, Ambient +1~2%/Sidecar +49%와 대비, 9/9 유의). latency는 nominal/high
      조건에서 세 profile 대비 일관되게 유의하게 느리지만(2개 부하 조건 재현) near-saturation에서는 차이
      소멸(원인 미규명). app CPU는 high 조건에서만 간헐적 유의, memory는 9/9 유의한 차이 없음
      (`docs/evidence/performance/2026-08-01-canonical-waypoint-baseline-final.md`)
- [x] Phase 7 Evidence validated — Phase 7 완료
- [x] 클러스터를 Waypoint→순수 Ambient로 복구, orchestrator-service를 4 replica로 전환해 Phase 9 실험 2 재개
- [x] Phase 9 실험 2(ADR-0029) 완료(2026-08-02): replica=4 10회 `STOP_PRECISION_REACHED`. p99 저하 방향은
      확인(유의, +20%)됐지만 ADR-0027 방향성 연구의 크기(+95%)는 재현 안 됨. ztunnel 메모리는 방향성
      연구와 반대로 유의하게 증가(+79%, "추가 조사 필요"로 기록). ztunnel CPU 증가는 재현 안 됨
      (`docs/evidence/performance/2026-08-02-phase9-ambient-replica-scaling-formal.md`)
- [x] Phase 9 결론 validated — 실험 1·2·3 종합해 Phase 9 종료
- [x] Phase 10 범위 설계(ADR-0030): Chaos Mesh는 자원 위험 대비 불필요하다고 판단해 배제, Pod
      kill(kubectl)과 chain-wide delay(기존 파라미터)로 축소. `experiments/resilience.py`(pod-kill,
      Prometheus 기반 recovery-time 계산) 구현·테스트 완료. `hop_delay_ms` 파라미터를
      discovery_spec/formal_spec/BaselineMeasurement에 추가(기존 fingerprint 불변 확인)

## 다음 작업

1. **Phase 10 Evidence 작성**: pod-kill(10/10) + chain-wide delay(15/15, `SESSION_COMPLETED`이나
   cpuCoreSecondsPerRequest 정밀도 미수렴)를 분석해 `docs/evidence/performance/`에 결과 문서를 쓰고
   ADR-0030에 결과를 반영한 뒤 Phase 10을 종료한다. 데이터는 이미 `results/`에 있음 — 재측정 불필요.
2. Waypoint의 near-saturation에서 latency 차이가 사라지는 메커니즘과 ztunnel 메모리가 replica 확장에
   따라 왜 늘어나는지(방향성 연구와 반대 결과)는 둘 다 미규명 — Phase 10/11 이후 후속 과제로 기록한다.
3. Phase 10 Evidence 완료 후 Phase 11(최종화): 선택 Matrix, 새 환경 재현, 최종 보고서.

## 현재 한계

- 로컬 Compose runner 결과는 자동으로 `INVALID` 처리되며 성능 Evidence로 사용할 수 없다.
- 이 클러스터(노드당 allocatable 2 vCPU)는 p95 ≈5ms/p99 ≈8ms보다 작은 latency 차이를 통계적으로 구분하지 못한다. Mesh profile 오버헤드가 이보다 작게 나오면 `확인된 차이 없음`으로만 보고해야 한다.
- nominal(8 RPS) 조건은 No Mesh에서 15회까지도 p99 정밀도 기준에 수렴하지 않았다. cross-profile 비교에서 nominal의 p99는 다른 조건보다 넓은 CI를 감안해 해석한다.
- Sidecar profile은 세 조건 모두 15회 상한에도 latency 정밀도가 수렴하지 않았다(No Mesh보다 CI가 넓음). No-Mesh 대비 예비 비교(Evidence 문서 참고)는 방향성 참고용일 뿐이며, 정식 profile 간 통계 비교 도구는 아직 없다(Phase 8에서 구현 예정).
- Ambient는 high 조건만 15회 상한에도 p99가 수렴하지 않았다(세 profile 중 가장 넓은 단일 미달 폭, 10.00ms).
- Sidecar/Ambient 도입 후 메모리 여유가 더 빠듯해졌다(`NODE_MEMORY_HEADROOM_LOW`가 Phase 5/6에서 가장 흔한 무효 요인). Phase 7(Waypoint) 정식 반복측정에서 무효율 30~45%로 실제 확인됐다 — VM 자원은 바꾸지 않고 반복 횟수만 늘려서 극복했다. Phase 9 실험 2(replica=4)에서도 같은 제약이 예상된다.
- **Phase 6의 replica/node 확장 측정은 아직 하지 않았다** — 지금 Evidence는 고정 replica(서비스당 1개) 조건에서만 유효하다.
- kafka/producer/worker의 Ambient HBONE 연결이 여전히 타임아웃된다(SYNC_CHAIN 범위 밖이라 이번 Evidence에는 영향 없음, Phase 9 비동기 파이프라인 작업 시 재확인 필요).
- **Prometheus/Tempo는 24h retention이 실제로 강제되고 있어 Phase 4~7 run들의 원본 metric/trace는 이미 만료돼 다시 조회할 수 없다**(Prometheus는 자체 TSDB retention, Tempo는 살아있는 compactor로 확인). Runner가 저장하는 `raw/prometheus-window.json`도 구간 전체 집계 스칼라값일 뿐 실제 시계열이 아니다. 반면 **Loki(로그)는 `retention_period: 24h`가 설정만 돼 있을 뿐 compactor/retention_enabled가 없어 실제로는 강제되지 않는다** — 2026-07-23 시점 로그도 여전히 조회 가능함을 직접 확인했다. 다만 확인해보니 애플리케이션이 lifecycle/error 로그만 남기고 요청 단위 로그를 남기지 않아, 로그가 남아있어도 시간축 상관 분석에 쓸 만한 내용은 없었다(`docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md`). 향후 시간축 상관 분석이 필요한 실험은 run 종료 직후(24h 이내) metric/trace를 별도로 조회하거나 Runner에 `query_range` 캡처를 추가해야 하고, 로그 기반 분석을 쓰려면 애플리케이션 로깅 자체를 더 상세하게 바꿔야 한다.
- **Phase 7(Waypoint)은 2026-07-30에 해결됐다** — 근본 원인은 `orchestrator-service` NetworkPolicy의 waypoint ingress 규칙이 HBONE 포트(15008)를 빠뜨린 템플릿 버그였다. `cilium monitor --type drop`으로 Cilium이 이 포트의 SYN을 정책 위반으로 드롭하는 것을 직접 확인했다. 이전에 "Istio 버전과 무관한 근본 비호환"으로 내렸던 결론은 틀린 추론이었다 — NetworkPolicy는 Istio 재설치로 바뀌지 않는 리소스이므로, 버전을 바꿔도 같은 실패가 재현된 것은 애초에 당연한 결과였다. 포트 추가 후 20/20·50/50 연속 성공, Waypoint 자체 rq_total 증가로 실제 트래픽 통과를 검증했다. Phase 8의 3-profile 비교 결론 자체는 Waypoint와 무관하므로 그대로 유효하다.
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
- Waypoint 버전 재설치 재현(최종): Istio 1.29.6 완전 재설치, 순수 Ambient 정상 확인 후 Waypoint 재구성 →
  20회 배치 재시도 `success=0 fail=20`, 1.30.3과 동일 실패 재현 → 버전 독립적 비호환으로 최종 판단
- 최종 복구: Waypoint 라벨/Gateway 제거, `helm upgrade` 재적용, SYNC_CHAIN 3/3 HTTP 200 재확인 (Istio 1.29.6 기준)
- Python 전체 unittest: 31 passed (compare_profiles.py 신규 테스트 4개 포함)
- Phase 8 비교 도구 실행: 36개 metric 비교 중 significant 13건 (network bytes/request 9건 전부 significant,
  나머지는 latency 1건 · throughput 1건(미미) · memory 1건(원인 불명) · cpu-per-request 0건)
- Git: analysis.py 리팩터링 + compare_profiles.py + Phase 8 Evidence 커밋 예정
- Replica-scaling: ADR-0027, `experiments/replica_scaling.py`, 18/18 run `COMPLETED` (Sidecar/Ambient × 1/2/4 replica × 3회)
- Python 전체 unittest: 27 passed
- Git: ADR-0027 `30abbef`/`6f90e72`, replica_scaling.py `b702871`, replica-scaling Evidence 커밋 예정
- Python 전체 unittest: 33 passed (baseline.py conditions/extra_spec_fields 신규 테스트 2개 포함)
- Runner 개선: `KubernetesAdapter.window_timeseries()` 추가, `raw/prometheus-timeseries.json`으로 15초
  간격 실제 시계열 저장 시작(게이트 미적용, 실패해도 run 무효화 안 함)
- Phase 9 실험 1: Sidecar mTLS DISABLE 10회 `STOP_PRECISION_REACHED` (nominal, Istio 1.29.6). PERMISSIVE
  대비 network bytes/request -341B(~1%)만 감소 → mTLS는 Sidecar 전체 오버헤드(Phase 8 기준 10,469B)의
  ~3%만 설명, 가설 기각. p95/p99는 유의하게 악화(+12.4ms/+18.9ms)했으나 Istio 1.30.3(before)/1.29.6(after)
  버전 confound가 있어 확정하지 않음(사용자 지시로 같은 버전 대조군 측정은 중단)
- Wire-level mTLS 검증: `istioctl proxy-config listener`로 DISABLE 시 inbound listener에 tlsContext 없음 확인
- Git: Runner 시계열 캡처 `aaa5a56`, ADR-0028 confound 기록 `1b0ba9e`, Phase 9 Evidence 커밋 예정
- Phase 9 실험 2(Ambient replica=4) 진행 중 사용자 지시로 중단, orchestrator-service 1 replica로 원복
- Waypoint 재진단: `cilium monitor --type drop`으로 waypoint(identity 49325)→orchestrator-service
  (identity 10965) 15008 SYN이 `Policy denied`로 drop되는 것을 직접 확인 (Envoy/istioctl/cilium-dbg
  수준 진단으로는 안 보이던 것)
- 근본 원인 확정: `deploy/charts/meshperf/templates/networkpolicies.yaml`의 orchestrator-service
  ingress 규칙(waypoint from)이 포트 8080만 허용, 15008 누락. 포트 추가 후 20/20, 50/50 연속 성공,
  Waypoint rq_total 증가로 실제 트래픽 통과 검증(거짓 양성 아님)
- Runner에 Waypoint 자원 수집 추가(`window_timeseries`/`_summary`가 `resources.waypoint`를 항상
  `null`로 두던 것을 실제 쿼리로 교체), sidecar 쿼리에서 waypoint pod 제외해 이중 집계 방지
- Python 전체 unittest: 36 passed
- Git: NetworkPolicy 수정 + Waypoint 자원 수집 `6711f53`
- 문서 정정: 이전 "버전 독립적 근본 비호환" 결론을 오류로 정정 — `phase-07-p1-waypoint-blocked`,
  ADR-0026 amendment, 이 파일에 모두 반영
- Phase 7 Waypoint 정식 baseline: nominal/high/near-saturation 각 15회 `INCONCLUSIVE_MAX_RUNS`
- Waypoint 실측 자원: request당 CPU 0.0014~0.0016 core-s, 메모리 peak ~45MB(Sidecar와 동일 모델)
- Waypoint cross-profile 비교 9건: network bytes/request 9/9 유의(Ambient·Sidecar 사이, No-Mesh 대비
  +16~18%), latency는 nominal/high 조건에서 세 profile 대비 일관되게 유의, near-saturation은 유의하지 않음
- Python 전체 unittest: 36 passed
- 클러스터: Waypoint 라우팅 제거, 순수 Ambient 복구, orchestrator-service 4 replica로 전환(scrape targets
  10 확인)
- Git: Phase 7 최종 Evidence 커밋 예정
- Phase 9 실험 2: replica=4 10회 `STOP_PRECISION_REACHED`, replica1 vs replica4 비교 완료
- Python 전체 unittest: 43 passed (resilience.py 테스트 4개, hop_delay_ms 테스트 2개 포함)
- Git: Phase 10 스코프(ADR-0030) + resilience.py `5f14c6d`, Phase 9 실험 2 Evidence 커밋 예정
- Phase 10 pod-kill 정식측정: 10/10회 완료, recovery 29.9~39.9초(2가지 클러스터로 갈림), peakErrorRate
  38~73%
- Phase 10 chain-delay(50ms, nominal) 정식측정: 3세션(5블록×3)=15/15회 완료, `SESSION_COMPLETED`,
  cpuCoreSecondsPerRequest만 정밀도 미수렴(observedRelative 10.6%, 기준 5%/0.01)
- Git: Unicode 디코드 크래시 수정 `07c2283`, error-rate 쿼리/k6 summary 필드 수정 `ecb9e83`
- **2026-08-03 인시던트 복구**: 정전으로 손상된 `mesh-cp-01` etcd를 kubeadm reset+init으로
  재부트스트랩(K8s v1.36.2, pod-cidr 10.244.0.0/16, service-cidr 10.96.0.0/12 — 손상 전 apiserver/
  controller-manager manifest에서 실측), Cilium 1.19.6(kubeProxyReplacement, ipam=kubernetes,
  k8sServiceHost/Port 명시 필요 — 없으면 ClusterIP 부트스트랩 순환 문제로 cilium 자체가 안 뜸) 재설치,
  Gateway API v1.4.1 + MetalLB 0.16.1 + local-path-provisioner v0.0.36 재설치, observability
  스택(kube-prometheus-stack/Loki/Tempo/OTel Collector) 재설치, `meshperf` Helm(no-mesh→ambient)
  재배포, Istio 1.29.6(istiod/istio-cni/ztunnel) 재설치 — istio-cni는 Cilium이 `cni.exclusive`
  기본값으로 conflist를 계속 덮어써서 처음엔 안 떴음, `cni.exclusive=false` 설정 후 Cilium daemonset
  재시작해서 해결
- 재구축 검증: 노드 3/3 Ready, Cilium 3/3 + Operator 2/2 + Hubble Relay/UI 1/1, MetalLB Controller
  1/1 + Speaker 3/3 + GatewayClass 4종 Accepted, NetworkPolicy 11 KNP + 1 CNP, Prometheus benchmark
  job 7개 `up=1`, ztunnel 3/3 + `ambient.istio.io/redirection: enabled` 확인, SYNC_CHAIN E2E(ping/
  chain/fanout/payload/async) 전부 통과(X-Correlation-Id/X-Experiment-Run-Id 헤더 필수 — 없으면
  내부 hop 호출에서 400/500), orchestrator-service 1 replica, Python 실험 러너 dry-run
  `COMPLETED`/invalidatingFactors 없음으로 측정 파이프라인 전체 복구 확인
- kafka/producer/worker의 Ambient HBONE 타임아웃은 재발(기존에도 문서화된 SYNC_CHAIN 범위 밖 한계,
  재구축으로 인한 새 문제 아님)
- etcd 백업 보존 위치: `mesh-cp-01:/tmp/etcd-backup-20260803T015518Z.tar.gz`(복구 실패 시 참고용,
  손상된 데이터라 재사용 불가 — 새 etcd는 완전히 새로 부트스트랩됨)

## 재개 절차

1. 이 파일과 [전체 체크리스트](checkpoints/phase-checklists.md)를 읽는다.
2. `git status -sb`와 현재 브랜치를 확인한다.
3. 진행 중 체크포인트의 미완료 항목부터 시작한다.
4. 변경 근거, 검증 결과와 다음 작업을 이 파일에 갱신한다.
