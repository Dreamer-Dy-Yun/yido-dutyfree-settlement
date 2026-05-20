# role-reference-map.md

## 역할별 참조 문서

### Orchestrator
- `common-rules.md`
- `role-reference-map.md`
- `orchestrator.md`
- 필요 시 현재 plan/review 관련 기준 문서

### Sub-Agent
- `common-rules.md`
- `role-reference-map.md`
- `sub-agent.md`
- 할당된 todo 문서

### QA
- `common-rules.md`
- `role-reference-map.md`
- `qa.md`
- 할당된 review 문서

## 역할별 읽기/수정 범위

### Orchestrator (작성/갱신 가능)
- `plan/active/*`
- `todo/*`
- `review/*` (QA 대상)
- `plan/done/*`, `plan/archived/*` (이동/정리)
- `done/*` (참조)

### Sub-Agent (read-only)
- `plan/active/*`
- `todo/*`(본인 할당 항목)
- todo 지정 범위 외의 `common` 규칙 문서

### QA (read-only)
- `plan/*`, `todo/*`, `review/*`, `done/*`의 지정 항목

## 문서 간 의존성 규칙
- Orchestrator는 `todo` 작성 시 반드시 `plan/active`를 기준으로 한다.
- Sub-Agent는 `todo` 규칙대로 작업 후 `review`를 작성한다.
- QA는 `review`로부터 done 이동 여부를 판단한다.
- 역할별 문서 변경 시 `role-reference-map.md`를 먼저 점검/갱신한다.
