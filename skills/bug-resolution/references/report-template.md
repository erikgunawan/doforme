# doforme analysis report

## Context

- contract_version: 2
- stage: analyze
- analysis_status: complete | blocked
- repository: <target name/root>
- revision: <verified revision or unknown>
- issue_ref: <local file, URL, inline, or unknown>
- summary: <one sentence>
- expected: <intended behavior and its basis, or unknown>
- actual: <reported/observed behavior, or unknown>
- environment: <known versions and trigger, or unknown>

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

## Issue validity

- verdict: valid_bug | not_a_bug | duplicate | needs_information
- rationale: <reason referencing E IDs; missing details if any>
- duplicate_of: <verified reference or none>

## Evidence

| ID | Provenance | Location | Observation | Limitations |
| --- | --- | --- | --- | --- |
| E1 | source / test_source / user_report / existing_log | path:line-line or supplied context | factual finding | what it does not prove |

If no usable evidence exists, say so instead of fabricating a row.

## Reproduction

- status: not_run | user_reported
- inspected: <test source or supplied logs, with E IDs, or none>
- proposed_check: <minimal reproduction and expected result, not executed>
- reason_not_run: <read-only tool boundary and any missing environment>

## Root-cause hypotheses

For each grounded hypothesis:

- id: H1
- claim: <trigger → failing condition → observed behavior>
- supports: <E IDs>
- contradicts: <E IDs or none observed>
- confidence: low | medium | high — <reason>
- falsification: <specific check that could disprove the claim; not executed>

If no hypothesis is grounded, state `none` and explain the evidence gap.

## Confidence

- technical_confidence:
  - validity: low | medium | high — <reason>
  - root_cause: low | medium | high — <reason and unresolved alternatives>
- requirements_status: verified_for_scope | needs_information | conflict — <reason>
- technical_validation: not_run
- business_acceptance: not_evaluated
- resolution_status: not_established

## Acceptance traceability

| AC / R / S IDs | Related E / H IDs | Contradiction or gap | Proposed observable verification |
| --- | --- | --- | --- |
| AC1 / R1 / S1 | E/H IDs or gap | finding | proposed check, not executed |

## Next steps

| Priority | Action | Purpose / evidence gap | Requires execution or mutation? |
| --- | --- | --- | --- |
| 1 | concrete bounded proposal | what it establishes | no / execution / mutation |

## Limitations and handoff

- Missing inputs/access and unverified assumptions: <explicit list or none>
- Source changes: none; execution: none; persisted state: none.
- Ready for future planning: yes | no — <why, using dependency contract>
- Clarifying questions: <specific questions or none>

Planning readiness is a recommendation only; no downstream command is invoked.
