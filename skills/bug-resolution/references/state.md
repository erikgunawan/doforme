# State contract v1 — conversation-only stage results

Neither analyze nor plan writes state, including no `.doforme` directory.
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
concurrency rules before enabling retries/resume. None exists in v0.3.
Report status is computed from evidence on each invocation; no report implies
an automatic transition. A blocked plan must identify its failed prerequisites
and contain no implementation steps. State/graph contract versions remain 1. Analyze and plan result contracts
are v2 to require business requirement evidence and acceptance traceability.
Stage completion still never implies business acceptance or issue resolution.
