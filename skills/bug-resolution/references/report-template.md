# doforme analysis report

## Context

- contract_version: 1
- stage: analyze
- analysis_status: complete | blocked
- repository: <target name/root>
- revision: <verified revision or unknown>
- issue_ref: <local file, URL, inline, or unknown>
- summary: <one sentence>
- expected: <intended behavior and its basis, or unknown>
- actual: <reported/observed behavior, or unknown>
- environment: <known versions and trigger, or unknown>

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

- validity: low | medium | high — <reason>
- root_cause: low | medium | high — <reason and unresolved alternatives>

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
