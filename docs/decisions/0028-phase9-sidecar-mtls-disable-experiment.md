# ADR-0028: Phase 9 개선 실험 1 — Sidecar mTLS DISABLE 단일 변수 실험

- 상태: accepted
- 날짜: 2026-07-30

## Context

Phase 8 통계 비교(`docs/evidence/performance/2026-07-30-phase8-cross-profile-comparison.md`)에서 가장 강한
단일 신호는 network bytes/request였다: Sidecar는 세 부하 조건(8/17/22 RPS) 모두에서 No-Mesh 대비 요청당
네트워크 바이트가 일관되게 ~49% 증가했다(9/9 비교 전부 고신뢰 유의). 이 결과로부터 나온 첫 번째 개선
가설은 "Envoy 사이드카가 매 hop마다 붙이는 mTLS 핸드셰이크/레코드 오버헤드가 이 증가분의 주 원인"이라는
것이다.

이 가설을 가장 직접적으로 검증하는 단일 변수 실험은 mTLS를 끄고(다른 모든 조건은 고정) 같은 조건에서
다시 측정해 network bytes/request가 실제로 줄어드는지 보는 것이다. mTLS를 끄면 Envoy는 여전히 프록시로
동작하지만(HTTP/2 프레이밍, 라우팅 등은 그대로) 암호화 핸드셰이크와 레코드 오버헤드만 사라지므로, 이 실험은
"mTLS가 원인의 전부인지, 아니면 일부인지"를 구분해준다.

## Decision

### 실험 설계

- 독립 변수: `PeerAuthentication.spec.mtls.mode` — `PERMISSIVE`(Phase 5 canonical, 이미 측정됨) vs
  `DISABLE`(이번 신규 측정).
- 고정: 다른 모든 조건은 Phase 5 canonical Sidecar baseline과 동일 — Istio 1.30.3, 동일 리소스 설정,
  동일 워크로드(SYNC_CHAIN 3-hop, payload 1 KiB, hop delay 1 ms).
- 부하 조건: **nominal(8 RPS) 하나만** 측정한다. Phase 8의 가장 강한 신호가 세 조건 모두에서 동일한
  방향/크기로 나타났으므로(§6.7), 세 조건을 반복 검증할 한계효용이 낮다고 판단해 범위를 좁힌다. high/
  near-saturation은 이 실험에서 확인하지 않는다.
- 반복 횟수: Phase 4~6과 동일한 정식 기준(10~15회, bootstrap 95% CI 정밀도 게이트, ADR-0023)을 그대로
  적용한다 — 이 실험은 방향성 확인이 아니라 Phase 9가 요구하는 "before/after paired 최소 10회" 정식
  검증이다.
- Helm/차트 변경: `deploy/charts/meshperf/templates/peerauthentication.yaml` 신규 — `values.sidecar.mtlsMode`
  가 설정된 경우에만 `PeerAuthentication` 리소스를 생성한다(기본값 빈 문자열 → 리소스 없음 → 기존 Phase
  5/6 배포와 완전히 동일한 동작, 회귀 없음). `deploy/environments/sidecar-mtls-disabled/values.yaml` 신규
  오버레이(`mtlsMode: DISABLE`).
- Fingerprint 격리: `experiments/baseline.py`의 `formal_spec()`에 `extra_spec_fields` 파라미터를 추가해
  spec에 `meshVariant: "mtls-disabled"`를 병합한다. `canonical(spec)`이 dict 전체를 해시하므로 이 필드
  하나만으로 기존 Phase 5 Sidecar canonical fingerprint와 이번 실험의 fingerprint가 완전히 분리된다 —
  `run_id_prefix`도 `phase9-sidecar-mtls-disabled`로 별도 지정해 결과 디렉터리 자체도 분리한다.
- 비교 방법: 기존 Phase 5 Sidecar nominal 15회 데이터(`results/phase5-sidecar-baseline-nominal`)를
  "before(PERMISSIVE)", 신규 측정을 "after(DISABLE)"로 놓고 `experiments/compare_profiles.py`의 독립
  2-표본 bootstrap 차이 검정을 그대로 재사용한다.

## Alternatives

- **STRICT ↔ DISABLE 비교**: STRICT는 이 클러스터에서 Prometheus 스크레이프를 깨뜨린 이력이 있어(Phase 5
  기록) 다시 시도하지 않는다. 기각.
- **모든 프로필/모든 부하 조건에서 반복**: 통계적으로 더 견고하지만 정식 반복 1회당 8 RPS 기준 약 42분
  (2,525초)이 걸려 15회면 10시간 이상 소요된다. 세 조건 모두 반복하면 프로젝트 일정상 비합리적으로
  커진다. Phase 8에서 이미 세 조건 모두 같은 방향/크기의 결과를 확인했으므로 기각.
- **mTLS cipher suite만 바꾸는 미세 조정**: Istio/Envoy 설정에서 세밀한 cipher 조정은 이 클러스터의
  Istio 버전에서 지원 범위가 불확실하고, "mTLS 자체가 원인인가"라는 더 근본적인 질문에 먼저 답하는 것이
  우선순위가 높다고 판단해 이번 실험에서는 제외한다(향후 후속 실험 후보로 기록).

## Consequences

- 이 실험 결과로 network bytes/request 감소가 확인되면: "Sidecar 오버헤드의 상당 부분은 mTLS"라는
  구체적 근거가 생기고, 실제 운영에서 mTLS를 켤지 끌지의 trade-off(보안 vs 비용)를 정량적으로 설명할 수
  있게 된다.
- 감소가 확인되지 않으면: 오버헤드의 주 원인이 mTLS가 아니라 HTTP/2 프레이밍이나 다른 Envoy 처리 단계임을
  시사하며, 이는 그 자체로 유효한 "실패한 개선 가설" Evidence로 보존한다(Phase 9 요구사항).
- mTLS DISABLE은 프로덕션에서 권장되는 설정이 아니므로, 이 실험 결과를 "이렇게 설정하라"는 권고가 아니라
  "오버헤드의 원인 분해"라는 진단 목적으로만 서술한다.

## Amendment (2026-07-30): Istio-version confound caught before drawing conclusions

The first DISABLE measurement (10 valid runs, `STOP_PRECISION_REACHED`) was compared against the existing
Phase 5 canonical Sidecar nominal baseline as "before." Before reporting the result, a version check
(`kubectl get deployment istiod -o jsonpath='{.metadata.labels.app.kubernetes.io/version}'`) found the
cluster is now running **Istio 1.29.6**, not the 1.30.3 Phase 5 was measured on — because Istio was
completely reinstalled at 1.29.6 during the Phase 7 Waypoint version-retry, after Phase 5's data had already
been collected. This ADR's own "고정" section assumed identical Istio version and explicitly said so, but
that assumption silently broke without anyone re-checking it, so the planned single-variable experiment
(mTLS mode only) had actually become a two-variable one (mTLS mode **and** Istio version) without being
caught until this point.

**Fix attempted, then deliberately abandoned:** a same-version control (`phase9-sidecar-1296-permissive-control`,
Sidecar PERMISSIVE on Istio 1.29.6, same nominal condition and precision gate) was started to isolate mTLS
mode as the only variable. On explicit user instruction, this control run was stopped before completion —
the decision was to accept the version confound rather than spend several more hours re-measuring, since the
version difference (1.30.3 vs 1.29.6) was judged unlikely to change the qualitative conclusion. The result is
reported in `docs/evidence/performance/2026-07-30-phase9-mtls-disable-experiment.md` using the original
**1.30.3 PERMISSIVE vs 1.29.6 DISABLE** comparison, with the confound stated explicitly rather than hidden —
network-bytes conclusions are treated as robust to this gap, latency conclusions are explicitly not.

## Validation and rollback

- `PeerAuthentication` 적용 후 `istioctl authn tls-check` 또는 Envoy config dump로 실제 plaintext 연결이
  되는지 확인한다.
- 측정 종료 후 `helm upgrade meshperf ... -f deploy/environments/sidecar/values.yaml`로 즉시 PERMISSIVE로
  복귀하고 SYNC_CHAIN E2E를 재확인한다 — `mtlsMode: ""` 오버레이 적용 시 `peerauthentication.yaml`이 조건부
  템플릿이므로 리소스가 자동으로 제거된다.
- Prometheus 스크레이프가 STRICT 때처럼 깨지지 않는지 확인한다(DISABLE은 STRICT보다 위험도가 낮지만,
  실측으로 재확인한다).
