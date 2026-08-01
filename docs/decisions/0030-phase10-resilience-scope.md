# ADR-0030: Phase 10 회복탄력성 실험 범위와 도구 선택

- 상태: accepted
- 날짜: 2026-08-01

## Context

Phase 10(`docs/phases/phase-10-resilience.md`)은 "정상 상태의 개선이 장애 중 성공률과 복구 특성을
악화시키지 않는지"를 검증하도록 요구한다. Fault Matrix는 4가지를 명시한다: target delay/HTTP 5xx/reset,
Pod kill과 graceful termination, network delay/loss, Kafka worker stop/restart와 backlog drain.

이 프로젝트는 지금까지 fault 주입 기능을 구현한 적이 없다 — `ExperimentSpec`에 `faultSchedule` 필드가
자리만 잡아두고 있었고(`experiments/runner/cli.py`/`kubernetes.py`가 이 필드의 존재만 확인해
`FAULT_CLEANUP_UNVERIFIED` 게이트에 쓸 뿐, 실제 fault를 주입하는 코드는 없다), README의 기술 기준선에
"k6, Chaos Mesh"라고 미리 계획만 되어 있었다.

이 클러스터는 이미 자원이 빠듯하다 — Phase 7/9에서 `NODE_MEMORY_HEADROOM_LOW` 무효율이 30~45%에 달했다.
Chaos Mesh는 매 노드마다 특권(privileged) DaemonSet(`chaos-daemon`)이 필요해서, 설치 자체가 이 프로젝트의
다른 canonical 측정과 자원 조건을 달라지게 만들 위험이 있다.

## Decision

### 도구: 이번 범위(Pod kill, chain-wide delay)는 Chaos Mesh 없이 kubectl + 기존 앱 파라미터로 구현

`ChainRequest.work`(`contracts/openapi/mesh-benchmark-api.yaml`)를 실제로 확인해보니 `work`(delayMs/
errorRate)는 **hop 하나가 아니라 SYNC_CHAIN 전체에 균일하게 적용**되는 파라미터였다 — 즉 "workload-a
에만 지연을 주입"하는 것은 지금 API로는 불가능하고, 이를 가능하게 하려면 `/runs/{runId}/faults/{target}`
(`armFault`/`disarmFault`, 이미 OpenAPI 계약에는 정의돼 있지만 Java 서비스 어디에도 구현되지 않은
엔드포인트)을 새로 구현해야 한다는 것도 확인했다. 이번 Phase 10 범위에서는 이 신규 Java 개발을 포함하지
않기로 하고, 대신 **이미 존재하는 두 메커니즘만으로 구현 가능한 두 fault**로 범위를 좁혔다:

- **Pod kill**: Chaos Mesh 없이 `kubectl delete pod`만으로 충분하다 — Deployment가 즉시 새 Pod를
  만들어 복구하므로 "장애 발생 → 자동 복구"라는 시나리오 자체가 별도 인프라 없이 성립한다. 특권
  DaemonSet을 설치할 필요가 없어 이미 빠듯한 클러스터 자원에 부담을 주지 않는다.
- **Chain-wide delay**: `ExperimentSpec.workloadConfig.work.delayMs`를 정상(1ms)보다 크게 올린 별도
  spec으로 정식 반복측정을 돌린다 — hop 하나만 격리하지는 못하지만, "체인 전체에 지연이 생겼을 때
  profile별로 성공률/latency가 어떻게 달라지는가"라는 질문에는 그대로 답이 된다. 이 한계는 정직하게
  기록한다(hop 단위 격리 fault가 아니라는 것).
- **Network delay/loss, Kafka worker stop/restart, 그리고 hop 단위로 격리된 fault(`armFault`
  API 구현)는 이번 범위에서 제외**하고 알려진 잔여 작업으로 남긴다 — Chaos Mesh 설치나 신규 Java
  컨트롤러 개발 없이는 안전하게 구현할 수 없고, 이미 자원이 빠듯한 클러스터에 특권 DaemonSet을
  추가하는 것의 위험 대비 효익이 낮다고 판단했다.

이는 ADR-0027(replica-scaling 범위 축소), ADR-0026(Waypoint 선택 경로)에서 쓴 것과 같은 "필요하지만
지금 범위에는 없음을 숨기지 않는다" 원칙을 그대로 적용한 것이다.

### 측정 대상 profile: Ambient만

Phase 10은 "개선이 장애 대응을 악화시키지 않는가"를 확인하는 것이 목적이므로, 이미 이 프로젝트의
가장 자세한 자원 모델을 갖춘 Ambient profile 하나에서만 진행한다. No-Mesh/Sidecar/Waypoint까지 4개
profile 전부에서 장애 주입을 반복하면 측정 매트릭스가 4배로 커진다 — 회복탄력성 자체가 mesh profile마다
다르게 나타나는지는 이번 범위에서 확인하지 않고 후속 과제로 남긴다.

### 반복과 정밀도

Fault 실험은 "before(정상)"와 "after(fault 주입)"를 같은 seed로 최소 10회씩 paired 비교한다(Phase 9와
같은 기준). 지표는 장애 중 성공률, p99, retry amplification과 fault 해제 후 정상화까지 걸리는 시간
(recovery time)이다.

## Alternatives

- **Chaos Mesh를 설치해 모든 fault 유형을 통일된 도구로 구현**: 일관성은 있지만 특권 DaemonSet을 이미
  자원이 빠듯한(무효율 30~45%) 클러스터에 추가로 얹는 위험 대비, 이번에 선택한 두 fault(Pod kill,
  chain-wide delay)는 기존 kubectl/앱 파라미터만으로 충분히 구현 가능해 불필요한 위험이라 기각. Network
  delay/loss처럼 커널 레벨 조작이 실제로 필요한 fault를 다룰 때 재검토한다.
- **`/runs/{runId}/faults/{target}` API를 지금 구현해 hop 단위로 격리된 fault를 만듦**: 계약에 이미
  정의돼 있어 "설계"는 끝나 있지만, Java 컨트롤러 신규 구현 + 이미지 재빌드 + digest 갱신이 필요해
  이번 Phase 10 범위에 넣기엔 비용이 크다. Chain-wide delay로 대체하고 이 API 구현은 후속 과제로 남긴다.
- **Fault Matrix 4개 전부 정식 측정**: 이상적이지만 이미 프로젝트가 열흘 넘게 진행된 시점에서 4배
  범위 확장은 비합리적이다. 2개로 좁히고 나머지는 명시적으로 후속 과제로 남기는 쪽을 선택.

## Consequences

- Network delay/loss, Kafka worker stop/restart, hop 단위로 격리된 fault(`armFault` API)는 Phase 10
  Evidence에서 "설계 검토했으나 미측정"으로 명시하고, Phase 11 최종 보고서의 알려진 한계에도 반영한다.
- Chain-wide delay 결과는 "hop 하나의 장애"가 아니라 "체인 전체가 동시에 느려질 때"의 시나리오로
  해석해야 한다는 점을 Evidence에 명시한다.

## Validation and rollback

- 모든 fault 실험은 최대 지속시간과 강도 상한을 코드에 명시하고, 실험 종료 시 자동으로 fault를
  해제(disarm)했는지 확인한 뒤에만 run을 유효 처리한다.
- Pod kill 실험 후 해당 Deployment의 replica 수와 상태가 실험 시작 전과 동일한지(`kubectl get deployment`)
  확인한다.
- Chain-wide delay 실험 후 `work.delayMs`가 정상값(1ms)으로 되돌아간 spec으로 SYNC_CHAIN이 정상
  동작하는지 재확인한다.
