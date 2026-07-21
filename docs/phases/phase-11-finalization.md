# Phase 11 — 최종화와 재현

## 목적

환경 종속성을 숨기지 않는 선택 Matrix와 제3자가 재현 가능한 결과 패키지를 만든다.

## 작업

1. Scenario와 요구 기능별 No Mesh/Sidecar/Ambient/Waypoint 선택 Matrix를 작성한다.
2. 권장 설정마다 적용 조건, 이득, 자원 비용, 기능 손실과 rollback 기준을 연결한다.
3. manifest → raw query/output → summary → graph → claim 링크를 검사한다.
4. 새 namespace 또는 재구성 환경에서 대표 실험을 재실행한다.
5. 버전, 하드웨어, 부하 범위와 외삽 금지 조건을 최종 보고서에 명시한다.

## 최종 산출물

- 재현 절차와 버전 고정 manifest
- raw/summary/report bundle과 실패한 개선 목록
- workload별 의사결정 Matrix
- 알려진 한계와 후속 backlog

## Gate

- 진입: Phase 4~10 Evidence 연결 완료
- 종료: 새 환경 대표 재현 성공, 깨진 링크 없음, 근거 없는 결론 없음
