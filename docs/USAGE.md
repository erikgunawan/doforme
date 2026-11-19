# Using doforme

For everyday use, follow [guided short commands](GUIDED-USAGE.md): `/doforme:init`,
`/doforme:analyze BUG-301`, then `/doforme:fix BUG-301` after planning. That mode
saves reports automatically and guides scope approval. Doctor without input is
repository-level; status without an ID lists saved runs. Ticket selection
prioritizes GitHub origin with explicit source labels.

The following sections describe **advanced mode** with explicit reports/inputs/paths.
Advanced manual reports are returned in chat and not automatically saved. Stage
workers use separate contexts; short-command coordinators stay in the main session
to receive user answers. Commands are listed in the [generated reference](REFERENCE.md).

## Main workflow

1. Inspect/configure the repository with init.
2. Supply issue content, requirement sources, and applicable AC.
3. Check local prerequisites with doctor.
4. Run analyze → plan → fix → test → review → pr manually or through the runner.
5. Review the draft/evidence; business acceptance and publication are separate.

Complete means a stage met its contract, not that an issue is resolved. Passing
tests apply to tested scope/AC. Business acceptance remains not_evaluated and
resolution_status not_established.

## Set up once per repository

```text
/doforme:init --inspect
/doforme:init --write
```

The first command writes nothing. The second creates two onboarding drafts without
overwriting existing files. Fill `.doforme/requirements.md` with actual evidence:
business-document excerpts, Jira tickets, Figma annotations/designs, or repository
specifications, locators/versions, applicable scope, and owner AC confirmation.
A URL alone is not content; scope approval is not implementation acceptance.

Do not assume one source always overrides another. Material conflicts require
the requirement owner's decision. Figma visual validation cannot be claimed from
text alone. See the [source example](requirement-input.example.md).

`.doforme/repository.json` holds requirement paths, default test commands, temporary
artifacts, and timeout/turn/cost caps. Add direct commands after reading the invoked
test/code/configuration. A profile grants no fix/test permission. Review and commit
setup before a workflow requiring a clean baseline.

## Prepare per-issue input

Source text exports can be bundled with hashes/provenance using [source snapshots](SOURCES.md).
This tool reads explicitly selected local exports; it grants no authority and
fetches no live remote documents.

Save input outside the target checkout, for example `/absolute/inputs/bug-123.json`:

```json
{
  "issue_ref": "BUG-123",
  "issue_text": "The final page skips an item. Expected [5], observed [] for the input described in the requirement source.",
  "edit_paths": ["pagination.py", "test_pagination.py"],
  "test_commands": ["PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination"],
  "artifact_paths": []
}
```

This uses the pagination fixture, not universal scope. Choose paths/runners
appropriate to your repository. Issue input may add requirement sources, select
specific commands, and lower caps. It cannot remove profile sources or raise caps.

```text
/doforme:doctor --input /absolute/inputs/bug-123.json --profile .doforme/repository.json --output /absolute/runs/bug-123
```

Run output must not exist, must have an existing parent, and must be outside both
target and plugin checkouts. Doctor does not create it. local_preflight passed
is a local technical check only; requirement content/authority and AC remain
unevaluated. See [doctor](PREFLIGHT.md).

To inspect effective configuration without models/tests/checkpoints:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --repo /absolute/target --profile .doforme/repository.json --input /absolute/inputs/bug-123.json --inspect-config
```

## Run stages manually

Each command uses a separate worker context. Supply prior reports explicitly;
do not rely on conversation memory. Commands produce reports but do not automatically
save files with the example names below. Save reviewed output at your report
location or pass complete inline inputs.

```text
/doforme:analyze ISSUE.md; sources and scope confirmation in REQUIREMENTS.md
/doforme:plan /absolute/reports/ANALYSIS.md
/doforme:fix /absolute/reports/PLAN.md; authorize edits ONLY pagination.py and test_pagination.py; authorize ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
/doforme:test /absolute/reports/PLAN.md /absolute/reports/FIX.md; authorize ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
/doforme:review /absolute/reports/PLAN.md /absolute/reports/FIX.md /absolute/reports/TEST.md
/doforme:pr /absolute/reports/PLAN.md /absolute/reports/FIX.md /absolute/reports/TEST.md /absolute/reports/REVIEW.md
```

Analyze/plan only read. Fix requires a clean baseline, matching plan revision,
exact edit scope, and direct permission. It observes a bug-related regression
failure and post-fix results; import/dependency errors are not regression evidence.
Independent test checks AC and actual tool results. Review checks content hashes,
diff, and evidence without running tests. PR only prepares draft title/body;
it does not create a remote PR or close an issue.

## End-to-end runner

Inspect effective scope first. This example directly authorizes input-matching
edits/tests; run it only after approving that scope:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --repo /absolute/target --profile .doforme/repository.json --input /absolute/inputs/bug-123.json --output /absolute/runs/bug-123 --allow-fix --allow-execution
```

Without grant flags, the runner may analyze/plan and stop before fixing. Profiles
or issue contents cannot enable flags themselves. Conversation equivalent:

```text
/doforme:endtoend --input /absolute/inputs/bug-123.json --profile .doforme/repository.json --output /absolute/runs/bug-123; authorize output creation; authorize edits ONLY pagination.py and test_pagination.py; authorize execution ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
```

The runner makes a separate model call per stage. Default stage caps are 180 seconds,
45 turns, and $1, adjustable downward through profile/input. Six stages are not
one call; runs may stop earlier and incur model costs.

Private output stores effective input, checkpoints, report history, and validation
evidence. Do not include unnecessary credentials or personal data. Targets are
currently limited to 20,000 files/100 MB; symlinks/special files are rejected.
Normal permissions and post-call audit are not an OS sandbox.

## Status, resume, and blocked results

Model execution has timeouts, a combined 16 MB output cap per stage, and POSIX
process-group cleanup. This is not OS isolation or a guarantee that tests cannot
access credentials still needed by the model. Read [operations and isolation limits](OPERATIONS.md)
before using untrusted source.

```text
/doforme:status /absolute/runs/bug-123
```

Or read status without a model:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --status --repo /absolute/target --output /absolute/runs/bug-123
```

Resume uses the original runner command, identical input/output/grants, and --resume.
Interrupted/failed/blocked stages need explicit --retry, with at most two attempts.
Retry cannot bypass requirement or verdict gates. Changed HEAD/content/policy/config/
grants reject resume. Partial edits need manual review/recovery; do not reset,
delete active locks, falsify revisions, or widen permissions to force continuation.

A non-bug issue or changes_requested review can stop handoff even when the previous
stage is complete. Read reasons/reports, not just process status. A complete runner
still means a draft is ready for review, not ready for publication.

Read-only [acceptance validation](ACCEPTANCE.md) checks supplied per-AC human
decisions bound to tested content/checkpoint/AC. Supplied decisions are labeled
attested, not authenticated owner identity. The validator changes no runner status
and closes no issues.

[Draft PR publication](PUBLISHING.md) is separate: default read-only preview; POST
requires --publish, a reviewed proposal digest, and a new private receipt. It does
not push, create branches, merge, or close issues. A separate handoff checks
byte-identical commits; normal status/resume freshness and old attestations are
not silently changed.

## Integrations and testing

Telegram is optional. Manual/end-to-end paths and status/resume remain available
without Telegram workflows or credentials; only notification delivery requires
additional opt-in/configuration.

For new-bug/resolved notifications in an application repository, use [Telegram configuration](TELEGRAM.md).
Manual and end-to-end fixes share the same notification gates: merged PR, passing
required checks, approver evidence/decision, and closed/completed issue. Passing
tests or a PR draft alone do not send resolved status.

[Integration readiness](INTEGRATION-READINESS.md) provides offline diagnosis or
explicit GitHub metadata reads. Configuration/secret presence is not successful
delivery evidence. The helper installs no secrets, activates/dispatches no workflows,
calls no models, and sends no messages.

GitHub intake/Telegram remain separate opt-in examples, not automatically active.
The documentation workflow only checks docs/history and offline tests; it processes
no issues and calls no models. See [integrations](INTEGRATIONS.md), [real runtime tests](RUNTIME-0.14.md),
and [test history](PHASES.md).

[Workflow acceptance](RUNTIME-0.16.md) covers profile-to-draft integration,
requirement stops, resume, and status. Without --live it only prints a plan;
--live uses synthetic repositories and may make up to eight model calls. It is
not an automatic production-source testing method.

Direct `/doforme:endtoend` routing, including requirement-blocked/no-execution-grant
cases, is tested separately in [slash acceptance](RUNTIME-0.17.md).

For real business issues, follow the [pilot procedure](PILOT.md). Target repository,
source permission, owner requirements/AC, and UAT evidence must be explicitly selected;
fixture results cannot replace that pilot.

[Roadmap status](ROADMAP.md) distinguishes helper implementation, fixture/model tests,
business pilots, live activation, and stable releases. Versions do not establish
that all operational conditions or owner decisions are complete.
