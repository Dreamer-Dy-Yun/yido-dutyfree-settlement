# Common Rules

## Common Principles

- Prefer file edit permission separation over role separation.
- Split all work around responsibility boundaries.
- One todo must cover one responsibility area.
- End every change in a verifiable state.
- When features, API contracts, folder/file responsibilities, or module boundaries change, update the related documentation immediately.

## File Access Permission

Every todo must declare these four categories.

- Editable files: files the assigned Sub-Agent may modify directly.
- Creatable files: files the assigned Sub-Agent may create.
- Read-only files: files that may be referenced but not modified.
- Forbidden files: files that should not be read, modified, or deleted.

## Same-File Edit Restriction

- Do not assign the same file to multiple Sub-Agents at the same time.
- If the same file is needed by multiple tasks, do not run them in parallel. Split them into sequential todos.
- When needed, perform a responsibility-splitting task first, then assign later work to separated files.

## Work Unit Standard

- One todo has one clear purpose.
- Each todo must list its reference plan and prerequisites.
- Keep work units small and describe input/output contracts.
- Plans move through `plan/active`, `plan/done`, and `plan/archived`.

## Input and Output Contract Standard

- Input: reference files, contract data, existing interfaces, and interfaces that must not change.
- Output: created/modified files, public functions/classes, return formats, and compatibility notes.
- Contract changes must be reflected in a plan before being decomposed into todos.

## Plan Lifecycle

- `plan/active/`: plans in progress or needing todo decomposition.
- `plan/done/`: plans whose related todos and reviews are complete.
- `plan/archived/`: discarded, paused, or replaced plans.
- A plan can move to `done` only after all linked todo/review work is complete.

## Required Review Items

Review documents must include:

- execution time
- reference plan
- reference todo
- performed work
- changed files
- created files
- unchanged files
- verification
- remaining issues
- QA requests

## Done Rule

- Move work to `mulAg/md/done/` only after QA confirms the completion criteria.
- Confirm completion criteria, plan linkage, and file access permission compliance.
- Move completed plans to `plan/done/` as durable decision records.

## Forbidden Actions

- Modify files not listed in the todo.
- Modify files outside the editable file list.
- Create files outside the creatable file list.
- Edit the same file in parallel from multiple Sub-Agents.
- Run follow-up todos before prerequisites are complete.
- Move work to done without review.
- Change plans or todos without QA review when the workflow requires QA.
