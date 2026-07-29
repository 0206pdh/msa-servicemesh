# ADR-0026: Waypoint 배포 범위와 자원 모델

- 상태: accepted
- 날짜: 2026-07-29

## Context

Phase 7은 Ambient 위에 선택적으로 배치하는 Waypoint proxy의 비용과 기능을 측정해야 한다. Istio 1.30.3은
`PILOT_ENABLE_AMBIENT=true`가 켜지면 `istio-waypoint` GatewayClass(`istio.io/mesh-controller`)를 자동
생성한다 — 별도 Helm chart 설치가 필요 없고, `gatewayClassName: istio-waypoint`인 `Gateway` 리소스를
만들면 istiod가 실제 Waypoint Deployment/Pod를 자동으로 프로비저닝한다.

Waypoint는 Sidecar(Pod당 1개)나 ztunnel(노드당 1개)과 또 다른 배포 단위다 — Waypoint 1개가 `istio.io/
use-waypoint` 라벨로 지정된 임의 개수의 서비스 계정(service account)의 L7 트래픽을 처리할 수 있다. 즉
"몇 개 서비스가 이 Waypoint를 쓰는가"에 따라 공유 정도가 달라진다.

이 클러스터는 이미 istiod + ztunnel(3개) + istio-cni(3개)가 떠 있고 worker 노드 메모리 요청이 29~53%
수준이라, Waypoint 전체 경로(5개 서비스 전부) 적용은 추가 자원 압박이 클 것으로 예상된다.

## Decision

### 배치 범위: 선택 경로(단일 hop) 우선, 전체 경로는 범위 축소

Phase 문서(`docs/phases/phase-07-waypoint.md`)는 "전체 경로와 선택 경로 profile을 분리"하도록 요구한다.
자원과 시간 제약을 고려해 **이번 Phase 7 정식 측정은 선택 경로(orchestrator-service 단일 hop)에만
Waypoint를 적용하는 구성으로 한정**한다. orchestrator-service는 SYNC_CHAIN에서 gateway로부터 요청을
받아 workload-a로 전달하는 중간 hop으로, L7 정책 삽입 지점으로 대표성이 있다.

전체 경로(5개 서비스 모두 Waypoint 경유) 측정은 이번 Phase 7 정식 Evidence에서 제외하고 별도 TODO로
남긴다 — Phase 6의 replica/node 확장 측정을 미완료로 명시한 것과 같은 원칙이다(가설 검증에 필요하지만
지금 범위에는 없음을 숨기지 않는다).

### 자원 크기

istiod chart의 waypoint 기본값(요청 100m CPU/128Mi 메모리, 제한 2 CPU/1Gi 메모리)은
`_internal_defaults_do_not_set` 아래에 있다 — Istio가 명시적으로 "직접 오버라이드하지 말라"고 이름 붙인
경로다. ADR-0024/0025와 달리 이번에는 강제로 축소하지 않고 **기본값을 그대로 사용**한다. 배포 시점 기준
worker 노드 헤드룸(CPU 43%, 메모리 31% 사용)이 이 기본 요청값을 충분히 수용하는 것을 실측으로 확인했다.

### 자원 귀속 모델

이번 Waypoint는 단일 서비스(orchestrator-service)만 사용하므로 Sidecar와 유사하게 **Pod(Waypoint
Deployment) 단위로 직접 귀속**할 수 있다 — ztunnel처럼 여러 워크로드가 공유하는 모델이 아니다. `resources.
waypoint` 슬롯에 request당 정규화한 CPU-seconds/메모리를 기록한다(Sidecar와 같은 계산 방식).

## Alternatives

- **전체 경로(5개 서비스) 동시 측정**: 가설 5("선택적 Waypoint와 telemetry sampling은 필요한 기능을
  유지하며 비용을 줄일 수 있다")를 더 완전히 검증하지만, 자원 압박과 측정 시간이 크게 늘어난다. 이번
  Phase 7에서는 기각하고 범위를 선택 경로로 좁힌다.
- **Waypoint 없이 Ambient만으로 L7 기능 부재를 문서만으로 기록**: 실측 없이 "L7 기능이 없다"고만 적으면
  Waypoint 추가 시 실제 비용을 알 수 없다. 최소 1개 hop이라도 실측하는 쪽을 선택했다.

## Consequences

- Phase 7 Evidence는 "orchestrator-service만 Waypoint 경유" 구성 결과이며, "5개 서비스 전부 Waypoint
  경유" 결과와 혼동하지 않도록 명시한다.
- `experiments/runner/kubernetes.py`에 waypoint 자원 쿼리(Pod 이름 패턴으로 특정, request당 정규화)를
  추가한다.
- 전체 경로 측정은 이 프로젝트의 알려진 잔여 작업 목록에 남는다.

## Validation and rollback

- Waypoint Gateway 생성 후 `kubectl get gateway`와 자동 생성된 Deployment가 `Ready`인지 확인한다.
- orchestrator-service로 가는 실제 트래픽이 Waypoint를 경유하는지 Waypoint Pod의 access log로 직접
  확인한 뒤에만 정식 측정을 시작한다(Sidecar/Ambient 때와 동일한 검증 기준).
