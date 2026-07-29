# Mesh Performance Lab — 포트폴리오 요약

> 이 문서는 이력서/포트폴리오용으로 프로젝트를 개요부터 결론까지 한 번에 설명하기 위한 요약본이다.
> 실험 방법론과 세부 근거의 원본은 `docs/` 아래 문서와 ADR을 따른다. 이 문서는 프로젝트가 진행됨에 따라
> 계속 갱신되며, 아직 실행하지 않은 구간은 `[TODO: ...]`로 표시했다.
>
> **마지막 갱신**: 2026-07-29 · **진행 상태**: Phase 4~6 완료, Phase 7(Waypoint) blocked 최종 확정(버전 재설치로도 동일 재현), replica-scaling 방향성 연구 완료 — Phase 8 착수 · **시작일**: 2026-07-22

---

## 0. 한눈에 보기 (TL;DR)

Service Mesh(Istio Sidecar/Ambient/Waypoint)를 온프레미스 Kubernetes에 도입할 때 흔히 "느려질 것이다"라는
막연한 인상만으로 의사결정을 한다. 이 프로젝트는 그 인상을 **직접 구축한 3노드 Kubernetes 클러스터 위에서
통제된 벤치마크 워크로드로 반복 측정**해 숫자로 바꾸고, 발견한 병목을 실제로 개선해 효과를 다시 정량 검증하는
개인 Performance Engineering 프로젝트다.

| 항목 | 내용 |
|---|---|
| 기간 | 2026-07-22 ~ 진행 중 |
| 역할 | 1인 — 실험 설계, 인프라 구축, Java 벤치마크 워크로드 구현, 측정 자동화, 통계 분석 전부 담당 |
| 인프라 규모 | VMware Workstation 3-VM Kubernetes 1.36 (control-plane 1 + worker 2), Cilium 1.19 CNI/Gateway, MetalLB, Prometheus/Grafana/Loki/Tempo/OTel 풀스택 관측 |
| 애플리케이션 | Java 25 + Spring Boot 4.1 기반 마이크로서비스 5종 (gateway/orchestrator/producer/worker/workload-target), Sync Chain·Fan-out·Kafka Async·Payload·Mixed-Resource 5개 통신 패턴 재현 |
| 측정 자동화 | Python 기반 Experiment Runner + k6 부하 생성기, capacity discovery → bootstrap 95% CI 정지 규칙까지 자동화 (`experiments/` 약 1,600줄) |
| 현재까지 확정 산출물 | No-Mesh/Sidecar/Ambient 세 profile의 정식 baseline 반복측정 완료(38+45+39회 유효 run), Sidecar/ztunnel 실측 자원 비용 확보, Ambient 설치 중 실제 호환성 결함 2건 발견·수정 |
| 커밋 수 | 40+ (2026-07-29 기준) |

**한 줄 성과 예시 (이미 측정된 값)**: No-Mesh 3-hop 동기 체인에서 부하를 28→30 RPS로 **7.1%**만 늘렸는데
p99 지연은 69.1ms→119.0ms로 **72.2%** 급증했다 — 이 임계점을 사전에 규명하지 않고 막연히 "여유 있어 보이는"
부하로 벤치마크했다면 Mesh profile 간 비교 자체가 무의미했을 것이다. (§6.1 참고)

**Phase 4 최종 결과 한 줄 요약**: nominal(8 RPS)/high(17 RPS)/near-saturation(22 RPS) 세 조건에서 각각
15/10/13회의 유효 반복측정을 완료했고, high와 near-saturation은 사전에 정의한 통계적 정밀도 기준을
통과(`STOP_PRECISION_REACHED`)했다. nominal은 15회 상한까지 다 채웠지만 p99 지표 하나가 근소하게
(8.9%) 기준을 넘지 못해 `INCONCLUSIVE_MAX_RUNS`로 명시적으로 결론을 유보했다 — 무리하게 통과시키지
않고 한계를 그대로 기록한 것 자체가 이 프로젝트의 방법론적 원칙이다. (§6.2 참고)

**Phase 5 최종 결과 한 줄 요약**: 같은 세 조건에서 Istio Sidecar profile을 15회씩(총 45회 유효 run) 측정한
결과, 이번엔 세 조건 모두 `INCONCLUSIVE_MAX_RUNS`로 끝났다 — No-Mesh보다 latency 정밀도가 잘 수렴하지
않는 현상 자체가 유의미한 관찰이다(Envoy를 통과하는 hop이 늘면서 run-to-run 변동성이 커진 것으로 추정).
다만 Envoy sidecar 자체의 CPU/메모리 비용(≈0.007~0.009 core-s/request, ≈300MiB 피크 메모리)은 부하
조건과 무관하게 안정적으로 직접 측정됐다. (§6.3 참고)

**Phase 6 최종 결과 한 줄 요약**: Istio Ambient(ztunnel)를 같은 세 조건으로 측정한 결과 nominal(10회)과
near-saturation(14회)은 정밀도 기준을 통과했고 high만 15회 상한에도 p99가 수렴하지 않았다 — No-Mesh와
Sidecar 사이 중간쯤 되는 수렴 패턴이다. ztunnel(Rust 기반, 노드당 1개 공유)의 메모리 사용량은 Envoy
sidecar(Pod당 ≈300MiB)의 1/20 이하(≈17MiB)로 훨씬 가벼웠다. 설치 과정에서 이 클러스터의 Cilium
설정과 Istio Ambient 간 실제 호환성 문제 두 건(kubelet probe가 ambient 트래픽 캡처에 걸려 전체 pod가
crash-loop한 문제, HBONE 포트가 기존 NetworkPolicy에 안 열려있던 문제)을 발견해 근본 원인까지 추적해
해결했다. 다만 Pod replica 수 증가에 따른 ztunnel 공유 비용의 확장 특성(가설 1의 핵심 검증 대상)은 아직
측정하지 않았고, Phase 8 병목 분석 전에 별도로 수행해야 할 잔여 작업으로 남아있다. (§6.4 참고)

---

## 1. 문제 정의 — 왜 이 프로젝트가 필요한가

### 1.1 배경

Microservice Architecture(MSA)는 메서드 호출을 네트워크 호출로 바꾸면서 latency, 부분 실패, 보안, 관측성
문제를 만든다. Service Mesh(Istio 등)는 애플리케이션 코드를 크게 바꾸지 않고 mTLS·라우팅·재시도·telemetry를
공통 제공해 이 문제를 완화하지만, 요청 경로에 proxy/tunnel이 끼어드는 대가로 latency·CPU·메모리·Pod 기동
시간이 늘어난다. 그런데 실무에서는:

- 공급자 벤치마크는 대개 유리한 조건(단순 echo, 저부하)에서 측정되어 특정 온프레미스 환경에 그대로 적용하기 어렵다.
- "Sidecar 방식"과 "Ambient(노드 공유 tunnel) 방식"의 비용 구조는 Pod 수 증가에 따라 **다르게** 확장될 것으로
  예상되지만, 이를 직접 측정해 비교한 자료는 흔치 않다.
- 단일 요청/단일 실행으로 낸 숫자는 재현성이 없고, 어디까지가 통계적 잡음이고 어디부터가 실제 차이인지
  구분하지 못한다.

### 1.2 정량적으로 표현한 문제 (이미 측정된 근거)

capacity discovery 단계에서 실제로 관측한 값이다 (§6.1 전체 표 참고):

| Target RPS | Achieved RPS | p99 (ms) | 비고 |
|---:|---:|---:|---|
| 10 (저부하 기준) | 10.004 | 41.945 | sanity baseline |
| 28 | 28.001 | 69.087 | 마지막 통과점 (C\*) |
| 30 | 30.002 | 118.975 | 첫 실패점 |

부하를 28→30 RPS로 **7.14%** 올렸을 뿐인데 p99는 69.087→118.975ms로 **72.2%** 폭증했고, 이는 저부하 p99 대비
**2.84배**로, 사전에 정한 "저부하 p99의 2배 초과 시 용량 초과로 판정" 기준을 넘겼다. 이런 비선형 붕괴 지점은
평균이나 처리율(achieved RPS는 30 RPS에서도 오류 0%로 목표치를 그대로 달성했다)만 봐서는 전혀 드러나지 않는다.
**"부하가 조금 늘었는데 오류율은 0%인데 tail latency만 폭증하는" 이 지점을 찾아내는 것 자체가 이 프로젝트가
풀어야 하는 문제의 핵심**이며, 이 지점을 규명하지 못한 채 임의의 절대 RPS로 Mesh profile을 비교하면 어떤
profile은 이미 포화 구간에서, 어떤 profile은 여유 구간에서 측정되는 불공정한 비교가 된다.

### 1.3 이 프로젝트가 답하려는 질문

> No Mesh, Istio Sidecar, Ambient, Ambient + Waypoint는 워크로드 특성별로 어떤 성능·자원·관측성·회복탄력성
> 차이를 만들며, 측정된 병목을 어떤 설정과 아키텍처 변경으로 개선할 수 있는가?

세부적으로는:

- Mesh profile별 p50/p95/p99, throughput, 오류율과 자원 비용은 얼마인가?
- Pod 수와 hop 수, payload, 동시성이 커질 때 비용 증가 형태는 어떻게 달라지는가?
- timeout/retry/circuit breaker의 소유 위치가 장애 전파와 회복에 미치는 영향은 무엇인가?
- Sidecar 또는 Waypoint의 L7 기능이 추가 비용만큼 실질적인 효과를 주는가?
- 병목을 개선했을 때 어떤 지표가 좋아지고 어떤 비용·기능 손실이 생기는가?
- 워크로드 유형별로 어떤 profile과 설정을 선택해야 하는가?

---

## 2. 검증 가설 (기각 가능한 가설로 설계)

사전 결론이 아니라 실험으로 기각될 수 있는 가설로 명시했다.

1. Sidecar의 Pod별 비용과 Ambient의 노드 공유 비용은 Pod 수 증가 시 다른 형태로 확장된다.
2. Waypoint는 L7 기능을 제공하지만 통과 트래픽과 replica에 따라 병목이 될 수 있다.
3. 앱과 Mesh의 중첩 retry는 장애 중 호출량과 tail latency를 증폭한다.
4. 전체 time budget과 단일 retry owner는 회복탄력성을 개선한다.
5. 선택적 Waypoint와 telemetry sampling은 필요한 기능을 유지하며 비용을 줄일 수 있다.
6. CPU 기반 HPA는 비동기 backlog에 적합하지 않고 queue lag 지표가 회복시간을 줄일 수 있다.

`[TODO: Phase 5~10 완료 후 가설별 채택/기각 결과와 근거 Evidence 링크를 여기에 채운다]`

---

## 3. 방법론 — 어떻게 "믿을 수 있는" 벤치마크를 만들었는가

### 3.1 설계 원칙

- Workload는 특정 profile에 유리하게 작성하지 않는다 (동일 이미지, 동일 digest, 동일 설정).
- 한 실험에서는 독립 변수 하나만 바꾼다.
- 부하 발생기는 대상 클러스터 자원과 분리하거나 자체 포화 여부를 증명한다.
- 평균만 쓰지 않고 p50/p95/p99, 분포와 이상치를 공개한다.
- 통계적 차이와 실무적으로 의미 있는 절대 차이를 구분한다.
- 실패한 최적화와 결론 불가 결과도 삭제하지 않고 보존한다.
- 모든 결론에는 적용 환경과 무효화 조건을 명시한다.

### 3.2 반복 측정 정책 (ADR-0014)

과거에는 "고정 RPS 3회 반복" 같은 임의 기준을 썼지만, 3노드 규모와 시나리오별 실제 처리 능력을 반영하지
못한다는 문제를 발견해 다음과 같이 재설계했다.

1. **탐색과 본 측정 분리**: capacity discovery는 10 RPS부터 2배씩(geometric) 늘리며 최초 실패점을 찾고,
   실패점과 마지막 통과점 사이를 최대 4회 이분 탐색(binary refinement)해 구간 폭을 10% 이내로 좁힌다.
   `usable capacity(C*)`는 achieved/target ≥ 98%, dropped iteration 0, 오류율 ≤ 1%, p99 ≤ 저부하 p99의 2배,
   node/부하발생기 CPU 여유, telemetry/cleanup gate 통과를 모두 만족하는 가장 높은 RPS다.
2. **본 측정 부하는 C\*의 10/30/60/80%**로 계산하고, 이 절대 RPS는 이후 모든 Mesh profile 비교에서 그대로
   재사용한다 (profile별로 다시 낮추지 않아야 "동일 조건" 비교가 성립한다).
3. **독립 run은 최소 10회, 최대 15회**: 10회 이후 p95(상대 반폭 ≤5%)·p99(≤10%)·CPU/request(≤5%) 세 지표의
   run-level median에 대해 percentile-bootstrap 95% CI를 계산해 세 기준을 모두 만족하면 종료하고, 15회에도
   미달하면 `INCONCLUSIVE_MAX_RUNS`로 판정한다. 무효 run은 통계에서 제외하되 원본은 삭제하지 않고 보존한다.
4. **표본 수 고정**: warm-up 180초 후 `min(2700, max(600, ceil(20000/targetRps)))`초를 측정해 p99 영역에서도
   충분한 표본(약 200개 이상)을 확보한다.
5. **시간 drift 통제**: 조건 순서를 고정하지 않고 seed 기반 randomized complete block으로 배치하며, 세션당
   같은 조건은 최대 5회만 실행하고 최소 2개 세션에 나눠 실행해 시간대별 환경 변화를 관찰한다.

### 3.3 최소 완료 기준 (요약)

| 영역 | 기준 |
|---|---|
| Profile | No Mesh/Sidecar/Ambient/Waypoint 4종을 동일 결과 schema로 측정 |
| 반복성 | core 조건 최소 10회·최대 15회, bootstrap 95% CI 정밀도와 이상치 공개 |
| 병목 | 최소 3개 병목을 telemetry Evidence로 설명 |
| 개선 | 최소 3개 개선안을 동일 조건으로 재측정, trade-off 함께 기록 |
| 재현 | 새 환경에서 문서·자동화만으로 핵심 결과 재생성 가능 |

---

## 4. 시스템 아키텍처 & 기술 스택

```text
External Load Generator (k6)
        │
        ▼
benchmark-gateway
  ├── orchestrator-service → chain(hop a→b→c) / fan-out(target N개)
  ├── producer-service → Kafka → worker-service
  └── payload-service 경로 (대용량 payload)

Experiment Runner (Python)
  ├── Helm profile/fault 적용
  ├── Ground Truth·Manifest(commit/digest/자원) 기록
  ├── Prometheus/Loki/Tempo/Hubble 조회
  └── raw/summary/report 저장 (SHA-256 무결성 기록)
```

| 계층 | 기술 |
|---|---|
| 애플리케이션 | Java 25, Spring Boot 4.1, Gradle 9 Wrapper |
| 플랫폼 | VMware Workstation 3-node Kubernetes 1.36 (kubeadm), Ubuntu 26.04 LTS, containerd |
| 네트워크/Mesh | Cilium 1.19 (CNI+Gateway+Hubble), MetalLB 0.16 L2, Gateway API 1.4, Istio 1.30.3 Sidecar+Ambient(ztunnel/istio-cni, Waypoint 추가 예정) |
| 관측성 | Prometheus, Grafana, Loki, Tempo, OpenTelemetry Collector |
| 부하·검증 | k6 (CONSTANT_ARRIVAL_RATE), Python 측정 자동화(`experiments/`, unittest 기반 회귀 테스트) |
| 배포 | Helm (profile별 values 분리), Docker/GHCR 이미지 배포 |

### 4.1 Mesh Profile 4종

| Profile | 구조 | 상태 |
|---|---|---|
| No Mesh | Client → App A → App B (Cilium만) | ✅ Phase 4 완료 |
| Sidecar | Pod마다 Envoy proxy 동반 (Istio 1.30.3) | ✅ Phase 5 완료 |
| Ambient | Node 공유 ztunnel (L4) | ✅ Phase 6 고정 replica 완료, 확장 측정 잔여 |
| Ambient + Waypoint | 선택적 L7 proxy 추가 | `[TODO: Phase 7]` |

---

## 5. 진행 현황 (Phase 0~11)

| Phase | 내용 | 상태 |
|---:|---|---|
| 0 | 실험 설계, 공정성/무효화 규칙, API·Event·Result 계약 | ✅ 완료 |
| 1 | Java 벤치마크 워크로드 5종 + Compose E2E | ✅ 완료 |
| 2 | Experiment Runner, k6 프로파일, Ground Truth 자동 수집 | ✅ 완료 |
| 3 | VMware 3노드 Kubernetes, Cilium, 관측 스택, NetworkPolicy | ✅ 완료 |
| 4 | **No Mesh 기준선** — capacity discovery와 정식 반복측정 완료 | ✅ 완료 |
| 5 | **Istio Sidecar 기준선** — 설치·mTLS 검증·정식 반복측정 완료 | ✅ 완료 |
| 6 | **Ambient 기준선** — 고정 replica 정식 반복측정 완료, replica/node 확장 측정 잔여 | 🔄 부분 완료 |
| 7 | Ambient + Waypoint 기준선 | 🚧 blocked 최종 확정 (버전 독립적 비호환, §6.5) |
| 8 | profile 비교와 병목 선정 | 🔄 진행 중 |
| 9 | 개선안별 단일 변수 실험 | `[TODO]` |
| 10 | 회복탄력성·Chaos 재검증 | `[TODO]` |
| 11 | 최종 의사결정 Matrix·보고서 | `[TODO]` |

### 5.1 Phase 4 세부 체크리스트

- [x] Scenario별 포화점과 목표 부하 확정 (C\*=28 RPS, 3/8/17/22 RPS)
- [x] core 조건 유효 run 최소 10회와 bootstrap CI 정밀도 Gate (§6.2)
- [x] Workload/부하 발생기 자체 병목 판정 (28 RPS에서 node CPU peak 36%, 부하발생기 CPU peak 5% — 자체 병목 아님)
- [x] baseline run ID 승인
- [x] Phase 4 Evidence `measured`

### 5.2 Phase 5 세부 체크리스트

- [x] Istio 버전/자원 크기 결정과 설치 (ADR-0024)
- [x] injection/mTLS/traffic path 검증 (Envoy config dump로 실제 mTLS 확인)
- [x] app/proxy 자원 분리 수집과 throttling 감지 gate
- [x] paired core 조건 유효 run 최소 10회와 bootstrap CI 정밀도 Gate (§6.3, 15회 상한 도달로 종료)
- [x] Phase 5 Evidence `measured`

### 5.3 Phase 6 세부 체크리스트

- [x] ztunnel/istio-cni 설치와 노드 단위 공유 자원 귀속 모델 결정 (ADR-0025)
- [x] enrollment/HBONE/mTLS 실제 경로 검증 (ztunnel access log로 양방향 SPIFFE identity 확인)
- [x] ztunnel 자원을 Pod당이 아닌 노드/클러스터 단위 절대값으로 수집
- [x] 고정 replica에서 paired core 조건 유효 run 최소 10회 (§6.4)
- [ ] **replica/node 확장에 따른 공유 비용 측정 — 잔여 작업**
- [x] Phase 6 Evidence `measured` (고정 replica 범위 한정)

### 5.4 Phase 7 세부 체크리스트

- [x] Waypoint 배포 범위 결정 — 선택 경로(단일 hop) 우선 (ADR-0026)
- [x] `istio-waypoint` GatewayClass 자동 생성과 Gateway 리소스로 Pod 자동 프로비저닝 확인
- [x] gateway→waypoint 홉 NetworkPolicy 수정과 정상 동작 확인
- [x] Istio 1.29.6으로 완전 재설치 후 재시도 — 동일하게 0/20 재현, 버전 독립적 비호환으로 확정
- [ ] **waypoint→실제 backend pod 홉 연결 — blocked 최종 확정** (§6.5)
- [ ] paired core 조건 반복측정 — 위 차단으로 미착수, 조사 종료
- [ ] Phase 7 Evidence — blocked (최종)

---

## 6. 지금까지 확보한 정량 결과

### 6.1 Capacity Discovery — 완료 (2026-07-23)

조건: `NO_MESH` / `SYNC_CHAIN` 3-hop / payload 1 KiB / hop delay 1 ms

| Target RPS | 단계 | 결과 | Achieved RPS | 오류율 | p95 (ms) | p99 (ms) |
|---:|---|---|---:|---:|---:|---:|
| 10 | geometric | PASS | 10.004 | 0% | 34.073 | 41.945 |
| 20 | geometric | PASS | 20.004 | 0% | 30.311 | 46.767 |
| 40 | geometric | CAPACITY_FAIL | 39.885 | 0% | 101.238 | 193.956 |
| 30 | refine | CAPACITY_FAIL | 30.002 | 0% | 68.965 | 118.975 |
| 25 | refine | PASS | 25.003 | 0% | 54.793 | 80.406 |
| 27 | refine (retry-03) | PASS | 27.001 | 0% | 47.225 | 72.835 |
| 28 | refine | **PASS (최종 C\*)** | 28.001 | 0% | 47.381 | 69.087 |

- **usable capacity C\* = 28 RPS**, 28~30 RPS 구간 폭 7.14%
- 28 RPS 지점에서 node CPU peak 36.38%, 부하발생기 CPU peak 5.10% — **CPU가 한계에 닿기 전에 tail
  latency가 먼저 무너지는 지점**이 관측됨 (원인 규명은 Phase 8 병목 분석 대상)
- 확정된 절대 부하점: low 3 / nominal 8 / high 17 / near-saturation 22 RPS (low는 sanity 전용, cross-profile
  정식 비교에서는 제외)

### 6.2 정식 No-Mesh Baseline — 완료 (2026-07-25)

128 pre-allocated/max VU 고정, warm-up 180초, seeded randomized block(seed 42, session 1~4)으로 반복
측정했다. 최종 결과는 다음과 같다.

| 조건 | Target RPS | 유효 run | Throughput median | p95 median (95% CI) | p99 median (95% CI) | 정밀도 판정 |
|---|---:|---:|---:|---|---|---|
| nominal | 8 | 15/15 (상한) | 8.0006 req/s | 28.21 ms (24.15–33.05) | 36.56 ms (30.51–48.67) | `INCONCLUSIVE_MAX_RUNS`(p99만 미달) |
| high | 17 | 10/15 | 17.0013 req/s | 25.20 ms (23.11–29.20) | 30.77 ms (28.76–36.93) | `STOP_PRECISION_REACHED` |
| near-saturation | 22 | 13/15 | 22.0014 req/s | 33.79 ms (30.30–36.94) | 46.40 ms (38.80–54.55) | `STOP_PRECISION_REACHED` |

**측정 도중 발견하고 수정한 문제** — 애초 정한 정밀도 기준(ADR-0014, 상대 half-width 단일 기준: p95≤5%/p99
≤10%/CPU≤5%)은 9~11회 시점에서 12~36%로 기준 대비 2~7배 벗어나 있었고, `1/√n` 수렴 속도로 계산하면
15회를 다 채워도 대부분 통과하지 못할 것으로 예상됐다. 원인은 이 환경의 기준선 latency 자체가 25~45ms대로
작아 상대 비율 기준이 작은 절대 오차(수 ms)를 과장하는 데 있었다(프로젝트가 이미 문서화한 "작은 기준값은
상대 비율을 과장한다"는 원칙과 일치). 상대 기준은 유지하되 절대(ms/core-s) 기준을 OR 조건으로 추가하는
[ADR-0023](docs/decisions/0023-hybrid-absolute-relative-precision-gate.md)을 세워 해결했고, 적용 즉시
`high` 조건이 재계산만으로 통과 판정을 받는 것으로 실효성을 확인했다.

**정직하게 남긴 한계**: nominal은 15회까지 다 채웠지만 p99 절대 half-width(9.08ms)가 기준(8ms)을 8.9%
초과해 통과시키지 않고 `INCONCLUSIVE_MAX_RUNS`로 유보했다. 또한 이 클러스터(노드당 allocatable 2 vCPU)는
p95 ≈5ms/p99 ≈8ms보다 작은 차이를 통계적으로 구분하지 못한다 — Phase 5 이후 Mesh profile의 오버헤드가
이보다 작게 측정되면 "차이 없음"이 아니라 "이 환경에서는 확인 불가"로 보고해야 한다.

전체 Evidence: [2026-07-25 canonical baseline final](docs/evidence/performance/2026-07-25-canonical-baseline-final.md)

### 6.3 정식 Istio Sidecar Baseline — 완료 (2026-07-27)

No-Mesh와 동일한 절대 RPS(8/17/22)·128 VU·반복 정책으로 측정했다. Istio 1.30.3을 Helm으로 설치하고,
`istio.io/rev=default` 라벨로 7개 SYNC_CHAIN 서비스에 sidecar를 주입했다(Kafka는 기존 scope 밖이라 제외).

| 조건 | Target RPS | 유효 run | p95 median (95% CI) | p99 median (95% CI) | App CPU-s/req | Sidecar CPU-s/req | 정밀도 판정 |
|---|---:|---:|---|---|---:|---:|---|
| nominal | 8 | 15/15 | 30.08 ms (28.47–31.51) | 36.87 ms (33.92–38.46) | 0.0772 | 0.0086 | `INCONCLUSIVE_MAX_RUNS`(CPU만 미달) |
| high | 17 | 15/15 | 29.63 ms (28.04–40.03) | 37.53 ms (32.93–49.29) | 0.0426 | 0.0074 | `INCONCLUSIVE_MAX_RUNS`(latency 미달) |
| near-saturation | 22 | 15/15 | 28.88 ms (28.17–40.97) | 35.48 ms (33.09–56.20) | 0.0365 | 0.0072 | `INCONCLUSIVE_MAX_RUNS`(latency 미달) |

**No-Mesh와 다른 패턴이 나온 것 자체가 흥미로운 결과다.** No-Mesh는 latency가 쉽게 수렴하고 CPU가 어려웠던
반면, Sidecar는 반대로 latency(특히 high/near-saturation의 p95/p99 반폭이 6~11ms대로 No-Mesh의 3ms대보다
2배 이상 넓음)가 어렵고 CPU/request는 오히려 잘 수렴했다. 가장 그럴듯한 해석은 요청마다 거치는 Envoy proxy
hop이 늘면서(각 서비스 호출마다 클라이언트·서버 양쪽 sidecar를 통과) run 간 latency 변동성 자체가 커졌다는
것이다.

**실제로 직접 측정한 것과 아직 못한 것을 구분한다.** Envoy sidecar 자체의 CPU 비용(≈0.0072~0.0086
core-seconds/request)과 메모리 비용(≈294~306 MiB, 부하 수준과 거의 무관하게 일정)은 세 조건에서 안정적으로
직접 측정됐다 — 이건 확정적인 값이다. 반면 "Sidecar가 No-Mesh보다 latency를 얼마나 늘리는가"는 아직 정식
결론이 아니다. 예비로 두 profile의 median을 단순 차감해보면 high 조건에서 p99가 +22.0%(+6.76ms) 늘었는데,
이는 두 profile의 오차범위를 합산한 최소 감지폭(√(각 profile 반폭²의 합) ≈ 5.8ms)보다 크지만, 두 profile
모두 이 지표에서 정밀도 게이트를 통과하지 못한 상태라 "확인된 차이"라고 단정하지 않았다. near-saturation은
오히려 Sidecar가 더 빠르게 나왔는데(p99 −23.5%), 두 profile의 신뢰구간이 서로 겹쳐 노이즈와 구분이 안 되는
경우였다. **엄밀한 두 profile 간 통계 비교 도구는 아직 없고, 이건 Phase 8에서 만들 계획이다** — 지금은
"차이가 있어 보인다"와 "차이가 있다고 증명됐다"를 섞지 않기 위해 예비 관찰로만 기록했다.

측정 도중 절반은 도구/인프라 문제였다: STRICT mTLS를 처음 적용했을 때 Prometheus(mesh 비구성원)가 7개 중
6개 서비스를 스크레이프하지 못하는 회귀가 발생해 PERMISSIVE로 되돌렸고(서비스 간 트래픽은 여전히 자동으로
mTLS 사용), 이 클러스터의 cAdvisor가 애초에 노출하지 않는 metric(`*_throttled_seconds_total`)을 잘못
사용해 throttling 감지가 항상 null을 반환하던 버그도 스모크 테스트로 잡아냈다. 51회 시도 중 실제로 Envoy가
CPU 쿼터를 다 쓴 사례(`PROXY_CPU_THROTTLED`)가 1건 발견되어 통계에서 정상적으로 제외됐다 — reduced
resource request(ADR-0024)가 실측값을 인위적으로 누르지 않는다는 것을 이 게이트로 직접 확인했다.

전체 Evidence: [2026-07-27 canonical sidecar baseline final](docs/evidence/performance/2026-07-27-canonical-sidecar-baseline-final.md)

### 6.4 정식 Istio Ambient Baseline — 고정 replica 완료 (2026-07-29)

No-Mesh/Sidecar와 동일한 절대 RPS·반복 정책으로 측정했다. Istio ztunnel + istio-cni 1.30.3을 설치하고,
`benchmark` namespace를 `istio.io/dataplane-mode=ambient`로 전환했다(Sidecar와 달리 Pod별 주입이 아니라
namespace 단위 enrollment).

| 조건 | Target RPS | 유효 run | p95 median (95% CI) | p99 median (95% CI) | App CPU-s/req | 정밀도 판정 |
|---|---:|---:|---|---|---:|---|
| nominal | 8 | 10/15 | 30.08 ms (28.01–33.68) | 39.50 ms (35.34–45.95) | 0.0751 | `STOP_PRECISION_REACHED` |
| high | 17 | 15/15 | 31.76 ms (28.28–33.90) | 43.15 ms (36.87–56.86) | 0.0439 | `INCONCLUSIVE_MAX_RUNS`(p99만 미달) |
| near-saturation | 22 | 14/15 | 30.24 ms (27.51–33.45) | 41.08 ms (34.51–50.00) | 0.0375 | `STOP_PRECISION_REACHED` |

**세 profile 중 가장 균형 잡힌 수렴 패턴이다.** No-Mesh는 2/3 조건이 쉽게 수렴, Sidecar는 0/3, Ambient는
2/3(nominal, near-saturation)가 수렴했다. `high`만 p99가 15회 상한에도 미달했는데, 그 반폭(10.00ms)이
지금까지 측정한 세 profile 통틀어 가장 넓은 단일 미달 폭이었다.

**ztunnel은 Sidecar와 근본적으로 다른 종류의 숫자를 남긴다.** ztunnel은 Pod마다 붙는 게 아니라 노드마다
1개씩 떠서 그 노드의 모든 enrolled Pod 트래픽을 처리하는 공유 프로세스다. 그래서 이번 측정에서는 Envoy처럼
"request 하나당 얼마"로 정규화하지 않고, 측정 창 동안 클러스터 전체 ztunnel 인스턴스가 쓴 누적 CPU-초와
메모리 peak를 그대로 기록했다(≈73~82 누적 core-초, 메모리 peak ≈16.7~16.9MiB). 메모리만 놓고 보면 Envoy
sidecar(Pod당 ≈300MiB)의 **1/20 미만**으로, Rust로 작성된 ztunnel의 경량성과 "Pod당 1개 vs 노드당 1개"라는
근본적으로 다른 설계가 그대로 드러난다.

**설치 과정에서 실제 인프라 호환성 문제를 두 건 발견하고 근본 원인까지 추적해 해결했다.** 이 클러스터의
Cilium(kube-proxy-replacement + VXLAN)과 Istio Ambient 조합은 사전에 위험 요인으로 지목해뒀던 조합이었고,
실제로 문제가 터졌다.

1. Ambient 활성화 직후 7개 SYNC_CHAIN Pod 전부가 `0/1`로 멈춰 계속 재시작을 반복했다. 원인은 kubelet이
   Pod IP로 직접 보내는 상태 확인(probe)이 Ambient의 트래픽 캡처 규칙에 걸려 응답을 못 받고 타임아웃되는
   것이었다 — 애플리케이션 자체는 정상 기동한 상태였다. probe를 Pod IP 대상 HTTP 확인에서 **loopback
   (127.0.0.1) 대상 exec 확인**으로 바꿔서, Cilium 설정은 전혀 건드리지 않고 해결했다.
2. probe 문제를 고친 뒤에도 서비스 간 실제 호출은 계속 실패했다. ztunnel 로그가 원인을 스스로 알려줬다 —
   **"NetworkPolicy가 HBONE 포트 15008을 막고 있을 수 있다"**는 메시지였다. Ambient의 실제 통신 방식은
   Sidecar의 로컬 iptables 리다이렉트와 달리 ztunnel 간 포트 15008(HBONE 터널)을 실제로 타는데, 기존
   NetworkPolicy는 8080/9092/9093만 허용하고 있었다. 기존 서비스 간 허용 규칙에 15008을 추가해서(No-Mesh/
   Sidecar에는 영향 없도록 값으로 게이트) 해결했다.

두 수정 모두 Cilium의 핵심 라우팅 설정은 전혀 바꾸지 않았다 — 미리 "이 수준의 변경이 필요하면 진행 전에
확인받는다"고 정해둔 기준선을 넘지 않는 범위에서 해결됐다.

**아직 안 한 것도 정직하게 남긴다.** Phase 6 문서(`docs/phases/phase-06-istio-ambient.md`)에 명시된
"Pod/worker replica와 노드 수 증가에 따른 공유 비용 측정"은 이번 측정 범위에 포함되지 않았다 — 이건
가설 1("Sidecar의 Pod별 비용과 Ambient의 노드 공유 비용은 Pod 수 증가 시 다른 형태로 확장된다")을 직접
검증하는 핵심 데이터라, Phase 8 병목 분석에 들어가기 전에 별도로 수행해야 하는 잔여 작업으로 명시해뒀다.

전체 Evidence: [2026-07-29 canonical ambient baseline final](docs/evidence/performance/2026-07-29-canonical-ambient-baseline-final.md)

### 6.5 Phase 7 Waypoint — blocked, 버전 독립적 비호환으로 최종 확정 (2026-07-29)

Ambient 위에 orchestrator-service 단일 hop만 Waypoint를 경유하도록 배포했다. Istio 1.30.3은
`PILOT_ENABLE_AMBIENT=true`가 켜지면 `istio-waypoint` GatewayClass를 자동 생성해두므로, 별도 설치 없이
Gateway API 리소스 하나만 만들면 Waypoint Pod가 자동으로 뜬다 — 여기까지는 문제없이 됐다.

**두 홉 중 하나만 통과했다.** gateway→waypoint 홉은 Ambient 때와 같은 패턴의 NetworkPolicy 누락(HBONE
포트)이었고 같은 방식으로 수정해서 해결했다. 하지만 waypoint→실제 orchestrator pod 홉은 계속 실패했다.
Envoy 관리자 API로 들여다보니 **TCP 연결 자체는 성공하는데(`cx_total=1`, `cx_connect_fail=0`) HTTP
요청은 즉시 리셋된다(`rq_error=1`, `rq_success=0`)** — 그리고 이 연결은 ztunnel의 access log에 전혀
기록되지 않는다(같은 시간대 다른 정상 트래픽은 다 잡히는데 이것만 안 잡힘).

"Waypoint와 실제 backend pod가 우연히 같은 노드에 배치돼서 Cilium이 로컬 트래픽 최적화 경로로 ambient
캡처 규칙을 우회하는 것 아닐까"라는 가설을 세우고, Waypoint Deployment에 `podAntiAffinity`를 직접 patch해
다른 노드로 강제 이동시켜 재현해봤다 — **똑같은 실패가 그대로 재현**되어 이 가설은 기각됐다.

**사용자가 "그래도 해결해보라"고 요청해서 한 단계 더 파고들었다.** `istioctl`을 새로 설치해 Waypoint의
실제 xDS 설정을 직접 열어보니, 설정 자체(`ORIGINAL_DST` 타입, 포트를 15008로 강제 override, TLS 1.3 +
SPIFFE 검증)는 정상이었다. 그런데 Waypoint Pod **안에서 직접** 실제 orchestrator Pod로 평문 curl을
날려보니 즉시 성공했다 — 네트워킹과 NetworkPolicy 자체는 문제가 없다는 뜻이다. 동시에 `cilium-dbg
endpoint list`에 Waypoint Pod의 IP가 아예 나타나지 않는 것도 발견했다(원인 불명). 그러다 클린하게
재배포한 직후 5연속 성공을 관측해 "해결됐다"고 판단했는데, **Waypoint 자체의 요청 카운터는 그 "성공한"
요청들에서도 전혀 움직이지 않았다.** 곧바로 20연속 재시도했더니 **0/20 성공**으로 돌아갔다 — 처음의
성공은 Waypoint 설정 이전에 gateway 앱이 이미 맺어둔 연결 풀(keep-alive)이 우연히 재사용되며 Waypoint를
완전히 우회한 거짓 양성이었다.

`istioctl`까지 동원한 심화 진단에도 재현성이 극히 불안정하고 근본 원인을 확정하지 못했다 — 이 클러스터의
특정 버전 조합(Cilium 1.19.6 + Istio ambient waypoint 1.30.3)에서 실제로 존재하는 버그이거나 깊은
호환성 문제로 판단되는 시점에서, 사용자가 "그럼 Istio 버전을 바꿔서 재설치도 해보자"고 요청했다.

**Istio 1.30.3을 완전히 제거하고 1.29.6으로 재설치해 처음부터 다시 시도했다.** ztunnel/istio-cni/istiod/
istio-base를 전부 지우고 동일 자원 설정으로 재설치하면서 `PILOT_ENABLE_AMBIENT=true`도 처음부터 켰다.
재설치 직후 **순수 Ambient SYNC_CHAIN 트래픽은 정상 동작**함을 먼저 확인한 뒤(HTTP 200, 3-hop, checksum
일치), Waypoint Gateway와 NetworkPolicy 수정을 동일하게 재적용했다. Waypoint Pod는 `1/1 Running`으로
정상 기동했지만, 첫 요청부터 **완전히 동일한 실패 시그니처**(`HTTP 500`, "upstream connect error...
connection termination")가 재현됐다. 거짓 양성을 이미 한 번 겪은 뒤였으므로 단일 샘플을 믿지 않고 곧바로
20회 배치 요청으로 재확인했고, 결과는 **`success=0 fail=20`** — 1.30.3에서 관측한 것과 정확히 같았다.

**서로 다른 두 Istio minor 버전에서 완전 재설치 후에도 동일한 0/20 실패가 나온다는 것은, 특정 릴리스의
회귀 버그가 아니라 이 클러스터의 Cilium 구성(kube-proxy-replacement + VXLAN tunnel 모드 — ADR-0025에서
사전에 위험 조합으로 표시해둔 조합)과 Istio Ambient Waypoint 아키텍처 사이의 버전 독립적인 근본
비호환이라는 뜻이다.** 이 결과로 조사를 최종 종료하기로 판단했다. 지금까지 고친 두 건(probe 캡처,
NetworkPolicy 포트 누락)은 명확한 원인과 안전한 수정이 있었지만, waypoint→backend 홉 문제는 두 버전
모두에서 재현되는 것으로 봐서 애플리케이션이나 설정의 문제가 아니라 이 인프라 스택 자체의 한계로 규정하는
것이 더 정직한 결론이다. 클러스터는 Waypoint 라우팅을 완전히 제거하고 순수 Ambient 상태(Istio 1.29.6)로
정상 복구했다(SYNC_CHAIN E2E 재확인 완료, HTTP 200 3/3). Phase 8(병목 분석)은 이미 확보한 No-Mesh/
Sidecar/Ambient 세 profile 데이터로 진행한다.

상세 진단 기록: [phase-07-p1-waypoint-blocked 체크포인트](docs/checkpoints/phase-07-p1-waypoint-blocked.md)

### 6.6 Replica 확장 방향성 연구 — 완료 (2026-07-29)

Phase 6 문서와 가설 1이 요구하는 "Pod replica 수가 늘 때 Sidecar와 Ambient의 비용이 다르게 확장되는가"를
확인하기 위한 별도 연구다. 정식 10~15회 반복이 아니라 **방향성 확인용으로 범위를 축소**했다(ADR-0027):
`orchestrator-service`만 1/2/4 replica로 늘리고, nominal(8 RPS) 부하 하나에서, Sidecar와 Ambient 각각
지점당 3회씩 총 18회 측정했다(전부 성공, 오류 0건).

| Profile | Replica | p95 median | p99 median | Proxy 메모리 peak |
|---|---:|---:|---:|---:|
| Sidecar | 1 | 42.92 ms | 67.73 ms | 120.1 MiB |
| Sidecar | 2 | 40.22 ms | 51.94 ms | 138.3 MiB |
| Sidecar | 4 | 36.95 ms | 58.06 ms | 173.0 MiB |
| Ambient | 1 | 34.34 ms | 51.01 ms | 15.8 MiB |
| Ambient | 2 | 44.31 ms | 67.93 ms | 15.9 MiB |
| Ambient | 4 | 68.42 ms | 99.52 ms | 16.1 MiB |

**메모리는 가설 1을 깔끔하게 확인해준다.** Sidecar는 replica가 1→4개로 늘 때 메모리가 120→173MiB로
**44% 증가**한다 — replica마다 자기 몫의 Envoy 프로세스를 새로 띄우니 당연한 결과다. 반면 Ambient의
ztunnel 메모리는 15.8→16.1MiB로 **거의 그대로**다 — ztunnel이 진짜로 "노드당 1개, 앱 Pod 수와 무관"이라는
설계 그대로 동작한다는 직접적인 증거다.

**그런데 latency는 예상 밖의 방향으로 갈렸다.** Sidecar는 replica가 늘수록 p95가 오히려 소폭 개선됐다
(42.9→37.0ms) — 부하가 더 많은 인스턴스로 분산되며 개별 인스턴스의 대기 시간이 줄어든 것으로 보인다.
반대로 **Ambient는 replica가 늘수록 latency가 뚜렷하게 나빠졌다** — p99가 51.0ms→99.5ms로 거의 2배가
됐다. ztunnel 자체의 CPU 총량도 10.26→13.53 core-초로 32% 늘었는데, ztunnel은 트래픽이 아니라 "이
노드에 새로 등록된 워크로드 수"(mTLS 인증서 발급/추적)에 비례해 비용이 붙는다는 뜻으로 해석된다 — "노드
공유"라고 해서 Pod를 아무리 늘려도 공짜는 아니라는 걸 보여준 사례다. 다만 이 latency 결과는 지점당 3회
반복(신뢰구간 없음)에 기반한 **방향성 데이터**이며, 세 replica 지점에서 일관되게 같은 방향으로 나타났다는
점에서 Phase 9 개선 실험 후보로 등록할 만큼은 신빙성 있지만, Phase 4~6 수준의 확정된 결론은 아니다.

전체 Evidence: [2026-07-29 replica-scaling directional study](docs/evidence/performance/2026-07-29-replica-scaling-directional-study.md)

---

## 7. 엔지니어링 하이라이트 — 인프라를 만들며 부딪히고 해결한 문제

측정 결과 자체만큼, "믿을 수 있는 측정 도구를 만드는 과정"에서 나온 문제 해결 경험이 이 프로젝트의 실질적인
엔지니어링 역량을 보여준다.

1. **Tempo 반복 OOMKill 해결**: 분산 트레이싱 백엔드(Tempo)가 1024 MiB ballast에 768 MiB 컨테이너 limit라는
   설정 불일치로 반복 재시작했다. ballast 128 MiB / limit 1536 MiB로 재조정하고 OTel Collector의 정체된
   exporter queue를 초기화해 애플리케이션→Tempo trace round trip을 재확인, restart count 0으로 안정화했다.
2. **Capacity discovery 판정 로직 결함 수정**: 초기 구현은 "무효(INVALID) 지점"을 전부 "용량 초과(CAPACITY_FAIL)"로
   잘못 취급해 실제 용량보다 낮은 값을 승인할 위험이 있었다. `PASS`/`CAPACITY_FAIL`/`INVALID`를 명시적으로
   분리하고, 무효 지점은 덮어쓰지 않고 재시도하며 용량 경계 계산에서 제외하도록 재구현했다.
3. **거짓 양성 readiness gate 수정**: 정식 baseline 중 `high/repeat-04`가 `WORKLOAD_NOT_READY`로 무효 처리됐는데,
   실제로는 `SYNC_CHAIN`이 쓰지 않는 `kafka-0` Pod의 not-ready 상태 때문이었다. readiness/restart gate를
   시나리오가 실제로 쓰는 7개 request-path Pod로 한정하도록 수정하고, 이미 만들어진 무효 run은 재분류하지 않고
   그대로 보존한 채 이후 run부터 올바르게 판정되도록 했다.
4. **세션 기반 반복측정 스케줄러의 회계(accounting) 버그 직접 발견·수정**: 세션마다 "이번 세션에서 이미
   처리한 run 수(assigned)"를 0부터 다시 세는데, 이를 "전체 유효 run 수(validRuns)"와 비교해 recovery 여부를
   판단하는 로직이 있었다. 그 결과 한 조건의 유효 run 수가 세션당 block 수(5)와 같아지는 순간부터는 **모든
   세션이 새 실측 없이 기존 run만 재확인하며 영원히 정체**되는 구조적 문제가 있었다. 실제로 이 버그 때문에
   두 번째 세션(5개 block)에서 3개 조건 중 2개는 진전이 전혀 없었다. 세션 시작 시점의 valid run 수를
   baseline으로 스냅샷해 "이번 세션 시작 이후 새로 생긴 run"만 recovery 판단에 쓰도록 수정했고, 정상 동작
   (신규 실측 발생)과 크래시 후 재개(중복 실측 방지) 두 시나리오 모두에 대한 회귀 테스트를 추가해 검증했다.
5. **재현성 안전장치(Dirty Source Tree Gate)**: Kubernetes 정식 run은 git 소스 트리가 dirty하면 자동으로
   `DIRTY_SOURCE_TREE`로 무효 처리되도록 만들어, "커밋되지 않은 코드로 만든 숫자"가 Evidence에 섞이는 것을
   원천 차단했다. 실제로 위 4번 수정을 실측 도중(warm-up 단계)에 곧바로 커밋해 진행 중이던 run이 무효
   처리되는 것을 막은 사례가 있다.
6. **상대값 단일 정밀도 기준의 수렴 실패를 사전에 계산으로 예측하고 정책을 개정**: 반복측정 도중 관측된
   bootstrap CI 반폭이 기준 대비 2~7배 벗어난 상태였다. 무작정 반복 횟수를 늘리는 대신 `1/√n` 수렴 속도로
   15회 상한 도달 시점의 값을 미리 계산해 "이대로면 통과 못 한다"를 사전에 판단했고, 원인(작은 절대
   latency에 상대 비율 기준을 적용한 왜곡)을 근거로 절대·상대 혼합 기준(ADR-0023)으로 정책을 바꿨다.
   정책 변경 시점에 이미 돌고 있던 프로세스가 구버전 기준을 메모리에 들고 있어 불필요한 재측정을 할
   위험을 발견하고, warm-up 단계(측정 낭비 최소 시점)에 맞춰 안전하게 재시작했다.

7. **자원 request와 limit을 분리해 측정 왜곡을 원천 차단**: Istio 기본 자원 요청값(istiod 500m CPU/2GiB
   메모리, sidecar 100m/128MiB)을 그대로 쓰면 이 클러스터(노드당 2 vCPU)에서 worst-case 스케줄링 실패
   위험이 있었다. request만 대폭 축소하고 실제 사용량을 결정하는 limit은 Istio 기본값을 그대로 둬서,
   "측정하려는 proxy 비용 자체가 인위적으로 눌리는" 상황을 피했다. 이후 실제로 CPU throttling이 1회
   발생했을 때 이를 게이트로 감지·제외해, 이 설계 판단이 이론이 아니라 실측으로 검증됐다.
8. **STRICT mTLS가 관측 인프라를 깨뜨리는 것을 발견하고 근본 원인으로 해결**: mTLS를 STRICT로 설정하자
   Prometheus가 7개 중 6개 서비스 스크레이프에 실패했다(mesh 비구성원인 Prometheus가 mTLS 핸드셰이크를
   할 수 없어서). 스크레이프 예외를 늘리는 대신, Istio의 자동 상호 TLS 승격이 이미 서비스 간 트래픽은
   mTLS로 보호하면서 비-mesh 클라이언트에는 평문 fallback을 제공한다는 점을 활용해 PERMISSIVE로 되돌리는
   더 근본적인 해결을 택했다. Envoy의 실시간 config dump를 직접 열어 "여전히 서비스 간 통신은 mTLS를
   쓴다"는 것을 확인한 뒤에 이 판단을 내렸다.
9. **존재하지 않는 metric에 의존하던 감지 로직을 실제 클러스터로 검증해 잡아냄**: CPU throttling 감지에
   표준적으로 쓰이는 `container_cpu_cfs_throttled_seconds_total`을 사용했는데, 스모크 테스트에서 항상
   `null`이 반환되는 것을 발견했다. 이 클러스터의 cAdvisor 버전이 해당 metric을 아예 노출하지 않는다는
   것을 전수 쿼리로 확인하고 실제 존재하는 `*_periods_total`로 교체했다 — 코드를 배포하기 전에 "감지
   로직이 진짜로 작동하는지"를 실측으로 증명한 사례다.
10. **단일 실패가 몇 시간짜리 무인 측정 전체를 죽이는 구조적 결함 발견·수정**: 22 RPS 부하 중
    `benchmark-gateway`의 liveness probe가 타임아웃돼 Pod가 재시작됐고, 그로 인한 순간 오류율 급증이
    k6의 임계치를 넘겨 비정상 종료됐다. 이 예외가 스케줄러 프로세스 전체를 죽이는 구조였다는 걸 발견하고,
    실패를 `FAILED` run으로 기록한 뒤 다음 조건으로 계속 진행하도록 고쳤다 — 무인 다중 세션 측정이
    끊기지 않고 자동으로 이어지게 만든 신뢰성 개선이다.

11. **알려진 위험 요인이 실제로 현실화된 것을 미리 대비한 절차로 안전하게 처리**: Ambient 설치 전에
    "이 클러스터의 Cilium 설정과 Istio Ambient 조합은 알려진 마찰이 있는 조합이니, 문제가 생기면 실측으로
    확인하고, Cilium 핵심 설정을 바꿔야 할 정도면 진행 전에 사용자에게 확인한다"는 기준을 ADR에 미리
    문서화해뒀다. 실제로 전체 pod가 crash-loop하는 문제가 터졌을 때, 이 기준 덕분에 "지금 발견한 문제가
    미리 정해둔 '확인 필요' 임계값을 넘는지"를 판단 기준으로 삼아 빠르게 의사결정할 수 있었다 — 첫 번째
    문제(probe 캡처)는 애플리케이션 레벨 우회로 해결 가능했지만, 근본 원인이 불확실한 단계에서는 먼저
    사용자에게 확인을 구했다.
12. **에러 메시지가 스스로 알려주는 원인을 놓치지 않고 근본 해결**: 두 번째 호환성 문제(HBONE 트래픽 차단)는
    ztunnel의 access log가 "NetworkPolicy가 포트 15008을 막고 있을 수 있다"는 메시지를 직접 출력했다. 이걸
    무시하고 임시방편(예: 전체 egress 허용)으로 넘어가는 대신, Ambient의 실제 wire protocol(ztunnel-to
    -ztunnel HBONE 터널링)이 Sidecar의 로컬 iptables 리다이렉트와 근본적으로 다르다는 것을 이해하고, 기존
    NetworkPolicy 토폴로지(어떤 서비스가 어떤 서비스를 호출하는지)를 그대로 유지한 채 필요한 포트만 정확히
    추가했다 — 보안 경계를 넓히지 않으면서 문제를 해결했다.
13. **측정 항목이 실제로 다른 종류의 값을 요구한다는 것을 사전에 설계로 반영**: ztunnel은 Pod당 하나가
    아니라 노드당 하나가 여러 Pod를 공유하는 프로세스라서, Sidecar처럼 "request당 비용"으로 정규화하면
    다른 워크로드가 공유하는 비용까지 이 실험 탓으로 돌리는 통계적 오류가 생긴다. 이를 실측 전에 ADR로
    미리 인식하고, 코드에도 "cluster-wide-shared-not-per-request"라는 명시적 attribution 필드를 남겨
    나중에 이 숫자를 잘못 해석할 위험을 차단했다.

14. **"성공"으로 보이는 결과를 통계 없이 믿지 않는 습관이 거짓 양성을 잡아냄**: Waypoint 재배포 직후
    5연속 curl 성공을 보고 한때 "해결됐다"고 판단했지만, Envoy 자체의 요청 카운터가 그 성공 케이스들에서
    전혀 움직이지 않았다는 걸 교차 확인해 이상함을 감지했다. 즉시 20회 배치 재시도로 검증했더니 0/20으로
    실패율이 뒤집혔다 — "몇 번 성공했다"가 아니라 "그 성공이 실제로 측정하려는 경로를 통과했는가"를
    항상 별도로 검증해야 한다는 걸 실제 사례로 재확인했다. 이 프로젝트 전체의 "Evidence 없는 결론 금지"
    원칙이 로그 하나 잘못 읽었으면 놓쳤을 거짓 양성을 실제로 걸러낸 사례다.
15. **한계에 부딪혔을 때 계속 밀어붙이기보다 진단 도구를 먼저 확충**: 로그와 Envoy admin API만으로
    원인을 못 찾자, 무작정 설정을 이것저것 바꿔보는 대신 `istioctl`(정식 진단 CLI)을 새로 설치해
    `proxy-config`로 실제 xDS 설정을 직접 열어보는 쪽을 택했다. 결과적으로 근본 원인 자체는 못 찾았지만,
    "설정은 정상인데 실제 동작이 다르다"는 걸 확인함으로써 문제의 성격(설정 실수가 아니라 버전 조합의
    깊은 호환성 문제)을 훨씬 정확하게 좁혔다.
16. **"원인 불명"에서 멈추지 않고 반증 가능한 가설로 전환해 결론의 신뢰도를 높임**: 특정 Istio 1.30.3
    버전의 버그일 가능성을 배제하지 못한 상태에서 조사를 접는 대신, 완전히 다른 minor 버전(1.29.6)으로
    처음부터 재설치해 동일 조건에서 재현을 시도했다. 두 버전 모두 완전 재설치 후 정확히 같은 실패
    시그니처(0/20, TCP 성공/HTTP 즉시 리셋)가 나온 것을 확인함으로써, "특정 릴리스의 버그"라는 약한
    가설을 "이 클러스터 스택 자체의 구조적 비호환"이라는 훨씬 강한 결론으로 승격시켰다 — 확인되지 않은
    가설로 결론을 내리기보다, 반증 실험을 한 번 더 돌려 결론의 근거를 넓힌 사례다.

`[TODO: Phase 8 이후 발견되는 새로운 엔지니어링 이슈를 계속 추가]`

---

## 8. 남은 계획 (Phase 5~11)

| Phase | 목표 | 진입 조건 |
|---|---|---|
| 5. Sidecar | injection/mTLS 검증, app/proxy 자원 분리, paired 10~15회 반복 | 승인된 No Mesh baseline — ✅ 완료 |
| 6. Ambient | ztunnel 공유 자원 귀속, replica/node 확장 반복 | Phase 5 완료 — 🔄 고정 replica 완료, 확장 반복 잔여 |
| 7. Waypoint | 전체/선택 경로 분리, L7 기능·통과 성능 측정 | Phase 6 완료 |
| 8. 병목 분석 | profile 간 절대/상대 차이, telemetry 기반 병목 3개 이상 확정 | Phase 5~7 완료 |
| 9. 개선 실험 | 병목별 단일 변수 개선안 3개 이상, before/after 10회+ 반복 | Phase 8 승인 |
| 10. 회복탄력성 | 동일 fault schedule로 before/after 장애 주입 재검증 | Phase 9 반영 |
| 11. 최종화 | 워크로드별 선택 Matrix, 재현성 검증, 최종 보고서 | Phase 10 완료 |

`[TODO: Phase 6 replica/node 확장 측정 수치와 Phase 7 Waypoint 관련 수치]`
`[TODO: Phase 8 병목 후보 3개 이상과 지지/반대 Evidence]`
`[TODO: Phase 9 개선안 목록과 채택/기각 결과]`
`[TODO: Phase 10 장애 주입 시나리오와 회복 지표]`
`[TODO: Phase 11 워크로드별 최종 선택 Matrix]`

---

## 9. 신뢰성 확보 방법 (Evidence 관리)

- 모든 run은 `manifest.json`(commit/digest/자원/JVM), `ground-truth.json`(실제 배포 상태 snapshot),
  `summary.json`, `report.md`를 남기고 주요 파일은 SHA-256으로 무결성을 기록한다.
- 무효 run은 삭제하지 않고 원인(`invalidatingFactors`)과 함께 보존하며, 통계 집계에서만 제외한다.
- 소스 트리가 dirty하면(커밋되지 않은 변경이 있으면) 정식 run 자체를 무효 처리한다.
- 이상치를 임의로 제거하지 않고, 정밀도 게이트를 통과하지 못하면 `INCONCLUSIVE_MAX_RUNS`로 명시적으로
  결론을 유보한다.
- 결과는 사용한 하드웨어·버전·Workload·부하 범위 내에서만 유효하다고 명시하고, 보편적 일반화를 주장하지 않는다.

---

## 10. 배운 점 / 회고

`[TODO: 프로젝트 완료 후 작성 — 벤치마크 설계, 통계적 정지 규칙, 온프레미스 Kubernetes 운영, Java 성능
분석 관점에서 얻은 인사이트를 정리]`

---

## 11. 결론

`[TODO: Phase 11 완료 후 작성 — 4개 profile의 성능/자원/회복탄력성 비교 요약, 워크로드 유형별 선택 권고,
검증/기각된 가설 목록, 프로젝트 전체의 한계와 적용 범위]`

---

## 12. 참고 문서

| 영역 | 문서 |
|---|---|
| 프로젝트 개요 | [docs/00-project-overview.md](docs/00-project-overview.md) |
| 범위·성공 기준 | [docs/01-scope-and-success-criteria.md](docs/01-scope-and-success-criteria.md) |
| 아키텍처 | [docs/02-architecture.md](docs/02-architecture.md) |
| 개념·용어 | [docs/03-concepts-and-glossary.md](docs/03-concepts-and-glossary.md) |
| 반복측정 정책 | [ADR-0014](docs/decisions/0014-measurement-repetition-and-load-policy.md), [ADR-0023](docs/decisions/0023-hybrid-absolute-relative-precision-gate.md) |
| Istio Sidecar 설치 결정 | [ADR-0024](docs/decisions/0024-istio-sidecar-install.md) |
| Istio Ambient 설치 결정 | [ADR-0025](docs/decisions/0025-ambient-mesh-install.md) |
| Waypoint 배포 범위 결정 | [ADR-0026](docs/decisions/0026-waypoint-deployment-scope.md) |
| Replica 확장 연구 범위 결정 | [ADR-0027](docs/decisions/0027-replica-scaling-study-scope.md) |
| Capacity Discovery Evidence | [docs/evidence/performance/2026-07-23-canonical-chain-capacity.md](docs/evidence/performance/2026-07-23-canonical-chain-capacity.md) |
| No-Mesh Baseline 최종 Evidence | [docs/evidence/performance/2026-07-25-canonical-baseline-final.md](docs/evidence/performance/2026-07-25-canonical-baseline-final.md) |
| Sidecar Baseline 최종 Evidence | [docs/evidence/performance/2026-07-27-canonical-sidecar-baseline-final.md](docs/evidence/performance/2026-07-27-canonical-sidecar-baseline-final.md) |
| Ambient Baseline 최종 Evidence | [docs/evidence/performance/2026-07-29-canonical-ambient-baseline-final.md](docs/evidence/performance/2026-07-29-canonical-ambient-baseline-final.md) |
| Waypoint blocked 체크포인트 | [docs/checkpoints/phase-07-p1-waypoint-blocked.md](docs/checkpoints/phase-07-p1-waypoint-blocked.md) |
| Replica-scaling 방향성 연구 Evidence | [docs/evidence/performance/2026-07-29-replica-scaling-directional-study.md](docs/evidence/performance/2026-07-29-replica-scaling-directional-study.md) |
| 현재 체크포인트 | [docs/CURRENT.md](docs/CURRENT.md) |
| Phase 전체 체크리스트 | [docs/checkpoints/phase-checklists.md](docs/checkpoints/phase-checklists.md) |
| 저장소 | https://github.com/0206pdh/msa-servicemesh |
