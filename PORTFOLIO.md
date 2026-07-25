# Mesh Performance Lab — 포트폴리오 요약

> 이 문서는 이력서/포트폴리오용으로 프로젝트를 개요부터 결론까지 한 번에 설명하기 위한 요약본이다.
> 실험 방법론과 세부 근거의 원본은 `docs/` 아래 문서와 ADR을 따른다. 이 문서는 프로젝트가 진행됨에 따라
> 계속 갱신되며, 아직 실행하지 않은 구간은 `[TODO: ...]`로 표시했다.
>
> **마지막 갱신**: 2026-07-25 · **진행 상태**: Phase 4 (No-Mesh baseline) 완료, Phase 5 진입 대기 · **시작일**: 2026-07-22

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
| 현재까지 확정 산출물 | No-Mesh 3-hop 동기 체인의 usable capacity `C* = 28 RPS` 규명, 절대 부하점 3종(nominal/high/near-saturation) 확정, **정식 baseline 반복측정 완료**(총 38개 유효 run) |
| 커밋 수 | 28+ (2026-07-25 기준) |

**한 줄 성과 예시 (이미 측정된 값)**: No-Mesh 3-hop 동기 체인에서 부하를 28→30 RPS로 **7.1%**만 늘렸는데
p99 지연은 69.1ms→119.0ms로 **72.2%** 급증했다 — 이 임계점을 사전에 규명하지 않고 막연히 "여유 있어 보이는"
부하로 벤치마크했다면 Mesh profile 간 비교 자체가 무의미했을 것이다. (§6.1 참고)

**Phase 4 최종 결과 한 줄 요약**: nominal(8 RPS)/high(17 RPS)/near-saturation(22 RPS) 세 조건에서 각각
15/10/13회의 유효 반복측정을 완료했고, high와 near-saturation은 사전에 정의한 통계적 정밀도 기준을
통과(`STOP_PRECISION_REACHED`)했다. nominal은 15회 상한까지 다 채웠지만 p99 지표 하나가 근소하게
(8.9%) 기준을 넘지 못해 `INCONCLUSIVE_MAX_RUNS`로 명시적으로 결론을 유보했다 — 무리하게 통과시키지
않고 한계를 그대로 기록한 것 자체가 이 프로젝트의 방법론적 원칙이다. (§6.2 참고)

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
| 네트워크/Mesh | Cilium 1.19 (CNI+Gateway+Hubble), MetalLB 0.16 L2, Gateway API 1.4 — 이후 Istio Sidecar/Ambient/Waypoint 추가 예정 |
| 관측성 | Prometheus, Grafana, Loki, Tempo, OpenTelemetry Collector |
| 부하·검증 | k6 (CONSTANT_ARRIVAL_RATE), Python 측정 자동화(`experiments/`, unittest 기반 회귀 테스트) |
| 배포 | Helm (profile별 values 분리), Docker/GHCR 이미지 배포 |

### 4.1 Mesh Profile 4종 (정의 — 실측은 Phase 5~7)

| Profile | 구조 | 상태 |
|---|---|---|
| No Mesh | Client → App A → App B (Cilium만) | ✅ Phase 4 완료 |
| Sidecar | Pod마다 Envoy proxy 동반 | `[TODO: Phase 5]` |
| Ambient | Node 공유 ztunnel (L4) | `[TODO: Phase 6]` |
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
| 5 | Istio Sidecar 기준선 | 🔄 진입 대기 |
| 6 | Ambient 기준선 | `[TODO]` |
| 7 | Ambient + Waypoint 기준선 | `[TODO]` |
| 8 | profile 비교와 병목 선정 | `[TODO]` |
| 9 | 개선안별 단일 변수 실험 | `[TODO]` |
| 10 | 회복탄력성·Chaos 재검증 | `[TODO]` |
| 11 | 최종 의사결정 Matrix·보고서 | `[TODO]` |

### 5.1 Phase 4 세부 체크리스트

- [x] Scenario별 포화점과 목표 부하 확정 (C\*=28 RPS, 3/8/17/22 RPS)
- [x] core 조건 유효 run 최소 10회와 bootstrap CI 정밀도 Gate (§6.2)
- [x] Workload/부하 발생기 자체 병목 판정 (28 RPS에서 node CPU peak 36%, 부하발생기 CPU peak 5% — 자체 병목 아님)
- [x] baseline run ID 승인
- [x] Phase 4 Evidence `measured`

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

`[TODO: Phase 5 이후 발견되는 새로운 엔지니어링 이슈를 계속 추가]`

---

## 8. 남은 계획 (Phase 5~11)

| Phase | 목표 | 진입 조건 |
|---|---|---|
| 5. Sidecar | injection/mTLS 검증, app/proxy 자원 분리, paired 10~15회 반복 | 승인된 No Mesh baseline |
| 6. Ambient | ztunnel 공유 자원 귀속, replica/node 확장 반복 | Phase 5 완료 |
| 7. Waypoint | 전체/선택 경로 분리, L7 기능·통과 성능 측정 | Phase 6 완료 |
| 8. 병목 분석 | profile 간 절대/상대 차이, telemetry 기반 병목 3개 이상 확정 | Phase 5~7 완료 |
| 9. 개선 실험 | 병목별 단일 변수 개선안 3개 이상, before/after 10회+ 반복 | Phase 8 승인 |
| 10. 회복탄력성 | 동일 fault schedule로 before/after 장애 주입 재검증 | Phase 9 반영 |
| 11. 최종화 | 워크로드별 선택 Matrix, 재현성 검증, 최종 보고서 | Phase 10 완료 |

`[TODO: Phase 5 착수 시 Istio 버전, injection 방식, 클러스터 자원 확장 여부 기록]`
`[TODO: Phase 6~7 ztunnel/Waypoint 관련 수치]`
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
| Capacity Discovery Evidence | [docs/evidence/performance/2026-07-23-canonical-chain-capacity.md](docs/evidence/performance/2026-07-23-canonical-chain-capacity.md) |
| No-Mesh Baseline 최종 Evidence | [docs/evidence/performance/2026-07-25-canonical-baseline-final.md](docs/evidence/performance/2026-07-25-canonical-baseline-final.md) |
| 현재 체크포인트 | [docs/CURRENT.md](docs/CURRENT.md) |
| Phase 전체 체크리스트 | [docs/checkpoints/phase-checklists.md](docs/checkpoints/phase-checklists.md) |
| 저장소 | https://github.com/0206pdh/msa-servicemesh |
