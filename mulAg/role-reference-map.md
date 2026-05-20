# Role Reference Map

## Role Reference Documents

### Orchestrator

- `mulAg/common-rules.md`
- `mulAg/role-reference-map.md`
- `mulAg/orchestrator.md`

### Sub-Agent

- `mulAg/common-rules.md`
- `mulAg/role-reference-map.md`
- `mulAg/sub-agent.md`

### QA

- `mulAg/common-rules.md`
- `mulAg/role-reference-map.md`
- `mulAg/qa.md`

## Role File Access Ranges

### Orchestrator

- Read-only: `mulAg/common-rules.md`, `mulAg/role-reference-map.md`
- Editable: `mulAg/orchestrator.md`, `mulAg/md/plan/*`, `mulAg/md/todo/*.md`, `mulAg/md/review/*.md`
- Creatable: `mulAg/md/todo/*.md`, new plan documents under `mulAg/md/plan/`
- Forbidden: files outside the assigned orchestration scope

### Sub-Agent

- Read-only: `mulAg/common-rules.md`, `mulAg/role-reference-map.md`, `mulAg/orchestrator.md`, `mulAg/md/todo/*.md`
- Creatable: `mulAg/md/review/*.md`
- Editable: only files explicitly listed in the assigned todo
- Forbidden: files outside the assigned todo and files assigned to other Sub-Agents

### QA

- Read-only: `mulAg/common-rules.md`, `mulAg/role-reference-map.md`, `mulAg/orchestrator.md`, `mulAg/sub-agent.md`, `mulAg/qa.md`, `mulAg/md/`
- Creatable: `mulAg/md/done/*.md`
- Editable: workflow state documents only when moving reviewed work according to QA rules
- Forbidden: source files and work outputs outside QA scope

## Change Rule

- Update this document first when role reference ranges or document responsibilities change.
- If a conflict appears, realign work using `role-reference-map.md` and `orchestrator.md`.
