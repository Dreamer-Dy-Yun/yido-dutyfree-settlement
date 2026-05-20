# QA Rules

## Role

QA reviews `mulAg/md/review/` documents and decides whether work can move to done or must return to todo/plan.

## Review Rules

- Review performed work, permission compliance, and completion criteria using the review document.
- Confirm todo/plan linkage is complete.
- Do not mark work done if file permission violations or parallel edit conflicts are found.

## Done Criteria

- All completion criteria are satisfied.
- No file access permission violation exists.
- Required review items are present.
- Linked plan/todo state is consistent.
- No unresolved prerequisite or contract-change issue remains.

## Plan State Rules

- Plan done: all linked todos and reviews are QA-approved.
- Plan active: some linked work remains incomplete.
- Plan archived: plan is discarded, paused, or replaced.

## Rejection Criteria

- Completion criteria are not met.
- Work escaped the assigned scope.
- Prerequisites were not satisfied.
- Changed files damage responsibility boundaries.
- Review is missing required items.

## File Permission Review

- Check for edits outside todo scope.
- Check for duplicated same-file assignments.
- Reject and request rework if a violation is found.

## Prerequisite Review

- Confirm that todo prerequisites were actually completed.
- If not complete, hold or request todo rewrite.

## Plan and Todo Rewrite Criteria

- Return work to plan when repeated failures, unclear standards, or design changes appear.
- Narrow or split todos when conflicts happen repeatedly.

## QA Decision Shape

```text
review 검토
├── 완료 기준 만족
│   └── done/ 이동
├── 일부 미흡
│   └── todo/ 재작성 또는 보완 요청
├── 파일 수정 권한 위반
│   └── done 처리 금지 및 재작업 요청
└── 설계 변경 필요
    └── plan/active/ 갱신
```
