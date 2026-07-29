# Replica-scaling cost study (directional) — Sidecar vs Ambient

- Completed: 2026-07-29 (Asia/Seoul)
- Scope: [ADR-0027](../../decisions/0027-replica-scaling-study-scope.md) — directional confirmation only,
  **not** a formal 10–15-rep statistical baseline
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, hop delay 1 ms, nominal load only (8 RPS)
- Scaled service: `orchestrator-service` at 1 / 2 / 4 replicas (all other services fixed at 1 replica)
- Reps per point: 3, warm-up 60s / measurement 180s (capacity-discovery-level window, not the 20,000-request
  formal floor)
- Hypothesis under test (project hypothesis 1): "Sidecar's per-pod cost and Ambient's per-node shared cost
  scale differently as pod count grows."

## Result

| Profile | Replicas | p95 median (ms) | p99 median (ms) | Proxy CPU-s (absolute, whole run window) | Proxy memory peak |
|---|---:|---:|---:|---:|---:|
| Sidecar | 1 | 42.92 | 67.73 | 10.71 | 120.1 MiB |
| Sidecar | 2 | 40.22 | 51.94 | 9.96 | 138.3 MiB |
| Sidecar | 4 | 36.95 | 58.06 | 10.03 | 173.0 MiB |
| Ambient | 1 | 34.34 | 51.01 | 10.26 | 15.8 MiB |
| Ambient | 2 | 44.31 | 67.93 | 11.04 | 15.9 MiB |
| Ambient | 4 | 68.42 | 99.52 | 13.53 | 16.1 MiB |

"Proxy CPU-s" is the **whole-window absolute total**, not per-request or per-pod: for Sidecar it is the sum
of every Envoy sidecar's CPU-seconds across all 7 SYNC_CHAIN services in the `benchmark` namespace (not just
`orchestrator-service`'s own replicas — see Limits below); for Ambient it is the cluster-wide ztunnel total
per ADR-0025's existing definition. All 18 runs (2 profiles × 3 replica counts × 3 reps) completed with zero
errors and no invalidating factors.

## Reading the two costs separately

**Memory is the clean, unambiguous signal.** Sidecar's total proxy memory grows from 120.1 → 173.0 MiB
(+44%) as `orchestrator-service` goes from 1 to 4 replicas — each additional replica brings its own Envoy
process with its own baseline memory footprint, so total memory scales with pod count almost exactly as the
project's Sidecar mental model predicts. Ambient's ztunnel memory stays essentially flat (15.8 → 16.1 MiB,
+2%) across the same replica range — strong, direct confirmation that ztunnel's memory cost is a per-node
property, not a per-app-pod one.

**CPU is more nuanced than "flat vs linear."** Sidecar's aggregate CPU-seconds barely moves (10.71 → 9.96 →
10.03) — expected, since total request volume is fixed (8 RPS × 180s ≈ 1,440 requests regardless of replica
count) and load-balancing the same volume across more Envoy instances doesn't increase total proxying work
much. Ambient's ztunnel CPU, however, **increases by 32%** (10.26 → 13.53) over the same range, even though
ztunnel is architecturally one-per-node, not one-per-pod. The most likely explanation is that ztunnel's
per-workload bookkeeping (mTLS certificate issuance/rotation, connection identity tracking for each new pod)
has a real, non-zero marginal cost per enrolled workload — "shared per node" does not mean "free to add more
enrolled pods to that node."

**Latency shows the most interesting — and least certain — divergence.** Sidecar's p95 modestly *improves*
with more replicas (42.9 → 40.2 → 37.0 ms), consistent with load-balancing reducing per-instance queueing.
Ambient's latency *worsens* substantially over the same range (p95 34.3 → 44.3 → 68.4 ms; p99 51.0 → 67.9 →
99.5 ms — nearly double from 1 to 4 replicas). This is the most direct signal in this dataset resembling
project hypothesis 2 ("a mesh proxy can become a bottleneck as the workload it serves scales up"), except it
shows up on ztunnel (Ambient's L4 component) rather than a Waypoint (L7 component, unmeasurable this phase
per the Phase 7 blocker). **This latency divergence is based on only 3 reps per point with no bootstrap CI
and must be read as directional, not confirmed** — but the direction is consistent (monotonic across all
three replica counts) and large enough (nearly 2x) that it is a strong candidate for the Phase 9 improvement
backlog to investigate formally.

## Evidence integrity

- `results/phase8-replica-scaling-sidecar-r1/repeat-03/summary.json` — SHA-256 `5D4D5407DF7928DB030F0AF08755AE20FB8948AAC06E564955C26E56E7439370`
- `results/phase8-replica-scaling-sidecar-r2/repeat-03/summary.json` — SHA-256 `9F62AAEADE3710FC9AA82D601DE7AE0637E8153B2233032E65FD4B210AB7E849`
- `results/phase8-replica-scaling-sidecar-r4/repeat-03/summary.json` — SHA-256 `00C23B308084956742E5FB07A790A5E7567C4C9817CB32D0EE29F8F479EA9825`
- `results/phase8-replica-scaling-ambient-r1/repeat-03/summary.json` — SHA-256 `9823C5A26C3B670E9817A6050C3F816385C02ED4EBB23181F07D9046CEC1BF5E`
- `results/phase8-replica-scaling-ambient-r2/repeat-03/summary.json` — SHA-256 `0BC87D9E359CE43B27C7D0C6B82FA1FB59FF6EF4AACA04B901612F27EEC336E5`
- `results/phase8-replica-scaling-ambient-r4/repeat-03/summary.json` — SHA-256 `773AE0F8BC2F3CAD84C95925D9A4BF85CCEC8F74A5D7FA4925955619282EB411`

All 18 run artifacts (raw + summary) are preserved in the ignored local `results/` tree.

## Limits recorded for downstream (Phase 8+) use

- The Sidecar proxy CPU/memory figures are **whole-mesh totals** (all 7 services' sidecars), not
  `orchestrator-service`-specific. Since only `orchestrator-service` scales while the other 6 services stay
  at 1 replica, the ~6-replica baseline dilutes the marginal signal from `orchestrator-service`'s own
  scaling. Memory's clear upward trend is still attributable to the scaled service (the other 6 are
  constant), but a more precise per-service breakdown would need per-pod (not per-namespace) Prometheus
  queries, which this directional study did not implement.
- Only one service was scaled, one load level (nominal) was tested, and only 3 reps per point were
  collected — no bootstrap CI, no precision gate. Treat every number here as directional evidence for
  Phase 8, not a citable confidence interval on par with the Phase 4–6 canonical baselines.
- This study reuses the No-Mesh-derived nominal RPS (8) but does not re-verify capacity at each replica
  count — it is possible that at 4 replicas the system has more headroom than at 1, which is not exercised
  here since load was held constant by design.

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 27 tests passed
- All 18 runs: `status: COMPLETED`, `invalidatingFactors: []`
- Source tree clean (non-dirty) for every contributing run
