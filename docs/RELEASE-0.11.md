# Local release candidate 0.11.0

This is a local installation candidate, not a published release or a claim of
production readiness. No GitHub push/PR, workflow activation, account secret, or
Telegram message is part of this phase. Distribution license/icon decisions
remain with the owner.

## Reproduced and corrected issues

Ten new regression tests first failed against 0.10.0. They demonstrated:

- requirement path aliases were not canonicalized before write-scope overlap;
- existing source could be declared as a temporary artifact;
- a completed non-bug analysis became a workflow failure rather than a triage stop;
- status did not require every prerequisite/evidence artifact or verify displayed reports;
- a named pipe could be opened by snapshotting and hang the host;
- inherited Git redirection/helper settings were not isolated, and a repository
  external-diff helper could run during supposedly read-only host inspection.

0.11 canonicalizes configured paths, rejects duplicate/overlapping scopes, and
requires scratch artifacts to be new files at initialization. Legitimately
created artifacts can survive a verified idempotent resume. Requirement sources
remain read-only even when the config used `./` aliases.

Stage completion is separate from permission to advance: not_a_bug/duplicate
analysis or changes_requested review stops the workflow as blocked. Explicit
retry cannot skip that gate. Status and resume now share prerequisite/report/
evidence checks; a complete flag alone cannot establish completion. Displayed
report JSON/Markdown must match the verified history artifact.

Snapshot and checkpoint readers reject non-regular files before opening them.
Git inspection clears inherited GIT_* redirection, disables global/system config
and fsmonitor, avoids optional index locks, and uses no-ext-diff/no-textconv.
Agent Git calls require the corresponding safe prefix; plain helper-enabled
Git inspection is rejected by trace audit. Stage methods and allowed tools use
the same command shapes.

## Verification

Seventy-three deterministic tests pass, including the original ten reproductions
and tests for fsmonitor suppression, scratch-artifact resume, false completion,
negative review gates, and unsafe model Git calls. These are actual local tests;
mocked executor cases do not imply a new real-model full run. The earlier
six-stage real model run is recorded under version 0.9 in [phase history](PHASES.md).
No new model-based business acceptance is claimed.

The release archive is built from the local commit using git archive plus gzip
with fixed metadata, then extracted to a fresh directory. Verify metadata and
all command/agent/skill resources with Claude's validator and the local checker.
Archive checksum and exact commit belong in the external verification file,
not a self-referential checksum inside the source commit.

Catalog checks still report missing license/icon and marketplace installation
advice. Local --plugin-dir loading does not require publication. Runner scope
audits remain post-call checks, not an OS sandbox or authority attestation.
A changed plugin policy deliberately invalidates old checkpoints; no silent
migration through stronger gates is performed.
