# Phase 9 개선 실험 1 — Sidecar mTLS DISABLE (ADR-0028)

- Completed: 2026-07-30 (Asia/Seoul)
- Scope: [ADR-0028](../../decisions/0028-phase9-sidecar-mtls-disable-experiment.md)
- Hypothesis under test: "Phase 8에서 확인된 Sidecar의 network bytes/request ~49% 증가(No-Mesh 대비)의 주된
  원인은 Envoy가 붙이는 mTLS 핸드셰이크/레코드 오버헤드다."
- Independent 변수: `PeerAuthentication.spec.mtls.mode` — PERMISSIVE(mesh 기본값) vs DISABLE
- 조건: nominal(8 RPS) 하나, SYNC_CHAIN 3-hop, payload 1 KiB, hop delay 1 ms
- 반복: 정식 10~15회, bootstrap 95% CI 정밀도 게이트(ADR-0023) — DISABLE 측은 **10회 만에
  `STOP_PRECISION_REACHED`**로 수렴(참고: 기존 Phase 5 PERMISSIVE canonical 측정은 같은 조건에서 15회
  상한까지도 `INCONCLUSIVE_MAX_RUNS`였다 — 이번 DISABLE 측정이 더 빨리 수렴한 것 자체도 하나의 관찰이다)

## 알려진 제약: Istio 버전 confound (의도적으로 수용)

Phase 5의 canonical Sidecar nominal baseline(PERMISSIVE, `results/phase5-sidecar-baseline-nominal`, 15회
`INCONCLUSIVE_MAX_RUNS`)은 **Istio 1.30.3**에서 측정됐다. 이번 DISABLE 측정 시점에는 Phase 7 Waypoint
버전 재시도 과정에서 클러스터가 **Istio 1.29.6**으로 완전히 재설치된 상태였다(`kubectl get deployment istiod
-o jsonpath='{.metadata.labels.app.kubernetes.io/version}'`로 확인). 즉 아래 비교는 엄밀히는 "mTLS 모드
하나만 다른" 단일 변수 비교가 아니라 **Istio 1.30.3+PERMISSIVE vs Istio 1.29.6+DISABLE**이라는, 두 변수가
동시에 다른 비교다.

같은 버전(1.29.6)의 PERMISSIVE 대조군을 새로 측정해 이 confound를 제거하는 방안을 시작했으나, 측정에
추가로 몇 시간이 더 걸리는 것과 mTLS 자체가 두 Istio minor 버전 사이에서 근본적으로 다르게 동작할
가능성은 낮다는 점을 감안해 **버전 차이는 무시하고 기존 Phase 5 데이터를 그대로 "before"로 사용하기로
의도적으로 결정**했다. 아래 결과, 특히 latency 관련 결과는 이 확인되지 않은 가정 위에 있다는 점을
명시한다.

## Result

| Metric | PERMISSIVE (1.30.3, before) | DISABLE (1.29.6, after) | Diff (after−before) | 95% CI | Significant |
|---|---:|---:|---:|---|---|
| throughputRps | 8.0006 (n=15) | 8.0006 (n=10) | +0.0000 | [-0.0003, 0.0000] | No |
| p95Ms | 30.08 ms | 42.51 ms | **+12.43 ms** | [10.80, 15.40] | **Yes** |
| p99Ms | 36.87 ms | 55.78 ms | **+18.91 ms** | [15.39, 25.89] | **Yes** |
| cpuCoreSecondsPerRequest (app) | 0.0772 | 0.0858 | +0.0086 | [-0.0012, 0.0223] | No |
| memoryPeakBytes (app) | 2,631,483,392 B | 2,589,124,608 B | -42,358,784 B | [-334,983,168, 107,925,504] | No |
| networkBytesPerRequest | 31,859.19 B | 31,517.57 B | **-341.63 B** | [-445.82, -95.74] | **Yes** |

## Reading the result: hypothesis rejected, and an unexpected latency signal

**Hypothesis 1 is rejected.** Disabling mTLS reduced network bytes/request by only ~341 bytes (~1.1% of
Sidecar's own baseline), while Phase 8 found Sidecar's *total* overhead over No-Mesh at this same nominal
condition to be **+10,469 bytes** (~49%). Even taking the DISABLE reduction at face value, mTLS accounts for
at most ~3.3% (341/10,469) of Sidecar's network-bytes overhead over No-Mesh. **The other ~97% comes from
something other than mTLS encryption itself** — most likely Envoy's own HTTP/2 framing, the extra
envoy-to-envoy hop indirection, or connection/stream metadata overhead that exists regardless of whether the
payload is encrypted. This is a genuine negative result for the hypothesis ADR-0028 set out to test, and is
preserved as such rather than reframed as a success.

**An unexpected, statistically significant latency change appeared: DISABLE is *slower*, not faster.** p95 is
12.4ms higher and p99 is 18.9ms higher with mTLS disabled — the opposite of the naive expectation that
removing encryption overhead would reduce latency. Given the Istio-version confound accepted above, **this
cannot be attributed to mTLS mode with confidence** — it may just as easily be an Istio 1.30.3-vs-1.29.6
behavioral difference (e.g., connection pooling, HTTP/2 defaults, Envoy version bump) that has nothing to do
with mTLS. This is flagged as an open, unconfirmed observation, not a claim that "disabling mTLS makes Sidecar
slower" — that claim would require the same-version control that was intentionally not run here.

**App-level CPU and memory are unaffected**, consistent with every other cross-profile comparison in this
project (Phase 8, §6.7): mesh configuration changes at the proxy layer don't measurably change the
application container's own resource cost.

## Evidence integrity

- `results/phase9-comparison/nominal-permissive-vs-mtls-disabled.json` — SHA-256
  `6f140e4078546fec1a53b82ea26acfa4e19e3caa2518abe4e220963b118fc1d8`
- DISABLE measurement: `results/phase9-sidecar-mtls-disabled-nominal/repeat-{02..11}` (10 valid runs,
  `repeat-01` is a `FAILED` run from an unrelated process interruption during setup, correctly excluded)
- PERMISSIVE (before) measurement: `results/phase5-sidecar-baseline-nominal` (existing Phase 5 canonical
  Evidence, 15 valid runs, `INCONCLUSIVE_MAX_RUNS`)
- Mesh mode verified at the wire level before measuring: `istioctl proxy-config listener` on the
  orchestrator-service sidecar showed no `tlsContext`/`transportSocket` on the inbound listener under
  DISABLE, confirming plaintext operation (not just the PeerAuthentication CR being present)

## Limits recorded for downstream use

- **The Istio-version confound (1.30.3 before vs 1.29.6 after) was accepted deliberately, not overlooked.**
  Any claim from this experiment about latency must carry this caveat; the network-bytes finding is less
  sensitive to this concern since a ~97%-attributed-elsewhere result would hold even if the small remaining
  ~3% shifted somewhat under a clean same-version comparison.
- This experiment used a single load condition (nominal, 8 RPS) — not re-verified at high/near-saturation.
- mTLS DISABLE is a diagnostic setting, not a production recommendation; this Evidence explains *where
  overhead comes from*, not *what to configure*.

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 33 passed
- DISABLE measurement: 10/10 valid runs `COMPLETED`, zero `invalidatingFactors`
