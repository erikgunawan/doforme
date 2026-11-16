# Local phase history and verification

Earlier uncommitted work was reconstructed into coherent cumulative snapshots,
then committed without rewriting milestone 1. The 0.2/0.3 snapshots are phase
reconstructions, not claims of byte-for-byte historical working trees.

| Version | Phase | Local verification |
| --- | --- | --- |
| 0.1 | analyze plugin | existing f4b787b; validation in VALIDATION.md |
| 0.2 | planning and graph foundation | 10 tests; strict component validation |
| 0.3 | business requirement evidence | 11 tests; strict component validation |
| 0.4 | scoped fixes | 14 tests; strict component validation; recorded red/green fixture evidence |
| 0.5 | independent scoped testing | 16 tests; strict component validation; real model test passed AC1–AC3, no-authorization case blocked validation, both targets unchanged |

Version 0.5 model traces had no permission denials. Read-only Git inspection was
used in both cases; only the authorized case executed unittest. Test results do
not establish independent code review or business acceptance. Fixture inputs are
synthetic. No push or remote PR was made. Prior validation documents describe
what was true at the time of their original runs (including then-uncommitted work).


Version 0.6 adds independent review and content binding. Eighteen regression tests
and strict components passed. Actual model checks: matching tested content passed
review; a test file changed after validation was blocked despite the same HEAD.
Both review targets stayed byte-for-byte unchanged with no permission denials or
test execution. The stale report used inconsistent complete/blocked status wording;
the method now explicitly requires blocked status whenever verdict is blocked.
Advance gates must require both completion and verdict pass, never status alone.
Test reports now carry before/after Git blob IDs for every material input so
review can detect dirty-tree changes after testing. Scope authority and snapshots
remain supplied evidence, not authenticated live business acceptance.


Version 0.7 adds PR preparation only (no remote publication). Twenty tests and
strict components passed. Actual model runs prepared an evidence-backed draft
from a passing review and blocked a changes_requested review. The first positive
attempt appended an unauthorized echo helper; the command was denied. The method
was tightened to stop on denial and prohibit helpers; a fresh positive rerun had
no denials. All targets remained unchanged. Drafts retained pending business
acceptance and publication_ready no, with no invented issue number or remote PR.


Version 0.8 adds the sequential local CLI adapter and /endtoend entry point.
Thirty-four deterministic tests passed, including scope/authorization, tool audit,
actual test-result requirements, regression-before-fix evidence, and stop gates.
The first real adapter runs exposed unavailable automatic structured output in
restricted-agent mode and stopped without edits. Explicit raw JSON envelopes with
local validation fixed the protocol: a real missing-requirement run now returned
blocked at analyze with no downstream call. A positive real integration run was
started separately; final results are recorded in the subsequent state phase.
The adapter never publishes remotely, and complete means draft preparation only.


Version 0.9 adds graph v2, atomic private checkpoints, attempt history, single-run
locks, /status, fingerprint-checked resume, bounded explicit retry and partial-
edit recovery stops. Forty-six deterministic tests passed. A real blocked analyze
run persisted a checkpoint; after plugin policy changed, status correctly marked
it stale and resume refused without a model call or checkpoint mutation.
The positive adapter integration reached analyze/plan/fix/test complete with real
regression and independent validation. Review returned a valid pass envelope
preceded by one progress sentence; the strict initial parser stopped. The new
parser accepts exactly one complete JSON object after a short prefix while still
rejecting duplicate keys or multiple objects; the saved actual review trace
passed this parser, envelope validation and read-only audit offline. A fresh full
checkpoint integration is run after freezing this version; its final outcome is
recorded below when complete. No remote publication or business acceptance.


On 2026-11-14, the frozen 0.9 full real-model integration completed analyze,
plan, fix, test, review and PR draft in sequence. The runner's observed summary
reported every stage complete, fresh true, publication_ready false,
business_acceptance not_evaluated, resolution_status not_established and
remote_actions none. This exercised real scoped edits and test tool results,
independent review with content binding, and draft generation. No external PR.
Temporary run artifacts became unavailable after the execution environment reset;
the observed tool output remains the record. A second real resume/status check
could not be performed on those lost temp files. Idempotent resume is covered
by deterministic tests, not claimed as a second observed live run.

Version 0.10 adds inactive GitHub issue/Telegram integration, default dry-run,
explicit live opt-ins, no issue-body shell interpolation, trusted source paths,
fixed-host notification with uncertain-delivery receipts and no automatic retry.
It also persists actual validation tool outputs/exit evidence privately and filters
GitHub/Telegram credentials from model subprocesses. Fifty-eight deterministic
tests cover these changes with mock senders; no Telegram message or GitHub Actions
run occurred. Upstream action pins and Telegram API shape were checked against
official sources. Workflow YAML syntax and safety-critical configuration were
checked locally; actionlint was unavailable. Live activation requires owner review,
account/secrets, CLI/runner compatibility and separate publication approval.


Version 0.11 (2026-11-14) is the local release-hardening phase. Ten regression
reproductions failed on 0.10 before fixes; 73 tests passed afterward. Fixes cover
canonical requirement/scope aliases, existing-source artifact declarations,
non-bug/review handoff gates, full status/report/evidence integrity, special-file
snapshot blocking and Git helper/redirection suppression. See RELEASE-0.11.md.
No new real-model six-stage run is claimed; local deterministic checks and an
extracted release-candidate validation are the scope of this phase. No publication
or notification activation is included.

Version 0.12 (2026-11-15) adds repository onboarding through /doforme:init.
Default inspection is read-only; explicit --write creates only a reusable repo
profile and an unconfirmed requirement/AC template. Existing owner files are
preserved. Profiles hold reusable defaults and caps; explicit per-issue inputs
hold issue text and exact edit scope. Composition retains profile requirement
sources, rejects raised caps and protects active inputs. --inspect-config shows
the effective config without model calls, execution or checkpoint creation.
Legacy full configs remain supported without --profile. Shared local policy was
extracted without changing the workflow graph or adding external dependencies.

All 94 deterministic tests passed, as did the local structure/resource checks,
strict command/agent/skill validation and local plugin manifest validation.
A standalone CLI smoke in a disposable Git fixture verified inspection, exactly
two draft files, repeated setup preserving bytes, and effective-config preview.
A declared package script that would create a marker never ran; source and Git
HEAD remained unchanged. No new real-model command or six-stage run is claimed.
The plugin directory submission still needs an owner-selected license; the
validator also notes a missing catalog icon. These catalog checks do not change
the passing local-plugin verdict. No other real repo was initialized, and no
business acceptance, integration activation, push or PR is part of this phase.

Version 0.13 (2026-11-16) adds /doforme:doctor for read-only fresh-workflow
preflight. It checks local plugin structure, the selected Git root and revision,
clean baseline, bounded regular-file checkout, explicit profile/input composition,
source readability, full-workflow scope/commands, CLI presence and an optional
new external output path. No source/test/model execution, repair, installation,
authentication probe, checkpoint creation or remote action is performed.
Unchanged generated requirement drafts and empty sources block the local check.
Other readable source content remains semantically unevaluated; a passing local
preflight cannot grant execution or establish verified business requirements.
The workflow graph and existing runner gates remain unchanged.

All 113 deterministic tests passed (19 new), including standalone CLI positive
and blocked exit/report cases in disposable Git fixtures. Configured test code
and a sentinel Claude executable were never invoked; target content and HEAD
were preserved in the positive case, and no output directory was created.
Tests also covered dirty/untracked baselines, malformed config, explicit profile
loading/caps, empty/binary/oversized sources, missing CLI, symlinks/FIFOs and
output location boundaries. Structure/resource checks, strict manifest and
command/agent/skill local validations passed. The existing catalog license/icon
limitations remain. No new real-model slash-command run, live integration,
business acceptance, push or PR is claimed for this phase.

Version 0.14 (2026-11-16) adds repeatable opt-in real-Claude acceptance tests for
the init and doctor utility commands. The initial real init invocation exposed a
path/command mismatch: the model guessed skills/../scripts and added Python -I.
Normal exact-command permissions denied it; no write occurred. Utility commands
now supply their resolved absolute helper path and prohibit extra Python options
or path reconstruction. The permission boundary was not broadened. Local checks
enforce helper-path declarations for init/doctor/status/endtoend.

A new four-case real-model suite then passed inspection-only init, explicitly
authorized two-file init, passing doctor, and unconfirmed-template blocked doctor.
Each case had one observed helper call, zero denials, unchanged HEAD, no package/
test sentinel execution, and only its exact permitted target changes. Doctor
created no checkpoint/output and retained not_evaluated business requirements.
Private raw evidence and a policy-digest summary were retained outside this repo;
see RUNTIME-0.14.md for the recorded scope and repeat command. All 123 deterministic
tests plus strict local manifest/command/agent/skill validations passed.
No new full six-stage run or real-model status/endtoend test is claimed. No live
integration, real business acceptance, push or PR occurred in this phase.

Version 0.15 (2026-11-16) adds dedicated Indonesian installation and usage
guides, an imported Git-backed change ledger and generated CHANGELOG/command
reference. A repository-local pre-commit hook updates/stages only the three
managed outputs from intended staged changes; content identities bind history
to Git blobs/modes. Existing hooks and unstaged owner edits are preserved.
AGENTS.md and CONTRIBUTING.md require future changes to keep narrative docs
current; automatic metadata is not claimed to infer semantic user guidance.

All 138 offline tests passed, including real synthetic Git commits with the hook,
idempotent updates, staged/unstaged separation, stale/rewritten/missing history,
content changes under the same path, rename/delete and multi-commit squash
coverage. The local hook was enabled for this doforme checkout. The new GitHub
documentation workflow uses pinned checkout and contents:read, checks generated
docs/history coverage and runs offline tests only. YAML syntax/configuration
was checked locally; actionlint was unavailable. Hosted verification is recorded
below. The workflow becomes available only after publication and repository
Actions policy permits it; required status rules remain owner configuration.
No new model calls, live issue intake, business acceptance or external
notifications were performed in this documentation phase.

After publishing commit 9f8635e on 2026-11-16, the first hosted
[documentation/history run](https://github.com/erikgunawan/doforme/actions/runs/43797371270)
completed successfully. Its logs show generated-doc/history coverage verified
against f3324ea, the plugin structure check passed, and all 138 offline tests
passed. The workflow had contents:read and invoked no model. This demonstrates
the hosted check is active for this repo; required branch-status enforcement
has not been configured. This follow-up evidence update is itself recorded by
the same automatic history hook.

Version 0.16 (2026-11-16) adds opt-in real-model acceptance of profile-based
workflow requirements, all six stages, completed resume and /doforme:status.
The first suite stopped at PR after successful analyze/plan/fix/test/review:
the model appended an unallowed status option and shortened the diff check.
Prompt, executor permissions and Git audit now share an exact command catalog;
the observed variants remain rejected rather than receiving broader grants.

Fresh suite B completed analyze through PR draft with real red/green evidence,
independent test/review, fresh content binding, unchanged HEAD and exactly two
edited fixture files. Unconfirmed requirements blocked at analyze despite the
same direct execution/edit grants. Completed resume made no model call and
changed no target/checkpoint files. Its first slash-status test was denied for
quote spelling, so the original overall suite summary remains failed. After a
test-only fix accepting bounded equivalent quoting of the same exact arguments,
a separate fresh status session passed with one helper call, zero denials,
fresh true and no target/checkpoint mutation. Saved production completion and
resume were independently reverified under the same unchanged policy digest.

All 148 offline tests passed, including rejection of observed Git variants,
no-retry/fixture guards and exact-argv quote equivalence. Strict local component
checks passed. RUNTIME-0.16.md records the separate runs and their boundaries;
no final whole-suite rerun after quote normalization or /endtoend slash-routing
test is claimed. Raw traces/checkpoints remain private in sibling artifacts.
All inputs/owner confirmations are synthetic; no actual business acceptance,
issue resolution, live integration, notification or remote PR is established.

Version 0.17 (2026-11-16) validates actual /doforme:endtoend slash routing with
three independent synthetic Git fixtures. On frozen staged plugin tree
753290e4d39a8dcb6443c4a448cbd3126c8baf2a, unconfirmed requirements blocked at
analyze; absent execution/edit grants blocked before fix after complete analyze/
plan; explicit scoped authorization completed all six stages. All had fresh
checkpoints, unchanged HEAD and zero permission denials. Only the authorized case
changed the two named pagination files. The same immutable tree passed 153 offline
tests, plugin structure and generated-doc checks. RUNTIME-0.17.md describes the
real helper-output/checkpoint audit and private evidence. Concurrent later-phase
files were excluded from this tested export. No pilot on a real issue, business
acceptance, remote PR or live integration is claimed.

Version 0.18 (2026-11-16) implements a read-only business-acceptance sidecar.
It binds explicit canonical AC statements/source confirmations, complete fresh
workflow/report/validation identities and current content before evaluating a
supplied owner claimant's per-AC accepted/rejected/pending attestation and hashed
local UAT evidence. Twelve focused tests passed, covering missing/changed criteria,
stale workflow/evidence, identity fields, coverage and acceptance states. The tool
reports attested decisions with owner identity/authority not_verified, preserves
the original workflow and leaves resolution/publication unestablished. No actual
owner/UAT artifact has been supplied; real business acceptance remains pending.

Version 0.19 (2026-11-16) records pilot preparation and its actual prerequisites,
not a completed real pilot. The authorized GitHub account observed no open issues
in erikgunawan/doforme; a connected Drive metadata search for doforme documents
returned no results. No different target/issue, owner-confirmed AC or permission
to edit another repo was supplied. PILOT.md provides the input checklist,
execution/evidence procedure and explicit stop conditions. No target source was
modified and no synthetic fixture was relabeled as a real business issue. Pilot
execution remains pending the requested owner inputs; this is a preparation commit.

Version 0.20 (2026-11-16) implements portable source-snapshot ingestion for
explicit local business-document/Jira/Figma/spec/user exports. It preserves exact
UTF-8 bytes, bounded provenance, source/capture times and SHA-256 in new private
external bundles; authority stays unconfirmed. Seventeen focused tests passed,
including duplicate/escaping/symlink/FIFO/size/credential-origin/malformed-kind
cases and partial creation behavior. No model, source code or remote fetch ran.
This completes local acquisition infrastructure, not live Docs/Jira/Figma access:
an actual approved source URL/account and applicability confirmation are still
missing. SOURCES.md records the supported contract and live limitation.

A cross-review follow-up (0.20.1) corrected a phase18 association bug before
publication: an AC ID and a different AC's statement could previously be found
independently in the same source file. Binding now requires the exact statement
on its uniquely labeled canonical AC entry and rejects ambiguous layouts. The
swapped-statement/layout regressions pass; all 14 acceptance tests passed.
ACCEPTANCE.md also makes the before-commit-only freshness restriction explicit;
a publication commit handoff does not silently migrate a human attestation.
