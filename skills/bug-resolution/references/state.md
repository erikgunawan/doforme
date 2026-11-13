# State contract v1 — future design

Milestone 1 writes no state, including no `.doforme` directory. Reports are
conversation results. This document reserves a small provider-neutral vocabulary,
not a database schema or a promise of resume support.

A future state record should carry `contract_version`, `run_id`, `issue_ref`,
`repository`, `revision`, `stage`, `status`, `result_ref`, and `blocked_reason`.
Use an explicit revision and issue identity to prevent reuse across unrelated
targets; unknown revision must be revalidated before a later mutation.

Proposed statuses: `pending → running → complete | blocked | failed`.
`complete` means the stage produced a valid result, not that a bug is fixed.
Validity and confidence remain separate fields of the analyze result. Resume
must check prerequisites and freshness; it must not treat file existence alone
as completion. A later implementation must choose storage, atomic updates, and
concurrency rules before enabling retries/resume. Do not build these in v0.1.
