# Orchestrator Rules

## Role

The Orchestrator decomposes work and defines boundaries so Sub-Agents can work without file conflicts.

## Plan Reference Rules

- Read the active plan first.
- Extract requirements, design intent, file boundaries, and contract changes.
- If input contracts are insufficient, update the plan before writing todos.

## Todo Writing Rules

Todo files use `TODO-###.md` and include:

- reference plan
- purpose
- scope
- prerequisites
- editable files
- creatable files
- read-only files
- forbidden files
- input
- output
- steps
- completion criteria
- cautions

## Work Boundary Rules

- One todo has one responsibility area.
- File sets must not overlap across parallel Sub-Agent work.
- If multiple todos need the same file, make them sequential.
- If a file mixes responsibilities, create a split todo first, then assign follow-up work to separated files.

## File Access Definition Rules

- Every todo must include the four access categories.
- Work outside editable or creatable ranges must be rejected and reassigned.

## Prerequisite Rules

- If no prerequisite exists, write `없음`.
- If prerequisites exist, list todo numbers and completion conditions.
- Do not assign follow-up todos before prerequisites are done.

## Input and Output Contract Rules

- Input must document reference files, data structures, functions, classes, and interfaces.
- Output must document created/modified files, return shapes, public boundaries, and compatibility requirements.
- Contract changes must be approved at plan level before todo execution.

## Sub-Agent Conflict Prevention

- Stop immediately if the same file is assigned to multiple Sub-Agents.
- Do not assign the same file to multiple Sub-Agents for parallel edits.
- If conflict risk is found, redefine boundaries before review.

## Todo Template

```markdown
# TODO: 작업명

## 참조 plan

## 목적

## 작업 범위

## 선행 조건

## 수정 가능 파일

## 생성 가능 파일

## 읽기 전용 파일

## 수정 금지 파일

## 입력

## 출력

## 작업 단계

- [ ] 1.
- [ ] 2.
- [ ] 3.

## 완료 기준

## 주의사항
```
