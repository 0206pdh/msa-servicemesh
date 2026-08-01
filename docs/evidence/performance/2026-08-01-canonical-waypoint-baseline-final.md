# Phase 7 — 정식 Ambient + Waypoint Baseline (최종)

- Completed: 2026-08-01 (Asia/Seoul)
- Scope: [ADR-0026](../../decisions/0026-waypoint-deployment-scope.md) — 선택 경로(orchestrator-service
  단일 hop) Waypoint. 연결 문제 해결 경위는
  [phase-07-p1-waypoint-blocked 체크포인트](../../checkpoints/phase-07-p1-waypoint-blocked.md)
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, hop delay 1 ms
- 조건: nominal(8 RPS)/high(17 RPS)/near-saturation(22 RPS), Phase 4~6과 동일한 canonical 조건
- Istio 1.29.6, Cilium 1.19.6, orchestrator-service 1 replica (다른 6개 서비스도 1 replica 고정)
- 반복: 정식 10~15회, bootstrap 95% CI 정밀도 게이트(ADR-0023)

## Result — 정밀도 게이트

| 조건 | 유효 반복 | 결정 | p95 median (CI) | p99 median (CI) |
|---|---:|---|---|---|
| nominal | 15 | `INCONCLUSIVE_MAX_RUNS` | 36.36 ms (32.49–42.46) | 49.08 ms (42.55–77.43) |
| high | 15 | `INCONCLUSIVE_MAX_RUNS` | 45.18 ms (33.04–58.61) | 73.37 ms (45.44–92.49) |
| near-saturation | 15 | `INCONCLUSIVE_MAX_RUNS` | 32.91 ms (31.06–37.50) | 45.92 ms (42.68–82.21) |

세 조건 모두 15회 상한까지도 latency 정밀도 기준에 수렴하지 못했다 — Sidecar가 세 조건 모두
`INCONCLUSIVE_MAX_RUNS`였던 것과 같은 패턴이다(Sidecar/Waypoint 둘 다 Envoy 기반 L7 처리가 개입해
run-to-run 변동성이 No-Mesh/Ambient보다 크다는 정황적 근거). `cpuCoreSecondsPerRequest`(app)는 세 조건
모두 정밀도를 통과했다.

무효화 사유는 세 조건 모두 거의 전부 `NODE_MEMORY_HEADROOM_LOW`였다 — Ambient 위에 Waypoint 프록시가
추가로 얹히면서 이 3-VM 클러스터의 메모리 여유가 Sidecar/Ambient 때보다 더 빠듯해졌다(무효율 약
30~45%). VM 자체의 메모리 할당은 이 프로젝트의 다른 모든 canonical 측정과 동일하게 유지했다 — 하드웨어
조건을 바꾸면 지금까지의 비교가 무효가 되므로, 무효 처리는 그대로 두고 반복 횟수만 늘려 극복했다.

## Waypoint 자체 자원 (request당 정규화, Sidecar와 동일 모델 — ADR-0026)

| 조건 | Waypoint CPU-s/req (median) | Waypoint 메모리 peak (median) |
|---|---:|---:|
| nominal | 0.0016 | 45.55 MB |
| high | 0.0016 | 45.17 MB |
| near-saturation | 0.0014 | 44.97 MB |

Waypoint는 단일 서비스(orchestrator-service)만 경유하므로 ztunnel처럼 클러스터 전체에 걸쳐 공유되는
비용이 아니라, Sidecar처럼 Pod 하나에 직접 귀속되는 비용이다. 이번이 이 프로젝트에서 Waypoint 자원이
처음으로 실측된 것이다(이전까지는 `resources.waypoint`가 항상 `null`이었다 — 2026-07-30 Runner 개선으로
해결).

## Cross-profile 비교 — Waypoint vs No-Mesh/Sidecar/Ambient

Phase 8과 동일한 독립 2-표본 bootstrap 차이 검정(`experiments/compare_profiles.py`)을 재사용했다.

### Network bytes/request — 가장 깔끔한 신호

| 조건 | No-Mesh | Ambient | Waypoint | Sidecar |
|---|---:|---:|---:|---:|
| nominal | 21,390 B | 21,653 B | **24,891 B** | 31,859 B |
| high | 21,566 B | 22,031 B | **25,378 B** | 32,746 B |
| near-saturation | 22,475 B | 22,830 B | **26,454 B** | 34,004 B |

**Waypoint는 세 조건 모두에서 정확히 Ambient와 Sidecar 사이에 위치하며, No-Mesh 대비 ~16~18% 증가로
Ambient(~1~2%)보다는 확실히 무겁지만 Sidecar(~49%)보다는 가볍다.** 9개 비교(3조건 × 3profile쌍) 전부
유의했다. 이는 Waypoint의 아키텍처(ztunnel/HBONE 위에 L7 Envoy 홉을 하나 추가)와 정확히 일치하는
결과다 — Ambient의 가벼운 L4 기반 위에 L7 처리 비용이 얹히지만, Sidecar처럼 모든 hop마다 전용 프록시가
붙는 것보다는 여전히 가볍다.

### Latency — 부하 조건에 따라 나타났다 사라지는 패턴

| 비교 | nominal | high | near-saturation |
|---|---|---|---|
| Waypoint vs No-Mesh (p95) | **+8.16ms 유의** | **+19.98ms 유의** | -0.88ms 유의하지 않음 |
| Waypoint vs No-Mesh (p99) | +12.52ms 유의하지 않음 | **+42.60ms 유의** | -0.47ms 유의하지 않음 |
| Waypoint vs Sidecar (p95/p99) | **둘 다 유의(+6.29/+12.21ms)** | **둘 다 유의(+15.55/+35.84ms)** | 둘 다 유의하지 않음 |
| Waypoint vs Ambient (p95/p99) | **둘 다 유의(+6.28/+9.58ms)** | **둘 다 유의(+13.42/+30.22ms)** | 둘 다 유의하지 않음 |

**nominal과 high 조건에서는 Waypoint가 세 profile 모두보다 일관되게 느리지만, near-saturation에서는 그
차이가 통계적으로 사라진다.** 이 패턴은 Phase 8에서 봤던 "한 조건에서만 유의하고 다음 조건에서
재현되지 않는" 단발성 신호와는 다르다 — 여기서는 **두 개의 서로 다른 부하 조건(nominal, high)에서
같은 방향으로 재현**됐고, 세 가지 다른 baseline(No-Mesh/Sidecar/Ambient) 전부와 비교해도 같은 패턴이
나온다. 다만 near-saturation에서 사라지는 이유는 알 수 없다 — near-saturation 자체의 CI가 세 조건 중
가장 넓어서(p99 42.68–82.21ms) 정밀도 부족으로 실제 차이를 못 잡아낸 것일 수도 있고, 22 RPS 근처에서
Waypoint의 상대적 오버헤드가 실제로 옅어지는 것일 수도 있다 — 이 데이터만으로는 구분할 수 없다.

### App CPU-per-request — high 조건에서만 유의, 나머지는 차이 없음

Waypoint vs No-Mesh는 high 조건에서만 유의(+0.0162 core-s/req, ~37% 증가), nominal/near-saturation은
유의하지 않음. Waypoint vs Sidecar도 high 조건에서만 유의. Waypoint vs Ambient는 세 조건 모두 유의하지
않음. Memory는 9개 비교 전부 유의하지 않음 — Phase 8과 마찬가지로 mesh 구성 변경이 애플리케이션 자체의
메모리에는 영향을 주지 않는다는 패턴이 Waypoint에도 그대로 이어진다.

## Evidence integrity

- Canonical run 디렉터리: `results/phase7-waypoint-baseline-{nominal,high,near-saturation}` (각 15개
  유효 run)
- 비교 산출물(SHA-256): `results/phase7-comparison/`
  - `nominal-no-mesh-vs-waypoint.json` — `d1c2706520dff442f7f5b9c4d4d20e6e3b4187ea2b01d20ab7bda960192b09af`
  - `nominal-sidecar-vs-waypoint.json` — `abee496cd0c1a111ee427dfcff2343ead536997e76ba07e036eacdfc571c1dcb`
  - `nominal-ambient-vs-waypoint.json` — `ec1d9fdca54ec423a012465467e58cb7b8793f4b3eb28e87a8d2d9c84408eaa7`
  - `high-no-mesh-vs-waypoint.json` — `37bdfa68b68921cd695fca9f10b507b194ec51db6e1d1b94f0f72e51847ab3de`
  - `high-sidecar-vs-waypoint.json` — `d388101588d20ab6279767f9681fb06a87c02071cad5a80786851105778f8eb9`
  - `high-ambient-vs-waypoint.json` — `7ba6e0e2c562f22fcf2e539f52eeb274497de1976b8c7574c627216ed1cfaaf2`
  - `near-saturation-no-mesh-vs-waypoint.json` — `de1f3ac83f7c4210150bfe5432571b5da7cd0f06065673078ccd38bfbe1cbfa2`
  - `near-saturation-sidecar-vs-waypoint.json` — `014064d76e1478aef3bc128be92d40ab145ab37ae37c8bcc4244c3c9ca769b2a`
  - `near-saturation-ambient-vs-waypoint.json` — `b7bb5f7e4a9c5c233cd3aef91a9e9bb6fcc449ddbb119362bf7b33e246aec32a`
- `near-saturation`의 No-Mesh 쪽 비교는 Phase 4 canonical Evidence가 이미 지정한 fingerprint
  (`bb11467b...`)로 고정해 `repeat-04`(pre-128-VU superseded config)를 제외했다 — Phase 8과 동일한 처리.

## Limits recorded for downstream use

- 이 Evidence는 orchestrator-service 단일 hop 선택 경로 구성이다. 5개 서비스 전부 Waypoint 경유하는
  "전체 경로" 구성은 측정하지 않았다(ADR-0026에서 처음부터 범위 밖으로 명시).
- 세 조건 모두 latency가 15회 상한까지 수렴하지 않아 CI가 상대적으로 넓다 — Sidecar와 같은 수준의 한계다.
- near-saturation에서 latency 차이가 사라지는 정확한 메커니즘은 규명하지 못했다(정밀도 부족 vs 실제
  현상 구분 불가) — Phase 9 후속 실험 후보로 남긴다.
- Waypoint 자체 자원(CPU/메모리)은 이번이 첫 실측이라 다른 profile들처럼 여러 phase에 걸친 재현성 확인은
  아직 없다.

## Verification

- `python -m unittest discover -s experiments -p 'test_*.py'`: 36 passed
- 전체 45개 run(3 조건 × 15회) `status: COMPLETED`, `invalidatingFactors: []`
- 배포 검증: 20/20, 50/50 연속 성공(측정 시작 전 사전 검증), Waypoint `rq_total` 실측 증가 확인
  (phase-07-p1-waypoint-blocked 체크포인트 참고)
