# Mesh Performance Lab — 포트폴리오 요약

> 이 문서는 이력서/포트폴리오용으로 프로젝트를 개요부터 결론까지 한 번에 설명하기 위한 요약본이다.
> 실험 방법론과 세부 근거의 원본은 `docs/` 아래 문서와 ADR을 따른다. 이 문서는 프로젝트가 진행됨에 따라
> 계속 갱신되며, 아직 실행하지 않은 구간은 `[TODO: ...]`로 표시했다.
>
> **마지막 갱신**: 2026-08-03 · **진행 상태**: Phase 0~11 전체 완료(Waypoint 정식 측정, mTLS/replica-scaling
> 개선 실험, pod-kill/chain-delay 회복탄력성 실험, 선택 Matrix와 최종 결론 포함) · **시작일**: 2026-07-22

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

### 가설별 최종 결과 (Phase 4~10 완료 후)

| # | 가설 | 결과 | 근거 |
|---:|---|---|---|
| 1 | Sidecar의 Pod별 비용과 Ambient의 노드 공유 비용은 Pod 수 증가 시 다른 형태로 확장된다 | **확인됨** | 메모리: Sidecar 120→173MiB(+44%, Pod별 선형), Ambient(ztunnel) 15.8→16.1MiB(+2%, 방향성 연구 §6.6)로 확장 형태 자체가 다르다. 단 latency/CPU 축에서는 이야기가 더 복잡하다 — Ambient도 정식 측정(§6.9)에서 replica 확장 시 p99 +20%(유의), ztunnel 메모리도 오히려 +79%로 늘어(방향성 연구와 반대) "Ambient는 replica가 늘어도 비용이 거의 안 붙는다"는 단순한 그림은 아니다 |
| 2 | Waypoint는 L7 기능을 제공하지만 통과 트래픽과 replica에 따라 병목이 될 수 있다 | **부분 확인** | nominal/high 부하에서 세 profile보다 일관되게 느림(§6.5) — "병목이 될 수 있다"는 확인됐다. 다만 near-saturation에서는 차이가 사라져(원인 미규명) 부하 축의 전체 그림은 불완전하고, **replica 축은 아예 측정하지 않았다**(Waypoint는 이 프로젝트에서 항상 replica=1로만 측정) |
| 3 | 앱과 Mesh의 중첩 retry는 장애 중 호출량과 tail latency를 증폭한다 | **미측정** | ADR-0030에서 hop 단위 fault(`armFault` API)를 범위 밖으로 명시적으로 제외했고, 이 앱/Mesh 어느 쪽에도 retry 정책이 구성되어 있지 않다 — retry amplification을 측정할 대상 자체가 없었다. Phase 11 이후 후속 과제 |
| 4 | 전체 time budget과 단일 retry owner는 회복탄력성을 개선한다 | **미측정** | 애플리케이션에 `X-Request-Deadline-Epoch-Ms` 헤더(전체 time budget)는 이미 구현돼 있지만, 이를 "단일 retry owner" 아키텍처와 비교하는 개선 실험은 이번 범위에 포함하지 않았다. 후속 과제 |
| 5 | 선택적 Waypoint와 telemetry sampling은 필요한 기능을 유지하며 비용을 줄일 수 있다 | **부분 확인**(선택적 Waypoint만) | 선택적 경로(단일 hop) Waypoint의 network bytes가 Ambient·Sidecar 사이(+16~18%)로, 전체 Sidecar(+49%)보다 확실히 저렴하다는 것은 확인됐다(§6.5). **telemetry sampling 축은 아예 실험하지 않았다** — trace/metric sampling rate를 바꾼 개선 실험은 이번 범위 밖 |
| 6 | CPU 기반 HPA는 비동기 backlog에 적합하지 않고 queue lag 지표가 회복시간을 줄일 수 있다 | **미측정** | Kafka 비동기 파이프라인은 E2E 스모크만 확인했고 정식 반복측정하지 않았다(Phase 9 범위에서 제외, §6.7 참고). HPA/autoscaling 실험 자체를 이번 프로젝트에서 하지 않았다. 후속 과제 — 게다가 Ambient의 kafka/producer/worker HBONE 연결이 타임아웃되는 알려진 미해결 문제도 있어(§8.4), 이 축을 측정하려면 그 문제부터 해결해야 한다 |

**종합**: 6개 가설 중 1개는 확인, 2개는 부분 확인(제공된 기능의 절반만 검증), 3개는 이번 프로젝트
범위에서 아예 측정하지 않았다 — 이는 실패가 아니라 **범위를 의도적으로 좁힌 결과**다(ADR-0030 등에서
사전에 명시). 미측정 가설 3개는 모두 "장애 전파/복구 메커니즘 자체를 바꾸는 개선"(retry 소유권, HPA
지표 교체)이라는 공통점이 있다 — 이번 프로젝트는 "profile 선택과 설정 조정"까지는 정식으로 답했지만,
"애플리케이션/오케스트레이션 아키텍처를 바꾸는 개선"은 후속 프로젝트의 영역으로 남는다.

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
| 네트워크/Mesh | Cilium 1.19 (CNI+Gateway+Hubble), MetalLB 0.16 L2, Gateway API 1.4, Istio 1.29.6 Sidecar+Ambient+Waypoint(ztunnel/istio-cni) |
| 관측성 | Prometheus, Grafana, Loki, Tempo, OpenTelemetry Collector |
| 부하·검증 | k6 (CONSTANT_ARRIVAL_RATE), Python 측정 자동화(`experiments/`, unittest 기반 회귀 테스트) |
| 배포 | Helm (profile별 values 분리), Docker/GHCR 이미지 배포 |

### 4.1 Mesh Profile 4종

| Profile | 구조 | 상태 |
|---|---|---|
| No Mesh | Client → App A → App B (Cilium만) | ✅ Phase 4 완료 |
| Sidecar | Pod마다 Envoy proxy 동반 (Istio 1.30.3) | ✅ Phase 5 완료 |
| Ambient | Node 공유 ztunnel (L4) | ✅ Phase 6 고정 replica 완료, 확장 측정 잔여 |
| Ambient + Waypoint | 선택적 L7 proxy 추가 | ✅ Phase 7 완료 (§6.5) |

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
| 6 | **Ambient 기준선** — 고정 replica 정식 반복측정 완료, replica 확장은 §6.6/§6.9로 별도 완료 | ✅ 완료 |
| 7 | Ambient + Waypoint 기준선 | ✅ 완료(§6.5) |
| 8 | profile 비교와 병목 선정 | ✅ 완료 (통계 비교 + 시간축 분석 한계 기록, §6.7) |
| 9 | 개선안별 단일 변수 실험 | ✅ 완료 (§6.8~6.9) |
| 10 | 회복탄력성 (pod-kill, chain-wide delay) | ✅ 완료 (§6.10) |
| 11 | 최종 의사결정 Matrix·보고서 | ✅ 완료 (§8.1~8.4, §10, §11) |

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
- [x] Istio 1.29.6으로 완전 재설치 후 재시도 — 당시 "버전 독립적 비호환"으로 판단했으나 이후 오류로 정정
- [x] **waypoint→실제 backend pod 홉 연결 — 2026-07-30 해결** (§6.5, NetworkPolicy 포트 누락이 원인)
- [x] paired core 조건 반복측정 — 2026-08-01 완료 (nominal/high/near-saturation 각 15회)
- [x] Phase 7 Evidence — 완료 (§6.5)

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

### 6.5 Phase 7 Waypoint — 연결 문제 해결 (2026-07-29 ~ 2026-07-30)

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

**한 단계 더 파고들었다.** `istioctl`을 새로 설치해 Waypoint의 실제 xDS 설정을 직접 열어보니, 설정
자체(`ORIGINAL_DST` 타입, 포트를 15008로 강제 override, TLS 1.3 + SPIFFE 검증)는 정상이었다. 그런데
Waypoint Pod **안에서 직접** 실제 orchestrator Pod로 평문 curl을 날려보니 즉시 성공했다 — 다만 이건
포트 8080으로 직접 붙인 테스트라, 실제로 실패하던 경로(15008)와는 다른 경로였다는 게 나중에 밝혀진다.
동시에 `cilium-dbg endpoint list`에 Waypoint Pod의 IP가 아예 나타나지 않는 것도 발견했다(원인은 끝내
못 찾음). 그러다 클린하게 재배포한 직후 5연속 성공을 관측해 "해결됐다"고 판단했는데, **Waypoint
자체의 요청 카운터는 그 "성공한" 요청들에서도 전혀 움직이지 않았다.** 곧바로 20연속 재시도했더니
**0/20 성공**으로 돌아갔다 — 처음의 성공은 Waypoint 설정 이전에 gateway 앱이 이미 맺어둔 연결 풀
(keep-alive)이 우연히 재사용되며 Waypoint를 완전히 우회한 거짓 양성이었다.

**Istio 버전을 완전히 바꿔서(1.30.3 → 1.29.6) 재설치해도 똑같이 재현됐다.** ztunnel/istio-cni/istiod/
istio-base를 전부 지우고 재설치했는데도 동일한 실패 시그니처와 0/20 결과가 그대로 나왔다. 여기서
**"서로 다른 두 버전에서 재현되니 특정 릴리스 버그가 아니라 이 클러스터의 근본적인 아키텍처 비호환"**
이라고 결론짓고 조사를 종료했었다 — 하지만 이 결론은 **다음 날 틀린 것으로 밝혀졌다.**

**실제 원인은 훨씬 단순했다.** 다시 파고들면서 이번엔 애플리케이션 로그나 Envoy 통계 대신 **패킷 레벨을
직접 봤다** — `cilium monitor --type drop`을 waypoint pod가 있는 노드에서 돌려놓고 요청을 보내자,
`drop (Policy denied) ... 10.244.2.165:xxxxx -> 10.244.2.39:15008 tcp SYN`이라는 로그가 즉시 잡혔다.
**Cilium이 waypoint→backend HBONE 포트(15008)의 SYN 패킷을 NetworkPolicy 위반으로 계속 드롭하고
있었던 것이다.** `orchestrator-service`의 NetworkPolicy를 열어보니, waypoint pod로부터의 ingress를
허용하는 규칙이 포트 **8080만** 열어두고 15008을 빠뜨린 단순한 템플릿 실수였다 — 바로 위에 있는
gateway→orchestrator-service 규칙은 두 포트를 다 올바르게 열어뒀는데, waypoint 관련 규칙 하나만
포트가 누락돼 있었다. 포트를 추가하고 재배포하자 20/20, 이어서 50/50 연속 성공했고, **Waypoint 자체의
`rq_total` 카운터가 요청 수만큼 실제로 증가**하는 것까지 확인해 거짓 양성이 아님을 검증했다.

**"버전이 달라도 똑같이 실패한다"는 관찰 자체는 맞았지만, 거기서 내린 결론이 틀렸었다.** NetworkPolicy는
Kubernetes/Cilium 리소스이지 Istio 설치의 일부가 아니다 — Istio를 통째로 재설치해도 Helm이 관리하는
NetworkPolicy는 전혀 건드려지지 않고 그대로 남아있었다. 그러니 "버전을 바꿔도 실패가 재현된다"는 것은
"Istio 버전이 원인이 아니다"까지만 증명하는 것이었는데, 그걸 "이 클러스터의 근본적인 아키텍처 문제"라는
훨씬 강한 결론으로 확대 해석한 것이 실수였다. 재설치 과정에서 **바뀌지 않은 것**(우리 자신의 Helm 차트가
관리하는 NetworkPolicy)을 의심했어야 했는데, 재설치로 **바뀐 것**(Istio 자체)에만 집중한 것이다. 이
프로젝트 전체가 "Evidence 없는 결론 금지"를 원칙으로 삼고 있지만, 이 경우는 "반증 실험 하나를 통과했다"를
"가능한 다른 원인을 전부 배제했다"로 착각한 사례였고, 정직하게 기록해 둔다.

Waypoint 프록시 자체의 자원 수집(`resources.waypoint`)도 이번에 처음 구현했다 — 이전까지는 항상
`null`로 비어 있었다. 이제 Sidecar와 같은 방식(request당 정규화)으로 CPU/메모리를 측정할 수 있다.

상세 진단 기록(진단 과정 전체와 오류 정정 경위 포함): [phase-07-p1-waypoint-blocked 체크포인트](docs/checkpoints/phase-07-p1-waypoint-blocked.md)

**정식 반복측정도 완료했다(2026-08-01).** nominal/high/near-saturation 세 조건에서 Phase 4~6과 같은
기준(10~15회, bootstrap CI)으로 측정했다 — 세 조건 모두 15회 상한까지 `INCONCLUSIVE_MAX_RUNS`(Sidecar와
같은 패턴). 무효율이 30~45%로 Sidecar/Ambient 때보다 높았는데(Waypoint가 Ambient 위에 프록시를 하나 더
얹으니 이 3-VM 클러스터의 메모리 여유가 더 빠듯해진 것), **VM 자원 할당은 다른 모든 canonical 측정과
동일하게 유지한 채** 반복 횟수만 늘려서 극복했다 — 여기서 VM 메모리를 늘렸다면 지금까지의 No-Mesh/
Sidecar/Ambient 비교 전부와 하드웨어 조건이 달라져 비교 자체가 무효가 됐을 것이다.

Phase 8과 같은 방식으로 No-Mesh/Sidecar/Ambient 세 profile과 9번 비교한 결과:

| 지표 | 결과 |
|---|---|
| network bytes/request | 세 부하 조건 모두에서 **정확히 Ambient와 Sidecar 사이**에 위치(No-Mesh 대비 +16~18%, Ambient +1~2%·Sidecar +49%와 대비). 9/9 비교 전부 유의 |
| p95/p99 latency | nominal·high 조건에서는 No-Mesh/Sidecar/Ambient 전부보다 **일관되게 유의하게 느림**. near-saturation에서는 이 차이가 사라짐(원인 미규명) |
| app CPU-per-request | high 조건에서만 간헐적으로 유의, 나머지는 차이 없음 |
| app memory | 9/9 비교 전부 유의한 차이 없음(다른 모든 profile 비교와 같은 패턴) |

network bytes 결과는 Waypoint의 아키텍처와 정확히 들어맞는다 — Ambient의 가벼운 L4 기반(ztunnel/HBONE)
위에 L7 처리를 위한 Envoy 홉을 하나 추가한 구조이니, Ambient보다는 무겁고 모든 hop마다 전용 프록시가
붙는 Sidecar보다는 가벼운 게 당연하다. Latency 결과는 흥미로운 패턴이다 — 서로 다른 두 부하
조건(nominal, high)에서 같은 방향으로 재현됐다는 점에서 Phase 8의 단발성 신호들보다 신뢰도가 높지만,
near-saturation에서 사라지는 이유는 이 데이터만으로는 설명할 수 없다(정밀도 부족인지 실제 현상인지
구분 불가) — Phase 9 후속 실험 후보로 남겨뒀다.

전체 Evidence: [2026-08-01 canonical Waypoint baseline final](docs/evidence/performance/2026-08-01-canonical-waypoint-baseline-final.md)

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

### 6.7 Phase 8 profile 간 정식 통계 비교 — 완료 (2026-07-30)

Phase 4~6에서 확보한 No-Mesh/Sidecar/Ambient 세 profile의 정식 반복측정 데이터를 서로 비교하는 도구
(`experiments/compare_profiles.py`)를 새로 만들었다. 세 profile은 각자 독립된 반복측정 세션으로
측정됐기 때문에(예: Sidecar의 3번째 run과 Ambient의 3번째 run은 서로 짝지어진 관계가 아니다) 엄밀한
"paired" 검정 대신 **독립 2-표본 bootstrap**(그룹별로 각각 10,000회 리샘플링, 두 median 차이의 95% CI)을
사용했다. nominal/high/near-saturation 3개 부하 조건 × 3개 profile 쌍 × 6개 지표 = 36개 비교를 수행했다.

| 지표 | 유의한 비교 수 | 요약 |
|---|---:|---|
| network bytes/request | 9/9 (전부 유의) | Sidecar가 세 부하 조건 모두에서 No-Mesh 대비 **~49% 증가**(일관됨), Ambient는 ~1-2%만 증가 |
| p95/p99 latency | 1/18 | high(17 RPS) 조건 No-Mesh vs Ambient 1건만 유의(p99 +12.4ms), near-saturation에서는 방향이 뒤집혀 재현 안 됨 |
| throughput | 1/9 | 통계적으론 유의하나 크기가 0.0003 RPS로 실질적 의미 없음 |
| memory (application) | 1/9 | No-Mesh가 Sidecar보다 251MB 높음 — 인과 메커니즘 불명, mesh 비용 주장으로 보지 않음 |
| CPU-per-request (application) | 0/9 | 세 profile 어디서도 애플리케이션 자체의 요청당 CPU 비용에 유의한 차이 없음 |

**가장 깔끔한 발견은 network bytes/request다.** Sidecar는 세 부하 조건(8/17/22 RPS) 모두에서 No-Mesh 대비
정확히 같은 패턴으로 요청당 네트워크 바이트가 약 10,200~11,500바이트(~49%) 늘어난다 — Envoy가 매 hop마다
붙이는 mTLS 핸드셰이크/레코드와 HTTP/2 프레이밍 오버헤드가 원인으로 추정된다. Ambient는 같은 비교에서
증가폭이 260~470바이트(~1-2%)로 Sidecar의 약 1/20~1/40 수준이다 — "Ambient가 Sidecar보다 wire-level에서
가볍다"는 아키텍처적 설명에 처음으로 구체적인 수치 근거가 붙었다.

**Latency 차이는 36개 비교 중 단 1건만 유의했고, 그 1건조차 다음 부하 단계에서 재현되지 않았다.** high
조건에서 Ambient가 No-Mesh보다 p99가 12.4ms 느리다는 결과가 나왔지만, near-saturation에서는 오히려
Ambient가 더 빠른 방향(유의하지 않음)으로 나타났다. 실제 병목이라면 부하가 늘수록 같은 방향으로 심해져야
하는데 방향이 뒤집혔으므로, **이 1건을 "확정된 결론"으로 보지 않고** 36번 검정 중 우연히 나온 유의한
결과일 가능성(다중비교 문제)까지 감안해 "추가 검증이 필요한 신호" 정도로만 기록했다. 다만 방향 자체는
Phase 6.6 replica-scaling 연구의 "Ambient latency가 replica 증가에 따라 나빠진다"는 관찰과 같은 방향이라,
Phase 9에서 ztunnel의 공유 자원 저하 가설을 더 깊게 확인할 근거는 된다.

**애플리케이션 자체의 요청당 CPU 비용은 9개 비교 전부 유의한 차이가 없었다** — 이건 "차이를 못 찾음"이
아니라 의미 있는 부정 결과다. 세 profile 중 어느 것도 애플리케이션 프로세스 자체의 연산 비용을 바꾸지
않는다는 뜻이며, mesh 오버헤드는 (이미 Phase 5/6에서 별도로 측정한) 프록시 자체의 CPU/메모리와, 이번에
새로 확인한 network bytes 증가로 좁혀진다.

Phase 8 결과로부터 도출한 Phase 9 개선 가설 후보 3건: (1) Sidecar의 mTLS+HTTP/2 프레이밍이 network 오버헤드의
주 원인이라는 가설, (2) ztunnel 공유 프록시가 부하/replica 증가에 따라 latency 병목이 될 수 있다는 미확정
가설(반복 측정 필요), (3) mesh 비용은 proxy/network 계층에 국한되고 application 계층에는 전이되지 않는다는
확인된 부정 결과 — 이는 Phase 9 개선 작업의 타겟을 애플리케이션이 아니라 프록시 설정(mTLS 핸드셰이크 재사용,
connection pooling 등)으로 좁혀준다.

Phase 8 체크리스트의 마지막 항목인 "시간축 metric/trace/resource 상관 분석"은 시도 과정에서 한 번 틀렸다가
바로잡은 결론에 도달했다. 처음에는 "관측 스택 전체가 24시간 retention이니 다 사라졌다"고 판단했는데,
실제로 확인해보니 이건 절반만 맞는 얘기였다. Prometheus는 자체 TSDB retention으로, Tempo는 실제로 30초
마다 도는 compactor로 24시간 retention을 **진짜로 강제**하고 있어서(Phase 4 run이 남긴 실제 trace ID를
직접 조회해 `NotFound`로 재확인) 이 둘의 과거 데이터는 정말 사라졌다. 하지만 Loki(로그)는 retention 값만
설정돼 있을 뿐 그걸 강제하는 compactor 자체가 없어서, 2026-07-23 시점 로그도 실제로는 남아있었다 — 처음엔
라벨 이름을 잘못 써서(`namespace` 대신 실제로는 `k8s_namespace_name`) "없다"고 잘못 판단했었는데, 이걸
바로잡고 나니 데이터가 그대로 있었다. 그래서 남아있는 로그가 실제로 쓸모가 있는지 직접 열어봤다 —
latency가 가장 높았던 run 구간(Ambient high 조건, p99 63.9ms)의 로그를 뒤져봤더니 WARN/ERROR가 0건,
전체 로그도 20분 구간에 딱 2줄(그마저도 무관한 kafka 로그)뿐이었다. 즉 로그는 살아있지만 애플리케이션이
요청 단위 로그를 남기지 않고 lifecycle/error만 기록하도록 돼 있어서, 이번 분석에 쓸 만한 내용은 없었다.
없는 데이터를 짜맞추는 대신, "metric/trace는 정말 사라졌고 로그는 남아있지만 내용이 없다"는 이 정확한
결론으로 Phase 8을 마무리했다.

전체 Evidence: [2026-07-30 Phase 8 cross-profile comparison](docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md)

### 6.8 Phase 9 개선 실험 1 — Sidecar mTLS DISABLE, 가설 기각 (2026-07-30)

Phase 8의 가장 강한 신호(Sidecar network bytes/request가 No-Mesh 대비 ~49% 증가)를 보고 세운 첫 번째
가설 — "이 증가분의 주된 원인은 Envoy가 붙이는 mTLS 핸드셰이크/레코드 오버헤드다" — 를 직접 검증했다
(ADR-0028). mTLS를 `PeerAuthentication` 리소스로 끄고(`DISABLE`), 나머지는 전부 고정한 채 nominal(8 RPS)
조건에서 정식 10~15회 반복 측정을 새로 돌렸다 — 10회 만에 정밀도 게이트를 통과했는데, 이는 기존
PERMISSIVE 측정이 15회 상한까지도 수렴하지 못했던 것과 대비된다.

**결과는 가설을 기각했다.** mTLS를 꺼도 network bytes/request는 겨우 341바이트(~1%)만 줄었다 — Phase 8이
찾아낸 Sidecar의 전체 오버헤드(10,469바이트, ~49%) 중 mTLS가 설명하는 부분은 최대 3% 남짓이라는 뜻이다.
나머지 97%는 mTLS 암호화 자체가 아니라 Envoy의 HTTP/2 프레이밍이나 envoy-to-envoy 홉 자체의 부가 정보처럼
다른 곳에서 온다는 것이 이번 실험의 결론이다. "그럴듯해 보이는 첫 번째 가설"이 실제로는 틀렸다는 것을
직접 측정으로 확인하고, 그대로 정직하게 기록했다.

측정 도중 뜻밖의 발견도 하나 나왔다 — mTLS를 끄니 latency가 오히려 유의하게 **나빠졌다**(p95 +12.4ms,
p99 +18.9ms). 그런데 이 결과를 보고하기 전에, 비교 대상으로 쓴 기존 Phase 5 baseline이 Istio 1.30.3에서
측정된 반면 지금 클러스터는 Waypoint 재시도 때 1.29.6으로 통째로 재설치돼 있다는 걸 발견했다 — 즉 "mTLS
모드 하나만 바꾼" 게 아니라 Istio 버전까지 같이 달라진 비교였던 것이다. 같은 버전으로 다시 측정해
확인하려 했으나, 시간 대비 실익이 적다는 판단(사용자 지시)에 따라 이 버전 차이는 감수하기로 하고, latency
결과는 "확정 아님"이라는 꼬리표를 붙인 채로만 보고했다 — network bytes 결론(mTLS가 원인의 극히 일부)은
이 confound에 크게 영향받지 않는다고 판단해 그대로 유지했다.

전체 Evidence: [2026-07-30 Phase 9 mTLS-disable experiment](docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md)

### 6.9 Phase 9 개선 실험 2 — Ambient replica 확장, 방향은 확인·크기는 불일치 (2026-08-02)

§6.6 방향성 연구가 3회 반복만으로 관찰했던 "Ambient는 replica가 늘수록 latency가 나빠진다"를 이번엔
정식 10회 반복(bootstrap CI)으로 재확인했다. orchestrator-service를 1replica(기존 Phase 6 데이터
재사용)와 4replica(신규 측정)로 비교했다.

| 지표 | replica=1 | replica=4 | 변화 | 유의성 |
|---|---:|---:|---:|---|
| p99 latency | 39.50 ms | 47.40 ms | **+20%** | 유의 |
| p95 latency | 30.08 ms | 32.63 ms | +8% | 유의하지 않음 |
| ztunnel 메모리 | 16.9 MB | 30.25 MB | **+79%** | 유의 |
| ztunnel CPU | 82.44 core-s | 83.16 core-s | +1% | 유의하지 않음 |

**p99 저하 방향은 확인됐지만, 크기는 방향성 연구가 시사했던 것과 크게 달랐다.** ADR-0027의 3회 반복
데이터는 p99가 거의 2배(+95%) 나빠지는 것으로 나왔는데, 이번 정식 측정은 +20%에 그쳤다. 더 놀라운 건
**ztunnel 메모리다** — 방향성 연구는 "메모리는 거의 안 변한다"(+2%)는 게 핵심 결론 중 하나였는데,
정식 측정에서는 오히려 79%나 늘어서 정반대 방향이 나왔다. 측정 창 길이(방향성 연구는 180초, 이번은
정식 2,525초)나 Istio 버전 차이(1.30.3 vs 1.29.6, 이 프로젝트에서 두 번째로 마주친 같은 종류의
confound) 중 무엇이 원인인지는 이 데이터만으로 가릴 수 없어 "추가 조사가 필요한 신호"로만 기록했다.

이 결과는 그 자체로 방법론적으로 중요한 사례다 — **빠른 3회 반복 방향성 연구는 "뭔가 있다"는 신호는
정확히 잡아냈지만("p99가 나빠진다"는 방향), 정확한 크기나 다른 지표(메모리)에 대한 결론까지는 신뢰할
수 없다는 것을 이 프로젝트 스스로 증명한 셈이다.** 방향성 연구를 정식 결론처럼 취급하지 않아야 하는
이유가 추상적 원칙이 아니라 실제 데이터로 확인된 순간이다.

전체 Evidence: [2026-08-02 Phase 9 Ambient replica-scaling formal](docs/evidence/performance/2026-08-02-phase9-ambient-replica-scaling-formal.md)

### 6.10 Phase 10 회복탄력성 — Pod kill과 chain-wide delay (2026-08-02~03)

Chaos Mesh는 이미 자원이 빠듯한 클러스터(Phase 7/9에서 무효율 30~45%)에 특권 DaemonSet을 더 얹는 위험이
크다고 판단해 배제하고(ADR-0030), kubectl과 기존 앱 파라미터만으로 구현 가능한 두 fault로 범위를
좁혔다 — **Ambient profile 하나만** 측정했다(cross-profile fault 비교는 범위 밖).

**Pod kill**(orchestrator-service, 10/10회): nominal 8 RPS 부하 중 pod를 강제 종료하면 Deployment가
자동으로 재생성한다. Recovery time은 중앙값 39.9초(29.9~39.92초)로, 이번 재구축 작업 중 실측한 이
애플리케이션의 JVM 콜드스타트 시간(26~28초)과 잘 맞아 **recovery time은 사실상 새 Pod의 JVM 기동
시간이 지배적**이라는 해석이 가장 설득력 있다. Fault 중 peak error rate는 37.5~73.3%로 컸는데, 이는
replica=1 조건이기 때문이며(로드밸런서가 트래픽을 돌릴 다른 replica가 없음) "Ambient가 pod-kill에
강하다"는 뜻이 아니라 "Kubernetes 자체의 self-healing이 mesh profile과 무관하게 작동한다"는 것만
확인한다.

**Chain-wide delay**(50ms/hop, 3-hop 전체, nominal 8 RPS, before=Phase 6 canonical 재사용): 15회 중
11 valid, `SESSION_COMPLETED`. p95/p99가 각각 +160.7ms/+166.7ms(둘 다 유의) 늘었는데, 이는 injected
delay(3×50ms=150ms)와 거의 정확히 일치한다. **핵심 발견은 errorRate가 before/after 둘 다 정확히
0이라는 것** — chain 전체에 hop당 50ms 지연이 걸려도 SYNC_CHAIN은 연쇄 실패나 timeout 없이 요청을
완주시켰다. CPU/request는 유의하게 늘었지만(+36.6%, 요청이 더 오래 자원을 점유하는 당연한 결과),
memory는 유의한 차이가 없었다. **Ambient는 이 스트레스 조건에서 "성공률을 해치지 않고 latency만
비례해서 늘어나는" 예측 가능한 성능 저하(graceful degradation) 패턴을 보였다.**

Evidence 작성 중 이 프로젝트에서 **세 번째로 같은 종류의 Istio 버전 confound**(ADR-0028/0029와 동일
패턴)를 발견했다 — chain-delay의 before(Phase 6, Istio 1.30.3)와 after(2026-08-02 측정, Istio 1.29.6)가
서로 다른 버전이었다. `manifest.json`의 `createdAt` 타임스탬프로 직접 확인했다. p95/p99의 큰 폭(150ms대)은
버전 차이로 설명하기 어렵지만, 정직하게 명시했다.

**2026-08-03 정전 인시던트**: Phase 10 데이터 수집 완료 *직후* 호스트 전원 손실로 `mesh-cp-01`의 etcd가
손상됐다(bbolt backend가 자신의 consistent-index를 잃고 존재하지 않는 snapshot 파일을 찾다 panic). 손상된
데이터를 백업한 뒤 kubeadm reset+init부터 Cilium/MetalLB/observability/Istio Ambient까지 **클러스터
전체를 처음부터 재구축**했다 — 이 복구 작업 자체가 뜻하지 않게 Phase 11이 요구하는 "새 환경에서 대표
실험 재현" 요건을 실제 사고 상황에서 검증한 셈이 됐다(§8.1 참고). 측정 데이터 자체는 인시던트 이전에
git에 안전하게 반영되어 영향받지 않았다.

전체 Evidence: [2026-08-03 Phase 10 회복탄력성 결과](docs/evidence/performance/2026-08-03-phase10-resilience-results.md)

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
16. **반증 실험을 설계했지만, 그 결과를 과잉 해석한 실수를 그대로 기록함**: 특정 Istio 1.30.3 버전의
    버그일 가능성을 배제하려고 완전히 다른 minor 버전(1.29.6)으로 재설치해 재현을 시도한 것 자체는 합리적
    설계였다. 문제는 그 결과("두 버전 모두 동일하게 실패")의 해석이었다 — 이걸 "특정 릴리스 버그가
    아니다"까지만 결론짓지 않고 "이 클러스터 스택 자체의 근본적인 아키텍처 비호환"이라는 훨씬 강한
    주장으로 확대했다. 실제로는 NetworkPolicy(Istio 재설치로 전혀 바뀌지 않는 리소스)의 단순한 포트
    누락이 원인이었다(§6.5, 18번 항목). "재현 실험 하나를 통과했다"를 "다른 가능한 원인을 전부
    배제했다"로 착각한 이 실수를, 나중에 발견한 뒤 숨기지 않고 정정 경위까지 그대로 남겼다 — 실수 자체
    보다 실수를 어떻게 다뤘는지가 이 프로젝트의 원칙("Evidence 없는 결론 금지")을 더 잘 보여준다.
17. **자기 자신의 결론도 다시 검증해서 틀린 부분을 바로잡음**: Phase 8 시간축 상관 분석에서 처음엔
    "관측 스택 전체가 24시간 retention이라 다 사라졌다"고 결론지었다. 그런데 이 결론을 재검증하는
    과정에서 Loki 로그를 조회할 때 잘못된 라벨 이름(`namespace`)을 써서 실제로 존재하는 데이터를 "없다"고
    잘못 판단했었다는 걸 발견했다. 라벨을 바로잡아 다시 조회하니 2026-07-23 시점 로그가 실제로 남아있었고,
    Loki의 retention 설정은 이를 강제하는 compactor가 아예 없어 값만 있고 실제로는 적용되지 않는다는 것도
    확인했다. 여기서 멈추지 않고 "그럼 그 로그가 실제로 쓸모 있는가"까지 직접 열어서 확인했다(WARN/ERROR
    0건, 전체 2줄) — 데이터가 있다는 것과 그 데이터가 유용하다는 것은 다른 질문이라는 걸 끝까지 구분해서
    검증한 사례다. Prometheus/Tempo는 반대로 재검증 결과 원래 결론(진짜로 사라짐)이 맞다는 것도 실제
    trace ID 조회로 재확인했다 — 이 프로젝트 전체를 관통하는 "Evidence 없는 결론 금지" 원칙을 자기 자신의
    이전 결론 앞에서도 그대로 적용한 사례다.
18. **"blocked, 조사 종료"로 닫아둔 문제를 다시 열어서 실제로 해결함**: Waypoint 문제를 한 번 "버전
    독립적 비호환"으로 최종 결론짓고 넘어갔지만, 최종 벤치마크 workload별 비교를 완성하려면 Phase 7이
    필요하다는 판단에 따라 다시 파고들었다. 이번엔 애플리케이션 로그나 Envoy 통계 대신 처음으로
    `cilium monitor --type drop`을 써서 패킷 레벨을 직접 봤고, 몇 분 만에 "Cilium이 15008 포트를
    정책 위반으로 드롭하고 있다"는 결정적 증거를 잡았다. 원인은 우리 자신의 Helm 차트 NetworkPolicy
    템플릿의 포트 누락이라는, 며칠간의 진단 끝에는 허무할 만큼 단순한 설정 실수였다. 도구를 한 단계 더
    깊은 계층(설정 조회 → 패킷 캡처)으로 바꾸자마자 몇 달째 안 보이던 원인이 바로 보였다는 것 자체가,
    "안 보인다"와 "없다"를 구분해야 한다는 이 프로젝트의 원칙을 실제로 증명한 사례다.

19. **정전으로 손상된 etcd를 삭제 대신 원인 진단부터**: 2026-08-03 호스트 전원 손실 후 클러스터가 안
    올라와서 조사해보니, etcd가 부팅 시 계속 panic하고 있었다. 로그를 끝까지 읽어 "bbolt 백엔드의
    consistent-index가 0으로 읽히면서 존재하지 않는 snapshot 파일(`.snap.db`)로 복구를 시도하다 실패"라는
    정확한 실패 지점을 확인한 뒤에야 복구가 불가능하다고 판단했고, 되돌리기 전에 손상된 데이터 자체를
    먼저 백업했다(`tar czf`) — 복구 시도 중 추가 실수가 나더라도 원본을 보존해두는 것이 원칙이다.
20. **kube-proxy 없는 클러스터에서 Cilium을 올릴 때의 부트스트랩 순환 문제를 실측으로 발견**: 재구축 중
    `kubeProxyReplacement=true`로 Cilium을 처음 설치했더니 자기 자신도 못 뜨는 순환 문제가 생겼다 — Cilium의
    설정용 init 컨테이너가 apiserver의 ClusterIP(10.96.0.1)로 접속을 시도하는데, 그 ClusterIP 자체가
    kube-proxy나 Cilium의 데이터플레인이 있어야 라우팅되기 때문이다. `k8sServiceHost`/`k8sServicePort`를
    실제 apiserver 주소로 명시해 이 순환을 끊었다 — 이론으로 알고 있던 문제를 실제로 겪고 나서야
    수정 위치가 명확해졌다.
21. **istio-cni가 계속 죽는 원인을 로그가 스스로 알려준 힌트로 해결**: Istio CNI DaemonSet이 계속
    `NotReady`였는데, 로그에 "Cilium CNI가 감지됨, `cni.exclusive=false`를 확인하라"는 경고가 이미 있었다.
    Cilium을 `cni.exclusive=false`로 재설치했지만 여전히 실패해서 더 파보니, 설정(ConfigMap)은 바뀌었지만
    Cilium Pod 자체가 재시작되지 않아 새 설정을 읽지 않고 있었다 — DaemonSet을 수동으로 롤링 재시작한
    뒤에야 해결됐다. "설정을 바꿨다"와 "그 설정이 실제로 적용됐다"를 항상 구분해서 검증해야 한다는
    이 프로젝트의 반복된 교훈이 여기서도 그대로 적용됐다.
22. **손으로 짠 스모크 테스트 페이로드가 만든 가짜 실패를 실제 버그와 구분**: 재구축 후 SYNC_CHAIN을
    수동으로 검증하다 chain/fanout/payload/async 호출이 전부 400/500을 반환해서 처음엔 인프라 문제로
    의심했다. 소스 코드(`ChainController`, `CorrelationIdFilter`)를 직접 읽어 `X-Correlation-Id`/
    `X-Experiment-Run-Id` 헤더가 없으면 내부 hop 호출에서 실패한다는 것을 발견하고, 정식 k6 워크로드가
    항상 이 헤더를 보낸다는 것도 확인했다 — 인프라를 더 건드리기 전에 "내 테스트 방법이 틀렸을 가능성"을
    먼저 배제한 사례다.

`[TODO: Phase 11 완료 이후 발견되는 새로운 엔지니어링 이슈를 계속 추가]`

---

## 8. Phase 진행 이력 (Phase 5~11)

| Phase | 목표 | 상태 |
|---|---|---|
| 5. Sidecar | injection/mTLS 검증, app/proxy 자원 분리, paired 10~15회 반복 | ✅ 완료 |
| 6. Ambient | ztunnel 공유 자원 귀속, 고정 replica 반복 | ✅ 완료(고정 replica 범위, replica 확장은 §6.6/§6.9로 별도 수행) |
| 7. Waypoint | 전체/선택 경로 분리, L7 기능·통과 성능 측정 | ✅ 완료(§6.5) |
| 8. 병목 분석 | profile 간 절대/상대 차이, telemetry 기반 병목 3개 이상 확정 | ✅ 완료 (§6.7) |
| 9. 개선 실험 | 병목별 단일 변수 개선안 3개 이상, before/after 10회+ 반복 | ✅ 완료 (§6.8~6.9) |
| 10. 회복탄력성 | pod-kill과 chain-wide delay before/after 측정 | ✅ 완료 (§6.10) |
| 11. 최종화 | 워크로드별 선택 Matrix, 재현성 검증, 최종 보고서 | ✅ 완료 (§8.1, §8.2, §11) |

### 8.1 재현성 검증 — 2026-08-03 클러스터 전체 재구축

Phase 11의 "새 namespace 또는 재구성 환경에서 대표 실험을 재실행한다" 요건은 계획된 실습이 아니라
**실제 인시던트 복구 과정에서 검증됐다**. 2026-08-03 호스트 전원 손실로 `mesh-cp-01`의 etcd가 손상되어
클러스터 전체(Kubernetes control-plane, Cilium, MetalLB, observability 스택, Istio Ambient, 애플리케이션
Helm 릴리스)를 문서와 자동화만으로 처음부터 재구축했다:

1. `kubeadm reset`(3노드) → `kubeadm init`(K8s v1.36.2, pod-cidr/service-cidr은 손상 전 apiserver/
   controller-manager manifest에서 실측한 값 그대로 재사용) → worker 재join
2. Cilium 1.19.6(kubeProxyReplacement, ipam=kubernetes) → Gateway API v1.4.1 + MetalLB 0.16.1 →
   local-path-provisioner v0.0.36 → observability 스택(kube-prometheus-stack/Loki/Tempo/OTel
   Collector) → `meshperf` Helm(no-mesh values로 우선 배포·검증) → Istio 1.29.6(istiod/istio-cni/
   ztunnel) → `meshperf`를 ambient values로 전환
3. 검증: 노드 3/3 Ready, Cilium 3/3 + Operator 2/2 + Hubble 1/1, MetalLB 1/1 + Speaker 3/3 +
   GatewayClass 4종 Accepted, NetworkPolicy 11 KNP + 1 CNP(원래 배포와 동일한 개수), Prometheus
   benchmark job 7개 `up=1`, ztunnel 3/3 + ambient 캡처 라벨 확인, **SYNC_CHAIN E2E(ping/3-hop
   chain/3-target fan-out/4 KiB payload/3-task async) 전부 통과**, Python 실험 러너 dry-run
   `COMPLETED`(무효화 요인 없음)로 측정 파이프라인 전체 정상 확인

재구축 과정에서 실제로 겪은 문제(부트스트랩 순환, `cni.exclusive`, 콜드스타트 진단)는 §7의 19~22번
항목에 기록했다. **이 재현은 계획된 "새 namespace 실험"보다 더 강한 증거다** — 통제된 반복이 아니라
예정에 없던 실제 장애 상황에서, 이 프로젝트의 문서(버전/설정값)와 automation(Helm chart, Python
runner)만으로 처음부터 다시 세워도 같은 결과 파이프라인이 재현된다는 것을 실증했다.

전체 기록: [docs/CURRENT.md](docs/CURRENT.md)의 2026-08-03 인시던트 절 참고.

### 8.2 manifest→raw→summary→graph→claim 링크 감사

Phase 11 요건에 따라 이 문서(§6)의 정량 주장이 실제로 존재하는 데이터를 가리키는지 표본 감사했다.
`experiments/compare_profiles.py` 산출물 SHA-256 해시(Phase 8: 9건, Phase 9: 1건, Phase 10: 1건)를
현재 로컬 `results/`의 실제 파일과 다시 계산해 **11/11 전부 일치**함을 확인했고, Phase 4~7·9 canonical
baseline의 원본 run 디렉터리(`repeat-XX`)가 삭제 없이 그대로 남아있음도 확인했다. 깨진 링크는
발견되지 않았다.

### 8.3 워크로드/시나리오별 선택 Matrix

지금까지 측정한 모든 결과(§6)를 종합해, "어떤 상황에서 어떤 profile을 선택해야 하는가"로 뒤집어
정리한 것이다. **이 Matrix는 이 프로젝트의 측정 범위(§8.4 적용 범위 참고) 안에서만 유효하다** — 특히
노드당 2 vCPU라는 작은 규모, SYNC_CHAIN 3-hop 워크로드, 8/17/22 RPS 부하 범위를 벗어나는 환경에는
그대로 적용할 수 없다.

| 시나리오 / 요구사항 | 권장 | 근거 | 자원/기능 비용 | Rollback 기준 |
|---|---|---|---|---|
| **네트워크 바이트가 병목**(대역폭 제한, 대용량 payload, 높은 처리량) | **Ambient** | network bytes/request가 No-Mesh 대비 +1~2%뿐(Sidecar +49%, Waypoint +16~18%, §6.7) | ztunnel 노드당 공유(가벼움), 단 replica 확장 시 latency/메모리 증가 확인됨(§6.9, 아래 항목 참고) | network bytes가 예산을 초과하면 즉시 재평가 |
| **mTLS/zero-trust가 필요하지만 비용에 민감** | **Ambient**(Sidecar에서 mTLS만 끄는 것은 효과 없음) | mTLS는 Sidecar 전체 오버헤드의 ~3%만 설명(§6.8) — Sidecar를 쓰면서 mTLS를 꺼도 거의 안 줄어든다. mTLS를 포함해도 Ambient가 훨씬 가볍다 | Ambient는 mTLS "무료"에 가까움(ztunnel이 이미 처리) | — |
| **Pod당 메모리가 빠듯한 클러스터, 서비스당 replica가 많음** | **Ambient**(단, 아래 예외 확인) | Sidecar 메모리는 replica 1→4에서 120→173MiB(+44%, Pod마다 자기 몫)로 선형 증가. Ambient(ztunnel)는 15.8→16.1MiB(+2%, 방향성 연구 §6.6)로 거의 불변 | **예외**: 정식 반복측정(§6.9)에서는 ztunnel 메모리가 오히려 16.9→30.25MB(+79%)로 유의하게 늘었다(방향성 연구와 반대, 원인 미확정) — "Ambient는 replica가 늘어도 공짜"라고 안심하지 말고 실측 필요 | replica 확장 전후 ztunnel 메모리를 반드시 재측정 |
| **replica가 많은 서비스의 latency 민감도가 높음** | **주의 — Ambient도 replica 증가에 따라 p99가 나빠진다** | 정식 측정(§6.9)에서 replica 1→4 시 p99 +20%(유의). 방향성 연구는 최대 +95%까지 관찰(신뢰구간 없음, 재현 안 됨) | Sidecar는 오히려 replica가 늘수록 p95가 소폭 개선(부하 분산 효과, §6.6) — 이 축만 보면 Sidecar가 유리할 수 있음 | p99가 SLA를 넘으면 replica 수를 낮추거나 Sidecar 재검토 |
| **특정 서비스에만 L7 기능(재시도, circuit breaking, 헤더 기반 라우팅)이 필요, 전체는 불필요** | **Waypoint(선택 경로)** | network bytes가 Ambient와 Sidecar 사이(+16~18%, §6.5)로 L7 기능을 필요한 경로에만 추가하는 절충 | latency가 nominal/high에서 세 profile보다 일관되게 느림(near-saturation에서는 차이 소멸, 원인 미규명). **배포가 까다롭다** — 이 프로젝트에서 NetworkPolicy HBONE 포트(15008) 누락 버그를 2건 발견(§6.5) | Waypoint 도입 시 모든 waypoint-인접 NetworkPolicy에 HBONE 포트가 열려 있는지 반드시 확인 |
| **일반 서비스 간 통신, L7 기능 불필요, latency에 극도로 민감** | **No-Mesh 또는 Ambient**(Sidecar 비교는 미확정) | 36개 cross-profile latency 비교 중 유의한 건 1건뿐이고 그마저 다음 부하 단계에서 재현 안 됨(§6.7) — 이 환경(p95 ≈5ms/p99 ≈8ms 미만 차이는 통계적으로 구분 불가)에서는 "Ambient가 No-Mesh보다 확실히 느리다"는 근거가 약하다 | Sidecar는 latency 정밀도 자체가 잘 수렴하지 않아(§6.3) 비교 신뢰도가 낮음 | — |
| **Pod 장애(crash, 재시작)에 대한 자동 복구가 필요** | **모든 profile 동일**(Kubernetes 자체 기능) | pod-kill이 자동 복구되는 것은 Deployment의 self-healing이지 mesh profile의 기능이 아님(§6.10) — 이 프로젝트는 Ambient만 측정했지만 이 메커니즘 자체는 profile-agnostic | replica=1이면 fault 중 peak error rate가 크다(37.5~73.3%) — 가용성이 중요하면 replica ≥2 | — |
| **의존 서비스의 latency 저하(전체 체인이 동시에 느려지는 상황)에 대한 내성** | **Ambient는 확인됨**(성공률 유지, latency만 비례 증가, §6.10). Sidecar/No-Mesh/Waypoint는 미확인 | chain 전체에 50ms/hop 지연을 걸어도 errorRate 0 유지, latency는 injected delay와 거의 정확히 비례 | cross-profile 비교를 하지 않아 "Ambient가 다른 profile보다 낫다"는 뜻은 아님 | — |

### 8.4 적용 범위와 외삽 금지 조건

이 Matrix와 §6의 모든 정량 결과는 **다음 조건을 벗어나면 그대로 적용할 수 없다**:

- **하드웨어**: VMware Workstation 가상 3노드, worker 노드당 allocatable 2 vCPU. 이 환경은 p95
  ≈5ms/p99 ≈8ms보다 작은 latency 차이를 통계적으로 구분하지 못한다 — 이보다 코어 수가 많거나 적은
  환경에서는 mesh profile 간 오버헤드의 상대적 크기 자체가 달라질 수 있다.
- **버전**: Kubernetes v1.36.2, Cilium 1.19.6, Istio 1.29.6(이 프로젝트 진행 중 1.30.3에서 재설치로
  바뀜 — ADR-0028/0029/Phase 10에서 세 번 confound로 나타남), Java 25 + Spring Boot 4.1. 다른 버전
  조합에서는 이 프로젝트가 발견한 특정 수치(예: mTLS가 오버헤드의 3%만 설명)가 재현되지 않을 수 있다.
- **워크로드**: SYNC_CHAIN 3-hop, payload 1 KiB, hop delay 1ms(기본) 조건에서 측정했다. Fan-out,
  Kafka 비동기 파이프라인, 대용량 payload 시나리오는 E2E 스모크만 확인했고 정식 반복측정하지 않았다 —
  이 Matrix를 그런 워크로드에 그대로 적용할 수 없다.
- **부하 범위**: 8/17/22 RPS(usable capacity 28 RPS 기준 10~30%)에서만 정식 측정했다. 이보다 훨씬
  높은 부하(포화 근접~초과)나 훨씬 낮은 부하에서의 profile 간 상대적 순위는 이 데이터로 알 수 없다.
- **replica 범위**: 1과 4 두 지점만 측정했다(§6.6, §6.9) — 2, 3, 5 이상에서의 거동은 두 지점 사이/
  바깥을 선형 보간·외삽한 것이 아니라 실측하지 않은 영역이다.
- **회복탄력성 범위**: pod-kill과 chain-wide delay 두 fault, Ambient profile 하나만 측정했다(§6.10).
  Network delay/loss, Kafka worker 중단, hop 단위로 격리된 fault, 그리고 Sidecar/No-Mesh/Waypoint의
  fault 반응은 측정하지 않았다 — "Ambient가 장애에 강하다"는 일반적 결론으로 확대해석하면 안 된다.
- **측정되지 않은 근본 원인들**: Waypoint의 near-saturation에서 latency 차이가 사라지는 메커니즘,
  Ambient replica 확장 시 ztunnel 메모리가 방향성 연구와 반대로 증가한 원인 — 둘 다 이 프로젝트
  범위에서는 규명하지 못했다.

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

**벤치마크 설계**: "3회 반복"처럼 임의로 정한 기준은 처음엔 합리적으로 보여도, 실제로 돌려보면 이 환경
고유의 특성(작은 절대 latency, 3-hop 변동성)과 충돌한다는 걸 반복해서 겪었다. ADR-0023(절대·상대 혼합
정밀도)과 §6.9(방향성 연구 vs 정식 반복의 크기 차이)는 같은 교훈을 두 번 다른 방식으로 확인해준
셈이다 — **"몇 번 반복했다"가 아니라 "신뢰구간이 실제로 무엇을 감지할 수 있는가"를 먼저 계산해야
한다.** 방향성 연구(3회)는 "뭔가 있다"를 정확히 잡아내는 데는 유용했지만, 크기나 부호(ztunnel 메모리)
까지 믿는 순간 틀렸다.

**통계적 정지 규칙**: 이 프로젝트에서 가장 자주 나온 판정은 `STOP_PRECISION_REACHED`가 아니라
`INCONCLUSIVE_MAX_RUNS`였다 — Sidecar는 9개 조건 중 세 조건 모두, Waypoint도 세 조건 모두 이렇게
끝났다. 처음엔 "실패"처럼 느껴졌지만, 돌이켜보면 이것 자체가 **"이 환경에서는 이 정도 크기의 차이를
구분할 수 없다"는 정직한 정보**였다 — 억지로 통과시키거나 반복 횟수를 무한정 늘리는 대신 상한에서
멈추고 그 사실 자체를 결론에 포함시키는 것이 옳은 태도였다.

**온프레미스 Kubernetes 운영**: 클라우드 관리형 서비스라면 겪지 않았을 문제(kube-proxy 없는 클러스터의
Cilium 부트스트랩 순환, `cni.exclusive` 설정이 적용되려면 재시작이 필요하다는 것, etcd가 정전에 얼마나
취약한지)를 직접 겪었다. 특히 2026-08-03 인시던트는 "측정 결과와 인프라 상태는 분리해서 관리해야
한다"는 원칙(git에는 Evidence만, `results/`는 로컬 전용)이 실제로 재난 복구 상황에서 왜 중요한지를
증명했다 — etcd가 완전히 날아가도 몇 주치 측정 결과와 결론은 전혀 흔들리지 않았다.

**Java 성능 분석**: JVM 콜드스타트(26~30초)가 pod-kill recovery time의 지배적 요인이라는 걸 발견한
것(§6.10)은 "mesh profile 비교"라는 원래 목적과는 결이 다르지만, 실무적으로는 더 실행 가능한
인사이트였다 — 회복탄력성을 개선하려면 mesh 설정보다 **JVM 시작 시간 자체**(native image, CDS
아카이브, readiness probe 튜닝)를 먼저 봐야 한다는 뜻이다.

**가장 반복적으로 나온 실수 패턴**: "재현 실험을 통과했다"를 "다른 원인을 전부 배제했다"로 착각한 것
(§6.5의 Waypoint 오판, 18번 항목)과 "설정을 바꿨다"를 "그 설정이 적용됐다"로 착각한 것(§7의 21번,
Cilium daemonset 재시작 누락)이 이 프로젝트에서 최소 두 번씩 나왔다. 둘 다 **"관찰된 현상"과 "그
현상에 대한 해석" 사이에 검증되지 않은 가정 하나가 숨어있었다**는 공통점이 있다 — 다음 프로젝트에서는
이 두 가지 실수 패턴을 체크리스트로 만들어 명시적으로 확인하는 습관을 들일 만하다.

---

## 11. 결론

**4개 profile을 하나의 문장으로 요약하면**: No-Mesh는 기준점, **Ambient는 이 프로젝트가 측정한 범위
안에서 가장 균형 잡힌 선택**(network bytes +1~2%, latency는 No-Mesh와 통계적으로 구분 안 됨, mTLS
사실상 무료)이지만 **replica 확장에는 무비용이 아니다**(p99 +20%, ztunnel 메모리 +79%, 둘 다 정식
신뢰구간으로 확인됨). Sidecar는 network bytes(+49%)와 Pod당 메모리(replica 비례 증가)가 뚜렷한 대가이고
latency 정밀도 자체가 잘 수렴하지 않아 비교 신뢰도가 낮다. Waypoint는 선택적 L7이 필요할 때 Ambient와
Sidecar 사이의 절충안이지만 배포가 까다롭고(NetworkPolicy 버그 2건 실제 발견) 특정 부하 구간에서
latency 손해가 있다. 회복탄력성 측면에서는 pod-kill 자동 복구와 chain-wide latency 스트레스 아래에서의
graceful degradation을 Ambient에서 확인했지만, 이건 Kubernetes 자체 기능(pod-kill)과 Ambient 고유
특성(latency 스트레스) 각각의 결과이지 "Ambient가 장애에 제일 강하다"는 cross-profile 결론이 아니다.

**워크로드 유형별 선택 권고**는 §8.3(선택 Matrix)에 8개 시나리오로 정리했다 — 요약하면 **"네트워크
비용과 mTLS가 중요하면 Ambient, 특정 경로에만 L7이 필요하면 Waypoint(배포 주의), replica가 많은
서비스는 두 profile 모두 확장 비용을 실측하라"**는 것이다.

**가설 검증 결과**(§2 상세): 6개 중 1개 확인(mesh별 비용 확장 형태 차이), 2개 부분 확인(Waypoint
병목 가능성 — replica 축 미검증, 선택적 경로 비용 절감 — telemetry sampling 축 미검증), 3개는
이번 범위에서 아예 측정하지 않음(retry amplification, retry-owner 개선, HPA/queue-lag) — 모두
장애 전파·복구의 소유권을 바꾸는 아키텍처 변경이라는 공통점이 있어 후속 프로젝트로 남긴다.

**프로젝트 전체의 한계와 적용 범위**(§8.4 상세): VMware 3노드(노드당 2 vCPU), Kubernetes
v1.36.2/Cilium 1.19.6/Istio 1.29.6(진행 중 1.30.3→1.29.6 재설치가 있었고 이게 세 번 confound로
드러남), SYNC_CHAIN 3-hop 워크로드, 8/17/22 RPS 부하, replica 1/4 두 지점, fault는 pod-kill/chain-delay
두 종류·Ambient 하나의 profile로 측정했다는 것을 벗어나면 이 결론들을 그대로 적용할 수 없다. 이 범위
안에서는, **Evidence 없는 결론을 내지 않는다는 원칙을 프로젝트 시작부터 끝(정전 복구 포함)까지
일관되게 지켰다**는 것이 가장 중요한 산출물이다 — 개별 수치보다, "무엇을 확인했고 무엇을 확인하지
못했는지"를 숨기지 않고 구분하는 방법론 자체가 이 프로젝트의 결론이다.

---

## 12. 참고 문서

| 영역 | 문서 |
|---|---|
| 프로젝트 개요 | [docs/00-project-overview.md](docs/00-project-overview.md) |
| 무엇을 왜 테스트했는가 (처음부터 끝까지 설명) | [docs/testing-explained.md](docs/testing-explained.md) |
| 인프라 YAML 완전 정복 (설정 파일 한 줄씩 설명) | [docs/infrastructure-deep-dive.md](docs/infrastructure-deep-dive.md) |
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
| Waypoint 진단·해결 체크포인트 | [docs/checkpoints/phase-07-p1-waypoint-blocked.md](docs/checkpoints/phase-07-p1-waypoint-blocked.md) |
| Waypoint 정식 baseline 최종 Evidence | [docs/evidence/performance/2026-08-01-canonical-waypoint-baseline-final.md](docs/evidence/performance/2026-08-01-canonical-waypoint-baseline-final.md) |
| Replica-scaling 방향성 연구 Evidence | [docs/evidence/performance/2026-07-29-replica-scaling-directional-study.md](docs/evidence/performance/2026-07-29-replica-scaling-directional-study.md) |
| Phase 8 profile 간 통계 비교 Evidence | [docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md](docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md) |
| Phase 9 mTLS DISABLE 실험 결정 | [ADR-0028](docs/decisions/0028-phase9-sidecar-mtls-disable-experiment.md) |
| Phase 9 mTLS DISABLE 실험 Evidence | [docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md](docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md) |
| Phase 9 Ambient replica-scaling 정식 실험 결정 | [ADR-0029](docs/decisions/0029-phase9-ambient-replica-scaling-formal-experiment.md) |
| Phase 9 Ambient replica-scaling 정식 실험 Evidence | [docs/evidence/performance/2026-08-02-phase9-ambient-replica-scaling-formal.md](docs/evidence/performance/2026-08-02-phase9-ambient-replica-scaling-formal.md) |
| Phase 10 회복탄력성 범위 결정 | [ADR-0030](docs/decisions/0030-phase10-resilience-scope.md) |
| Phase 10 회복탄력성 결과 Evidence | [docs/evidence/performance/2026-08-03-phase10-resilience-results.md](docs/evidence/performance/2026-08-03-phase10-resilience-results.md) |
| 현재 체크포인트 | [docs/CURRENT.md](docs/CURRENT.md) |
| Phase 전체 체크리스트 | [docs/checkpoints/phase-checklists.md](docs/checkpoints/phase-checklists.md) |
| 저장소 | https://github.com/0206pdh/msa-servicemesh |
