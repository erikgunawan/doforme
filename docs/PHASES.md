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

Version 0.21 (2026-11-16) integrates bounded POSIX execution into ClaudeExecutor:
combined stdout/stderr capture (16 MB default), deadlines/cancellation, process
group cleanup and unrelated credential-environment filtering. Twelve real
subprocess tests and two adapter regressions passed; the workflow adapter's
49-test suite passed. Partial bounded traces remain private while diagnostics
avoid raw child output. A same-session process group is not OS isolation;
setsid escapes, model-auth inheritance, CPU/memory/network isolation and scale
remain outside this implementation. Read-only Docker/bwrap probes failed in the
current allowed environment without changing host settings. OPERATIONS.md records
these limits; arbitrary untrusted production execution is not declared ready.
The initial live adapter probe rejected the legitimate empty --setting-sources
argument before spawning Claude. After accepting empty option values (while
still rejecting empty executable/NUL arguments), a fresh immutable-tree probe
ran real read-only analyze and blocked on unconfirmed requirements, with fresh
state, unchanged HEAD, no edits or denials. Both outcomes remain recorded; no
new six-stage run under this executor or OS sandbox proof is claimed.

Version 0.22 (2026-11-16) adds a separate controlled draft-PR adapter. Default
preview uses read-only GitHub.com metadata, original report/content integrity,
remote full-tree/ancestry/diff scope and duplicate-PR checks. Explicit publication
requires a reviewed preview digest and an exclusive durable private receipt
before POST; uncertain delivery/branch movement is disclosed without auto retry.
No push, branch creation, merge or issue closure occurs. A content-identical
commit handoff preserves original reports and normal status/resume freshness;
it does not migrate human acceptance. Ten focused mock-API/real-local-Git tests
passed, including the commit handoff and case-canonical repository regression
found in cross-review. No actual remote PR or live publication test was performed;
head/base branches, reviewed proposal and authorization remain operator inputs.

Version 0.23 (2026-11-16) adds an offline-by-default integration readiness guard
with explicit read-only GitHub metadata checks. Fifteen tests passed, including
malformed/incomplete workflow/secret records and exact template/path/base64 checks.
An actual authorized metadata query on erikgunawan/doforme observed repository
issue intake, optional analysis and Telegram not configured: no active intake
workflow, opt-in variables/pinned CLI version or expected repository secret names
were present. Organization/environment secrets were not inferred. Evidence is
private in sibling artifacts. No actual event/trusted owner-confirmed sources or
Telegram recipient were supplied, so activation/live verification remains pending.
No secret value was read, setting changed, workflow dispatched, model called or
notification sent. INTEGRATION-READINESS.md distinguishes configuration from live
verification; this commit is readiness infrastructure, not claimed live activation.

Version 0.24 (2026-11-16) adds reproducible candidate packaging/verification from
an explicit full clean HEAD commit or matching existing tag. Eleven real-Git/
archive tests passed: deterministic private artifacts, exact source selection,
regular-file/credential/evidence path checks, Git replacement-ref suppression,
bounded decompression, content/hash/mode/traversal/tamper guards and stable-claim
rejection. The packager makes no tag/release/push or license choice and reports
stable_ready/publication_ready false. Actual candidate construction requires this
phase's clean committed source; artifacts/verification remain outside Git.
ROADMAP.md records the distinction between completed infrastructure and pending
real pilot, owner acceptance, live connectors/integrations, OS isolation and
license/release decisions. v1.0 or completion of all live gates is not claimed.
After combining the independently developed components, all 234 offline tests,
plugin structure/resource checks and generated-doc checks passed. The real-model
phase17 slash suite and phase21 bounded-executor probe remain evidence for their
respective immutable policies; they are not relabeled as a full model run of
the final combined candidate. Each roadmap phase/preparation has its own commit,
with a separate phase18 cross-review fix rather than rewritten history.

Version 0.25 (2026-11-18) adds standalone target-repo configuration for Telegram
new-bug and owner-attested resolved messages. Only bug-labeled issues qualify.
Resolved requires current closed/completed state, matching closure timeline,
merged default-branch PR/SHA, successful required GitHub Actions checks, current
unedited approver declaration and same-issue approver QA/UAT evidence naming that
SHA. Test/model completion or bare issue closure does not establish acceptance.
Reopen invalidates old evidence. Source/AC relationship and business sufficiency
remain explicitly owner-attested, not independently inferred by the helper.

The inactive templates copy a standalone helper into the app repo; no full plugin
or model key is required for notifications. A durable artifact attempt precedes
Telegram, state is revalidated before POST, and retained receipt/local-attempt
guards stop duplicate/uncertain retries within their documented retention bounds.
No project source/test code or PR branch is executed in the Telegram-secret job.
Twenty-three focused tests passed, including mock-API/transport gates and actual
isolated CLI/module-shadow rejection; YAML triggers/read-only scopes
were checked locally. No live repo activation, Telegram delivery, credential setup
or real business acceptance was performed. TELEGRAM.md provides the full repo
settings, CI template, operator evidence procedure and delivery limitations.
The combined offline suite passed all 257 tests. Template YAML, triggers,
read-only permissions, default-branch checkout, secret separation and durable
receipt-before-send ordering were checked locally; no hosted target-project
notification workflow or real Telegram recipient was exercised.


## Guided user experience — v0.26.0

Public commands now coordinate in the main conversation for guided setup, issue
selection, concrete approvals, and saved-report lookup. Restricted worker agents
and the audited engine remain separate. Advanced explicit-input invocations are
preserved through packaged references, exact utility helpers, and restricted
report-stage worker delegation.

The guided helper previews setup/session/scope/execution before confirmation,
resolves local or fixed-origin GitHub issue IDs, stores private issue-addressed
sessions, pauses at requested stages, and binds approved plan scope before fix.
End-to-end can pause after the read-only plan. New sessions preserve old reports
and do not inherit edit grants. No project configuration, source, Telegram setting,
Git mutation or remote publication is performed by this implementation task.

Validation: the full offline suite passes, including guided host tests for scope
confirmation, wrong-order commands, per-stage pause, end-to-end plan pause/resume,
report reuse, changed-source rejection, issue isolation, new sessions, and lock
protection. CLI 2.1.327 plugin validation passes (listing-icon warning only).

Two real Claude Code smoke calls on a disposable fixture passed: short init read
actual fixture sources and asked applicability/AC questions without writes;
short fix without a session explained analyze/plan prerequisites and asked before
continuing, without writes, tests, or worker execution. Observed helper/tool traces
and snapshots were checked. Combined reported model cost: $0.1348038. Private
local evidence: /tmp/doforme-guided-live-20261119/summary.json (temporary, not a
published or durable acceptance artifact).

The complete multi-turn interactive approval flow and six-stage real KlikDown
fix remain for the user pilot. Synthetic executors establish host control flow
only, not model quality, browser QA, owner acceptance or a completed KlikDown pilot.


## Guided pilot feedback — v0.27.0

Repository-level doctor no longer depends on ticket selection. Status discovery
lists actual saved sessions without fetching GitHub; freshness is checked only
when a run is selected. Issue selection defaults to GitHub when origin identifies
a GitHub repo, labels every source, excludes PRs/templates, and offers an explicit
local choice if GitHub access fails. The bounded first page is not claimed to be
an exhaustive repository issue list.

The coordinator now has an explicit requirement-blocker recovery path: retain
technical findings, ask scoped applicability/AC questions, distinguish source
research from owner decisions, and preview config changes in the same conversation.
Confirmation is not inferred from source consistency, empty committed templates,
or old session grants. Changed requirements still require fresh analysis; no
report verdict rewriting, Git mutation, or acceptance claim is introduced.

Validation: 286 offline tests passed, including repository-only doctor, draft
and empty-command detection, GitHub-first selection, fixed-host GET arguments,
explicit local discovery, no silent fallback on gh failure, PR/template filtering,
bounded-list completeness disclosure, and saved-run-only status discovery.
CLI 2.1.327 plugin validation passed with the existing listing-icon warning.

Three real Claude Code smoke calls on a disposable repo passed: doctor invoked
the repository doctor helper without issue selection; empty status invoked saved
session discovery and explained that no run existed; issue-less analyze used
GitHub origin and displayed actual GitHub issue number/title with an explicit
local/offline option. No source, Git HEAD, configuration, or messages changed.
Evidence: /tmp/doforme-guided-feedback-live-20261119/summary.json (temporary).

A fourth live coordinator test used an explicitly synthetic, blocked analysis
checkpoint, not a real model investigation. It read the report and asked a
specific D3/AC applicability question, preserving source and checkpoint. The first
attempt used a shell cat shortcut and failed the strict helper-trace assertion;
instructions were tightened rather than relaxing the assertion. The fresh rerun
passed using approved helper/file tools. Evidence:
/tmp/doforme-requirement-recovery-live-20261119-v2/summary.json (temporary).
Total reported cost including the rejected trace: $0.3729788.

These tests do not establish complete multi-turn owner-confirmation/config-save
acceptance, browser correctness, or a successful real KlikDown fix. The existing
pilot must still supply confirmed requirement scope and actual test/QA evidence.

## English documentation

Reviewed all 90 Markdown files and translated remaining Indonesian documentation,
examples, diagram labels, and packaged guided-conversation examples into English.
Machine field names, report contracts, and actual source locators are preserved;
the KlikDown source-heading literal in Telegram configuration remains unchanged
because it identifies the original target document.

The documentation generator now emits English reference/changelog text. Curated
English summary translations are keyed by change ID in docs/history-translations.json;
original committed docs/changes.json entries remain unchanged. Tests cover display
translation, staged versus unstaged mapping content, invalid mappings, and history
immutability. All 289 offline tests and plugin validation passed. Code-fence counts,
JSON example structure, and local section anchors were checked. No model calls,
project-source edits, or notification sends were required for this translation.

Packaged skill text changes also change the policy digest; existing workflow
checkpoints may require a new run even though command contracts are unchanged.

## README workflow visuals

The README now leads with an outcome-focused introduction, an embedded eight-frame
20.1-second GIF, benefit-oriented feature copy, and an editable SVG showing the
complete issue-to-resolution lifecycle. The illustration distinguishes the six
runner stages/local PR draft from the team's publication, review, CI, QA/UAT,
merge, closure, and optional owner-attested Telegram resolution process.

Assets use example data and are labeled as workflow illustrations. They do not
claim a live Claude recording, successful KlikDown repair, or business acceptance.
A separate preview page documents the storyboard and a future real-demo checklist.
The optional Pillow/font-based media generator lives under docs/media; it adds
no plugin runtime dependencies or execution capabilities.

Every GIF frame was decoded and visually inspected. GIF dimensions, duration,
loop metadata, SVG XML, and SVG text bounds were checked. The SVG was rendered
and inspected in Chrome. Documentation/link/history checks and appropriate offline
documentation tests are run before committing. No model calls, target-source
changes, GitHub publication, or notification sends are part of these visual changes.

## Neutral README media palette

Replaced the dark blue/teal media palette with warm white, charcoal, and neutral
gray. The active stage uses an inverse monochrome treatment; sentence-case labels,
smaller corner radii, and removal of a redundant footer tagline reduce decoration.
The workflow, scene timings, example-data notice, and approval boundaries remain
unchanged. All eight animation frames and the Chrome-rendered SVG were visually
reviewed. Text-token contrast ratios range from 6.64:1 to 15.28:1 for the used
foreground/background pairs; this is not a full accessibility conformance claim.

## Antigravity read-only preview — v0.28.0 (2026-11-23)

Added a native export with four explicit skills (doctor/status/analyze/plan), a
worker and a worker-scoped PreToolUse guard. The shared graph/checkpoint engine
selects an explicit adapter; Antigravity rejects stages beyond plan and edit/test
grants. Checkpoints bind runtime/CLI/installed-policy identities and retain hashed
raw events, normalized reads and guard receipts. Missing/stale installed guard code,
missing audit coverage, unexpected tools and ambiguous results fail closed.
The native entry point writes only private session/report state, not target setup
or source files. No automatic Claude fallback, Git mutation or publication is added.

The exporter includes tracked source paths from current working-tree bytes,
excludes untracked files and rejects protected/symlink paths and overwrites. It is
a development preview build, not a clean-commit release attestation. Source methods
remain shared; generated package copies are outside Git. The final package was
built and installed locally; other installed plugins were not replaced.

Validation: all 312 offline tests passed (21 focused adapter/export/guard tests,
plus native capability-boundary regressions). Native CLI 1.5.14 strict validation
passed with four skills, one agent and one hook, zero errors/warnings, and only an
informational generic-icon note. Packaged doctor and empty status ran on the
fixture without model execution or target changes. A real one-read model smoke
produced one parsed JSON object and a matching pre-execution receipt.
Claude plugin validation also passed with its existing listing-icon warning.
A real host-only guided preparation/preview check disclosed the unenforced dollar
and turn limits, rejected plan-before-analysis, and preserved fixture contents;
it did not call a model or test the whole conversational approval exchange.

A real model analyze-to-plan fixture run completed both stages, paused at plan,
and retained nine allowed guard receipts per stage. Analysis returned valid_bug;
requirements were explicitly synthetic and confirmed by the fixture author.
Target contents and HEAD stayed unchanged. Its immutable tested policy digest was
11512b85ef012127e5dffa3de74d02f0a95977dab35da01ceece1faa451cb2c3;
private temporary evidence is /tmp/doforme-agy-live-dev1/evidence-summary.json.
A separate real negative probe attempted to read a dummy file outside the fixture:
one guard denial was recorded, the host rejected the stage, and the dummy sentinel
was absent from captured output. Evidence is in that directory's negative-evidence.json.
The final requested-stop exit code, runtime-limit messaging and tracked-export
hardening were covered by offline regressions after the full fixture model run;
that earlier run is not relabeled as a fresh checkpoint of the changed plugin.

Unsuccessful development probes are not counted as passes: two initial 90-second
stage calls timed out without source changes; a tool smoke correctly failed when
customization inheritance disabled the guard; schema-flag probes yielded repeated
response objects with no structured_output. The final adapter keeps customization
inheritance for the guard, parses a single terminal JSON object strictly, and
rejects duplicate/ambiguous output. CLI init reports a platform-wide tool catalog,
not an effective allowlist; observed read_file(Path) events are normalized, and
pre-execution receipts establish actual guarded calls instead of trusting that catalog.

Limits: POSIX only; reviewed CLI range >=1.5.14,<1.6.0, with actual observations on
1.5.14. The host enforces time/output caps; dollar/turn limits are not enforced in
this provider and are disclosed before execution. Existing user customizations
can participate; these controls are not OS isolation. No complete conversational
multi-turn approval pilot, real KlikDown repair, business acceptance, fix/test/PR
support, Telegram send, push or remote release is claimed by this phase.

## Multi-runtime product description

Updated the README introduction and plugin/catalog descriptions to present
doforme for Claude Code and Antigravity CLI. An early runtime table distinguishes
the full Claude workflow from the read-only Antigravity preview, and the full-flow
illustrations and end-to-end options are explicitly attributed to Claude Code.
The installation overview uses the same positioning. The GitHub About description
was updated at the owner's request; this does not publish local source commits.
All 18 documentation tests and plugin structure/capability checks passed. No
runtime behavior, target source, model execution or notification changed.

## Antigravity command namespace correction — v0.28.1

Renamed native entry skill directories/frontmatter to analyze, doctor, plan and
status. Antigravity supplies the doforme: namespace, so including doforme- in
each skill name caused duplicated command prefixes. Coordinator instructions and
installation/usage examples now consistently use /doforme:analyze and its peers.
Package checks enforce the short names, and the export regression checks the
composed command namespace. Worker permissions and graph dependencies are unchanged.

Validation: 21 adapter/export tests, 25 capability-boundary tests and 18
documentation tests passed. Plugin checks and native strict validation passed
(informational generic-icon note only). The native package was rebuilt and the
local installation replaced. An actual `agy -p /skills` metadata query exited
successfully and listed doforme:analyze, doforme:doctor, doforme:plan and
doforme:status, with no doubled prefix. No model, target source or remote
publication was involved. Restart an existing CLI session after reinstalling to
refresh its cached command list. This does not revalidate old policy-bound runs.

## Antigravity guided setup — v0.29.0

Added the native init command, shared coordinator instructions, inspection/draft
compatibility and the existing digest-confirmed setup flow. The coordinator can
collect real source applicability/AC confirmations and reviewed test defaults,
preview the two configuration writes and save them only after explicit approval.
It does not directly edit files, commit setup, execute tests or grant fix scope.
Doctor now reports the shared setup/test-readiness gaps instead of suppressing
them. Four packaged-entry regressions cover inspection, immutable drafts, exact
setup confirmation, two-file-only changes and invalid flag combinations. The
25 focused native tests and native strict package validation passed with five
skills, one worker and one hook. No model or real target source was changed.
All 316 offline tests passed at this checkpoint.
This checkpoint adds setup; fix/test and the remaining stages are the next phase.

## Antigravity six-stage workflow — v0.30.0

Added fix, test, review, PR draft and endtoend entry skills. All ten public command
names now match the Claude workflow. The existing graph, requirement gates, scope
approvals, snapshots, revision bindings and retry limits remain shared. Four native
worker definitions separate read-only investigation/planning, scoped fixing,
independent testing and read-only review/PR preparation.

A local stdio MCP broker executes only stage-specific, host-approved argument
arrays selected by integer index. It accepts no model-supplied command text,
shell composition or arbitrary executable. Test processes receive filtered
environments, time/output bounds and private actual-exit/output receipts. Expected
red assertions are returned as observed command failures rather than rewritten as
tool success. The adapter binds each result to both original native events and
guard/broker receipts before the shared validation gates can advance.

Native metadata discovery needs one extra file: the CLI's broker-schema JSON.
Its exact non-secret contents must match the bundled tool definition. No broader
credential/cache access is granted. Only fix can write exact approved paths;
test/review/PR cannot edit source, and review/PR cannot run tests. Normalized Git
inspection/content-hash calls retain the existing safe-Git audit rules. Read-only
trace binding permits a reviewed scope update after Plan while still rejecting
requirement/issue changes. Cost/turn limits remain explicitly unenforced by this
provider; the host still enforces deadlines/output and a broker command-call cap.

Validation: all 324 offline tests passed, including 33 native tests for packaged
setup, scoped edits, command-index rejection, real red/green subprocess results,
MCP initialization/no-worker refusal, receipt association, schema-only metadata,
scope-upgrade binding and denial-latch behavior. Native strict validation passed
with ten skills, four workers, one hook and one local broker (generic-icon note
only). Claude validation passed with the existing listing-icon warning. The local
native installation was updated; no feature-phase source was pushed.

A real synthetic pagination run on Antigravity CLI 1.5.15 used the guided host
endtoend flow: Analyze/Plan completed without mutation grants, the actual plan was
reviewed, then exact scope was approved for pagination.py, test_pagination.py and
`python3 -B -m unittest test_pagination.py`, with no temporary artifacts. Fix,
independent Test, Review and local PR preparation all completed:

| Stage | Guard receipts | Actual command receipts | Outcome |
| --- | ---: | ---: | --- |
| Analyze | 11 | 0 | valid_bug, requirements verified for synthetic scope |
| Plan | 11 | 0 | Complete; paused before mutation |
| Fix | 29 | 9 | Actual assertion failure exit 1, then scoped pass exit 0 |
| Test | 27 | 10 | Independent scoped pass exit 0 |
| Review | 18 | 7 | pass; no source edits or test reruns |
| PR | 18 | 7 | Local draft complete; publication_ready false |

Only the planned source/test paths changed. The source endpoint became
min(start + size, len(items)); the new unittest module contained the three agreed
AC assertions. HEAD and requirement/issue inputs stayed unchanged, and the issue's
injection marker was not created. Business acceptance stayed not_evaluated,
resolution not_established and remote_actions none. This is fixture evidence,
not a real KlikDown repair or authenticated business-owner acceptance.

The immutable model-run policy was
9150de13e0fced582487434a48926628d3b98c4250c82c7d6e36c219635d40c2.
Private evidence: /tmp/doforme-agy-parity-live/evidence-summary.json and the saved
run history. A broker command smoke and scoped-edit smoke also passed. The first
edit smoke was correctly rejected for a blocked broker-schema read, even though
later allowed fixture operations occurred; that rejected run is not counted as a
pass. A fresh build allowed only verified broker metadata, not general cache reads.

After the full run, a mechanical denial latch was added: once a guard rejects a
call, later calls and broker commands in that worker are denied. All 114 recorded
allowed calls were revalidated with the final guard without re-executing them.
A real final negative probe started a closed worker: two calls were denied,
zero commands executed and its runner marker stayed absent. Evidence:
/tmp/doforme-agy-parity-denial/summary.json. The final hardened policy is not
relabeled as a fresh six-model run; original checkpoints remain bound to their
historical policy and become stale on an upgrade.
The exporter was also aligned to preserve every shared policy file, including
passive project-integration templates. A regression verifies equal source/export
engine policy digests. The frozen model-run source was archived with unchanged
integration files from the preceding commit and independently matched the recorded
policy digest. Export fidelity and denial hardening were validated after the full
model run, without claiming a second six-model run under that final policy.

Remaining limits: POSIX/local reviewed tooling, no OS isolation or authenticated
approval identity, no completed outer multi-turn slash-conversation pilot, and
provider-specific billing/turn behavior. Native guided commands and the advanced
shared host are supported; legacy Claude-only manual-report delegation syntax is
not translated. PR publication, owner UAT/acceptance, real project pilot and
Telegram delivery remain separate operations; nothing is silently activated.
