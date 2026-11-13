# doforme repair plan

## Context

- contract_version: 2
- stage: plan
- plan_status: complete | blocked
- repository: <current target>
- revision: <verified revision or unknown>
- issue_ref: <analysis issue identity>
- analysis_ref: <supplied report location or inline>
- summary: <intended repair, or why blocked>

## Dependency gates

| Gate | Result (pass / blocked / unknown) | Evidence / reason |
| --- | --- | --- |
| analysis_contract | ... | supported complete analyze report |
| requirements | ... | confirmed applicable sources and ACs, complete material coverage, no conflict |
| requirement_freshness | ... | material source snapshots re-read; provenance and versions checked |
| validity | ... | valid_bug and expected/actual contradiction |
| cause_and_confidence | ... | grounded H/E IDs; medium/high cause confidence |
| identity | ... | same target and issue; checkout-path differences explained |
| source_freshness | ... | material evidence re-read and corroborated |
| material_gaps | ... | essential gaps resolved |
| revision_binding | ... | verified revision or explicit unknown |

Only revision_binding may remain unknown in a complete read-only proposal.

## Evidence revalidation

| Analysis E/H ID | Current location | Current observation | Matches analysis? |
| --- | --- | --- | --- |
| ... | path:line-line | observation based on content actually read | yes / no / unknown |

No evidence available: state that instead of inventing rows.

## Requirement sources

| S ID | Kind | Origin | Locator actually read | Version | Access / read_status | Authority / confirmation reference | Freshness / limits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | business_document / jira / figma / repository_spec / user_confirmation | original reference | file:lines or inline | known or unknown | access / status | explicit applicability or unconfirmed | observed limits |

## Requirements and acceptance criteria

- requirements_status: verified_for_scope | needs_information | conflict

| R ID | Requirement and scope/exceptions | S ID / locator | Basis (explicit / interpretation / unknown) | AC coverage |
| --- | --- | --- | --- | --- |
| R1 | statement | reference | basis | AC IDs or gap |

| AC ID | R/S links | Conditions / input | Observable expected outcome | Basis (explicit / proposed) | confirmation_ref | Verification method |
| --- | --- | --- | --- | --- | --- | --- |
| AC1 | R1 / S1 | condition | expected result | basis | source reference or unconfirmed | proposed check |

## Requirement conflicts and gaps

- Conflicts: <competing S/R/AC statements, impact, resolution reference or unresolved>
- Material gaps/interpretations: <affected criteria, questions and who must clarify>
- Unavailable optional sources: <why they do not affect material scope, or none>

## Acceptance traceability

| AC / R / S IDs | Evidence / hypothesis | P step IDs | V check IDs / observable expected outcome | Coverage gap |
| --- | --- | --- | --- | --- |
| AC1 / R1 / S1 | E/H IDs | P1 | V1 / grounded outcome | none or explicit gap |

Every material AC and proposed change needs coverage; a gap blocks the plan.

## Implementation steps

For each proposed step:

- id: P1
- depends_on: <earlier P IDs or none>
- target: <path/symbol; existing or proposed new file>
- change: <bounded intended change, no patch>
- rationale: <S/R/AC/E/H IDs and causal reasoning>
- acceptance: <observable outcome>

Blocked plan: `none — prerequisites not satisfied`.

## Validation plan

| V ID / proposed check | AC IDs | Before fix | After fix | Purpose / tooling basis |
| --- | --- | --- | --- | --- |
| V1 / check | AC1 | expected failing behavior | expected corrected behavior | rationale |

- execution_status: not_run
- technical_validation: not_run
- business_acceptance: not_evaluated
- resolution_status: not_established
- absent tooling or environment: <limitations or none>
- Unconfirmed test ideas (non-gating): <proposals needing confirmation; excluded
  from implementation acceptance and test-file scope, or none>
- Consistency check: <P acceptance and V outcomes agree; controls distinguished
  from expected failing regressions; no executed outcome claimed>

## Risks and rollback

- risks: <scope/compatibility risks and mitigations>
- rollback: <bounded revert/recovery proposal, never performed>
- assumptions: <explicit list or none>

## State and handoff

- state_contract_version: 1
- stage: plan
- status: complete | blocked (matches plan_status)
- result_ref: conversation_only
- persisted: false
- blocked_reason: <specific dependency failure or none>
- ready_for_fix: no
- next_action: <review proposal, supply inputs, or rerun analyze>
- write_scope: none; execution: none; downstream_invoked: none.

A complete proposal does not mark fix/test/review/PR complete or authorize writes.
