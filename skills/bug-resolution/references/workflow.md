# Workflow graph contract v2

Implemented local sequence: `analyze → plan → fix → test → review → pr`.
Analyze/plan reports use v2; fix/test/review/pr reports use v1. Requirement and
stage-summary vocabularies remain v1. PR means draft content, never publication.

The portable [workflow.json](workflow.json) declares prerequisites, effects,
result contracts, host_checkpoint persistence and explicit_host_run orchestration.
The host adapter verifies the supported sequence/effects before execution and
checks [semantic gates](dependencies.md) via stage results plus trace/content
checks. A graph edge or complete status alone never grants authority.

Analyze/plan cannot mutate or execute. Fix requires direct exact edit/command
scope and a known matching revision. Test independently executes agreed checks
without file-edit tools. Review inspects content bound to the tested snapshot;
PR preparation requires review pass and current evidence. All source authority
and business assumptions follow [requirements.md](requirements.md).

`/endtoend` invokes the explicit host adapter in separate model contexts, passing
prior reports inline. `/status` reads a named checkpoint. Stage agents do not
write workflow state; the authorized host writes private atomic checkpoints,
locks and immutable attempt artifacts outside the target. Resume checks source,
revision, config, grants, report and policy digests, with bounded explicit retry.
Partial edits require manual review. See [state.md](state.md).

There are no implicit full-fix transitions, remote PRs, issue closure, or
non-Claude executor adapters in this graph. A separate inactive GitHub template
provides operator-opt-in intake/read-only analysis and new-issue Telegram
notification; it cannot authorize fix/publication or declare resolution. Technical completion does not establish business acceptance.
