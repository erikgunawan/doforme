# doforme PR preparation

## Context and prerequisite gates

- contract_version: 1
- stage: pr
- pr_status: complete | blocked
- repository: <verified root>
- revision: <verified HEAD>
- issue_ref: <verified reference or unknown>
- plan_ref / fix_ref / test_ref / review_ref: <explicit artifacts>
- gates: <contracts, identity/revision, AC coverage, review pass, current bindings,
  diff boundaries, source authority: pass/blocked with evidence>

## Draft proposal

- draft_ready: yes | no
- title: <concrete title or none when blocked>
- body: <copyable Markdown: symptom, confirmed requirements, scoped change,
  AC/test/command evidence, review/acceptance status, risk and missing checks>

## Publication and acceptance boundaries

- publication_ready: no
- remote_created: false
- issue_closed: false
- business_acceptance: not_evaluated | <explicit read owner acceptance reference>
- resolution_status: not_established
- human_review: pending
- content_binding: verified | stale | unknown
- remote_actions: none
- missing_publication_inputs: <repository write access, branch/base, publish
  authorization, human decision, business evidence as applicable>
- next_action: <human review/acceptance and separately authorized publication>

## State and handoff

- state_contract_version: 1
- stage: pr
- status: complete | blocked
- result_ref: conversation_only
- persisted: false
- downstream_invoked: none
