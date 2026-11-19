# Onboarding per repository

For the interactive setup and short issue commands, see [guided usage](GUIDED-USAGE.md).
The utilities below describe the preserved advanced helper interface.

The plugin is loaded once into the selected Claude session. Each target repo can
then have reusable defaults without copying plugin source or changing application
code. Onboarding is a separate utility, not an automatic bug-workflow stage.

## Inspect, then explicitly create draft files

```text
/doforme:init --inspect
/doforme:init --write
```

The first command is read-only. The second authorizes only these fixed files:

- `.doforme/repository.json`: reusable source paths, default validation commands,
  declared temporary artifacts, timeout/turn/budget caps.
- `.doforme/requirements.md`: explicitly unconfirmed source/AC template.

The helper detects tooling markers and package script names without running them.
It leaves test_commands empty rather than approving an inferred npm/pytest command.
It never grants write/execution scope, installs dependencies, initializes/commits
Git, changes .gitignore or application files, activates CI, or configures secrets.
Repeated setup preserves owner files, even if they need manual review. A partial
setup or unsafe/symlink path stops without overwriting; partial creations from an
I/O failure are disclosed and retained for manual recovery.

Standalone equivalents:

```bash
python3 /absolute/doforme/scripts/init_repo.py --repo /absolute/target
python3 /absolute/doforme/scripts/init_repo.py --repo /absolute/target --write
```

Use the selected Git root. A subfolder does not expand scope into its parent, and
a non-Git folder is not initialized automatically. An empty Git repo may receive
drafts with revision unknown; no readiness for fix is implied. Review and commit
the config/source inputs before using a workflow that requires a clean baseline.

## Review defaults and supply real requirements

Replace placeholder evidence with actual supplied business/Jira/Figma content,
original locator/version and explicit owner applicability/AC confirmation. A
generated S1/R1 row is unknown, never a new approved business rule. Profile syntax
being valid is not business acceptance. Existing source acquisition limits apply.
See [requirement input example](requirement-input.example.md).

Choose direct local test commands after reading their source/config. Detected
package scripts are candidates for review, not execution authorization. No
issue-specific edit_paths, issue text or allow-fix flag belongs in the repo profile.

## Keep issue input separate

For a particular issue, create an input such as the following outside the target
checkout to avoid untracked workflow inputs:

```json
{
  "issue_ref": "BUG-123",
  "issue_text": "Actual expected/observed behavior and trigger",
  "edit_paths": ["src/pagination.py", "tests/test_pagination.py"],
  "test_commands": ["PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_pagination"]
}
```

These paths/commands are examples, not a recommendation for every framework.
Explicitly select the profile; no silent discovery takes place:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --repo /absolute/target --profile .doforme/repository.json --input /absolute/issue.json --inspect-config
```

This prints the effective configuration only. It does not start a model, run a
test or write an output/checkpoint. Profile paths resolve from the repo root even
if the helper is invoked elsewhere. Profile/issue JSON must be bounded regular
files without duplicate keys or symlink targets.

Composition rules:

- Profile requirement sources always remain included; issue-specific sources can
  be added, not used to silently discard a material repo source.
- Issue input supplies exact edit paths. It can select exact validation commands
  or temporary artifacts instead of the repo defaults, subject to normal safety
  checks and direct caller authorization.
- Issue limits may be lowered, not raised above the repository caps.
- Active profile/issue input and all requirement sources remain read-only.
- Existing full run-config JSON still works unchanged without --profile.

After reviewing that scope, execute with an explicitly authorized external output
and the appropriate direct --allow-fix/--allow-execution flags. A profile itself
grants neither. Missing commands or requirement evidence still block advancement.
Resume validates the same effective config and source/policy fingerprints.

Before starting a fresh full workflow, use [doctor](PREFLIGHT.md) with the same
explicit input/profile to diagnose local blockers without model/test execution.
Passing that check does not confirm business requirements or authorize changes.

## Verification scope

Local tests cover dry-run/no execution, exact new-file scope, idempotence, owner
file preservation, partial failure disclosure, symlink/non-Git/subdirectory
rejection, strict profile schemas, protected requirement/profile inputs, caps,
explicit loading, legacy compatibility and no-run effective config inspection.
Actual model command smoke results are recorded in [phase history](PHASES.md).
No real target repository was initialized during development; tests use disposable
fixtures. No source outside this plugin or publication/integration settings changed.
