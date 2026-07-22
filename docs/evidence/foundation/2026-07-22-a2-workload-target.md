# A2 bounded Workload Target

- Status: validated
- Date: 2026-07-22
- Checkpoint: [A2](../../checkpoints/phase-01-a2-workload-target.md)

## 근거

Mesh 비용을 분리하려면 같은 seed/config가 같은 작업 선택과 payload checksum을 만들어야 하며, 실험 도구 자체가 노드를 무제한 고갈시키지 않아야 한다.

## 구현

- fixed/normal/exponential delay
- deterministic error selection
- CPU 10초, memory 64MiB, blocking I/O 10초 상한
- response 10MiB 상한과 SHA-256 checksum
- outcome/elapsed metric

## 검증

- 단위 테스트: 재현 checksum, fixed delay, error rate 1.0
- Compose: 동일 요청 2회 checksum 일치
- applied delay/memory와 metric 노출 확인

## 한계

- CPU 작업은 wall-clock busy loop이며 정밀 CPU instruction benchmark가 아니다.
- memory는 요청 수명 동안만 유지되고 장기 heap pressure는 별도 mixed scenario에서 다룬다.
