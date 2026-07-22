# 현재 작업 상태

이 파일은 세션 재개를 위한 단일 체크포인트다. 작업을 시작하거나 종료할 때 반드시 갱신한다. 완료 주장은 체크리스트와 Evidence가 일치할 때만 기록한다.

## 현재 위치

- Project: Mesh Performance Lab
- Overall Phase: Phase 1 — Benchmark Workload 구현
- Application Step: A3 — Sync Chain 시작 전
- Status: ready
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

## 다음 작업

1. A3 `/workloads/chain` contract와 hop route를 구현한다.
2. 절대 deadline을 남은 budget으로 전파하고 timeout/cancellation을 검증한다.
3. hop별 trace와 완료 hop 수를 확인한다.

## 현재 한계

- 실제 Workload API는 ping 골격 외에 구현되지 않았다.
- 성능 측정값은 아직 없다.
- Control Plane 인증 상세는 Phase 3 전에 ADR로 확정한다.

## 마지막 검증

- `java -version`: Temurin 25.0.3
- Java 서비스 5개 `gradlew test`: passed
- Compose 6개 healthy, ID/trace 전파와 config/Prometheus E2E: passed
- Git: `main`과 `origin/main` 동기화
- Latest commit at checkpoint creation: `1d5384c`

## 재개 절차

1. 이 파일과 [전체 체크리스트](checkpoints/phase-checklists.md)를 읽는다.
2. `git status -sb`와 현재 브랜치를 확인한다.
3. 진행 중 체크포인트의 미완료 항목부터 시작한다.
4. 변경 근거, 검증 결과와 다음 작업을 이 파일에 갱신한다.
