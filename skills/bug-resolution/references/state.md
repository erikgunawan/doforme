# State contracts

Stage report state summaries retain state_contract_version 1. Agents return
conversation results with persisted false. The explicitly invoked host runner
may persist those results in an authorized external private directory; this is
host_persisted true, not an agent permission to write state or modify the repo.

The checkpoint file has state_version 1: repository/HEAD, config and plugin policy
digests, exact workspace manifest, direct grants, results, artifact digests,
attempt counts, status, and any partial edits/manual-recovery requirement.
Updates are atomic; a single-owner lock prevents concurrent runners. Audit report
history is preserved. Only contiguous prerequisite stages can be restored.
Complete means the stage's evidence gate passed, never business issue resolution.

Status checks do not write. Resume verifies current bytes/revision/config/policy
and saved report integrity. Blocked/failed/interrupted work needs an explicit
retry (maximum two attempts). Partial source edits cannot be auto-retried. Stale
inputs/policy, different grants, edited reports, or unexpected files require
manual review and a new isolated run. No automatic reset, deletion or Git mutation.
Checkpoints detect accidental inconsistency, not malicious forgery by a person
with full control of both state and source. Supplied authority stays untrusted.
Graph contract is now v2 with host_checkpoint persistence and explicit_host_run;
there are no event-triggered transitions, remote publication or issue closure.
