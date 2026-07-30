# Checkpoint — `phase-07-p1-waypoint-blocked`

- Status: **resolved (2026-07-30)** — root cause found and fixed, was never a version/architecture
  incompatibility; see "최종 해결" section below. Kept as `phase-07-p1-waypoint-blocked` for history.
- Owner: dohyun
- Started at: 2026-07-29
- Updated at: 2026-07-30
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
- [x] **waypoint→실제 backend pod 홉 연결 성공 — 2026-07-30 해결** (아래 "최종 해결" 절 참고)
- [ ] paired core 조건 반복측정 — 착수 예정
- [ ] Phase 7 Evidence — 측정 진행 예정

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
- 결정(2026-07-29 시점, **이후 "최종 해결" 절에서 정정됨**): 서로 다른 두 Istio minor 버전(1.30.3,
  1.29.6)에서 완전 재설치 후에도 동일한 0/20 실패가 재현됨을 확인했다. 이는 특정 Istio 릴리스의 일시적
  버그가 아니라, 이 클러스터의 Cilium 구성(1.19.6, kube-proxy-replacement=true,
  routing-mode=tunnel/VXLAN — ADR-0025에서 사전에 위험 조합으로 표시됨)과 Istio Ambient Waypoint
  아키텍처 사이의 **버전 독립적인 근본 비호환**으로 당시에는 판단하고 조사를 종료했다. **이 결론은 다음날
  (2026-07-30) 잘못된 것으로 밝혀졌다 — 아래 "최종 해결" 절 참고.** 당시에는 클러스터를 Waypoint
  Gateway/라벨을 제거하고 순수 Ambient 상태로 복구했으며 SYNC_CHAIN 정상 동작을
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

## 실패와 판단 (해결됨 — 아래는 진단 경과의 기록)

- 실패 내용: Waypoint를 통과하는 SYNC_CHAIN 요청이 항상 500으로 실패.
- 최종 확인된 원인: `deploy/charts/meshperf/templates/networkpolicies.yaml`의 `orchestrator-service`
  NetworkPolicy에서 waypoint pod로부터의 ingress 규칙이 포트 8080만 허용하고 15008(HBONE, waypoint→
  backend 연결에 실제 사용되는 포트)을 빠뜨린 템플릿 버그. Cilium이 이 포트의 SYN을 정책 위반으로
  드롭하고 있었다(`cilium monitor --type drop`으로 직접 확인). istioctl/Envoy admin API/cilium-dbg
  수준의 진단으로는 발견하지 못했고, 패킷 레벨 캡처를 실행한 뒤에야 확인됐다.
- 한때 "버전 독립적 구조적 비호환"으로 결론지었던 것은 틀린 추론이었다 — 자세한 경위는 아래 "최종 해결"
  절의 "예전 결론이 틀렸던 이유"를 참고. NetworkPolicy는 Istio 재설치로 바뀌지 않는 리소스였으므로,
  버전을 바꿔도 동일하게 실패한 것은 애초에 당연한 결과였다.
- 해결: NetworkPolicy에 누락된 포트를 추가하고 재배포, 20/20·50/50 연속 성공과 Waypoint 자체 통계
  (`rq_total`) 증가로 실제 트래픽 통과를 확인했다. Phase 7 정식 반복측정을 진행한다.

## 최종 해결 (2026-07-30)

**사용자가 제시한 재검증 방법론(gateway 앱 connection pool 초기화, `istioctl ztunnel-config` 확인,
`cilium monitor --type drop`을 통한 패킷 레벨 확인)을 그대로 적용해 재시도한 결과, 몇 분 만에 실제 원인을
찾았다.**

`cilium monitor --type drop`을 waypoint pod가 있는 노드에서 실행한 채로 SYNC_CHAIN 요청을 보내자, 다음과
같은 로그가 즉시 잡혔다:

```
xx drop (Policy denied) flow ... identity 49325->10965: 10.244.2.165:43596 -> 10.244.2.39:15008 tcp SYN
```

**Cilium이 waypoint pod(identity 49325)에서 orchestrator-service pod(identity 10965)로 가는 15008(HBONE)
포트 SYN 패킷을 NetworkPolicy 위반으로 실시간 드롭하고 있었다.** `orchestrator-service`의 NetworkPolicy를
직접 열어보니 원인이 바로 보였다 — waypoint pod로부터의 ingress를 허용하는 규칙이 포트 **8080만** 열어뒀고
15008(waypoint가 backend에 연결할 때 실제로 쓰는 HBONE 포트)이 빠져 있었다. 같은 파일의 바로 위
규칙(gateway→orchestrator-service)은 8080과 15008을 둘 다 올바르게 열어뒀는데, waypoint→orchestrator-
service 규칙만 15008이 누락된 단순한 템플릿 실수였다(`deploy/charts/meshperf/templates/networkpolicies.yaml`).

포트를 추가하고 재배포하자 즉시 해결됐다 — 20회 배치 테스트 20/20 성공, 50회 연속 soak 테스트 50/50
성공, 그리고 결정적으로 **Waypoint 자체의 Envoy 통계(`rq_total`)가 요청 수만큼 실제로 증가**하는 것을
확인해 예전에 겪었던 "keep-alive 재사용에 의한 거짓 양성"이 아님을 검증했다.

### 예전 결론("버전 독립적 근본 비호환")이 틀렸던 이유

Istio를 1.30.3 → 1.29.6으로 완전히 재설치해도 동일하게 실패한다는 사실로부터 "Istio 버전과 무관한 깊은
아키텍처 비호환"이라고 결론 내렸던 것은 **논리적 오류였다.** NetworkPolicy는 Kubernetes/Cilium 리소스이지
Istio 설치의 일부가 아니다 — Istio를 완전히 재설치해도 Helm으로 관리되는 NetworkPolicy는 전혀 건드려지지
않고 그대로 남아있었다. 즉 "버전을 바꿔도 실패가 재현된다"는 것은 "Istio 버전이 원인이 아니다"까지만
증명하는 것이지, "이 클러스터의 근본적인 아키텍처 문제"라는 훨씬 강한 결론을 정당화하지 못한다. 재설치
과정에서 **바뀌지 않은 것**(우리 자신의 Helm 차트가 관리하는 NetworkPolicy)을 의심했어야 했는데, 재설치로
**바뀐 것**(Istio 자체)에만 집중해 그럴듯하지만 잘못된 결론에 도달했다. 이 프로젝트의 다른 곳에서는
"Evidence 없는 결론 금지" 원칙을 잘 지켰지만, 이 경우는 "반증 실험 하나를 통과했다"는 것을 "가능한 다른
모든 원인을 배제했다"로 착각한, 정직하게 기록해 둘 필요가 있는 실수다.

### 왜 이전 진단들은 이걸 못 찾았는가

- `istioctl proxy-config cluster`는 Envoy(waypoint)가 **어떻게 연결을 시도하도록 설정되어 있는지**만
  보여준다 — 그 연결이 네트워크 레벨에서 실제로 차단되고 있는지는 보여주지 않는다. 설정이 "정상"으로
  보인 것은 설정 자체는 실제로 정상이었기 때문이다(문제는 설정이 아니라 별도의 NetworkPolicy 리소스에
  있었다).
- `cilium-dbg endpoint list`에서 waypoint pod IP가 안 보였던 것은 별개의 관찰이었고(원인 미상으로 남음),
  이 NetworkPolicy 문제와 직접 연결되는 단서는 아니었다.
- Waypoint pod 안에서 실제 orchestrator pod로 평문 curl이 성공했던 것은, 그 테스트가 애초에 15008이 아닌
  8080으로 직접 접속했기 때문이다(HBONE 캡슐화를 거치지 않는 경로) — 그래서 "네트워킹 자체는 정상"이라는
  결론은 맞았지만, 정작 실패하는 경로(15008)와는 다른 경로를 테스트한 것이었다.
- 패킷 레벨 캡처(`cilium monitor --type drop`)를 실행하기 전까지는 "어느 계층에서 무엇이 차단되는지"를
  직접 볼 방법이 없었다 — Envoy 통계와 애플리케이션 로그만으로는 Cilium의 정책 판정 자체를 볼 수 없다.

클러스터는 Waypoint 상태로 유지하고 Phase 7 정식 반복측정을 진행한다.

## 다음 재개 지점

- 이 항목은 해결됐다. 다음 단계는 nominal/high/near-saturation 세 조건에서 Phase 4~6과 동일한 수준(10~15회,
  bootstrap CI 정밀도 게이트)의 정식 반복측정을 실행하는 것이다.
- 필요한 파일: `deploy/environments/waypoint/values.yaml`(이미 작성됨), ADR-0026.
- 클러스터 상태: Istio 1.29.6, Ambient + Waypoint(`orchestrator-waypoint`) 활성화, NetworkPolicy 수정
  적용 완료(Helm revision 27+).
