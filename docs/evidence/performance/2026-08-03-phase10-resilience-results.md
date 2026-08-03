# Phase 10 회복탄력성 결과 — Pod kill과 chain-wide delay (ADR-0030)

- Completed: 2026-08-03 (Asia/Seoul); pod-kill 측정 자체는 2026-08-02, chain-delay 측정은
  2026-08-02~03에 걸쳐 완료됨 (둘 다 2026-08-03 정전/클러스터 재구축 **이전**에 완료됨 — 인시던트와
  데이터 유효성은 무관, `docs/CURRENT.md` 참고)
- Scope: [ADR-0030](../../decisions/0030-phase10-resilience-scope.md) — Chaos Mesh 없이 kubectl
  pod kill과 앱 파라미터 기반 chain-wide delay 두 fault만, Ambient profile만
- Profile: Ambient(Istio 1.29.6), SYNC_CHAIN 3-hop, orchestrator-service 1 replica

## 실험 1: Pod kill (orchestrator-service)

### 방법

`experiments/resilience.py`: nominal 8 RPS로 300초 부하를 걸고 120초 지난 시점에
`kubectl delete pod`로 orchestrator-service pod를 강제 종료한다(Deployment가 즉시 재생성).
Prometheus `http_server_requests_seconds_count{uri="/api/v1/workloads/chain"}`의 30초 rate
기반 error-rate 시계열(10초 step)에서 recovery time(kill 시점부터 error rate가 2% 밑으로 떨어져
15초간 유지되는 시점까지)과 fault 중 peak error rate를 계산한다. ADR-0030이 명시한 대로 이 실험은
"20,000-request 정식 정밀도 floor"가 아니라 **directional 특성화**(10회 반복, 정밀도 게이트 없음)다 —
before/after는 각 run의 kill 이전/이후 구간으로 within-run 비교된다.

### 결과 (10/10 valid, `k6ExitCode=0` 전부)

| Metric | median | min | max |
|---|---:|---:|---:|
| recoverySeconds | 39.9 | 29.9 | 39.92 |
| peakErrorRateDuringFault | 59.2% | 37.5% | 73.3% |
| overallErrorRate(run 전체) | 3.65% | 3.58% | 3.71% |

`recoverySeconds`는 10회 중 4회가 ~29.9초, 6회가 ~39.9초로 정확히 10초 간격의 두 값으로만 나뉘었다
(중간값 없음). 이는 recovery 계산이 Prometheus 10초 step 위에서 "2% 밑으로 떨어진 첫 샘플"을 찾는
방식이라 실제 연속적인 복구 시간이 이 10초 격자에 양자화되어 보이는 것으로 판단한다 — 두 개의 서로
다른 복구 메커니즘이 있다는 근거는 없다. 30~40초라는 크기 자체는 이번 재구축 작업 중 실측한
orchestrator-service의 JVM(Java 25, Spring Boot) 콜드스타트 시간(26~28초, "Started ... in 28.222
seconds")과 잘 맞는다 — **recovery time은 사실상 새 Pod의 JVM 시작 시간이 지배적**이라는 해석이
가장 설득력 있다(readiness probe/스케줄링 오버헤드가 나머지 수 초를 더함).

`overallErrorRate`는 420초(warmup 60 + 부하 300 + after 60, 이 중 fault는 recovery 완료까지 최대
~40초)라는 전체 window에 대한 값이라 fault 자체의 심각도보다 훨씬 작게 보인다 — peak error rate(fault
구간 자체)를 대표값으로 써야 한다.

### 해석

Ambient profile에서 orchestrator-service pod kill은 **자동으로 복구된다**(Deployment 재생성 +
Kubernetes 서비스 디스커버리만으로 별도 개입 불필요) — 이는 이 프로젝트가 지금까지 확인한 mesh
profile 선택(Sidecar/Ambient/Waypoint)과 무관한, Kubernetes 자체의 기본 보장이다. Fault 중
peak error rate가 37.5~73.3%로 크다는 것은 이 클러스터의 orchestrator-service가 1 replica이기
때문이다(replica가 여러 개였다면 로드밸런서가 살아있는 replica로 트래픽을 돌려 peak error rate가
훨씬 낮았을 것) — 이 실험은 "replica=1 조건에서 Ambient의 pod-kill 복구가 다른 profile보다 나쁘지
않다"만 확인했을 뿐, "Ambient가 pod-kill에 강하다"는 일반적 결론은 아니다(cross-profile 비교를
하지 않았으므로 — 아래 한계 참고).

## 실험 2: Chain-wide delay (50ms/hop, nominal 8 RPS)

### 방법

`ExperimentSpec.workloadConfig.work.delayMs`를 정상값(1ms)에서 50ms로 올린 별도 spec으로 SYNC_CHAIN
3-hop 전체(orchestrator→workload-a→workload-b→workload-c, 매 hop 각 50ms)에 지연을 주입하고, 이
project의 표준 정밀도 gate(최소 10회, 최대 15회, p95 상대 5%/절대 5ms, p99 상대 10%/절대 8ms,
cpuCoreSecondsPerRequest 상대 5%/절대 0.01 core-s)로 정식 반복측정했다. "before"는 같은 조건(Ambient,
nominal 8 RPS, delayMs=1)의 기존 Phase 6 canonical baseline(`results/phase6-ambient-baseline-nominal`,
10회 `STOP_PRECISION_REACHED`)을 재사용했다.

**알려진 제약: Istio 버전 confound.** Phase 6 baseline은 2026-07-27에 측정되어 Istio 1.30.3 기준이고,
이번 chain-delay 측정은 2026-08-02에 진행되어 Istio 1.29.6(2026-07-30 재설치 이후) 기준이다 —
`manifest.json`의 `createdAt`으로 확인했다. ADR-0028/0029와 같은 종류의 confound이며, 사전에
인지하지 못한 채 진행됐다(이번 Evidence 작성 중 발견). p95/p99 latency 증가분(+160~167ms)은
injected delay(150ms)와 거의 정확히 일치해 버전 차이로 설명하기 어려운 큰 폭이므로 핵심 결론(latency는
비례해서 늘고 errorRate는 0을 유지)은 이 confound에 영향받지 않았을 가능성이 높지만, cpu/network
같은 작은 폭의 지표는 버전 차이의 영향을 배제할 수 없다.

**데이터 무결성 확인**: `state.json`의 `variant` 라벨이 `hop-3-payload-1KiB-delay-1ms`로 잘못
표시되어 있었다(discovery_spec의 variant 이름 생성기가 `hop_delay_ms` 파라미터를 문자열에 반영하지
않는 라벨링 버그) — 실제 적용된 값은 각 run의 `manifest.json`에서 `work.delayMs: 50`으로 직접
확인했다. 측정 자체는 올바른 파라미터로 수행됐고, 이 버그는 표시 라벨에만 있다.

### 결과: 3세션(5블록×3)=15/15 run 완료, `SESSION_COMPLETED`, 11/15 valid

| Metric | before (delay=1ms) | after (delay=50ms) | Diff | 95% CI | Significant |
|---|---:|---:|---:|---|---|
| throughputRps | 8.0006 | 8.0002 | -0.0005 | [-0.0005, -0.0001] | Yes (실질적 의미 없음, 둘 다 목표 8 RPS 달성) |
| p50Ms | 17.05 | 171.91 | +154.86 | — | — |
| p95Ms | 30.08 | 190.78 | **+160.70** | [153.71, 166.23] | **Yes** |
| p99Ms | 39.50 | 206.17 | **+166.67** | [157.46, 177.10] | **Yes** |
| cpuCoreSecondsPerRequest | 0.0751 | 0.1027 | **+0.0275** | [0.0046, 0.0322] | **Yes** |
| memoryPeakBytes | 2,749,843,456 | 2,938,519,552 | +188,676,096 (+6.9%) | [-64.5M, 267.1M] | No |
| networkBytesPerRequest | 21,653 | 21,757 | +103 (+0.5%) | [41, 165] | **Yes**(크기는 미미) |
| errorRate | 0.0 | 0.0 | 0 | — | 둘 다 0(injected error 없음, 순수 latency fault) |

정밀도: p95/p99는 gate를 통과했으나(observedRelative 2.9%/3.7%), **cpuCoreSecondsPerRequest는
15회 상한에도 미수렴**(observedRelative 10.6% vs 기준 5%/0.01) — 이 프로젝트의 다른 phase들에서
반복돼 온 `INCONCLUSIVE_MAX_RUNS`와 같은 패턴이다. 무효 run 5/26(before 1개, after 4개)은 전부
`NODE_MEMORY_HEADROOM_LOW`로, 클러스터 자원 여유가 빠듯한 이 프로젝트의 기존에 문서화된 한계와
일치한다.

### 해석

**Chain 전체에 50ms×3-hop을 주입하면 latency가 예측 가능하게, 에러 없이 늘어난다.** p50 기준
+154.9ms는 순수 injected delay(3×50ms=150ms)와 거의 정확히 일치한다 — 나머지 ~5ms는 스케줄링/네트워크
오버헤드로 설명 가능한 크기다. p95/p99도 같은 방향·비슷한 크기(+160~167ms)로 유의하게 늘었다.
**errorRate는 before/after 둘 다 정확히 0** — 순수 latency 증가만으로는 SYNC_CHAIN의 성공률이
전혀 흔들리지 않았다. 이는 Ambient profile이 hop당 latency 증가라는 스트레스 조건에서도 **연쇄
실패(cascading failure)나 timeout 유발 없이** 안정적으로 요청을 완주시킨다는 뜻이다.

**CPU/request가 유의하게 늘었다(+0.0275 core-s, +36.6%)**: 요청이 hop마다 50ms씩 더 오래 붙잡혀
있으니 스레드/커넥션이 그만큼 더 오래 자원을 점유한 결과로 해석하는 것이 자연스럽다 — mesh
profile(ztunnel/Envoy) 자체의 문제가 아니라 요청 처리 시간이 늘어난 데 따른 당연한 결과다.
network bytes/request는 통계적으로는 유의하지만 크기가 +0.5%로 무시할 만한 수준이며, memory는
유의하지 않았다.

**결론: Ambient는 chain-wide latency 스트레스 아래에서 "성공률을 해치지 않으면서 latency만
비례해서 늘어나는" 예측 가능한 성능 저하(graceful degradation) 패턴을 보였다** — Phase 10의
핵심 질문("정상 상태의 개선이 장애 중 성공률/복구 특성을 악화시키지 않는가")에 긍정적인 답을
주는 방향이다. 다만 이 실험은 Ambient 하나만 측정했으므로 "Sidecar/No-Mesh보다 낫다/못하다"는
cross-profile 결론은 낼 수 없다(ADR-0030에서 사전에 범위를 Ambient로 좁히기로 결정).

## 종합 판단

두 fault(pod kill, chain-wide delay) 모두에서 Ambient profile이 **에러 없이 자동으로 복구되거나
(pod kill) 성공률을 유지한 채 latency만 늘어나는(chain delay)** 패턴을 보였다 — 이번 범위(Ambient만,
두 fault만)에서는 "개선이 장애 대응을 악화시킨다"는 신호를 찾지 못했다. 단, 이는 **Ambient가
다른 profile보다 낫다는 뜻이 아니다** — cross-profile fault 비교를 하지 않았기 때문에, 이 결론은
"Ambient 자체가 이 두 fault 아래에서 病적으로 나쁘게 반응하지는 않는다"는 좁은 범위로만 해석해야
한다.

## Evidence integrity

- pod-kill: `results/phase10-pod-kill-orchestrator/repeat-01~10/result.json` (10/10, `k6ExitCode=0`
  전부)
- chain-delay after: `results/phase10-chain-delay-50ms-nominal/repeat-01~15` (15회 시도, 11 valid,
  `results/phase10-chain-delay-50ms/state.json` 최종 status `SESSION_COMPLETED`)
- chain-delay before(재사용): `results/phase6-ambient-baseline-nominal` (10회 `STOP_PRECISION_REACHED`,
  Phase 6 canonical Evidence와 동일 데이터)
- 비교 산출물: `results/phase10-comparison/nominal-vs-chain-delay-50ms.json` — SHA-256
  `70322ebdc3ae0a41b321b40ad2e8949ddc7ef049f647eb1d7a97c73a1391b5b4`

## Limits recorded for downstream use

- **Network delay/loss, Kafka worker stop/restart, hop 단위로 격리된 fault(`armFault` API)는
  측정하지 않았다** — ADR-0030에서 사전에 범위 밖으로 명시했다. Phase 11 최종 보고서의 한계에도
  반영해야 한다.
- Chain-wide delay는 "hop 하나의 장애"가 아니라 "체인 전체가 동시에 느려질 때"의 시나리오다 — hop
  단위로 격리된 지연의 영향은 이 실험으로 알 수 없다.
- 두 fault 모두 **Ambient profile 하나만** 측정했다 — Sidecar/No-Mesh/Waypoint에서 같은 fault를
  주입했을 때의 결과는 미확인이며, 이번 결과를 다른 profile로 일반화할 수 없다.
- pod-kill은 orchestrator-service replica=1 조건에서만 측정했다 — peak error rate(37.5~73.3%)는
  이 replica 수에 크게 의존적이며, replica가 여러 개인 배포에서는 다르게(더 낮게) 나올 가능성이 높다.
  이 실험은 replica 수의 영향을 분리하지 않았다.
- pod-kill의 recovery time bimodality(29.9초/39.9초)는 측정 방법(10초 Prometheus step 양자화)의
  산물일 가능성이 높다는 것으로 기록했으나, 이를 확정하려면 더 촘촘한 step(예: 5초)으로 재측정해야
  한다 — 하지 않았다.
- chain-delay의 `cpuCoreSecondsPerRequest` 정밀도는 15회 상한에도 미수렴했다(`CONTINUE`) — 이
  지표의 실제 신뢰구간은 표에 보고한 것보다 넓을 수 있다. 다른 지표(p95/p99/errorRate)의 결론에는
  영향 없다.
- chain-delay before(Istio 1.30.3, Phase 6 canonical)/after(Istio 1.29.6, 2026-08-02 측정) 사이에
  ADR-0028/0029와 같은 종류의 Istio 버전 confound가 있다 — 사전에 인지하지 못했고 이번 Evidence
  작성 중 `manifest.json` `createdAt`으로 발견했다. p95/p99의 큰 폭(+160ms대)은 confound로 설명하기
  어렵지만, cpu/network 같은 작은 폭 지표는 버전 차이 영향을 배제할 수 없다. Phase 11 최종 보고서에서
  이 클러스터의 측정 이력 전반에 버전 변경이 있었다는 것을 다시 한번 명시해야 한다(이미 세 번째로
  나온 같은 종류의 confound).

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 43 passed
- pod-kill: 10/10 valid, `k6ExitCode=0` 전부
- chain-delay: 11/15 valid, `SESSION_COMPLETED`(p95/p99 정밀도 충족, cpuCoreSecondsPerRequest 미충족)
