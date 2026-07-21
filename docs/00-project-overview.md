# 프로젝트 개요

## 문제 정의

Service Mesh는 mTLS, 트래픽 정책과 telemetry를 공통 제공하지만 데이터 플레인 구조에 따라 지연, CPU, 메모리, Pod 시작시간과 장애 양상이 달라진다. 단순 echo benchmark나 공급자 홍보 자료만으로는 특정 온프레미스 환경과 실제 통신 패턴에 적합한 구성을 결정하기 어렵다.

Mesh Performance Lab은 통제 가능한 Java MSA Workload를 사용해 profile을 공정하게 비교하고, 결과에서 발견한 병목을 실제로 개선해 선택 근거를 만든다.

## 검증 가설

1. Sidecar의 Pod별 비용과 Ambient의 노드 공유 비용은 Pod 수 증가 시 다른 형태로 확장된다.
2. Waypoint는 L7 기능을 제공하지만 통과 트래픽과 replica에 따라 병목이 될 수 있다.
3. 앱과 Mesh의 중첩 retry는 장애 중 호출량과 tail latency를 증폭한다.
4. 전체 time budget과 단일 retry owner는 회복탄력성을 개선한다.
5. 선택적 Waypoint와 telemetry sampling은 필요한 기능을 유지하며 비용을 줄일 수 있다.
6. CPU 기반 HPA는 비동기 backlog에 적합하지 않고 queue lag 지표가 회복시간을 줄일 수 있다.

이는 사전 결론이 아니라 실험으로 기각될 수 있는 가설이다.

## 프로젝트 가치

- 재현 가능한 Workload, 부하, fault와 결과 schema 제공
- No Mesh/Sidecar/Ambient/Waypoint의 동일 조건 비교
- Metrics/Logs/Traces/Hubble과 프로파일링을 통한 병목 설명
- 개선 전후의 효과와 비용을 같은 지표로 비교
- 워크로드별 선택 Matrix와 rollback 조건 제공

## 설계 원칙

- Workload는 특정 profile에 유리하게 작성하지 않는다.
- 한 실험에서는 독립 변수 하나만 바꾼다.
- 기준선과 개선 실험은 동일 이미지 digest와 데이터셋을 사용한다.
- 부하 발생기는 대상 클러스터 자원과 분리하거나 포화 여부를 증명한다.
- 평균만 사용하지 않고 p50/p95/p99, 분포와 이상치를 공개한다.
- 통계적 차이와 실무적으로 의미 있는 절대 차이를 구분한다.
- 애플리케이션, proxy, ztunnel, Waypoint 자원을 분리해 측정한다.
- 실패한 최적화와 결론 불가 결과도 보존한다.
- 모든 결론은 적용 환경과 무효화 조건을 명시한다.

## 대상 독자

- Kubernetes/Platform/SRE Engineer
- Service Mesh 도입을 검토하는 팀
- Java MSA 성능과 회복탄력성을 분석하는 개발자
- 실험을 재현하고 반박하려는 리뷰어
