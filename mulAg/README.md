# mulAg (Multi Agents)

This folder contains the operating rules and workflow records for multi-agent work in this frontend worktree.

## Core Principle

File edit permission is more important than role separation. Work must be split into small units, and each unit must declare editable files, creatable files, read-only files, and forbidden files.

## Role Documents

| File | Responsibility |
| --- | --- |
| `common-rules.md` | rules shared by Orchestrator, Sub-Agent, and QA |
| `role-reference-map.md` | role-specific reference documents and document access ranges |
| `orchestrator.md` | plan and todo decomposition rules |
| `sub-agent.md` | todo execution and review writing rules |
| `qa.md` | review validation and done/plan lifecycle rules |

## Workflow Folders

| Path | Responsibility |
| --- | --- |
| `md/plan/active/` | active plans that need execution or todo decomposition |
| `md/plan/done/` | completed plans kept as decision records |
| `md/plan/archived/` | discarded, paused, or replaced plans |
| `md/todo/` | executable work units for Sub-Agents |
| `md/review/` | Sub-Agent result reports waiting for QA |
| `md/done/` | QA-approved completed work records |
