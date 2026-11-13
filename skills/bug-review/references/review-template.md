# doforme review report

## Context and gates

- contract_version: 1
- stage: review
- review_status: complete | blocked
- verdict: pass | changes_requested | blocked
- repository: <verified root or unknown>
- revision: <verified HEAD or unknown>
- issue_ref: <same issue>
- plan_ref / fix_ref / test_ref: <explicit artifacts>
- prerequisite_gates: <contracts, revisions, requirement authority, material
  coverage, snapshot bindings, dirty-path scope: pass/blocked with evidence>

## Findings

| ID / priority | File:line | Trigger / defect / impact | S/R/AC and evidence | Requested correction |
| --- | --- | --- | --- | --- |
| ... | actually read location | concrete finding or none | grounded links | proposal only |

## Review evidence and limitations

- inspected_patch_and_files: <actual inspected paths/sections>
- ac_coverage_assessment: <confirmed ACs covered, missing or weakened assertions>
- content_binding: verified | stale | unknown — <computed bindings and gaps>
- security_and_regression: <concrete assessment, not universal safety guarantee>
- changed_during_review: none | <unexpected changes; do not revert>
- business_acceptance: not_evaluated
- resolution_status: not_established
- human_review: pending
- next_action: <correct findings, rerun validation, owner acceptance, or PR preparation>

## State and handoff

- state_contract_version: 1
- stage: review
- status: complete | blocked
- result_ref: conversation_only
- persisted: false
- downstream_invoked: none
- remote_actions: none
