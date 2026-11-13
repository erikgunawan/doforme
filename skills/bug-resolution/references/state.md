# State contract v1 — conversation-only stage results

No stage writes durable workflow state, including no `.doforme` directory.
Fix may edit explicitly authorized source/test files and run scoped checks.
Reports are conversation results. Plan emits an explicit stage/status summary
with `result_ref: conversation_only` and `persisted: false`. This is a small
provider-neutral handoff vocabulary, not durable storage or resume support.

A future state record should carry `contract_version`, `run_id`, `issue_ref`,
`repository`, `revision`, `stage`, `status`, `result_ref`, and `blocked_reason`.
Use an explicit revision and issue identity to prevent reuse across unrelated
targets; unknown revision must be revalidated before a later mutation.

Proposed statuses: `pending → running → complete | blocked | failed`.
`complete` means the stage produced a valid result, not that a bug is fixed.
Validity and confidence remain separate fields of the analyze result. Resume
must check prerequisites and freshness; it must not treat file existence alone
as completion. A later implementation must choose storage, atomic updates, and
concurrency rules before enabling retries/resume. None exists in v0.4.
Report status is computed from evidence on each invocation; no report implies
an automatic transition. A blocked plan must identify its failed prerequisites
and contain no implementation steps. State/graph contract versions remain 1. Analyze and plan result contracts
are v2 to require business requirement evidence and acceptance traceability.
Stage completion still never implies business acceptance or issue resolution.

Fix adds a fix_v1 result with complete/blocked/failed status and exact partial
changes. Complete requires scoped technical validation; review remains pending,
business acceptance not_evaluated, and resolution not_established. A blocked fix
may already contain test edits if the regression could not be demonstrated; no
status may hide those edits. State remains a conversation-only summary.
