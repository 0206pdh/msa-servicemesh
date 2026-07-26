# Checkpoint — `phase-05-p1-sidecar-install-and-baseline`

- Status: in-progress
- Owner: dohyun
- Started at: 2026-07-25
- Updated at: 2026-07-26
- Branch/commit: main/8afe58c
- Related Phase: [Phase 5](../phases/phase-05-istio-sidecar.md)
- Related contract/ADR: [ADR-0014](../decisions/0014-measurement-repetition-and-load-policy.md), [ADR-0023](../decisions/0023-hybrid-absolute-relative-precision-gate.md), [ADR-0024](../decisions/0024-istio-sidecar-install.md)

## 목표

Istio Sidecar profile을 승인된 No Mesh baseline과 동일한 SYNC_CHAIN 조건(3/8/17/22 RPS)으로 배포·검증하고,
동일한 반복측정 정책(ADR-0014/0023)으로 paired 정식 측정을 완료한다.

## 완료 조건

- [x] Istio 버전/설치 방식/자원 크기 결정 (ADR-0024)
- [x] Helm chart에 sidecar profile 지원 추가 (No Mesh values 영향 없음, 회귀 테스트로 확인)
- [x] istiod 설치와 정상 기동 확인
- [x] 7개 SYNC_CHAIN 서비스 sidecar 주입과 `2/2 Running` 확인 (Kafka는 기존 scope 밖이라 제외)
- [x] 실제 mTLS 적용 확인 (Envoy config dump로 TLS+client cert 필수 직접 확인)
- [x] app/proxy 자원 분리 수집 (istio-proxy 컨테이너 CPU/메모리/throttling 별도 쿼리)
- [x] Proxy CPU throttling 감지 gate 추가와 실제 metric 존재 검증
- [x] 스케줄러가 No Mesh profile/run-id를 그대로 재사용하도록 일반화 (기존 Phase 4 config fingerprint 불변 확인)
- [x] 단일 run 실패가 전체 세션을 중단시키지 않도록 스케줄러 견고성 개선
- [ ] paired core 조건(8/17/22 RPS) 유효 run 최소 10회와 bootstrap CI 정밀도 Gate — **진행 중**
- [ ] Phase 5 Evidence 문서 작성과 checklist 마감

## 변경 근거

- 문제: Phase 5는 No Mesh와 "동일 조건"으로 Sidecar 비용을 비교해야 하는데, 이 클러스터는 노드당 allocatable
  2 vCPU/~5.1Gi 메모리로 Istio 기본 자원 요청값을 그대로 쓰면 스케줄링 여유가 부족할 수 있었다.
- 선택: istiod/Envoy sidecar의 request만 축소하고 limit은 Istio 기본값 유지(ADR-0024) — 실측 CPU/메모리 값이
  인위적으로 눌리지 않도록.
- 대안: `istioctl`의 `demo`/`minimal` profile 사용을 검토했으나 로컬에 `istioctl`이 없고 Helm 기반 배포로
  통일하는 기존 관례와 맞지 않아 기각.
- 예상 trade-off: request를 낮추면 CPU 경합(contention) 시 상대적으로 덜 배정받을 수 있어(cgroup
  cpu.shares), 오버헤드가 과대평가될 여지가 이론상 있다. 8~22 RPS 수준에서는 노드 CPU 여유가 충분해
  경합 자체가 거의 발생하지 않는 것으로 판단했다.

## 변경 범위

- Application: 없음 (애플리케이션 코드 무변경)
- Infrastructure: `istio-base`/`istiod` Helm 설치(cluster), `benchmark` namespace `istio.io/rev=default`
  라벨(수동 설정, chart 비관리), PeerAuthentication 없음(Istio 기본 PERMISSIVE 그대로 사용)
- Contract/Data: `deploy/charts/meshperf` — `sidecar.*` values, 조건부 inject annotation, 조건부
  istiod egress NetworkPolicy. `experiments/` — profile/run-id-prefix 일반화, sidecar 자원 쿼리, throttle gate.
- Out of scope: Ambient/Waypoint(Phase 6/7), Istio ingress gateway(비교 경로 아님, network-and-mesh.md 참고)

## 검증 기록

| 검증 | 명령/방법 | 결과 | Evidence |
|---|---|---|---|
| unit | `python -m unittest discover -s experiments -p 'test_*.py'` | 24 passed | 커밋 `8afe58c` |
| 회귀 | No Mesh formal_spec() fingerprint 재계산 후 기존 manifest와 대조 | 동일 (3f24a3bd.../eb8cc074.../bb11467b...) | `test_formal_spec_no_mesh_fingerprint_is_stable` |
| Helm lint | `helm lint meshperf-check/meshperf -f {no-mesh,sidecar}-values.yaml` | 둘 다 0 failed | 수동 실행 로그 |
| Helm render | `helm template ... \| grep NetworkPolicy/inject` | no-mesh: 11 NP·주입 없음 / sidecar: 12 NP(istiod-egress 추가)·주입 7개 | 수동 실행 로그 |
| E2E | Cilium Gateway → benchmark-gateway → 3-hop chain, X-Correlation-Id 포함 | HTTP 200, `completedHops:3` | 수동 curl |
| mTLS | orchestrator-service `istio-proxy` Envoy `config_dump`의 virtualInbound:8080 filter chain | `transport_protocol=tls`, `require_client_certificate=true` (raw_buffer fallback 없음) | 수동 config_dump 캡처 |
| 관측성 회귀 | Prometheus `up{namespace="benchmark"}` 카운트 | STRICT 적용 중 6/7 실패 → PERMISSIVE 복귀 후 7/7 정상 | 수동 쿼리 로그 |
| 스모크 | 8 RPS, warm-up 10s/측정 30s 단발 실행 | sidecar CPU/메모리/throttling 정상 수집, 무효 요인 없음(dirty-tree 제외) | `results/phase5-sidecar-smoke`(정리됨, 문서에만 값 보존) |

## 실패와 판단

- 실패 내용: STRICT `PeerAuthentication` 적용 후 Prometheus가 6/7 서비스를 스크레이프하지 못함(`up=0`).
- 원인: Prometheus는 mesh 구성원이 아니라 평문 클라이언트인데, gateway 포트(8080)가 STRICT라 mTLS
  핸드셰이크 없이는 연결이 거부됨. 앱 API와 actuator/metrics가 같은 포트를 공유해 포트 단위로만 예외를
  줄 수 있는 Istio의 제약과 충돌.
- 해결: 네임스페이스 전체를 Istio 기본값인 PERMISSIVE로 되돌림. 서비스 간 트래픽은 여전히 자동으로
  mTLS를 사용하고(Envoy config_dump로 확인), 비-mesh 클라이언트(Prometheus)는 평문 fallback으로 정상
  동작한다. 프로덕션에서도 표준적인 패턴이라 이 선택이 비현실적인 완화가 아니라고 판단했다.
- 실패 내용 2: `container_cpu_cfs_throttled_seconds_total` 쿼리가 항상 `null`을 반환.
- 원인: 이 클러스터 cAdvisor 버전은 해당 metric을 노출하지 않음(모든 컨테이너에서 전역적으로 부재
  확인). `container_cpu_cfs_throttled_periods_total`만 존재.
- 해결: 쿼리·gate·summary 필드·analysis 추출을 전부 `*ThrottledPeriods`로 변경, 실제 데이터가 반환되는
  것을 스모크 테스트로 재확인.
- 실패 내용 3: 22 RPS(near-saturation) 정식 측정 중 `benchmark-gateway`가 liveness probe 타임아웃으로
  재시작, k6가 오류율 임계치(1%)를 초과해 exit code 99로 비정상 종료 → 처리되지 않은 예외가 스케줄러
  전체 프로세스를 죽임.
- 원인: (a) Sidecar profile은 같은 절대 RPS에서 No Mesh보다 여유가 적을 수 있다는 것 자체가 유의미한
  신호(비교 결과의 일부일 수 있음). (b) 스케줄러가 단일 run 실패를 흡수하지 못하는 구조적 결함.
- 해결: (a)는 원인 조사 없이 그대로 보존(무효 run으로 기록)하고 재시도. (b)는 `execute_session()`에
  try/except를 추가해 실패를 `FAILED` run으로 기록하고 다음 조건으로 계속 진행하도록 수정(`8afe58c`).

## 다음 재개 지점

- 첫 작업: `results/phase5-sidecar-baseline/state.json`을 읽고 조건별 `decision`이 모두 `CONTINUE`가
  아닐 때까지 session을 이어서 실행한다 (`--run-id-prefix phase5-sidecar-baseline --profile SIDECAR`).
- 필요한 파일: `MESHPERF_KUBECONFIG`, `MESHPERF_HUBBLE` 환경변수, `experiments/baseline.py`.
- 주의할 상태/환경: 정식 run은 git 소스 트리가 dirty하면 자동 무효 처리된다(`DIRTY_SOURCE_TREE`). 코드
  수정은 다음 run이 warm-up 단계일 때 커밋해 낭비를 줄인다.
- 완료 후: Evidence 문서(`docs/evidence/performance/`)를 작성하고 `docs/CURRENT.md`, `phase-checklists.md`,
  `PORTFOLIO.md`를 Phase 4 종료 때와 동일한 방식으로 갱신한 뒤 Phase 6(Ambient)에 착수한다.
