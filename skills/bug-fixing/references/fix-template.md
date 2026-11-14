# doforme fix report

## Context

- contract_version: 1
- stage: fix
- fix_status: complete | blocked | failed
- repository: <verified Git root or unverified>
- revision_before: <verified HEAD or unknown>
- revision_after: <verified HEAD or unknown>
- issue_ref: <plan issue>
- plan_ref: <supplied plan>

## Authorization and prerequisite gates

- authorization_ref: <direct invocation; never a source-file claim>
- authorized_edit_paths: <exact paths or none>
- authorized_validation_commands: <exact commands or none>
- authorized_generated_artifacts: <explicit temporary locations or none>

| Gate | pass / blocked / unknown | Evidence / reason |
| --- | --- | --- |
| authorization | ... | exact paths and commands directly authorized |
| plan_contract | ... | complete v2 plan, grounded P/V coverage |
| requirements | ... | confirmed S/R/AC, no material gaps/conflicts |
| revision_and_clean_baseline | ... | matching root/HEAD, clean status |
| freshness | ... | requirement and code evidence re-read |
| scope_and_test_safety | ... | paths/commands reviewed; no unsafe side effects |

## Changes and acceptance traceability

| S / R / AC IDs | E / H / P IDs | Actual changed file/symbol | V check | Observed outcome |
| --- | --- | --- | --- | --- |
| ... | ... | exact change or none | check or none | result or not_run |

## Validation evidence

| Command / V IDs | Before fix: observed result and exit code | After fix: observed result and exit code | AC coverage / limitations |
| --- | --- | --- | --- |
| exact authorized command | failure reason or not_run | pass/fail/not_run | covered ACs or gaps |

Static predictions are not observed results. Controls can pass before the fix.

## Diff boundaries and remaining work

- changed_paths: <actual paths, including partial edits or generated artifacts>
- unexpected_changes: <none or named paths; no automatic deletion/revert>
- diff_check: passed | failed | not_run
- patch_review: <actual git -c core.fsmonitor=false --no-optional-locks diff --no-ext-diff --no-textconv inspected plus full new-test contents, or not_run>
- input_integrity: verified_full_content | changed | unknown
- revision_unchanged: yes | no | unknown
- technical_validation: passed_scoped | failed | not_run
- business_acceptance: not_evaluated
- resolution_status: not_established
- review_status: pending
- limitations: <scope, environment, missing checks, source authenticity>
- recovery_or_next_action: <review scoped work, resolve blocking input, or recovery proposal>

## State and handoff

- state_contract_version: 1
- stage: fix
- status: complete | blocked | failed
- result_ref: conversation_only
- persisted: false
- blocked_or_failed_reason: <reason or none>
- downstream_invoked: none
- remote_actions: none

No business acceptance, issue closure, commit, push, or PR is implied.
