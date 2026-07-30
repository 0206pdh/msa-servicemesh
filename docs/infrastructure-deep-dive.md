# 인프라 YAML 완전 정복 — 파일 하나하나 무엇을 왜 이렇게 썼는가

이 문서는 이 프로젝트의 실제 YAML/Helm 설정 파일을 처음부터 끝까지 읽어가며 "이 줄이 왜 여기 있는지"를
설명하는 스터디용 문서다. [testing-explained.md](testing-explained.md)가 "무엇을 왜 측정했는가"를
다뤘다면, 이 문서는 "그 측정이 실제로 어떤 설정 위에서 돌아가는가"를 다룬다. YAML 문법을 전혀 몰라도
읽을 수 있도록 각 섹션 앞에 최소한의 문법 설명을 넣었다.

---

## 0. YAML과 Helm을 모른다면 먼저 이것부터

**YAML**은 JSON처럼 데이터를 표현하는 문법인데, 중괄호나 따옴표 대신 들여쓰기(스페이스)로 구조를
나타낸다.

```yaml
parent:
  child: value
  list:
    - item1
    - item2
```

위는 `{"parent": {"child": "value", "list": ["item1", "item2"]}}`와 같은 뜻이다. **들여쓰기 칸 수가
곧 구조**이므로, 탭 대신 스페이스를 쓰고 칸 수를 정확히 맞추는 게 중요하다.

**Kubernetes manifest**는 "이런 리소스를 이런 모습으로 클러스터에 만들어달라"는 선언문이다. 어떤 종류의
리소스인지(`kind: Deployment`, `kind: NetworkPolicy` 등)와 그 리소스의 세부 설정(`spec:` 아래)으로
구성된다.

**Helm**은 이런 manifest를 여러 벌 찍어내기 위한 "템플릿 엔진"이다. `{{ .Values.foo }}` 같은 문법은
"values 파일에 있는 foo 값을 여기에 끼워 넣어라"는 뜻이고, `{{- if .Values.foo }} ... {{- end }}`는
"foo 값이 참이면 이 블록을 포함하고, 아니면 통째로 뺀다"는 조건문이다. 즉 **같은 템플릿 파일 하나로,
values 파일만 바꿔서 No-Mesh/Sidecar/Ambient/Waypoint 네 가지 다른 결과물을 만들어낸다** — 이게 이
프로젝트가 "동일 Workload, Mesh 구성만 다르게"를 실제로 구현하는 방법이다.

---

## 1. 저장소 배치 지도

```text
deploy/
├── charts/meshperf/          # 이 프로젝트의 애플리케이션+Mesh 설정을 담은 Helm chart (본체)
│   ├── Chart.yaml            # chart 메타데이터(이름, 버전)
│   ├── values.yaml           # 기본값 — "아무 profile도 안 켜면 이렇게 배포된다"
│   └── templates/            # 실제 Kubernetes manifest 템플릿들
├── environments/             # profile별 values 오버레이 (no-mesh/sidecar/ambient/waypoint/...)
└── phase-03/                 # 애플리케이션과 무관한 "플랫폼" 자체의 설정
    ├── cilium/                #   CNI(네트워크의 가장 밑바닥)
    ├── metallb/               #   클러스터 밖에서 접근 가능한 IP를 배정하는 LoadBalancer
    ├── gateway/               #   Gateway API 스모크 테스트용
    ├── observability/         #   Prometheus/Grafana/Loki/Tempo
    └── storage/               #   PersistentVolume 스모크 테스트용

experiments/                  # Python으로 짠 실험 자동화 도구 (측정을 실행하고 결과를 모으는 코드)
docs/                         # 이 문서를 포함한 모든 설명 문서
results/                      # 실제 측정 결과(용량이 커서 git에는 안 올라감, .gitignore 처리)
```

**배포 순서**는 대략: 3대의 VM에 Kubernetes를 깐다 → `phase-03/`의 플랫폼 설정을 적용한다(Cilium, MetalLB,
관측 스택) → `charts/meshperf`를 원하는 profile(`environments/*.yaml`)로 배포한다 → `experiments/`의
Python 도구로 부하를 걸고 결과를 측정한다.

---

## 2. `deploy/charts/meshperf/values.yaml` — 이 chart의 "기본 설정판"

```yaml
global:
  imagePullPolicy: IfNotPresent
  otelEndpoint: http://otel-opentelemetry-collector.observability.svc.cluster.local:4318
  tracingSamplingProbability: "1.0"
```

- `imagePullPolicy: IfNotPresent` — 이미 노드에 다운로드된 이미지가 있으면 다시 안 받는다. (참고: 아래
  애플리케이션들은 태그가 아니라 `@sha256:...` **digest**로 이미지를 고정해서 쓰기 때문에, 애초에 "같은
  이름인데 내용이 다른 이미지"가 섞일 위험 자체가 없다.)
- `otelEndpoint` — 애플리케이션이 자신의 trace(요청 흐름 기록)를 어디로 보낼지. OpenTelemetry Collector라는
  중계 서비스의 Kubernetes 내부 DNS 주소다(`서비스이름.네임스페이스.svc.cluster.local:포트` 형식).
- `tracingSamplingProbability: "1.0"` — trace를 100% 다 수집한다는 뜻(0.1이면 10%만). 이 프로젝트는
  측정이 목적이라 전수 수집하는 쪽을 택했다.

```yaml
sidecar:
  enabled: false
  istioNamespace: istio-system
  xdsPort: 15012
  mtlsMode: ""

ambient:
  enabled: false
  hbonePort: 15008

waypoint:
  enabled: false
  orchestratorGatewayName: orchestrator-waypoint
```

이 세 블록이 **이 chart 전체의 핵심 스위치**다. 아래 템플릿 파일들에서 `{{- if .Values.sidecar.enabled }}`
같은 조건문이 이 값들을 읽어서 "이번 배포는 어떤 Mesh 구성인가"를 결정한다. `xdsPort: 15012`는 Istio의
control plane(istiod)이 설정을 내려보내는 포트, `hbonePort: 15008`은 Ambient가 pod 간 암호화 터널에
쓰는 포트다 — 둘 다 뒤에서 NetworkPolicy를 설명할 때 왜 중요한지 나온다. `mtlsMode: ""`는 빈 문자열이면
"아무 설정도 안 한다"는 뜻이고, `"DISABLE"`을 넣으면 mTLS를 끄는 실험(Phase 9 실험 1)에 쓴다.

```yaml
javaResources: &javaResources
  requests: {cpu: 100m, memory: 256Mi}
  limits: {cpu: "1", memory: 512Mi}
```

`&javaResources`는 YAML의 **앵커(anchor)** 문법이다 — 이 블록에 이름표를 붙여두고, 아래에서
`resources: *javaResources`(**참조**)로 똑같은 내용을 반복 없이 재사용한다. `cpu: 100m`은 "0.1 코어",
`requests`는 "이 정도는 보장해달라", `limits`는 "이 이상은 못 쓰게 막는다"는 뜻이다.

```yaml
services:
  benchmark-gateway:
    image: {repository: ghcr.io/0206pdh/meshperf-benchmark-gateway, digest: sha256:...}
    resources: *javaResources
    env:
      ORCHESTRATOR_BASE_URL: http://orchestrator-service:8080
```

여기서부터가 실제 애플리케이션 7개(`benchmark-gateway`, `orchestrator-service`, `workload-a/b/c`,
`producer-service`, `worker-service`) 각각의 정의다. `env`는 이 서비스에만 필요한 추가 환경변수 —
예를 들어 `orchestrator-service`는 다음 hop인 `workload-a`의 주소를 알아야 하므로
`WORKLOAD_BASE_URL: http://workload-a:8080`을 갖고 있다. `http://workload-a:8080`처럼 IP가 아니라
Kubernetes Service 이름으로 주소를 쓰는 것도 중요한 설계 — Pod는 재시작될 때마다 IP가 바뀌지만 Service
이름은 안정적이다.

나머지 `kafka:`, `gateway:`, `serviceMonitor:`, `networkPolicy:` 블록은 각각 아래 3~7절에서 해당 템플릿과
같이 설명한다.

---

## 3. `templates/deployments.yaml` — 애플리케이션 Pod를 실제로 띄우는 템플릿

```yaml
{{- range $name, $service := .Values.services }}
```

`range`는 반복문이다 — `values.yaml`의 `services:` 아래 7개 항목을 하나씩 돌면서, **이 템플릿 파일
하나로 Deployment 7개를 찍어낸다.** `$name`은 그때그때의 서비스 이름(`benchmark-gateway` 등), `$service`는
그 서비스의 설정 전체(image, resources, env)다.

```yaml
spec:
  replicas: {{ default 1 $service.replicas }}
```

`default 1 $service.replicas`는 "`$service.replicas`가 없으면 1을 써라"는 뜻 — 대부분의 서비스는
`values.yaml`에 `replicas`를 안 적어뒀으니 기본 1개로 뜨고, replica-scaling 연구/실험에서는
`kubectl scale`로 직접 바꿨다(차트 자체를 바꾸지 않고).

```yaml
    metadata:
      {{- if $.Values.sidecar.enabled }}
      annotations:
        sidecar.istio.io/inject: "true"
      {{- end }}
```

**이게 Sidecar 방식의 핵심 스위치다.** 이 annotation이 있으면 Istio의 "sidecar injector"라는 admission
webhook(Pod가 만들어지기 직전에 가로채서 내용을 바꿀 수 있는 Kubernetes 기능)이 자동으로 이 Pod에 Envoy
proxy를 추가로 끼워 넣는다. Ambient/Waypoint를 쓸 때는 `sidecar.enabled`가 `false`라서 이 annotation
자체가 안 붙고, 대신 Ambient는 이 templates 파일과 무관하게 **namespace 라벨**로 동작한다(6절 참고) —
Sidecar는 "Pod 단위 스위치", Ambient는 "namespace 단위 스위치"라는 차이가 이 부분에 그대로 드러난다.

```yaml
      containers:
        - name: {{ $name }}
          image: "{{ $service.image.repository }}@{{ $service.image.digest }}"
```

이미지를 태그(`:latest`, `:v1.2`)가 아니라 `@sha256:...` **digest**로 고정한다. 태그는 나중에 다른
이미지를 가리키도록 바뀔 수 있지만(같은 이름의 새 빌드를 push), digest는 내용 자체의 해시라서 "정확히
이 바이너리"임을 보장한다 — 측정 재현성을 위해 중요하다(어제 측정한 이미지와 오늘 측정한 이미지가 코드
수준에서 완전히 같다는 것을 보장).

```yaml
          env:
            - name: JAVA_TOOL_OPTIONS
              value: "-XX:InitialRAMPercentage=25 -XX:MaxRAMPercentage=75"
```

JVM(Java 실행 엔진)이 컨테이너에 할당된 메모리의 25~75% 범위에서 힙(heap) 크기를 스스로 조절하게
한다 — 컨테이너 메모리 limit(512Mi)를 인식하지 못하고 무작정 큰 힙을 잡으려다가 OOMKill(메모리 부족으로
강제 종료)당하는 걸 막는다.

```yaml
          readinessProbe:
            exec:
              command: ["wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:8080/actuator/health/readiness"]
```

**probe 3종**(readiness/startup/liveness)은 전부 `127.0.0.1`(자기 자신, loopback)로 접속한다. 원래는
Pod의 실제 IP로 접속하는 `httpGet` probe를 썼었는데, Ambient 모드에서는 Pod IP로 가는 트래픽이 ztunnel의
"ambient capture" 규칙에 걸려버려서(모든 트래픽을 가로채 암호화 터널을 통과시키려 함) probe가 자꾸
실패하는 문제가 생겼다. `127.0.0.1`로 우회하면 이 캡처 규칙을 거치지 않아 어떤 Mesh profile에서도 동일하게
동작한다 — Ambient 도입 후 실측으로 발견하고 고친 부분이다.

---

## 4. `templates/services.yaml`과 `servicemonitor.yaml` — 이름 안정성과 지표 수집

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    meshperf.io/metrics: "true"
spec:
  selector:
    app.kubernetes.io/name: {{ $name }}
  ports:
    - {name: http, port: 8080, targetPort: http}
```

Kubernetes **Service**는 "이 라벨을 가진 Pod들로 트래픽을 로드밸런싱해주는 안정적인 이름표"다. Pod가
죽고 새로 뜨면 IP는 바뀌지만 Service 이름(`orchestrator-service` 등)과 그 뒤의 라우팅은 그대로 유지된다.
`meshperf.io/metrics: "true"` 라벨은 아래 `ServiceMonitor`가 "어떤 Service들을 지표 수집 대상으로
삼을지" 고르는 데 쓰인다.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
spec:
  selector:
    matchLabels:
      meshperf.io/metrics: "true"
  endpoints:
    - {port: http, path: /actuator/prometheus, interval: 15s}
```

`ServiceMonitor`는 Prometheus Operator가 이해하는 특수 리소스다 — "이 라벨을 가진 Service들의
`/actuator/prometheus` 경로를 15초마다 긁어와라(scrape)"는 뜻이다. `/actuator/prometheus`는 Spring
Boot 애플리케이션이 자기 자신의 지표(요청 수, latency 등)를 Prometheus가 읽을 수 있는 형식으로
노출하는 표준 경로다.

---

## 5. `templates/networkpolicies.yaml` — 이 프로젝트에서 가장 많이 손봐야 했던 파일

Kubernetes의 `NetworkPolicy`는 **기본적으로 "허용된 것 외에는 전부 막는다"** 방식(default-deny)으로
동작하도록 이 프로젝트에서 설계했다. 즉 명시적으로 "A에서 B로, 이 포트로" 허용 규칙을 안 써두면 그
통신은 실제로 실패한다 — 이게 이 파일이 계속 문제의 근원이자 해결책이 되어온 이유다(Phase 5/6/7 각각
NetworkPolicy 누락으로 한 번씩 걸렸다).

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: meshperf-default-deny
spec:
  podSelector:
    matchLabels: {app.kubernetes.io/part-of: meshperf}
  policyTypes: [Ingress, Egress]
```

이 리소스가 핵심이다 — `ingress`/`egress` 규칙을 **하나도 안 적었다.** NetworkPolicy는 "허용 규칙이
하나라도 있으면 그 외 트래픽을 전부 차단"하는 방식이라, 규칙이 비어있는 이 정책 하나만으로 "이 라벨을
가진 모든 Pod는 기본적으로 모든 in/out이 막힌다"가 성립한다. 다른 NetworkPolicy들이 그 위에 "이건
허용"이라는 구멍을 하나씩 뚫어주는 구조다.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orchestrator-service
spec:
  podSelector:
    matchLabels: {app.kubernetes.io/name: orchestrator-service}
  ingress:
    - from:
        - podSelector: {matchLabels: {app.kubernetes.io/name: benchmark-gateway}}
      ports:
        - {protocol: TCP, port: 8080}
        {{- if .Values.ambient.enabled }}
        - {protocol: TCP, port: {{ .Values.ambient.hbonePort }}}
        {{- end }}
```

이게 SYNC_CHAIN의 실제 통신 경로(`benchmark-gateway → orchestrator-service → workload-a → workload-b →
workload-c`)를 그대로 NetworkPolicy로 옮긴 부분이다. 평소엔 포트 8080(앱 자신의 HTTP 포트)만 있으면
되는데, **Ambient가 켜지면 포트 15008(HBONE)도 추가로 열어야 한다** — No-Mesh/Sidecar일 때는 Pod가
서로 직접 8080으로 통신하지만, Ambient는 통신이 항상 ztunnel(노드 공유 프록시)을 거치는 HBONE 터널로
캡슐화되기 때문에, 애플리케이션 관점에서는 "같은 8080 통신"이라도 실제 패킷은 15008 포트로 오간다. 이
차이를 놓치면 Cilium이 15008 포트를 그냥 막아버려서 "코드는 멀쩡한데 연결이 안 되는" 상황이 생긴다 —
Phase 6에서 처음 겪었고, **Phase 7 Waypoint에서 이 패턴을 또 한 번 놓쳐서(waypoint→backend 방향의
15008이 빠짐) 며칠간의 장애 조사로 이어졌다.**

```yaml
    {{- if .Values.waypoint.enabled }}
    - from:
        - podSelector:
            matchLabels:
              gateway.networking.k8s.io/gateway-name: {{ .Values.waypoint.orchestratorGatewayName }}
      ports:
        - {protocol: TCP, port: 8080}
        - {protocol: TCP, port: {{ .Values.ambient.hbonePort }}}
    {{- end }}
```

바로 이 블록이 그 사건의 현장이다. `gateway.networking.k8s.io/gateway-name` 라벨은 Istio가 Waypoint
Pod에 자동으로 붙여주는 라벨이고(값은 Gateway 리소스 이름, 여기선 `orchestrator-waypoint`), 이 규칙은
"Waypoint pod로부터 오는 트래픽을 허용한다"는 뜻이다. **처음 작성했을 땐 `port: 8080` 한 줄만 있고
`port: {{ .Values.ambient.hbonePort }}` 줄이 없었다** — Waypoint가 실제 backend Pod에 연결할 때 쓰는
포트가 바로 15008(HBONE)인데 이걸 빠뜨린 것이다. `cilium monitor --type drop`으로 이 포트의 SYN
패킷이 정책 위반으로 드롭되는 걸 직접 본 뒤에야 이 한 줄을 추가했다(2026-07-30). 위쪽의
`benchmark-gateway`용 정책(gateway→waypoint 방향)은 처음부터 두 포트가 다 있었는데, 이 규칙만 대칭이
안 맞았던 게 원인이었다 — 자세한 진단 경위는 [testing-explained.md §3.5](testing-explained.md)와
[phase-07-p1-waypoint-blocked 체크포인트](checkpoints/phase-07-p1-waypoint-blocked.md)에 있다.

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: benchmark-gateway-ingress
spec:
  ingress:
    - fromEntities: [ingress]
      toPorts:
        - ports: [{protocol: TCP, port: "8080"}]
```

표준 Kubernetes `NetworkPolicy`가 아니라 **Cilium 전용** `CiliumNetworkPolicy`를 쓴 유일한 곳이다.
`fromEntities: [ingress]`는 "클러스터 밖에서 Gateway를 통해 들어오는 트래픽"이라는, 표준
NetworkPolicy로는 표현할 수 없는 Cilium만의 개념이다 — 이 프로젝트의 유일한 외부 진입점
(`benchmark-gateway`)에 "바깥에서 들어오는 요청은 8080으로만 허용"이라는 규칙을 걸기 위해 썼다.

---

## 6. `templates/peerauthentication.yaml` — mTLS 스위치 (Phase 9 실험 1용)

```yaml
{{- if .Values.sidecar.mtlsMode }}
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: meshperf-mtls-mode
spec:
  mtls:
    mode: {{ .Values.sidecar.mtlsMode }}
{{- end }}
```

`values.yaml`의 기본값(`mtlsMode: ""`)일 때는 이 파일 전체가 조건문에 걸려 **아무 리소스도 안 만든다**
— 그러면 Istio의 mesh-wide 기본값(PERMISSIVE, 암호화와 평문 통신을 둘 다 허용)이 그대로 적용된다.
`mtlsMode: "DISABLE"`을 넣으면 이 `PeerAuthentication` 리소스가 만들어지고, Istio가 이 namespace의
mTLS를 완전히 끈다. Phase 9 실험 1(ADR-0028)이 "mTLS가 Sidecar 오버헤드의 몇 %를 차지하는가"를
측정하기 위해 정확히 이 스위치 하나만 켰다 껐다 했다.

---

## 7. `templates/gateway.yaml`과 `kafka.yaml` — 진입점과 비동기 인프라

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
spec:
  gatewayClassName: {{ .Values.gateway.className }}   # "cilium"
  listeners:
    - {name: http, protocol: HTTP, port: 80}
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
spec:
  parentRefs: [{name: benchmark}]
  rules:
    - matches: [{path: {type: PathPrefix, value: /}}]
      backendRefs: [{name: benchmark-gateway, port: 8080}]
```

**Gateway API**는 Kubernetes의 최신 "외부 트래픽 진입" 표준이다(더 오래된 `Ingress` 리소스의 후속).
`Gateway`는 "이 포트로 트래픽을 받겠다"는 선언, `HTTPRoute`는 "받은 트래픽을 어디로 보낼지"의 라우팅
규칙이다. `gatewayClassName: cilium`이 바로 이 Gateway를 누가 실제로 구현하는지 결정한다 — Cilium이
이 Gateway를 보고 실제 MetalLB IP(`192.168.200.100`)로 들어오는 트래픽을 `benchmark-gateway` Service로
전달하도록 자기 자신의 데이터플레인을 설정한다.

`kafka.yaml`은 `StatefulSet`(Pod마다 고유하고 안정적인 이름과 저장공간이 필요한 워크로드용 리소스,
`Deployment`와 달리 Pod를 함부로 대체하지 않음)으로 단일 Kafka 브로커를 띄운다.
`KAFKA_PROCESS_ROLES: "broker,controller"`는 최신 Kafka(KRaft 모드, ZooKeeper 없이 Kafka 자체가
합의 프로토콜을 처리)를 단일 노드로 구성한다는 뜻 — 이 프로젝트는 Kafka의 분산 안정성을 검증하는 게
아니라 Async Pipeline Workload가 필요로 하는 최소 요건만 채우면 되므로 굳이 여러 노드로 안 늘렸다.

---

## 8. `deploy/environments/*.yaml` — 4~5개의 "설정 카드"

각 파일은 위 `values.yaml`의 기본값 중 일부만 덮어쓰는 작은 오버레이다.

| 파일 | `sidecar.enabled` | `ambient.enabled` | `waypoint.enabled` | 비고 |
|---|:---:|:---:|:---:|---|
| `no-mesh/values.yaml` | (기본 false) | (기본 false) | (기본 false) | 스위치 전부 꺼진 기본 상태 그대로 |
| `sidecar/values.yaml` | true | false | false | |
| `ambient/values.yaml` | false | true | false | |
| `waypoint/values.yaml` | false | true | true | Ambient 위에 Waypoint를 얹으므로 둘 다 true |
| `sidecar-mtls-disabled/values.yaml` | true | false | false | `sidecar.mtlsMode: DISABLE` 추가 (Phase 9 실험 1) |

실제 배포는 `helm upgrade meshperf ./charts/meshperf -f environments/ambient/values.yaml` 같은 명령으로,
"기본 chart + 이 오버레이 파일 하나"를 합쳐서 적용한다. **오버레이 파일에 없는 값은 chart의 기본값을
그대로 쓴다** — 예를 들어 `ambient/values.yaml`은 `javaResources`나 `services:` 블록을 아예 안
건드리므로, 애플리케이션 이미지/자원/환경변수는 모든 profile에서 100% 동일하다. **이게 바로 "동일
Workload, Mesh 구성만 다르게 비교한다"는 이 프로젝트의 핵심 원칙이 코드 수준에서 강제되는 지점이다** —
사람이 실수로 다른 값을 넣을 여지 자체가 구조적으로 없다.

Ambient/Waypoint는 위 표에 없는 스위치가 하나 더 있다 — **namespace 라벨** `istio.io/dataplane-mode:
ambient`다. 이건 Helm chart가 관리하지 않고(namespace는 chart 바깥의 리소스라서) `kubectl label
namespace benchmark istio.io/dataplane-mode=ambient`로 수동 적용한다. Sidecar는 "Pod에 붙는 annotation"
(3절)으로 켜지고, Ambient는 "namespace에 붙는 라벨"로 켜진다는 비대칭이 여기서도 드러난다 — 두 방식을
동시에 쓰면(예: Waypoint 재시도 중 namespace에 `istio.io/rev=default`와 `dataplane-mode=ambient`가
동시에 남아있던 사고) sidecar injection과 ambient capture가 충돌해 예상 못 한 동작이 나올 수 있다는 걸
직접 겪었다.

---

## 9. `deploy/phase-03/` — 애플리케이션보다 먼저 있어야 하는 것들

### 9.1 Cilium (`cilium/gateway-api-values.yaml`)

```yaml
kubeProxyReplacement: true
gatewayAPI:
  enabled: true
```

Cilium은 이 클러스터의 **CNI**(Container Network Interface, Pod에 IP를 주고 Pod 간 통신을 실제로
구현하는 가장 밑바닥 계층)다. `kubeProxyReplacement: true`는 "Kubernetes 기본 컴포넌트인 kube-proxy가
하던 일(Service → Pod 로 트래픽을 라우팅하는 것)을 Cilium이 커널의 eBPF로 대신 처리한다"는 뜻 — 더
빠르지만, Istio Ambient 같은 다른 저수준 네트워크 기술과 만나면 상호작용이 복잡해질 수 있는 조합이라
이 프로젝트에서도 초반부터 위험 요인으로 표시해뒀다(ADR-0025). 다만 실제 Waypoint 장애를 조사해보니
이 설정 자체가 아니라 훨씬 단순한 NetworkPolicy 실수가 원인이었다(5절 참고). `gatewayAPI.enabled: true`는
7절의 `Gateway`/`HTTPRoute` 리소스를 Cilium이 실제로 구현하게 켜는 스위치다.

이 파일에 안 보이지만 실제로 켜져 있는 값들(다른 `helm upgrade` 호출로 추가됨, `helm get values`로
확인 가능)도 있다 — `socketLB.hostNamespaceOnly: true`, `cni.exclusive: false`, `bpf.masquerade: false`.
이 셋은 Cilium과 Istio(어느 방식이든)를 같이 쓸 때 공식적으로 권장되는 조합이다.

### 9.2 MetalLB (`metallb/l2-pool.yaml`, `metallb/values.yaml`)

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
spec:
  addresses: ["192.168.200.100-192.168.200.110"]
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
spec:
  ipAddressPools: [vmnet8-lab]
  interfaces: [ens32]
```

**MetalLB**는 클라우드가 아닌 온프레미스 환경에서 "LoadBalancer 타입 Service에 실제 외부 IP를 배정해주는"
역할을 한다(AWS/GCP라면 클라우드가 자동으로 해주는 일). `IPAddressPool`은 "이 IP 대역을 나눠줄 수
있다"는 선언, `L2Advertisement`는 "이 IP들을 실제 네트워크 인터페이스(`ens32`)에서 ARP로 광고해서
다른 기기들이 찾아올 수 있게 한다"는 뜻 — L2(같은 네트워크 세그먼트)에서만 동작하는 가장 단순한 모드다
(더 복잡한 BGP 모드는 `frr.enabled: false`로 꺼져 있다). `192.168.200.100`이 바로 Gateway가 실제로
받는 주소이고, 모든 curl 테스트가 이 주소로 요청을 보낸 이유가 여기 있다.

### 9.3 관측 스택 (`observability/*.yaml`)

세 파일 모두 공통된 패턴이 있다 — **control-plane 노드(`mesh-cp-01`)에 고정 배치**
(`nodeSelector`/`tolerations`)하고, **자원을 빡빡하게 제한**한다. 3개 VM짜리 랩 환경에서 관측 스택이
실제 측정 대상(Worker 노드의 애플리케이션)의 자원을 뺏어가지 않도록 격리한 것이다.

```yaml
prometheus:
  prometheusSpec:
    retention: 24h
    retentionSize: 2GB
```

Prometheus는 **24시간 또는 2GB 중 먼저 도달하는 조건**까지만 데이터를 보관한다. 이 값 때문에 Phase 8
시간축 상관 분석 때 과거 run의 metric을 다시 조회하려다 이미 사라진 걸 확인했다 — 작정하고 설정한
값이지만, 그 정확한 함의(과거 데이터 재조회 불가)를 나중에야 체감한 사례다.

```yaml
loki:
  limits_config:
    retention_period: 24h
```

Loki(로그 저장소)도 겉보기엔 같은 24시간 설정이 있지만, **이 값을 실제로 강제하는 compactor 컴포넌트가
이 배포에는 없다** — 그래서 설정과 달리 로그는 실제로 훨씬 오래 남아있었다(Prometheus는 자체
TSDB(Time Series Database)가 스스로 retention을 지키지만, Loki는 별도 compactor가 있어야 지켜진다는
차이). "설정 파일에 그렇게 쓰여 있다"와 "실제로 그렇게 동작한다"가 다를 수 있다는 걸 직접 겪은
사례다 — Prometheus와 Loki를 나란히 놓고 비교하면 이 차이가 왜 생기는지 이해하기 좋다.

```yaml
tempo:
  retention: 24h
  memBallastSizeMbs: 128
  resources:
    limits: {memory: 1536Mi}
```

`memBallastSizeMbs`(메모리 ballast, GC 압박을 줄이려고 미리 확보해두는 더미 메모리)의 chart 기본값은
1024MiB인데, 이 값이 컨테이너 메모리 limit(원래는 더 작았음)보다 커서 Tempo가 뜨자마자 OOMKilled되는
사고가 있었다. `128`로 줄이고 `limits.memory`도 1536Mi로 넉넉하게 잡아서 해결했다 — "프레임워크의
기본값을 그대로 믿지 않고, 이 환경의 실제 자원 한도와 맞춰봐야 한다"는 교훈이 그대로 값에 남아있다.

---

## 10. YAML에서 Python 실험 코드로 — 어떻게 이어지는가

이 YAML들은 "클러스터가 어떤 모습이어야 하는가"만 선언한다. 실제로 부하를 걸고 결과를 재는 것은
`experiments/` 아래의 Python 코드다. 둘이 만나는 지점은 다음과 같다.

1. `experiments/capacity.py`의 `discovery_spec()`이 만드는 `ExperimentSpec`(dict) 안에
   `"profile": "AMBIENT"` 같은 문자열이 들어간다. 이 문자열은 **위 YAML 어디에도 직접 등장하지 않는다**
   — Runner가 이 profile 값에 따라 "지금 클러스터가 실제로 그 profile의 values 파일로 배포되어 있다"고
   가정하고 그에 맞는 Prometheus 쿼리(sidecar CPU를 볼지, ztunnel CPU를 볼지, waypoint CPU를 볼지)를
   고른다 — 즉 **"클러스터 배포 상태"와 "측정 spec의 profile 값"을 사람이 직접 일치시켜야 한다**(`helm
   upgrade -f environments/ambient/values.yaml`을 실행한 뒤에 `--profile AMBIENT`로 측정을 돌리는 식).
   둘이 어긋나면(예: 클러스터는 Sidecar인데 profile=AMBIENT로 측정) 엉뚱한 지표를 모으게 되므로, 매
   phase 전환 때마다 배포 상태를 실측으로 재확인하는 절차가 있다.
2. `experiments/runner/kubernetes.py`의 `window_snapshot()`이 Prometheus에 PromQL(Prometheus의 쿼리
   언어)을 날려서 CPU/메모리/네트워크를 긁어온다 — 이때 쿼리 대상 namespace(`benchmark`)와 라벨
   (`container="istio-proxy"`, `pod=~"ztunnel-.*"` 등)은 위 YAML들이 실제로 만들어내는 Pod/컨테이너
   이름과 정확히 일치해야 값이 나온다.
3. `experiments/runner/cli.py`의 `_manifest()`가 이번 run이 어떤 image digest, 어떤 profile로
   실행됐는지를 `manifest.json`에 기록한다 — 이 값이 나중에 "이 결과가 어떤 배포 상태에서 나온 것인지"를
   추적하는 유일한 근거가 된다(YAML 자체는 git 이력으로 바뀌지만, 특정 run 시점의 실제 배포 상태는
  이 manifest가 증언한다).

---

## 관련 문서

- [무엇을 왜 테스트했는가](testing-explained.md) — 이 설정들이 실제로 어떤 실험에 쓰였는지, 왜 그렇게
  설계했는지
- [핵심 개념과 용어](03-concepts-and-glossary.md) — 이 문서에서 짧게만 설명한 용어의 더 깊은 정의
- [ADR 목록](decisions/README.md) — 각 설정 변경의 결정 배경(특히 ADR-0023~0029)
- [phase-07-p1-waypoint-blocked 체크포인트](checkpoints/phase-07-p1-waypoint-blocked.md) — 5절에서
  다룬 NetworkPolicy 버그의 발견부터 해결까지 전체 경위
