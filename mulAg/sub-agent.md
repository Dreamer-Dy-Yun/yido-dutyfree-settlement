# Sub-Agent Rules

## Role

A Sub-Agent executes only the assigned todo and records the result in `mulAg/md/review/`.

## Todo Reference Rules

- Treat the assigned todo file as the single execution standard.
- Follow its completion criteria, input/output contract, and permission ranges.
- Do not use unrelated plans or todos to expand scope.

## Execution Rules

- Modify only files listed in `수정 가능 파일`.
- Create only files listed in `생성 가능 파일`.
- Leave step-by-step completion notes in the review.
- Keep the work verifiable.

## File Modification Limits

- Files not allowed by the todo must not be read, modified, or deleted.
- If an out-of-scope file appears necessary, stop that part and record the issue in review.

## Creatable File Limits

- Review result documents may only be created under `mulAg/md/review/REVIEW-###.md`.
- Other generated files require explicit Orchestrator assignment in the todo.

## Scope Escape Handling

- Do not directly fix out-of-scope issues.
- Record the reason, affected file, and proposed next action under remaining issues and QA requests.

## Review Template

```markdown
# REVIEW: 작업명

## 수행 일시

YYYY-MM-DD HH:mm:ss

## 참조 plan

## 참조한 todo

## 수행 내용

## 변경 파일

## 생성 파일

## 미변경 파일

## 검증 내용

## 남은 이슈

## QA 확인 요청 사항
```
