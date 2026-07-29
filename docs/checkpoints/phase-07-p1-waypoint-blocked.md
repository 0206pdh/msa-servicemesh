# Checkpoint — `phase-07-p1-waypoint-blocked`

- Status: blocked (final — confirmed cross-version incompatibility, closed)
- Owner: dohyun
- Started at: 2026-07-29
- Updated at: 2026-07-29
- Branch/commit: main (see commits referenced below)
- Related Phase: [Phase 7](../phases/phase-07-waypoint.md)
- Related contract/ADR: [ADR-0026](../decisions/0026-waypoint-deployment-scope.md)

## 목표

Ambient 위에 orchestrator-service 단일 hop으로 Waypoint proxy를 배치하고, 실제 트래픽이 통과함을
검증한 뒤 paired 정식 반복측정을 시작한다.

## 완료 조건

- [x] Waypoint 배포 범위와 자원 모델 결정 (ADR-0026)
- [x] `istio-waypoint` GatewayClass 자동 생성 확인 (istiod `PILOT_ENABLE_AMBIENT=true`의 부수 효과)
- [x] Gateway 리소스 생성과 Waypoint Pod 자동 프로비저닝 확인
- [x] gateway→waypoint 홉 NetworkPolicy 수정 (HBONE 15008)
- [ ] **waypoint→실제 backend pod 홉 연결 성공 — 미해결, Phase 7 차단 원인**
- [ ] paired core 조건 반복측정
- [ ] Phase 7 Evidence

## 변경 근거

- 문제: orchestrator-service를 Waypoint 경유로 설정하면 SYNC_CHAIN 요청이 거의 항상 500 오류로 실패한다.
- 1차 진단: Waypoint의 Envoy 관리자 API(`/clusters`)에서 `envoy://connect_originate/<pod-ip>:8080`
  클러스터가 `cx_total=1`(TCP 연결 성공), `cx_connect_fail=0`이면서 `rq_error=1`, `rq_success=0`(HTTP
  요청 즉시 실패)을 보인다. 이 연결은 ztunnel access log에 전혀 나타나지 않는다.
- 가설 1(기각): Waypoint Pod와 실제 orchestrator-service Pod가 같은 노드(mesh-worker-02)에 있어 Cilium이
  같은 노드 트래픽에 대해 ambient 캡처 경로를 우회하는 것으로 의심했다. Waypoint Deployment에
  `podAntiAffinity`를 직접 patch해 다른 노드(mesh-worker-01)로 강제 이동시켜 재현했으나 **동일한 실패
  시그니처가 그대로 재현**되어 이 가설은 기각됐다.
- 심화 진단(`istioctl` 추가 설치 후): `istioctl proxy-config cluster`로 Waypoint의 실제 xDS 설정을 확인해
  `outer_connect_originate` 클러스터가 `ORIGINAL_DST` 타입에 `upstreamPortOverride: 15008`, TLS 1.3 +
  SPIFFE 검증까지 정상적으로 구성되어 있음을 확인했다 — 설정 자체는 정상으로 보였다.
- 결정적 발견: Waypoint Pod 안에서 실제 orchestrator-service Pod로 **평문 curl은 즉시 성공**했다
  (`HTTP 200`, 실제 health 응답 수신) — 기본 Pod 간 네트워킹과 NetworkPolicy는 문제가 없다는 뜻이다.
  또한 `cilium-dbg endpoint list`에 Waypoint Pod의 IP가 **전혀 나타나지 않았다** — Cilium이 이 Pod를
  정상적인 관리 대상 endpoint로 인식하지 못하는 것으로 보이나, 원인은 특정하지 못했다.
- 거짓 양성 발견: 클린 재배포 직후 5회 연속 성공(`HTTP 200`, 3-hop 완료)을 관측해 "해결됐다"고 판단했으나,
  Waypoint 자체의 Envoy 통계(`rq_total`)는 그 "성공한" 요청들에서도 전혀 증가하지 않았다. 이어서 20회
  연속 재시도한 결과 **0/20 성공**으로 되돌아갔다. 즉, 초기 성공은 Waypoint 설정 이전에 gateway 앱이
  이미 맺어둔 keep-alive 연결 풀이 우연히 재사용되며 Waypoint를 완전히 우회한 결과였고, Waypoint 자체의
  backend 연결은 여전히 근본적으로 깨져 있다.
- 현재 상태: 근본 원인 미확정. `istioctl`까지 동원한 심화 진단에도 재현성이 극히 불안정하고(연결 풀
  상태에 따라 간헐적 거짓 양성 발생), 이 클러스터의 특정 버전 조합(Cilium 1.19.6 + Istio ambient waypoint
  1.30.3)에서 실제로 존재하는 버그이거나 깊은 호환성 문제로 판단된다.
- 버전 교체 재시도(최종 확인): 사용자 요청으로 Istio를 1.30.3 → **1.29.6**으로 완전 재설치(ztunnel,
  istio-cni, istiod, istio-base 전체 제거 후 재설치, `PILOT_ENABLE_AMBIENT=true`는 처음부터 설정)해
  재현을 시도했다. 재설치 직후 순수 Ambient SYNC_CHAIN 트래픽은 정상 동작함을 먼저 확인했다(HTTP 200,
  3-hop, checksum 일치). 이후 Waypoint Gateway를 동일하게 재생성하고 NetworkPolicy 수정을 재적용했으며,
  Waypoint Pod는 `1/1 Running`으로 정상 기동했다. 첫 요청은 동일한 실패 시그니처(HTTP 500, "upstream
  connect error... connection termination")를 그대로 재현했다. 거짓 양성 가능성을 배제하기 위해 단일
  샘플이 아닌 20회 배치 요청으로 재확인한 결과 **0/20 성공** — 1.30.3에서 관측한 것과 정확히 동일한 실패
  패턴이었다.
- 결정(최종): 서로 다른 두 Istio minor 버전(1.30.3, 1.29.6)에서 완전 재설치 후에도 동일한 0/20 실패가
  재현됨을 확인했다. 이는 특정 Istio 릴리스의 일시적 버그가 아니라, 이 클러스터의 Cilium 구성(1.19.6,
  kube-proxy-replacement=true, routing-mode=tunnel/VXLAN — ADR-0025에서 사전에 위험 조합으로 표시됨)과
  Istio Ambient Waypoint 아키텍처 사이의 **버전 독립적인 근본 비호환**으로 최종 판단하고 조사를 종료한다.
  클러스터는 Waypoint Gateway/라벨을 제거하고 순수 Ambient 상태로 복구했으며 SYNC_CHAIN 정상 동작을
  재확인했다(HTTP 200, 3/3). Phase 7은 이 상태로 최종 blocked 처리하고, Phase 8(병목 분석)은
  No-Mesh/Sidecar/Ambient 세 profile 데이터로 진행한다.

## 변경 범위

- Application: 없음
- Infrastructure: Waypoint Gateway 리소스와 라벨을 생성 후 삭제해 클러스터를 순수 Ambient 상태로 복구했다
  (`orchestrator-service` Service의 `istio.io/use-waypoint` 라벨 제거, Gateway 리소스 삭제 확인).
- Contract/Data: `deploy/charts/meshperf`에 `waypoint.*` values와 조건부 NetworkPolicy(gateway→waypoint
  egress, waypoint→orchestrator-service ingress)를 추가했다 — Waypoint 연결 문제 자체는 해결하지 못했지만,
  이 두 NetworkPolicy 수정은 실제로 필요했고 검증됐다(첫 번째 홉은 성공적으로 통과함을 확인).
  `deploy/environments/waypoint/values.yaml` 추가.
- Out of scope: 근본 원인 규명(istioctl 기반 심화 진단), 전체 경로(5개 서비스) Waypoint 구성.

## 검증 기록

| 검증 | 명령/방법 | 결과 | Evidence |
|---|---|---|---|
| unit | `python -m unittest discover -s experiments -p 'test_*.py'` | 24 passed | — |
| Helm lint/render | 4개 profile(no-mesh/sidecar/ambient/waypoint) lint 통과, gateway-name 셀렉터 개수 diff(0/0/0/1) | 통과 | 수동 실행 로그 |
| E2E (첫 홉) | gateway→waypoint HBONE 연결 | 성공 (NetworkPolicy 수정 후) | ztunnel access log |
| E2E (둘째 홉) | waypoint→실제 orchestrator pod | **실패**, TCP 연결/HTTP 요청 즉시 리셋 | Envoy `/clusters` 통계, 앱 로그의 `503`/`connection termination` |
| 재현 (노드 분리) | podAntiAffinity로 다른 노드 강제 배치 후 재시도 | 동일 실패 재현 — 같은 노드 가설 기각 | 수동 patch + curl 재시도 |
| 심화 진단 | `istioctl proxy-config cluster`로 xDS 설정 확인 | 설정 자체는 정상(ORIGINAL_DST, port override 15008, TLS 1.3+SPIFFE) | `istioctl` 출력 |
| 기본 연결성 | Waypoint Pod 내부에서 실제 orchestrator Pod로 평문 curl | 즉시 성공(HTTP 200) — 네트워킹/NetworkPolicy 자체는 정상 | 수동 curl |
| Cilium endpoint 확인 | `cilium-dbg endpoint list`에서 Waypoint Pod IP 검색 | **나타나지 않음** — 원인 불명 | 수동 조회 |
| 재현성 확인 | 클린 재배포 직후 5연속 성공 → Waypoint 자체 통계는 무변화 → 20연속 재시도 | **0/20 성공** — 최초 성공은 연결 풀 재사용에 의한 거짓 양성으로 판정 | 수동 curl 배치, Envoy `/clusters` `rq_total` |
| 버전 교체 재현 | Istio 1.30.3 → 1.29.6 완전 재설치 후 순수 Ambient 확인 → Waypoint 재구성 → 20회 배치 재시도 | 순수 Ambient는 정상(HTTP 200), Waypoint 경유는 **0/20 성공** — 1.30.3과 동일한 실패 재현 | 수동 curl 배치 (`success=0 fail=20`) |
| 최종 복구 확인 | Waypoint 라벨/Gateway 제거 후 SYNC_CHAIN 재확인 (1.29.6 기준) | HTTP 200, 3/3 성공 | 수동 curl |

## 실패와 판단

- 실패 내용: Waypoint를 통과하는 SYNC_CHAIN 요청이 항상 500으로 실패.
- 원인: 미확정(도구로 특정 불가). TCP 연결은 성공하지만 HTTP 계층에서 즉시 리셋되는 패턴과 ztunnel 로그
  부재로 미루어 Waypoint의 백엔드 연결(HBONE CONNECT 방식으로 추정)이 대상 Pod의 ambient 캡처 경로와
  프로토콜 불일치를 일으키는 것으로 의심되나, 이 클러스터의 도구(kubectl, Envoy admin API, istioctl,
  cilium-dbg)만으로는 정확한 근본 원인을 특정할 수 없었다.
- 버전 독립성 확인으로 결론 강화: 동일 실패가 Istio 1.30.3과 1.29.6 양쪽에서 완전 재설치 후에도 그대로
  재현됨을 확인했다. 두 개의 서로 다른 minor 버전에서 동일한 시그니처(TCP 성공, HTTP 즉시 리셋, 0/20)가
  나온다는 것은 특정 Istio 릴리스의 회귀 버그가 아니라 이 클러스터의 Cilium 조합과 Ambient Waypoint
  아키텍처 사이의 구조적 비호환일 가능성이 훨씬 크다는 뜻이다.
- 해결 또는 보류 이유(최종): 근본 원인은 istioctl/cilium-dbg 수준의 진단으로는 특정할 수 없었고, 버전
  교체로도 동일하게 재현되어 추가 재시도의 기대 수익이 낮다고 판단했다. 사용자와 상의해 이 항목을
  **최종적으로 blocked 확정**하고, 이미 유효한 No-Mesh/Sidecar/Ambient 세 profile 데이터로 Phase 8을
  진행하기로 했다. Waypoint는 L7 기능이 필요한 경로에서만 선택적으로 쓰는 구성요소라 프로젝트의 핵심
  비교(No-Mesh vs Sidecar vs Ambient)에는 영향이 없다.

## 다음 재개 지점 (참고용 — 현재는 재개 계획 없음)

- 이 조사는 종료되었다. 향후 재개한다면 Cilium 쪽 로그(datapath 레벨 tcpdump, `cilium monitor`)나 Istio
  업스트림 이슈 트래커 확인이 다음 단계가 될 것이나, 본 프로젝트 범위에서는 우선순위가 낮다.
- 필요한 파일: `deploy/environments/waypoint/values.yaml`(이미 작성됨), ADR-0026.
- 주의할 상태/환경: 클러스터는 현재 순수 Ambient 상태(Istio 1.29.6)로 복구되어 있다(Waypoint Gateway
  없음). 재시도 시 `helm upgrade meshperf ... -f deploy/environments/waypoint/values.yaml`과 동일한
  Gateway 리소스 재생성이 필요하다.
