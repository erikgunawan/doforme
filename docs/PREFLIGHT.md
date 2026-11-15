# Fresh-workflow preflight — v0.13

Use doctor after onboarding and before starting a fresh full workflow. It reports
actionable local blockers without repairing the checkout or executing the planned
work. It is a separate utility, not a new node in the bug-workflow graph.

```text
/doforme:doctor --input /absolute/issue.json --profile .doforme/repository.json --output /absolute/new-output
```

Input is mandatory. Profile and prospective output are optional and must be
selected explicitly. Existing complete configs work without --profile. Without
an input location, the command asks for it instead of searching arbitrary files.
Use [onboarding](ONBOARDING.md) to create reusable defaults and prepare issue input.

Standalone equivalent:

```bash
python3 -B /absolute/doforme/scripts/doctor.py --repo /absolute/target --input /absolute/issue.json --profile .doforme/repository.json --output /absolute/new-output
```

The helper prints JSON to stdout and returns exit code 0 for local checks passed,
1 for blockers, or 2 for invalid command arguments. It has no write, run, fix,
resume, retry or execution-authorization mode. No persistent report, checkpoint,
test artifact or write-permission probe is created. Python bytecode writes are
disabled. Only local read-only Git inspection is run; Claude is located on PATH
without invoking it. No network or login probe occurs.

## Checks and meaning

| Check | What is established | What remains outside the check |
| --- | --- | --- |
| Plugin structure | Packaged resources and capability declarations validate locally | Catalog eligibility and executable model behavior |
| Repository root/revision | Explicit selected Git root with an existing HEAD | Business applicability of that revision |
| Clean baseline | No tracked modifications or untracked files | Whether existing committed code is correct |
| Bounded checkout | Current snapshot uses regular files, no symlinks, within runner's 20,000-file/100-MB limits | Isolation from every possible external side effect |
| Configuration | Explicit legacy config or profile/input composition passes current scope/cap policy | Permission to execute any configured operation |
| Requirement sources | Declared files are nonempty, readable UTF-8 text under 1 MB each and not the unchanged generated draft | Authority, freshness, applicability, conflicts, AC coverage and visual acceptance |
| Edit scope / test commands | A full workflow has declared exact paths and syntactically accepted direct commands | Test safety, dependencies, correctness and sufficient assertions |
| Claude on PATH | A CLI executable can be located | Its version, identity, authentication, model access or compatibility |
| Optional output | New external destination, existing parent directory, no symlink path | Write permission and future availability |

The per-source 1-MB text bound is a preflight inspection limit. A larger source
needs a reviewed scoped excerpt for this utility; the check does not validate
that an excerpt covers all material requirements.

Checks use passed, blocked or not_checked. Failed prerequisites leave dependent
checks not_checked. Any blocker sets local_preflight to blocked. If no output
was supplied, output_location remains not_checked even when local_preflight is
passed; always inspect the individual results. Doctor does not instantiate the
checkpoint writer or silently create a missing parent directory.

## Responding to results

- Dirty checkout: review and preserve the owner's changes, then establish a clean
  intended baseline manually. Doctor does not stash, reset, commit or delete files.
- Missing source or unchanged generated draft: supply actual source excerpts and
  owner applicability/AC confirmation; do not just remove a marker to obtain pass.
- Missing edit scope or commands: review the specific issue and local test code,
  then provide exact scope. Detected package scripts do not authorize execution.
- Invalid profile/input or raised caps: correct the explicit input against the
  selected repo policy. Profile sources cannot be silently discarded.
- Existing output: inspect that checkpoint with /doforme:status. Doctor is not a
  recovery/resume gate, and no existing state is overwritten.
- Missing CLI: arrange installation/access separately. Doctor never installs or
  invokes it, and cannot confirm an account is signed in.

A full-workflow blocker does not automatically prohibit a separate read-only
/doforme:analyze with its own prerequisites. Passing preflight is a point-in-time
diagnostic, not a token that bypasses gates: the runner checks its baseline again
and every stage still validates its evidence. Requirements_status and business
acceptance stay not_evaluated; resolution_status stays not_established and
publication_ready stays false. Human/business acceptance cannot be inferred from
readable documents, a passing model report, or green technical tests.

## Verification

Deterministic tests cover positive and blocked diagnostics, CLI exit codes,
unchanged targets, no execution of configured test scripts or a sentinel Claude
executable, no output creation, unconfirmed templates, malformed input, source
encoding/size, profile caps, explicit loading, scope, symlink/FIFO handling and
fresh-output boundaries. These fixtures do not establish live model behavior,
real source authority or production readiness. See [phase results](PHASES.md).
