# Canonical Istio Sidecar baseline — final

- Completed: 2026-07-27 (Asia/Seoul)
- Profile: `SIDECAR` (Istio 1.30.3, Helm `istio-base`+`istiod`, PERMISSIVE mTLS mesh-wide)
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, fixed hop delay 1 ms
- Load-generator setting: 128 pre-allocated/max VUs for every condition (identical to No-Mesh)
- Absolute RPS reused unchanged from the No-Mesh canonical capacity per ADR-0014 (no re-discovery for this profile)
- Policy: [ADR-0014](../../decisions/0014-measurement-repetition-and-load-policy.md),
  [ADR-0023](../../decisions/0023-hybrid-absolute-relative-precision-gate.md),
  [ADR-0024](../../decisions/0024-istio-sidecar-install.md)
- Install/verification checkpoint: [phase-05-p1-sidecar-install-and-baseline](../../checkpoints/phase-05-p1-sidecar-install-and-baseline.md)

## Result

| Condition | Target RPS | Valid runs | Decision | Throughput median | p95 median (95% CI) | p99 median (95% CI) | App CPU-s/req median | Sidecar CPU-s/req median |
|---|---:|---:|---|---:|---|---|---:|---:|
| nominal | 8 | 15 | `INCONCLUSIVE_MAX_RUNS` | 8.0006 req/s | 30.08 ms (28.47–31.51) | 36.87 ms (33.92–38.46) | 0.0772 | 0.0086 |
| high | 17 | 15 | `INCONCLUSIVE_MAX_RUNS` | 17.0010 req/s | 29.63 ms (28.04–40.03) | 37.53 ms (32.93–49.29) | 0.0426 | 0.0074 |
| near-saturation | 22 | 15 | `INCONCLUSIVE_MAX_RUNS` | 22.0013 req/s | 28.88 ms (28.17–40.97) | 35.48 ms (33.09–56.20) | 0.0365 | 0.0072 |

All three conditions reached the 15-run cap without satisfying ADR-0023's hybrid precision gate on every
metric, unlike No-Mesh (where high and near-saturation reached `STOP_PRECISION_REACHED` at 10 and 13 runs).
This is a real, recorded outcome under ADR-0014, not a measurement failure — see "Why precision didn't
converge" below for the specific metrics and margins.

## Precision gate detail

| Condition | p95 rel / abs (≤5% or ≤5ms) | p99 rel / abs (≤10% or ≤8ms) | App CPU-s/req rel / abs (≤5% or ≤0.01) |
|---|---|---|---|
| nominal | 5.1% / 1.52 ms → **pass (both, barely)** | 6.2% / 2.27 ms → **pass (both)** | 14.4% / 0.0111 → **fail (both)** |
| high | 20.2% / 6.00 ms → **fail (both)** | 21.8% / 8.18 ms → **fail (both, just over)** | 17.7% / 0.0075 → **pass (absolute)** |
| near-saturation | 22.2% / 6.40 ms → **fail (both)** | 32.6% / 11.56 ms → **fail (both)** | 12.6% / 0.0046 → **pass (absolute)** |

Compare to No-Mesh, where the pattern was the opposite: latency precision converged relatively easily and
CPU/request precision was the harder metric to satisfy. Under Sidecar, `high` and `near-saturation` show
markedly wider latency CIs (p95 half-widths 6.0–6.4 ms vs. No-Mesh's 3.0–3.3 ms at the same RPS), while
CPU/request precision improved. The most direct reading is that Envoy's added CPU/memory management work
is fairly stable run-to-run, but the extra hop through two Envoy proxies (client + server side) per service
call introduces more session-to-session latency variance at this cluster's resource scale, not less.

## Why precision didn't converge

- `NODE_MEMORY_HEADROOM_LOW` was the single most common invalidating factor across all three conditions (5
  invalid runs total: 1 nominal, 1 high, 2 near-saturation, plus 1 more nominal run invalidated by
  `PROXY_CPU_THROTTLED`). This is consistent with the added memory pressure from istiod + 7 Envoy sidecars
  on 2-vCPU/~5.1Gi-allocatable nodes, which was already flagged as a risk in ADR-0024 and observed directly
  in the pre-measurement smoke test (§ phase-05-p1 checkpoint).
- `PROXY_CPU_THROTTLED` fired exactly once (one nominal run), confirming the gate added in commit `8afe58c`
  works against real cluster data — this is the first time this project has directly observed and excluded
  a real Envoy CPU-quota-exhaustion event from statistics, rather than assuming reduced resource requests
  were harmless (see the earlier discussion this addressed: whether ADR-0024's reduced *requests*, with
  *limits* left at Istio defaults, could understate real sidecar cost — this one throttled run shows the
  gate catches it when it does happen, and it happened only once in 51 total attempts across all three
  conditions).
- One `benchmark-gateway` restart (liveness probe timeout under 22 RPS load, session 2) crashed that k6 run
  outright before it could even reach the gate stage; this is recorded as a `FAILED` run
  (`phase5-sidecar-baseline-near-saturation/repeat-07`) and is the incident that motivated the scheduler
  resilience fix in commit `8afe58c`.

## Sidecar resource cost — preliminary cross-profile comparison

**This is a preliminary, non-rigorous comparison for orientation only.** Phase 8 owns the formal
cross-profile statistical comparison (a paired-difference test with combined uncertainty across both
profiles' CIs, which does not exist in the codebase yet). The numbers below are direct differences between
this Evidence's medians and Phase 4's
[final No-Mesh medians](2026-07-25-canonical-baseline-final.md), with no combined-uncertainty correction.

| Condition | No-Mesh p95 → Sidecar p95 | No-Mesh p99 → Sidecar p99 | No-Mesh CPU-s/req → Sidecar app+proxy CPU-s/req |
|---|---|---|---|
| nominal | 28.21 → 30.08 ms (+6.6%) | 36.56 → 36.87 ms (+0.8%) | 0.0787 → 0.0858 (app 0.0772 + proxy 0.0086, +9.0%) |
| high | 25.20 → 29.63 ms (+17.6%) | 30.77 → 37.53 ms (+22.0%) | 0.0443 → 0.0500 (app 0.0426 + proxy 0.0074, +12.9%) |
| near-saturation | 33.79 → 28.88 ms (−14.5%) | 46.40 → 35.48 ms (−23.5%) | 0.0449 → 0.0437 (app 0.0365 + proxy 0.0072, −2.7%) |

The near-saturation latency deltas are negative (Sidecar reading *faster* than No-Mesh), which is not a
credible "Sidecar improves latency" finding — it is far more consistent with the two profiles' confidence
intervals genuinely overlapping. No-Mesh near-saturation p99 CI is 38.80–54.55 ms; Sidecar's is
33.09–56.20 ms. These intervals overlap over nearly their entire range, so this comparison cannot
distinguish a real difference from noise at near-saturation load with the data collected so far.

The `high` condition shows the most consistent signal: both p95 (+17.6%) and p99 (+22.0%) increased, app
CPU stayed flat (−3.8%, within noise), and the added ~0.0074 core-seconds/request of proxy CPU is a real,
directly measured Envoy cost (not a difference-of-medians estimate). Applying the same combined-uncertainty
reasoning used earlier in this project (√(hw₁² + hw₂²) from each profile's own precision-gate half-width)
gives a rough real-difference floor around 5.8 ms for `high` p99 — the observed +6.76 ms delta sits just
above that floor, which is suggestive but not yet a confirmed difference given neither profile fully
converged on this metric. Nominal shows the proxy CPU cost cleanly (+0.0086 core-s/req, directly measured)
but the latency deltas are small enough (+1.87 ms p95, +0.31 ms p99) to be within this cluster's noise floor.

**Conclusion for now: the only claim this Evidence supports directly is the measured proxy CPU/memory
cost itself (≈0.007–0.009 core-seconds/request, ≈294–306 MiB peak memory, consistent across all three
load levels). Any claim about Sidecar's net latency overhead vs. No-Mesh must wait for Phase 8's proper
paired comparison.**

## Evidence integrity

- `results/phase5-sidecar-baseline/state.json`
  - SHA-256 `C3656465987C26E127A9F7AC6005CF55550229F5E67F4CC9E2734D29B2FF8F33`
- `results/phase5-sidecar-baseline-nominal/repeat-17/summary.json` (final nominal run)
  - SHA-256 `C21F50F5DA5D44377E4417FC8BDE229BA786158840AC089E26AC127B73C036B6`
- `results/phase5-sidecar-baseline-high/repeat-16/summary.json` (final high run)
  - SHA-256 `D2208AE94D6CAA0A63CA02CFC7DB2453A8F535912D38AAD366DBBA728D844625`
- `results/phase5-sidecar-baseline-near-saturation/repeat-18/summary.json` (final near-saturation run)
  - SHA-256 `9CA4652879B9B43386B0522826DB9363F8739AE936143F8071BDB9D228B8DCE2`

Full runner artifacts (including all invalid/failed runs) remain in the ignored local `results/` tree and
are not rewritten or deleted.

## Limits recorded for downstream (Phase 6+) comparisons

- Sidecar profile latency precision converged less easily than No-Mesh's did on this cluster; treat
  `high`/`near-saturation` p95/p99 comparisons involving Sidecar as lower-confidence than the equivalent
  No-Mesh numbers, and report the wider CIs alongside any claim.
- The reduced Envoy/istiod resource *requests* from ADR-0024 did not measurably suppress the real proxy CPU
  cost — the one observed `PROXY_CPU_THROTTLED` run was excluded, not silently averaged in — but memory
  headroom was tight enough to invalidate several attempted runs (4 `NODE_MEMORY_HEADROOM_LOW` + 1
  `PROXY_CPU_THROTTLED` + 1 `FAILED` crash out of 51 total attempts). Phase 6 (Ambient) should budget for the
  same or worse memory pressure, since ztunnel + waypoint components add further control/data-plane
  processes to the same nodes.
- No formal No-Mesh vs. Sidecar statistical comparison exists yet; the preliminary deltas above are
  orientation only and must not be cited as a confirmed overhead finding until Phase 8 builds proper
  paired-comparison tooling.

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 24 tests passed
- Final scheduler state: `results/phase5-sidecar-baseline/state.json` → `status: COMPLETED`
- Source tree clean (non-dirty) for every run contributing to the final statistics
