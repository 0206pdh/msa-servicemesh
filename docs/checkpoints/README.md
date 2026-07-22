# 체크포인트 운영 규칙

## 목적

Phase 진행 상태, 근거와 다음 시작점을 저장소에 남겨 세션이나 작업자가 바뀌어도 동일한 기준으로 재개한다.

## 필수 파일

- [현재 상태](../CURRENT.md): 프로젝트 전체에서 하나만 유지하는 재개 지점
- [전체 Phase 체크리스트](phase-checklists.md): Phase 진입·종료 Gate
- [체크포인트 템플릿](checkpoint-template.md): 작업 묶음별 진행 기록
- `docs/evidence/`: 검증 원본과 결론

## Phase 3 체크포인트

- [VMware 노드 사전 준비](phase-03-p1-vmware-node-prerequisites.md): 완료
- [Kubernetes 3노드와 Cilium/Hubble](phase-03-p2-kubernetes-cilium.md): 완료
- [MetalLB와 Cilium Gateway API](phase-03-p3-network-entrypoint.md): 완료
- [Prometheus/Loki/Tempo/OTel 관측 기반](phase-03-p4-observability.md): 완료
- [No-mesh Workload Helm 배포](phase-03-p5-no-mesh-workload.md): 완료
- [Workload NetworkPolicy](phase-03-p6-network-policy.md): 완료
- [Kubernetes runner와 telemetry Gate](phase-03-p7-kubernetes-runner-gates.md): 완료

## 갱신 시점

다음 시점마다 체크포인트를 갱신한다.

1. Phase 또는 Application Step 시작 직전
2. API/Schema/아키텍처 결정 직후
3. 의미 있는 구현 묶음과 테스트 완료 후
4. 실패, blocker 또는 실험 무효화 발생 시
5. 커밋·푸시 전후
6. Phase 종료 Gate 판정 시

## 상태 정의

- `planned`: 범위와 완료 조건만 확정
- `in-progress`: 구현 또는 검증 진행 중
- `blocked`: 외부 입력 없이는 진행 불가능
- `validated`: 기능과 검증 경로 통과
- `measured`: 반복 가능한 정량 결과 확보
- `rejected`: 가설 또는 개선 효과가 기준 미달
- `invalid`: 결과를 사용할 수 없는 실행

## 완료 규칙

- 체크박스만으로 완료 처리하지 않는다.
- 검증 명령과 결과, Evidence 경로, commit을 연결한다.
- 실패 테스트와 알려진 한계를 숨기지 않는다.
- 다음 Phase의 입력이 준비되지 않으면 현재 Phase를 닫지 않는다.
- `CURRENT.md`, Phase 체크리스트와 Evidence의 상태가 서로 다르면 가장 보수적인 상태를 따른다.
