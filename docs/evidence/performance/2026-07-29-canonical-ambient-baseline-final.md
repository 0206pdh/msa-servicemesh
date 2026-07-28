# Canonical Istio Ambient baseline — final

- Completed: 2026-07-29 (Asia/Seoul)
- Profile: `AMBIENT` (Istio 1.30.3 ztunnel + istio-cni, no waypoint)
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, fixed hop delay 1 ms
- Load-generator setting: 128 pre-allocated/max VUs for every condition (identical to No-Mesh/Sidecar)
- Absolute RPS reused unchanged from the No-Mesh canonical capacity per ADR-0014
- Policy: [ADR-0014](../../decisions/0014-measurement-repetition-and-load-policy.md),
  [ADR-0023](../../decisions/0023-hybrid-absolute-relative-precision-gate.md),
  [ADR-0025](../../decisions/0025-ambient-mesh-install.md)

## Result

| Condition | Target RPS | Valid runs | Decision | Throughput median | p95 median (95% CI) | p99 median (95% CI) | App CPU-s/req median |
|---|---:|---:|---|---:|---|---|---:|
| nominal | 8 | 10 | `STOP_PRECISION_REACHED` | 8.0006 req/s | 30.08 ms (28.01–33.68) | 39.50 ms (35.34–45.95) | 0.0751 |
| high | 17 | 15 | `INCONCLUSIVE_MAX_RUNS` | 17.0011 req/s | 31.76 ms (28.28–33.90) | 43.15 ms (36.87–56.86) | 0.0439 |
| near-saturation | 22 | 14 | `STOP_PRECISION_REACHED` | 22.0015 req/s | 30.24 ms (27.51–33.45) | 41.08 ms (34.51–50.00) | 0.0375 |

Two of three conditions converged on precision (nominal at 10 runs, near-saturation at 14) — a middle
pattern between No-Mesh (2 of 3 converged, at 10 and 13 runs) and Sidecar (0 of 3 converged). Only `high`
failed to converge, and only on p99.

## Precision gate detail

| Condition | p95 rel / abs (≤5% or ≤5ms) | p99 rel / abs (≤10% or ≤8ms) | App CPU-s/req rel / abs (≤5% or ≤0.01) |
|---|---|---|---|
| nominal | 9.4% / 2.83 ms → **pass (absolute)** | 13.4% / 5.31 ms → **pass (absolute)** | 10.6% / 0.0080 → **pass (absolute)** |
| high | 8.8% / 2.81 ms → **pass (absolute)** | 23.2% / 10.00 ms → **fail (both)** | 14.7% / 0.0065 → **pass (absolute)** |
| near-saturation | 9.8% / 2.97 ms → **pass (absolute)** | 18.9% / 7.75 ms → **pass (absolute)** | 7.0% / 0.0026 → **pass (absolute)** |

`high`'s p99 half-width (10.00 ms) is the widest single miss across all three profiles measured so far —
wider than any No-Mesh metric and only slightly wider than Sidecar's worst p99 miss (11.56 ms, near-saturation).

## ztunnel resource cost — a different kind of number than Sidecar's

Per ADR-0025, ztunnel's CPU/memory is **not** normalized per-request the way the Sidecar's Envoy cost was,
because ztunnel is a single per-node DaemonSet process shared by every ambient-enrolled pod on that node
(all 7 SYNC_CHAIN services plus Kafka), not a dedicated proxy per pod. The number below is the cumulative
CPU-seconds consumed by all ztunnel instances cluster-wide during each run's measurement window — it reflects
the whole enrolled workload's traffic, not just this one experiment's share of it.

| Condition | ztunnel cumulative CPU-s (median, per run window) | ztunnel memory peak (median) |
|---|---:|---:|
| nominal | 82.44 | 16.9 MiB |
| high | 75.72 | 16.7 MiB |
| near-saturation | 72.93 | 16.7 MiB |

Two things stand out. First, ztunnel's memory footprint (≈16–17 MiB) is over an order of magnitude smaller
than the Sidecar Envoy's (≈294–306 MiB per Pod in Phase 5) — consistent with ztunnel's lightweight Rust
implementation and its fundamentally different one-per-node vs. one-per-pod design. Second, ztunnel's CPU
figure here is a **whole-window cumulative total across 3 DaemonSet instances**, not a per-request rate, so
it is not directly comparable to Sidecar's `0.0072–0.0086` core-seconds-per-request figure without first
dividing by both the request count and the number of ztunnel instances actually serving this traffic — that
division was deliberately not done here, because ztunnel's baseline workload-management overhead (mTLS
session bookkeeping, connection tracking for every enrolled pod including idle ones) does not scale linearly
with only this experiment's request rate the way a dedicated per-pod sidecar's does.

No `ZTUNNEL_CPU_THROTTLED` events occurred in any run (query returns no data — see verification note below;
this is expected since ztunnel's chart does not set a CPU limit by default, so there is no CFS quota for it
to be throttled against).

## Preliminary cross-profile comparison

**Non-rigorous, orientation only — Phase 8 owns the formal statistical comparison.** Direct median deltas
against [No-Mesh](2026-07-25-canonical-baseline-final.md) and [Sidecar](2026-07-27-canonical-sidecar-baseline-final.md):

| Condition | No-Mesh p99 → Ambient p99 | Sidecar p99 → Ambient p99 |
|---|---|---|
| nominal | 36.56 → 39.50 ms (+8.0%) | 36.87 → 39.50 ms (+7.1%) |
| high | 30.77 → 43.15 ms (+40.3%) | 37.53 → 43.15 ms (+15.0%) |
| near-saturation | 46.40 → 41.08 ms (−11.5%) | 35.48 → 41.08 ms (+15.8%) |

`high` shows Ambient with the largest p99 increase over No-Mesh of any profile measured so far (+40.3%,
+12.38 ms), and this is also the one condition where Ambient itself failed to converge on p99 precision —
both facts point the same direction, but neither profile's CI is tight enough here to call this a confirmed
difference rather than a real-but-imprecisely-bounded one. `near-saturation`'s negative delta against
No-Mesh repeats the same pattern seen in the Sidecar comparison: both No-Mesh and Ambient's CIs at
near-saturation overlap substantially (No-Mesh 38.80–54.55 ms vs. Ambient 34.51–50.00 ms), so this is not
read as "Ambient is faster than No-Mesh," just as unresolved noise at this load level.

## What broke and what got fixed

Ambient enrollment surfaced two real, previously undiscovered compatibility issues with this cluster's
Cilium (kube-proxy-replacement + VXLAN tunnel routing) — exactly the risk flagged in ADR-0025 before
installing:

1. **kubelet probes hung under ambient capture.** All 7 pods crash-looped at `0/1` after enrollment;
   kubelet's direct `httpGet` probes to the pod IP were being intercepted by istio-cni's traffic redirection
   and never got a response (`context deadline exceeded`), even though the application itself had started
   correctly. Fixed by switching all three probes to `exec: wget --spider http://127.0.0.1:...`, which stays
   on loopback and is not subject to ambient's cross-veth capture. This required no Cilium configuration
   changes and applies to all profiles (harmless for No-Mesh/Sidecar, which never hit this path).
2. **HBONE traffic was silently dropped by NetworkPolicy.** Ambient's actual inter-pod wire protocol is
   ztunnel-to-ztunnel on port 15008 (HBONE), carrying the real destination port inside the tunnel — a
   fundamentally different wire pattern than Sidecar's local iptables `REDIRECT`, which never changes the
   externally-observed port from Cilium's point of view. The existing NetworkPolicies only allowed port
   8080/9092/9093, so `meshperf-default-deny` blocked every ambient-enrolled service-to-service call.
   ztunnel's own error message named the exact cause (`"maybe a NetworkPolicy is blocking HBONE port
   15008"`), which made this fast to diagnose. Fixed by adding port 15008 to every existing app-to-app
   policy, gated behind a new `ambient.enabled` value so No-Mesh/Sidecar policies are unchanged (verified via
   `helm template` port-count diff: 0 occurrences for no-mesh, 14 for ambient).

Both fixes are recorded in commit `b63c386`. Neither required changing Cilium's core routing/kube-proxy
-replacement configuration, so the "stop and ask before touching that" threshold set in ADR-0025 was never
crossed.

## Known limitation: kafka/producer/worker HBONE still times out

Even after the NetworkPolicy fix, `worker-service → kafka-0` connections over HBONE continue to time out
(`ztunnel` reports `ambient.istio.io/redirection: enabled` on `kafka-0`, so it is enrolled, but the
underlying connection never completes). `SYNC_CHAIN` does not exercise this path — it is the same
async/Kafka scope exclusion already established for the Phase 5 readiness gate (commit `4b06f88`) — so it
does not affect this Evidence. It was not investigated further within Phase 6's scope; flagged here in case
Phase 9's async-pipeline work needs Ambient support later.

## Evidence integrity

- `results/phase6-ambient-baseline/state.json`
  - SHA-256 `E2897891CE843A34B5E902FF4E50E9AD0FF0D0D92B5A6656D81AA7F3C2C20E47`
- `results/phase6-ambient-baseline-nominal/repeat-12/summary.json` (final nominal run)
  - SHA-256 `6D2FA3349523B55C854E16486E2768C32310FB8817F3EF2783C920D55FB2047C`
- `results/phase6-ambient-baseline-high/repeat-16/summary.json` (final high run)
  - SHA-256 `40036BE0BA5948443D80F01CA82D07D59FACC1674268C3EE360F70C9000AF8CA`
- `results/phase6-ambient-baseline-near-saturation/repeat-17/summary.json` (final near-saturation run)
  - SHA-256 `B8AFB03FCCD0C7D13485BBF3EE9B35F741F1F87182E3FC5723C38DFDF1828EC2`

Full runner artifacts (including all invalid/failed runs, and the two k6-crash `FAILED` runs from session 1
that motivated the Phase 5 scheduler resilience fix being exercised for real here) remain in the ignored
local `results/` tree and are not rewritten or deleted.

## Limits recorded for downstream (Phase 7+) comparisons

- ztunnel's reported CPU cost is a cluster-wide cumulative total, not a per-request or per-experiment
  figure. Any future Waypoint comparison that wants to isolate "this experiment's share" of shared
  data-plane cost will need new attribution logic, not a reuse of this number as-is.
- `high` is now the condition with the least-precise p99 estimate across all three measured profiles.
  Cross-profile claims at 17 RPS should treat p99 comparisons as the lowest-confidence of the three load
  levels.
- Memory pressure (`NODE_MEMORY_HEADROOM_LOW`, 4 invalid runs total) remains the most common invalidating
  factor with Ambient's control/data-plane processes added, consistent with the prediction recorded in the
  Phase 5 Evidence doc. Phase 7 (Waypoint) adds yet another proxy component per selected route and should
  budget for the same or worse pressure.
- kafka/producer/worker ambient enrollment has a live, unresolved HBONE connectivity issue (see above);
  out of scope for SYNC_CHAIN but a blocker if a future phase needs Ambient + async pipeline together.

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 24 tests passed
- Final scheduler state: `results/phase6-ambient-baseline/state.json` → `status: COMPLETED`
- Source tree clean (non-dirty) for every run contributing to the final statistics
- ztunnel CPU/memory queries verified against live data in a pre-measurement smoke test (2.37 cumulative
  core-seconds, ~11 MB memory over a 90s window) before the formal run began
- `container_cpu_cfs_throttled_periods_total` confirmed absent for ztunnel specifically because its Helm
  chart sets a CPU request with no limit by default (verified: istiod, which does have a limit, shows the
  same metric present with value 0) — not a repeat of the missing-metric bug fixed in commit `20981cc`
