---
name: workflow-preflight
description: Diagnose local full-workflow prerequisites without running or authorizing work
user-invocable: false
disable-model-invocation: true
---

# Read-only fresh-workflow preflight

Require a directly named issue/full-config JSON file. An optional repo profile
must also be selected explicitly; never discover a profile or issue automatically.
If input is missing, ask for its location without running the helper or searching.

Run exactly one properly quoted invocation:
`python3 <plugin>/scripts/doctor.py --repo <current-root> --input <issue-file>`.
Use the exact absolute helper path rendered in the command invocation. Never
derive it from this skill's location or add Python flags such as -I/-B/-m.
Append --profile <profile-file> and/or --output <new-external-output> only when
supplied directly. Output is a prospective destination, never a report file to
write. No --write, mutation/execution, resume or retry mode exists for this helper.

Report local_preflight, each blocked/not_checked item and practical next steps.
The helper checks local plugin structure, selected Git root/HEAD, clean baseline,
bounded regular-file checkout, explicit config composition, readable source files,
nonempty full-workflow scope/commands, CLI presence and optional new output path.
It never runs the detected CLI, source code, tests or a model. It neither repairs
the checkout nor creates configuration/checkpoints/reports. Do not run fixes to
turn a failed check green, hide blockers or turn not_checked into passed.

Unchanged generated requirement drafts and empty sources block local preflight.
Other readable content is only a syntactic prerequisite: authority, source version,
scope, conflicts, AC coverage and visual evidence still require analyze/plan and
explicit owner confirmation. Never claim verified_for_scope, ready_for_fix,
business acceptance or resolved on the basis of doctor. Direct execution grants
are still required. Authentication, model access, executable version, test safety,
write permissions and future freshness are not established by these checks.

This utility diagnoses a fresh full workflow. Existing checkpoint recovery belongs
to /doforme:status, not doctor. A blocked full-workflow check need not prevent
separate read-only /doforme:analyze when its own prerequisites are satisfied.
Use the user's language and preserve machine status names.
