# Phase 8 — cross-profile statistical comparison (No-Mesh vs Sidecar vs Ambient)

- Completed: 2026-07-30 (Asia/Seoul)
- Scope: formal comparison across the three canonical baselines already measured in Phase 4 (No-Mesh),
  Phase 5 (Sidecar), Phase 6 (Ambient). Waypoint is excluded — Phase 7 is final `blocked`
  (`docs/checkpoints/phase-07-p1-waypoint-blocked.md`).
- Tool: `experiments/compare_profiles.py` (new), backed by a `collect_valid_runs()` helper factored out of
  `experiments/analysis.py` so both the precision-gate scheduler and this comparison tool read the exact
  same COMPLETED/fingerprint-filtered run set.

## Method

Each profile's canonical baseline was measured as an independent repeated-measurement session (10-15 runs,
its own bootstrap precision gate — see the Phase 4/5/6 Evidence docs). Runs across profiles are **not**
index-matched (Sidecar's run 3 has no correspondence to Ambient's run 3), so a literal paired-difference test
is not meaningful here. Instead, for each metric and each load condition, this tool takes the raw per-run
values from both profiles' valid-run sets and computes an **independent two-sample bootstrap** (10,000
resamples per group, resampled separately, 95% CI on `median(profile B) - median(profile A)`). A difference
is only reported as significant when the CI excludes zero — everything else is `확인된 차이 없음`
(no confirmed difference), consistent with this project's existing precision-gate ethos of not overclaiming
from a small run count.

One directory required pinning `required_fingerprint` explicitly:
`results/phase4-chain-baseline-near-saturation/repeat-04` carries an older pre-128-VU config fingerprint
(already flagged `SUPERSEDED_CONFIG_FINGERPRINT` in the Phase 4 canonical Evidence) and was excluded by
fingerprint, matching the same 13-run set the Phase 4 Evidence itself certifies.

Metrics compared: `throughputRps`, `p95Ms`, `p99Ms`, `cpuCoreSecondsPerRequest` (application container only —
excludes `istio-proxy`/`istio-init`, see `kubernetes.py`'s `application_resource` query),
`memoryPeakBytes` (application only), `networkBytesPerRequest` (application only).

## Result — significant differences only (CI excludes zero)

| Condition | Comparison | Metric | Median A | Median B | Diff (B−A) | 95% CI | Read |
|---|---|---:|---:|---:|---:|---|---|
| nominal (8 RPS) | No-Mesh vs Sidecar | networkBytesPerRequest | 21,390 B | 31,859 B | +10,469 B | [10,446, 10,526] | Sidecar adds ~49% more bytes/request |
| nominal (8 RPS) | No-Mesh vs Sidecar | memoryPeakBytes | 2.883 GB | 2.631 GB | −251 MB | [−299M, −6.1M] | unexplained, see Limits |
| nominal (8 RPS) | Sidecar vs Ambient | networkBytesPerRequest | 31,859 B | 21,653 B | −10,206 B | [−10,274, −10,175] | Ambient ~32% lighter than Sidecar |
| nominal (8 RPS) | No-Mesh vs Ambient | networkBytesPerRequest | 21,390 B | 21,653 B | +263 B | [219, 300] | tiny (~1.2%) vs Sidecar's 49% |
| high (17 RPS) | No-Mesh vs Sidecar | throughputRps | 17.0013 | 17.0010 | −0.0003 | [−0.0006, −0.0000] | statistically real, practically negligible |
| high (17 RPS) | No-Mesh vs Sidecar | networkBytesPerRequest | 21,566 B | 32,746 B | +11,180 B | [11,119, 11,219] | same pattern as nominal |
| high (17 RPS) | No-Mesh vs Ambient | **p95Ms** | 25.20 ms | 31.76 ms | **+6.56 ms** | [1.66, 11.73] | only significant latency finding |
| high (17 RPS) | No-Mesh vs Ambient | **p99Ms** | 30.77 ms | 43.15 ms | **+12.38 ms** | [3.73, 19.94] | Ambient slower at this one load point |
| high (17 RPS) | No-Mesh vs Ambient | networkBytesPerRequest | 21,566 B | 22,031 B | +466 B | [286, 509] | small, consistent with nominal |
| high (17 RPS) | Sidecar vs Ambient | networkBytesPerRequest | 32,746 B | 22,031 B | −10,714 B | [−10,842, −10,667] | same pattern as nominal |
| near-saturation (22 RPS) | No-Mesh vs Sidecar | networkBytesPerRequest | 22,475 B | 34,004 B | +11,529 B | [11,403, 11,660] | same pattern, 3rd load level |
| near-saturation (22 RPS) | No-Mesh vs Ambient | networkBytesPerRequest | 22,475 B | 22,830 B | +355 B | [265, 413] | same pattern, 3rd load level |
| near-saturation (22 RPS) | Sidecar vs Ambient | networkBytesPerRequest | 34,004 B | 22,830 B | −11,174 B | [−11,320, −11,075] | same pattern, 3rd load level |

Every other cell across all 9 profile-pair × condition comparisons (27 metric checks not listed above) had a
CI that crossed zero — reported as **no confirmed difference**, not as "no effect"; see Limits.

## Reading the two clean signals

**Network bytes per request is the strongest, most consistent finding in this dataset.** Across all three
load conditions, Sidecar's per-request network footprint is ~10,200–11,500 bytes larger than both No-Mesh
and Ambient — a **~49% increase over No-Mesh**, remarkably stable across 8/17/22 RPS. Ambient's own increase
over No-Mesh is real (CI excludes zero in all three conditions) but two orders of magnitude smaller in
absolute terms (~260–470 bytes, ~1–2%). This is the clearest quantitative evidence in the project so far for
*why* Sidecar is architecturally heavier than Ambient at the wire level: every hop through a Sidecar's Envoy
adds full mTLS handshake/record overhead and HTTP/2 framing on a per-pod basis, whereas Ambient's HBONE
tunnel (per-node, connection-reused) amortizes that cost far more efficiently. This is consistent with (and
gives a concrete mechanism for) the Sidecar-vs-Ambient architecture described throughout Phase 5/6.

**Latency shows only one significant difference in 9 comparisons, and it does not replicate at the next load
level.** Ambient's p95/p99 are significantly higher than No-Mesh's at the high (17 RPS) condition, but the
same comparison at near-saturation (22 RPS) shows Ambient nominally *faster* than No-Mesh (median diff
−3.55 ms) with a CI that comfortably crosses zero. A real bottleneck effect should not reverse direction as
load increases further — the more likely explanation is that this single high-condition result is one
significant draw out of many tests (27 metric checks total across this analysis), and this cluster's own
established latency floor (~5 ms p95 / ~8 ms p99, from Phase 4's own limits notes) makes any single-condition
significant result worth treating cautiously rather than as a confirmed "Ambient is slower" claim. It is,
however, directionally consistent with the replica-scaling study's finding (§6.6 in PORTFOLIO.md) that
Ambient/ztunnel latency degrades as scale increases — both point at the same candidate mechanism (ztunnel's
per-workload/per-connection bookkeeping cost) without either one being a confirmed, standalone result on its
own.

**Application-level CPU-per-request shows no confirmed difference anywhere** (all 9 comparisons). This is a
meaningful negative result: none of the three profiles measurably changes how much CPU the *application
container itself* spends per request. Combined with the network-bytes finding, this narrows the mesh
overhead story to the proxy/wire layer (already measured directly in Phase 5/6 as sidecar CPU-seconds and
ztunnel CPU-seconds) rather than any spillover into the application process itself.

## Candidate bottleneck hypotheses for Phase 9

1. **Sidecar's per-hop mTLS + HTTP/2 framing is the dominant network-overhead mechanism.** Supported by a
   large, consistent (~49%), highly significant effect across all three load conditions. A concrete
   improvement candidate: measure whether HTTP/1.1 (no framing overhead) or reduced cipher suite negotiation
   changes this gap.
2. **ztunnel's shared per-node proxy may become a latency bottleneck under sustained load, but this is not
   yet confirmed.** One significant instance (high condition, this doc) plus one directional-only instance
   (replica-scaling study, §6.6) point the same direction but neither alone is conclusive — needs a dedicated
   Phase 9 experiment (more reps, a wider load sweep) before it can be treated as a confirmed cost.
3. **Mesh overhead on this workload manifests at the proxy/network layer, not the application layer.** Zero
   of 9 `cpuCoreSecondsPerRequest` comparisons were significant. Any Phase 9 optimization work should target
   proxy configuration (mTLS cipher/handshake reuse, connection pooling) rather than application-level
   tuning, since the application itself shows no measurable mesh-induced cost.

## Time-axis correlation — attempted, found infeasible retroactively

The remaining Phase 8 checklist item ("시간축 metric/trace/resource 상관 분석") called for correlating
metric/trace/resource timelines against the latency/network findings above. Attempting this surfaced two
independent reasons it cannot be done retroactively for the Phase 4-7 canonical runs (2026-07-23 to 2026-07-29):

1. **The observability stack's own retention is 24h by design**, not the 15-day default assumed: `kubectl get
   prometheus -o jsonpath='{.spec.retention}'` returns `24h` / `retentionSize: 2GB`, and Loki/Tempo carry the
   same `retention_period: 24h` / `block_retention: 24h`. Direct queries confirm data older than ~24-48h no
   longer exists (`up{namespace="benchmark"}` at 48h/72h/120h/168h-ago timestamps all return zero series,
   while 1h/6h/12h/24h-ago all return data). This was an intentional resource-conservation choice for the
   3-VM cluster (`docs/decisions/0011-delivery-and-observability-baseline.md`) but its exact `24h` value was
   not previously written down anywhere in the project's own limits notes.
2. **Even within the retention window, the Runner never captured genuine time-series per run.** Every run's
   `raw/prometheus-window.json` — the only telemetry artifact the Runner persists per run — is a whole-window
   scalar/vector snapshot (via `increase()`/`max_over_time()`-style instant queries over the full run
   duration), not a `query_range` time series. So even a live Prometheus instance with unlimited retention
   could not answer "did CPU spike specifically during the P99 latency spike sub-interval" for any
   already-completed run; that resolution was never recorded in the first place.

**Decision:** this checklist item is closed as infeasible-retroactively rather than left open indefinitely.
No fabricated or reconstructed correlation is reported. Going forward, any Phase 9 experiment that needs true
time-axis correlation must either analyze telemetry within the 24h window right after the run, or the Runner
would need a `query_range` capture added to `kubernetes.py`'s window snapshot step — noted as a backlog item
for Phase 9 experiment design, not implemented speculatively here.

## Limits recorded for downstream (Phase 9+) use

- **"No confirmed difference" is not "no difference."** With 10-15 runs per profile and this cluster's own
  established noise floor (~5 ms p95 / ~8 ms p99, per Phase 4's limits section), a true difference smaller
  than that floor would not be detectable by this method. Absence of significance in 27 of 36 checks reflects
  the limits of this sample size, not proof of equivalence.
- **Multiple-comparison risk was not corrected for.** 36 metric checks were run at a nominal 95% CI each;
  with no Bonferroni/FDR correction, roughly 1-2 false positives are statistically expected by chance alone
  at this count. The single significant high-condition latency finding (and the throughput micro-difference)
  should be read with this in mind — it is exactly the kind of isolated result that this concern predicts.
- **`memoryPeakBytes`'s one significant result (No-Mesh higher than Sidecar, nominal condition) has no
  identified causal mechanism.** Sidecar injection has no known reason to reduce the *application* process's
  own memory footprint (the proxy's memory is tracked separately in `sidecarMemoryPeakBytes`, not folded into
  this number). Treated as an unexplained result, not a mesh-cost claim, pending further investigation.
- This comparison uses **application-only** resource figures; the already-measured proxy-specific costs
  (Sidecar CPU 0.0072–0.0086 core-s/req, ~294–306 MiB peak; ztunnel 72.9–82.4 core-s/run-window absolute,
  ~16.7–16.9 MiB peak) are documented separately in the Phase 5/6 Evidence docs and are not re-derived here.
- Waypoint is excluded entirely (Phase 7 final blocked) — this analysis cannot speak to L7 proxy overhead,
  only L4 Sidecar vs L4 Ambient.

## Evidence integrity

All 9 comparison artifacts (SHA-256, generated by `experiments/compare_profiles.py`, ignored local `results/`
tree):

- `results/phase8-comparison/nominal-no-mesh-vs-sidecar.json` — `be867e5d6afb92ccfb36c7e8d51c970f61459332cb7e605ca13e37efcd97d02c`
- `results/phase8-comparison/nominal-no-mesh-vs-ambient.json` — `d2da53c16ffd1be69bb66aec4bb9dea86408675e828f854e70128e2a43337f5b`
- `results/phase8-comparison/nominal-sidecar-vs-ambient.json` — `57c45c1b6bafa3be12b633793394d8891d68a91045a3a885516537fb3c5986ba`
- `results/phase8-comparison/high-no-mesh-vs-sidecar.json` — `5fbacdf54ef483cf48cd36adaba8bd1e28f7fa2a2e64a1922e531bc8bfe72cb8`
- `results/phase8-comparison/high-no-mesh-vs-ambient.json` — `79625e8ca79f45793d310d6d1a9f229f54b35ad817ef9eb5059847f5ba52bd58`
- `results/phase8-comparison/high-sidecar-vs-ambient.json` — `253b94fbc78ac848f89a50ca612ff023d4994b2cdf891deaaee7a2976fedf6ac`
- `results/phase8-comparison/near-saturation-no-mesh-vs-sidecar.json` — `edb01a3c22f58af8cba194625f929a7859ee7b52e6b45f7e1ea7fcfecad713b5`
- `results/phase8-comparison/near-saturation-no-mesh-vs-ambient.json` — `da61600a566305f81a563978b718962755cdc9231f6f7ed40aa0cc17cb0b406b`
- `results/phase8-comparison/near-saturation-sidecar-vs-ambient.json` — `29838338267c473e0431e7e8151216a148da395917326c5904e9726548b25440`

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 31 passed (4 new tests for
  `compare_profiles.py`, plus a non-behavior-changing refactor of `analysis.analyze()` into
  `collect_valid_runs()` + `analyze()`, verified against all pre-existing `test_analysis.py` cases)
- Source condition directories unchanged (read-only comparison, no new experiment runs)
