# doforme test report

## Context and gates

- contract_version: 1
- stage: test
- test_status: complete | blocked | failed
- repository: <Git root or unknown>
- revision: <verified HEAD or unknown>
- issue_ref: <same issue>
- plan_ref: <plan v2>
- fix_ref: <fix v1>
- authorization_ref: <direct invocation or none>
- authorized_commands: <exact list or none>
- authorized_artifacts: <exact temporary locations or none>
- prerequisite_gates: <plan/fix, identity/revision, requirement freshness,
  changed-path scope, assertions and runner safety: pass/blocked with reasons>

## Acceptance results

| S / R / AC IDs | Actual test/assertion / V IDs | Exact command | Exit and observed outcome | passed / failed / skipped / not_run |
| --- | --- | --- | --- | --- |
| ... | ... | ... | output evidence or none | status |

## Coverage and integrity

- required_coverage: <material ACs and agreed checks; named gaps>
- optional_checks: <not-run checks and why optional>
- prior_fix_evidence: <supplied evidence vs independently executed results>
- source_and_input_integrity: unchanged | changed | unknown — <full comparison>
- revision_unchanged: yes | no | unknown
- unexpected_changes: <none or exact paths; no auto-cleanup>
- diff_check: passed | failed | not_run
- technical_validation: passed_scoped | failed | not_run
- review_status: pending
- business_acceptance: not_evaluated
- resolution_status: not_established
- limitations_and_next_action: <specific missing evidence/failure/review proposal>

## State and handoff

- state_contract_version: 1
- stage: test
- status: complete | blocked | failed
- result_ref: conversation_only
- persisted: false
- downstream_invoked: none
- remote_actions: none
