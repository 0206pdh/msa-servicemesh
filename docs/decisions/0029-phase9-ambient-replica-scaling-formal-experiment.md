# ADR-0029: Phase 9 개선 실험 2 — Ambient replica 확장 latency 저하 정식 확인

- 상태: accepted
- 날짜: 2026-07-30

## Context

ADR-0027의 replica 확장 방향성 연구(`docs/evidence/performance/2026-07-29-replica-scaling-directional-study.md`)는
orchestrator-service replica가 1→4로 늘 때 Ambient(ztunnel)의 p99 latency가 51.0ms→99.5ms로 거의 2배
나빠지는 것을 관찰했다. 다만 이 연구는 지점당 **3회 반복, bootstrap CI 없음**으로 명시적으로 범위를
축소한 방향성 확인용이었다(ADR-0027). Phase 8 cross-profile 비교(§6.7)에서도 high 조건 단일 비교에서
Ambient가 No-Mesh보다 유의하게 느리다는 결과가 한 번 나왔지만 다음 부하 단계에서 재현되지 않아 "확정 아님"
으로 남아있다. 두 결과 모두 같은 방향(ztunnel이 부하/replica 증가에 취약할 수 있다)을 가리키지만, 어느
쪽도 Phase 4~6 수준의 정식 반복측정으로 확인된 적이 없다.

Phase 9는 "병목별 단일 변수 개선안 최소 10회 반복" 검증을 요구한다. ztunnel latency 저하는 아직 "개선"이
아니라 "확인"이 필요한 가설이므로, 이번 실험의 목표는 최적화 자체가 아니라 **이 가설이 정식 반복측정에서도
살아남는지**를 확인하는 것이다.

## Decision

### 실험 설계

- 독립 변수: `orchestrator-service`의 replica 수 — 1 vs 4 (ADR-0027의 세 지점 중 효과가 가장 뚜렷했던
  양극단만 사용, 중간값인 2는 생략).
- 고정: Ambient profile, nominal(8 RPS) 부하 하나, SYNC_CHAIN 3-hop, 다른 6개 서비스는 전부 1 replica.
- 반복: 정식 10~15회, bootstrap 95% CI 정밀도 게이트(ADR-0023) — ADR-0027과 달리 이번엔 **정식 20,000
  request 최소 기준과 전체 duration(nominal 기준 2,525초/rep)을 그대로 적용**한다.
- **replica=1 데이터는 재사용, replica=4만 신규 측정**: Phase 6의 canonical Ambient nominal baseline
  (`results/phase6-ambient-baseline-nominal`, 10회 `STOP_PRECISION_REACHED`, orchestrator-service 1
  replica 고정)을 "before(replica=1)"로 그대로 사용한다. replica=4만 새로 정식 반복측정한다. 이렇게 하면
  전체 소요 시간이 약 절반으로 줄어든다.
- **Istio 버전 confound가 다시 존재함을 명시**: Phase 6 canonical(재사용, replica=1)은 Istio 1.30.3에서
  측정됐고, replica=4 신규 측정은 현재 클러스터(1.29.6)에서 진행된다. ADR-0028에서 사용자가 승인한 것과
  동일한 방식으로 **이 버전 차이는 감수하고 진행**한다 — 두 실험 모두 "버전보다 훨씬 큰 효과 크기(2배
  가까운 latency 차이)를 검증하는 것이 목적이므로 작은 버전 차이가 결론을 뒤집을 가능성은 낮다"는 판단을
  Phase 8/9 전체에 일관되게 적용한다.
- Fingerprint 격리: `run_id_prefix="phase9-ambient-replica4"`, `extra_spec_fields={"meshVariant":
  "replica-4-scaling-formal"}`, `expectedScrapeTargets=10`(고정 6개 서비스 + orchestrator-service 4
  replica) — `experiments/capacity.py`/`baseline.py`에 `expected_scrape_targets` 파라미터를 새로 추가해
  지원한다(기본값 7 유지, 기존 fingerprint 전부 불변 확인됨).
- 비교 방법: `experiments/compare_profiles.py`의 독립 2-표본 bootstrap 차이 검정. 지표는 p95Ms/p99Ms(핵심
  가설)에 더해 `ztunnelCpuCoreSecondsAbsolute`/`ztunnelMemoryPeakBytes`(ADR-0027이 발견한 부차 신호:
  ztunnel 메모리는 거의 불변, CPU는 32% 증가)도 포함한다.

## Alternatives

- **replica 1/2/4 세 지점 전부 정식 반복**: 통계적으로 더 촘촘하지만 소요 시간이 3배로 늘어난다. 이미
  ADR-0027에서 세 지점 모두 같은 방향으로 단조 증가함을 확인했으므로, 정식 확인은 효과가 가장 큰 양극단만
  으로 충분하다고 판단해 기각.
- **replica=1도 새로 측정(완전한 same-version 비교)**: 버전 confound를 완전히 제거할 수 있지만 소요
  시간이 두 배가 된다. ADR-0028에서 이미 사용자가 승인한 "버전 차이 감수" 원칙을 일관되게 적용해 기각.
- **nominal 대신 high/near-saturation도 확인**: Phase 8에서 Ambient의 유일한 유의미한 latency 차이가
  high 조건에서 나왔던 것을 감안하면 매력적이지만, 이미 시간이 많이 든 프로젝트에서 범위를 계속 넓히는
  것은 비합리적이라고 판단해 기각. nominal 하나로 방향성이 확인되면 그 자체로 충분한 결론이다.

## Consequences

- 이 실험이 ADR-0027의 방향성 관찰을 정식으로 확인하면: ztunnel의 replica-scaling latency 저하는 이
  프로젝트에서 신뢰구간을 갖춘 확정 결론이 되고, Ambient 채택 시 "replica 수가 많은 서비스에는 주의가
  필요하다"는 구체적인 운영 가이드가 된다.
- 확인되지 않으면: ADR-0027의 3회 반복 관찰은 우연이었거나 표본 부족에 의한 것으로 재평가하고, Phase 9
  결론에서 이 가설을 기각된 것으로 기록한다.

## Validation and rollback

- replica=4 배포 후 모든 Pod가 `Running`/`Ready`인지, `expectedScrapeTargets=10`이 실제로 충족되는지
  확인한다.
- 측정 종료 후 `kubectl scale deployment orchestrator-service --replicas=1`로 즉시 원복하고 SYNC_CHAIN
  E2E를 재확인한다.
- 클러스터 메모리 헤드룸이 4 replica에서도 `NODE_MEMORY_HEADROOM_LOW`를 상시로 유발하지 않는지 확인한다
  (ADR-0027에서 이미 3회 반복 기준으로는 문제없었음을 확인했으나, 정식 20,000-request 반복은 더 오래
  지속되므로 재확인한다).
