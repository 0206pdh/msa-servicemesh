# 핵심 개념과 용어

이 문서는 Mesh Performance Lab의 구현과 결과 해석에 사용하는 공통 용어 기준이다. 일반 정의와 함께 이 프로젝트에서의 역할과 측정 시 주의점을 설명한다.

## 1. 프로젝트의 구조

동일한 Java MSA Workload를 네 가지 네트워크 구성에서 반복 실행하고 성능·자원·회복탄력성 차이와 개선 효과를 측정한다.

```text
동일 Workload + 동일 부하 + 동일 배치
                  │
     ┌────────────┼────────────┐
  No Mesh      Sidecar      Ambient      Ambient + Waypoint
```

애플리케이션은 제품이 아니라 동기 호출, 병렬 호출, 비동기 메시지와 큰 Payload 같은 MSA 통신 패턴을 통제된 조건으로 재현하는 측정 대상이다.

## 2. MSA와 Service Mesh

### MSA

Microservices Architecture의 약자다. 큰 애플리케이션을 독립적으로 배포·확장 가능한 작은 서비스로 나눈 구조다. 배포 독립성은 높아지지만 메서드 호출이 네트워크 호출로 바뀌어 latency, timeout, retry, 부분 실패, 보안과 관측 문제가 생긴다.

### 부분 실패

전체 시스템이 동시에 죽는 대신 일부 서비스나 네트워크 구간만 느려지거나 실패하는 현상이다. Fan-out에서 target 하나만 timeout 되는 상황이 대표적이다.

### Service Mesh

애플리케이션 코드를 크게 변경하지 않고 서비스 간 통신에 다음 기능을 제공하는 인프라 계층이다.

- 서비스 identity와 mTLS
- traffic routing과 분할
- timeout, retry와 circuit breaking
- request metric, access log와 trace
- 서비스 간 접근 정책

요청 경로에 proxy 또는 tunnel이 추가되므로 latency, CPU, memory, network byte와 운영 복잡도가 증가할 수 있다. 제공 기능과 이 비용의 균형이 핵심 측정 대상이다.

### Istio

이 프로젝트에서 비교하는 Service Mesh 구현체다. Sidecar와 Ambient 방식을 모두 제공하므로 같은 생태계 안에서 두 아키텍처를 비교할 수 있다.

### Control Plane과 Data Plane

- Control Plane: 인증서, route와 policy 같은 설정을 배포하는 관리 계층. Istio에서는 주로 `istiod`가 담당한다.
- Data Plane: 실제 애플리케이션 요청이 지나는 계층. Sidecar proxy, ztunnel과 Waypoint가 속한다.

프로젝트 API도 같은 원칙으로 나눈다. `/api/v1/workloads/*`는 측정되는 Data Plane이고, 실험 생성·시작·종료·Fault는 측정 경로 밖의 Control Plane이다.

## 3. 네 가지 Mesh Profile

### No Mesh

Service Mesh 없이 Kubernetes Service 네트워크만 사용하는 기준 구성이다.

```text
Client → Application A → Application B
```

Mesh가 추가한 비용을 계산하기 위한 baseline이다. 보안·정책 기능도 동일하다는 뜻은 아니다.

### Sidecar

각 애플리케이션 Pod 안에 별도 proxy 컨테이너를 함께 배치하는 방식이다.

```text
Pod A                       Pod B
[App A → Sidecar Proxy] → [Sidecar Proxy → App B]
```

Pod별 L4/L7 제어와 상세 telemetry가 가능하지만 Pod마다 proxy CPU·memory, proxy 통과 latency와 시작 비용이 추가된다. `Sidecar`는 애플리케이션 옆에 붙어 다닌다는 뜻이다.

### Ambient Mesh

각 Pod에 Sidecar를 넣지 않고 노드 단위 공유 tunnel로 기본 보안과 L4 통신을 제공하는 방식이다.

```text
Pod A → Node ztunnel → Node ztunnel → Pod B
```

Pod별 proxy는 없어지지만 ztunnel이 여러 Pod의 traffic을 공유한다. 따라서 ztunnel CPU를 특정 Pod 하나에 그대로 귀속하거나 Sidecar 하나와 1:1 비교하면 안 된다.

### ztunnel

Ambient Mesh에서 노드별로 배치되는 경량 traffic tunnel이다. Workload identity, 연결과 mTLS 같은 기본 L4 기능을 담당한다. 자원은 해당 노드의 전체 실험 traffic과 연결해 해석한다.

### Waypoint Proxy

Ambient Mesh에서 HTTP routing, L7 authorization, retry와 상세 HTTP telemetry가 필요한 traffic에 선택적으로 배치하는 proxy다.

```text
Pod A → ztunnel → Waypoint → ztunnel → Pod B
```

전체 경로 적용과 필요한 경로만 적용하는 profile을 분리한다. Waypoint replica, 통과 RPS, queue와 saturation을 함께 측정한다.

### L4와 L7

- L4: TCP 연결, IP와 port 중심의 전송 계층
- L7: HTTP method, path, header 같은 애플리케이션 프로토콜 계층

L7은 더 세밀한 기능을 제공하지만 더 많은 정보를 해석하므로 처리 비용과 복잡성이 커질 수 있다.

### mTLS

Mutual TLS의 약자다. 통신 양쪽이 인증서를 검증하고 traffic을 암호화한다. 암호화뿐 아니라 서비스 identity 검증을 포함한다. 비교 시 적용 여부를 동일하게 맞추거나 기능 차이로 명시해야 한다.

## 4. Benchmark와 Workload

### Benchmark

정해진 조건에서 시스템 특성을 반복 측정하는 절차다. 한 번 부하를 걸어 숫자를 얻는 것은 신뢰할 수 있는 Benchmark가 아니다. 질문과 가설, 독립 변수, 고정 조건, 반복, 원본 데이터, 무효화 규칙과 적용 범위가 필요하다.

### Benchmark Workload

측정 대상에 일정한 일을 발생시키는 통제 가능한 애플리케이션이다. 실제 비즈니스 데이터 대신 delay, error, payload, CPU와 호출 구조를 parameter로 제공해 동일 조건을 재현한다.

### Scenario와 Profile

- Scenario: 어떤 통신 패턴을 실행하는가
- Profile: 어떤 Mesh 구성에서 실행하는가

Scenario는 `SYNC_CHAIN`, `FAN_OUT`, `ASYNC_PIPELINE`, `PAYLOAD`, `MIXED_RESOURCE`이며 Profile은 `NO_MESH`, `SIDECAR`, `AMBIENT`, `WAYPOINT`다.

### Baseline

변경 전 비교 기준이다. Mesh 비교에서는 No Mesh가 baseline이고, 개선 실험에서는 개선 전 설정이 baseline이다.

### Workload Target

설정된 delay, 오류, CPU, memory, blocking I/O와 response payload를 수행하는 말단 서비스다. 같은 이미지를 역할과 설정만 바꿔 여러 target/hop으로 배포한다.

### Bounded Work

최대 시간, 메모리와 payload 크기가 제한된 작업이다. 실험 도구가 노드 전체를 고갈시키거나 무한 loop·누수를 만들지 않도록 모든 parameter에 상한을 둔다.

### Deterministic Seed

난수 생성의 시작값이다. 동일 seed와 config는 동일 payload, 오류 선택과 fault schedule을 만들어 반복 실험의 차이를 줄인다.

## 5. 호출 구조

### Hop

요청이 한 서비스에서 다음 서비스로 이동하는 한 구간이다.

```text
Gateway → Service A → Service B → Service C
          hop 1       hop 2       hop 3
```

Hop이 늘면 네트워크 왕복, proxy 통과, 직렬화와 queue 비용이 누적된다. hop 증가당 p95/p99와 자원 증가를 측정한다.

### Sync Chain

서비스가 다음 서비스를 호출하고 응답을 기다리는 직렬 구조다.

```text
A → B → C → D
```

한 hop이 느려지면 전체가 느려진다. 남은 deadline 전파와 cancellation이 중요하다.

### Fan-out

하나의 요청이 여러 target 호출로 펼쳐지는 구조다.

```text
        ┌→ B
A ─────┼→ C
        └→ D
```

- Sequential: target을 순서대로 호출
- Parallel: target을 동시에 호출

Parallel은 정상 latency를 줄일 수 있지만 thread, connection과 순간 부하가 커진다.

### Partial Result

Fan-out target 일부가 실패해도 성공한 결과를 반환한다. 성공률은 높일 수 있지만 응답 완전성이 낮아지므로 별도 지표로 기록한다.

### Async Pipeline

Producer가 메시지를 발행하고 Worker가 나중에 처리하는 비동기 구조다.

```text
Producer → Kafka Topic → Worker(s)
```

HTTP latency 대신 publish/consume rate, consumer lag, oldest message age와 backlog drain time이 중요하다.

### Payload, Buffered와 Streaming

Payload는 요청이나 응답의 데이터 본문이다. 크기가 커지면 serialization, memory copy, network byte, compression과 proxy CPU 비용이 증가할 수 있다.

- Buffered: 전체 body를 메모리에 준비한 뒤 처리
- Streaming: body를 작은 단위로 순차 처리

Streaming은 peak memory를 낮출 수 있지만 구현과 측정이 복잡해질 수 있다.

## 6. Timeout과 회복탄력성

### Timeout, Deadline과 Cancellation

- Timeout: 특정 호출을 기다릴 최대 시간
- Deadline: 최종 요청이 완료되어야 하는 절대 시각
- Cancellation: 상위 요청 종료 시 진행 중인 하위 호출과 작업도 중단

각 hop은 deadline까지 남은 budget을 전달한다. 독립 timeout만 두면 상위 요청이 끝난 뒤 하위 작업이 계속될 수 있다.

### Retry와 Retry Amplification

Retry는 실패 요청을 다시 시도한다. 성공률을 높일 수 있지만 장애 중 호출량을 증폭한다. 애플리케이션과 Mesh가 동시에 retry하지 않도록 owner와 budget을 정한다. Retry amplification은 원래 요청 대비 실제 하위 호출 증가 비율이다.

### Circuit Breaker와 Bulkhead

- Circuit Breaker: 실패가 지속되는 target을 일정 시간 빠르게 차단
- Bulkhead: 동시 처리량이나 자원 pool을 격리해 한 장애가 전체를 소진하지 않게 함

### Fault Injection

delay, HTTP error, connection reset, Pod kill, worker stop을 의도적으로 발생시켜 장애 행동과 복구를 검증한다. 범위, 지속 시간, 강도와 cleanup을 제한한다.

## 7. 성능 지표

### Latency와 분위수

- p50: 절반의 요청이 이 시간 이하
- p95: 95%의 요청이 이 시간 이하
- p99: 99%의 요청이 이 시간 이하

평균은 느린 꼬리 요청을 숨길 수 있으므로 분위수를 함께 본다.

### Throughput과 RPS

Throughput은 단위 시간당 성공적으로 처리한 작업량이다. HTTP는 RPS, Kafka는 messages/sec로 표현한다.

- Target RPS: 발생시키려 한 요청률
- Achieved RPS: 실제 발생 또는 처리된 요청률

차이가 크면 부하 발생기 포화, dropped iteration 또는 target 포화를 확인한다.

### Error Rate

전체 요청 중 실패 비율이다. HTTP error, timeout, reset과 validation failure를 구분한다.

### Saturation과 CPU Throttling

Saturation은 CPU, thread, connection이나 queue가 한계에 가까워 처리량이 더 늘지 않는 상태다. CPU throttling은 컨테이너가 CPU limit 때문에 실행 시간을 제한받는 현상이다.

### Consumer Lag와 Backlog Drain Time

- Consumer Lag: 발행됐지만 아직 소비되지 않은 메시지 차이
- Backlog Drain Time: 발행 중단 후 남은 queue를 모두 처리하는 시간

### Resource Overhead

기준선 대비 추가된 CPU, memory, network와 latency 비용이다.

```text
absolute overhead = mesh value - baseline value
relative overhead = (mesh value - baseline value) / baseline value
```

작은 기준값은 상대 비율을 과장할 수 있어 절대값과 상대값을 함께 제시한다.

## 8. 실험 설계

### 독립·종속 변수와 고정 조건

- 독립 변수: 의도적으로 바꾸는 한 조건. 예: No Mesh → Sidecar
- 종속 변수: 변화에 따라 관측하는 결과. 예: p99, proxy CPU
- 고정 조건: image digest, Pod 배치, RPS, JVM과 telemetry처럼 바꾸지 않는 조건

### Confounding Variable

의도하지 않았지만 결과에 영향을 주는 혼란 변수다. 다른 노드 배치, background process, 서로 다른 이미지와 collector 포화가 예다.

### Warm-up과 Repetition

Warm-up은 JIT compilation, connection과 cache를 안정화하는 본 측정 전 구간이다. Repetition은 같은 조건의 반복이며 핵심 결론에는 최소 3개 유효 run을 요구한다.

### Run, ExperimentSpec, Manifest와 Ground Truth

- Run: 고유 `experimentRunId`를 가진 단일 실행
- ExperimentSpec: Profile, Scenario, seed, workload, load와 fault 명세
- Run Manifest: commit, image digest, 플랫폼, 배치, 자원, JVM과 telemetry 기록
- Ground Truth: 실제 배포·적용된 상태의 snapshot

### Invalidation

시간 동기화 실패, 부하 발생기 포화, telemetry 누락, Pod 재시작이나 cleanup 실패로 결과를 사용할 수 없다고 판정한다. run을 삭제하지 않고 `INVALID`로 보존한다.

### Before/After, Regression과 Rollback

- Before/After: 동일 조건에서 개선 변경 전후 비교
- Regression Metric: 개선 중 악화되면 안 되는 지표
- Rollback Threshold: 변경을 되돌릴 정량 기준

한 번에 독립 변수 하나만 변경한다.

## 9. 관측과 추적

### Observability

Metric, log, trace와 network flow로 시스템 내부 상태를 설명하는 능력이다.

### Cardinality

Metric label 조합 개수다. request ID처럼 계속 달라지는 값을 label로 넣으면 시계열이 폭증하므로 unbounded label을 금지한다.

### Trace, Span과 ID

- Trace: 요청이 여러 서비스를 통과한 전체 흐름
- Span: 흐름의 개별 작업 또는 hop
- Correlation ID: 요청 하나의 log와 오류를 연결
- Experiment Run ID: 한 실험의 여러 요청을 연결

W3C `traceparent`를 전파해 app과 Mesh 구간을 연결한다.

### Sampling

모든 trace/log 대신 일부만 수집한다. 비용은 줄지만 희귀 오류가 빠질 수 있어 비율과 방식을 manifest에 기록한다.

## 10. Kubernetes와 배포

### Pod, Node와 Replica

- Pod: Kubernetes의 기본 실행 단위
- Node: Pod를 실행하는 VM 또는 서버
- Replica: 같은 서비스를 실행하는 Pod 수

Sidecar는 Pod마다 존재하고 ztunnel은 Node에서 공유되므로 배치와 replica가 비교 결과에 영향을 준다.

### Requests와 Limits

- requests: 스케줄링 시 보장받으려는 자원
- limits: 컨테이너가 사용할 수 있는 최대 자원

비교 중 값이 달라지면 성능 차이를 Mesh 때문이라고 단정할 수 없다.

### HPA

CPU, RPS, Kafka lag 같은 지표로 replica를 자동 조절하는 Horizontal Pod Autoscaler다. 어떤 metric을 사용할지가 개선 실험 대상이다.

### Helm

Kubernetes manifest를 template과 values로 패키징한다. 공통 Workload는 유지하고 Mesh 설정만 profile values로 분리한다.

### Cilium과 Hubble

- Cilium: Kubernetes network와 NetworkPolicy를 제공하는 CNI
- Hubble: Cilium 기반 network flow 관측 도구

Mesh metric만으로 설명하기 어려운 연결과 drop을 확인하는 Evidence로 사용한다.

## 11. 프로젝트 서비스

| 서비스 | 역할 |
|---|---|
| benchmark-gateway | 측정 traffic 진입과 Scenario route |
| orchestrator-service | Sync Chain과 Fan-out 조정 |
| workload-service | delay/error/resource/payload Target |
| producer-service | Kafka benchmark task 발행 |
| worker-service | task 처리, 멱등성과 lag 실험 |
| experiment-runner | 환경 적용, k6 실행, 수집과 cleanup |
| web-console | 선택적 상태·결과 조회; 부하 생성 안 함 |

## 12. 결과 해석 원칙

- “가장 빠른 Mesh” 하나를 고르는 프로젝트가 아니다.
- 기능 범위가 다른 profile을 같은 기능처럼 비교하지 않는다.
- 평균보다 분포와 p95/p99를 본다.
- 상대 변화와 절대 변화를 함께 본다.
- app, Sidecar, ztunnel, Waypoint와 node 자원을 분리한다.
- 실패한 개선과 회귀도 기록한다.
- 결론은 사용한 하드웨어, 버전, Workload와 부하 범위 안에서만 유효하다.

## 관련 문서

- [프로젝트 개요](00-project-overview.md)
- [범위와 성공 기준](01-scope-and-success-criteria.md)
- [아키텍처](02-architecture.md)
- [전체 Phase](phases/README.md)
- [실험 계획](experiments/README.md)
- [현재 체크포인트](CURRENT.md)
