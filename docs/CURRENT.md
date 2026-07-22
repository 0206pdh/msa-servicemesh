# 현재 작업 상태

이 파일은 세션 재개를 위한 단일 체크포인트다. 작업을 시작하거나 종료할 때 반드시 갱신한다. 완료 주장은 체크리스트와 Evidence가 일치할 때만 기록한다.

## 현재 위치

- Project: Mesh Performance Lab
- Overall Phase: Phase 2 — 실험 자동화 로컬 구현 완료, VMware 검증 대기
- Application Step: A1~A7 구현 완료
- Status: validated-local
- Last updated: 2026-07-22

## 완료된 기준점

- [x] Phase 0 실험 방향, 공정성, Workload 경계 확정
- [x] Phase 0~11 상세 실행 문서 작성
- [x] Data/Control Plane OpenAPI lint 통과
- [x] Event/Result JSON Schema compile 통과
- [x] Java 25 설치 및 서비스 5개 Gradle test 통과
- [x] Compose 6개 서비스 healthy와 Gateway → Orchestrator smoke 확인
- [x] GitHub `0206pdh/msa-servicemesh` main 동기화
- [x] Mesh, Benchmark, Workload와 측정 용어 기준 문서화
- [x] A2~A6 bounded workload와 Compose 7-container E2E
- [x] Phase 2 runner, k6 profile, Ground Truth/raw/summary 구현
- [x] 같은 Compose smoke spec 3회 반복과 무효화 판정

## 다음 작업

1. Phase 3에서 VMware Kubernetes cluster와 관측 stack을 구축한다.
2. Kubernetes adapter의 telemetry/headroom/fault cleanup gate를 실측한다.
3. 유효한 No Mesh baseline 측정 전에는 개선 구현을 시작하지 않는다.

## 현재 한계

- 성능 측정값은 아직 없다.
- 로컬 Compose runner 결과는 자동으로 `INVALID` 처리되며 성능 Evidence로 사용할 수 없다.
- Kubernetes telemetry/headroom/fault cleanup 검증은 Phase 3 환경이 있어야 완료된다.
- Control Plane 인증 상세는 Phase 3 전에 ADR로 확정한다.

## 마지막 검증

- `java -version`: Temurin 25.0.3
- Java 서비스 5개 `gradlew test`: passed
- Compose 7개 healthy, chain/fanout/payload/async E2E: passed
- Python runner unit test: passed
- Docker k6 동일 spec 3회: artifact 생성, Compose adapter 무효화 passed
- Git: 이번 변경은 최종 검증 후 push 예정

## 재개 절차

1. 이 파일과 [전체 체크리스트](checkpoints/phase-checklists.md)를 읽는다.
2. `git status -sb`와 현재 브랜치를 확인한다.
3. 진행 중 체크포인트의 미완료 항목부터 시작한다.
4. 변경 근거, 검증 결과와 다음 작업을 이 파일에 갱신한다.
