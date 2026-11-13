# doforme repair plan

Synthetic plan fixture. The smoke harness replaces FIXTURE_HEAD with the exact
clean disposable repository HEAD after committing fixture inputs. This file is
then a named, untracked, read-only plan input; it is never an authorized output.

## Context

- contract_version: 2
- stage: plan
- plan_status: complete
- repository: Pagination fixture (current disposable target Git root)
- revision: FIXTURE_HEAD
- issue_ref: ISSUE.md
- analysis_ref: ANALYSIS.md (synthetic v2 report)
- summary: Correct the final-page endpoint and test confirmed AC1–AC3 only.

## Dependency gates

All material analyze/requirement/identity/source gates pass for the supplied
synthetic fixture; re-read them before mutation. Revision binding must match the
actual Git HEAD substituted above. This report grants no write authorization.

## Evidence revalidation

- E1: ISSUE.md:1-5 reports the final partial page incorrectly returns [].
- E2: README.md:3-5 requires all remaining items.
- E3/H1: pagination.py:1-4 caps an exclusive endpoint at len(items) - 1.
- Current fixture content matches these findings; no tests were run by the planner.

## Requirement sources

- S1: synthetic business_document; origin REQUIREMENTS.md:11-15;
  supplied_snapshot/read; version 2026-11-13-fixture; scope authority confirmed
  by fixture owner at REQUIREMENTS.md:5-9; current for this exercise only.
- S2: synthetic user_confirmation; origin REQUIREMENTS.md:5-9,17-21;
  local_document/read; version 2026-11-13-fixture; explicit AC confirmation.
- Not authenticated live sources; no real business acceptance is implied.

## Requirements and acceptance criteria

- requirements_status: verified_for_scope
- R1: up to size items per zero-based page; explicit S1:13; AC3 covered.
- R2: final page includes all remaining items; explicit S1:14; AC1/AC2 covered.
- AC1: page([1,2,3,4,5],2,2) returns [5]; R2/S1/S2; explicit; confirmation REQUIREMENTS.md:5-9,19.
- AC2: page([1,2,3,4],1,2) returns [3,4]; R2/S1/S2; explicit; confirmation REQUIREMENTS.md:5-9,20.
- AC3: page([1,2,3,4,5],0,2) returns [1,2]; R1/S1/S2; explicit; confirmation REQUIREMENTS.md:5-9,21.

## Requirement conflicts and gaps

- Conflicts: none in original supplied inputs. Re-read them to detect changes.
- Material gaps: none for confirmed AC1–AC3; no extra rules should be inferred.
- Optional sources: Jira/Figma unnecessary for this function's confirmed scope.

## Acceptance traceability

| AC/R/S IDs | E/H IDs | P steps | V checks |
| --- | --- | --- | --- |
| AC1/R2/S1,S2 | E1,E2,E3/H1 | P1,P2 | V1 |
| AC2/R2/S1,S2 | E2,E3/H1 | P1,P2 | V2 |
| AC3/R1/S1,S2 | E3/H1 | P1,P2 | V3 |

## Implementation steps

- P1, depends_on none: create test_pagination.py using unittest and only the three
  confirmed AC assertions. Target is a new file. Acceptance: assertions exactly
  match AC1–AC3; observe V1/V2 fail because of endpoint, V3 pass as control.
- P2, depends_on P1: edit pagination.py line 3 to cap the exclusive endpoint at
  len(items) instead of len(items) - 1. Do not alter signature or requirements.
  Acceptance: V1/V2/V3 pass. R2/E3/H1 justify this one-line correction.

## Validation plan

- Proposed command: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination
- V1/AC1: predicted assertion failure before fix ([] vs [5]), pass after.
- V2/AC2: predicted assertion failure before fix ([3] vs [3,4]), pass after.
- V3/AC3: predicted pass before and after ([1,2] control).
- execution_status: not_run
- technical_validation: not_run
- business_acceptance: not_evaluated
- resolution_status: not_established
- No runtime dependencies or test configuration. Python standard library unittest
  suffices. The fixture is originally for source inspection; a separate direct
  smoke invocation explicitly authorizes execution only in its disposable copy.
- Unconfirmed ideas: excluded from test scope and acceptance.

## Risks and rollback

- Risks: external callers depending on the truncated final page would change;
  confirmed R2 requires correction. Input validation stays out of scope.
- Rollback proposal: restore the original endpoint and remove the new test file;
  never perform destructive recovery automatically.
- Assumptions: Python 3 standard slice behavior; synthetic source provenance.

## State and handoff

- state_contract_version: 1
- stage: plan
- status: complete
- result_ref: conversation_only
- persisted: false
- blocked_reason: none
- ready_for_fix: no
- write_scope: none; execution: none; downstream_invoked: none.
- next_action: explicit direct invocation authorizes exact paths/command and
  independently revalidates every prerequisite before any edits.
