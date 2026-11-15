# Utility runtime acceptance — v0.14

This phase exercises real plugin slash commands, not only direct helper calls or
synthetic model traces. The suite uses fresh synthetic Git repositories under a
new external private output directory. It never initializes another real project,
publishes changes, or starts the six-stage fix workflow.

## Repeating the suite

```bash
python3 -B tests/runtime_utilities.py --output /absolute/new-acceptance-output
python3 -B tests/runtime_utilities.py --output /absolute/new-acceptance-output --live
```

The first invocation only prints a plan and creates no files. --live explicitly
enables up to four model calls with normal Claude permissions, a $1 cap and a
180-second timeout per call. Git/Python and a working Claude Code installation,
account and model connection are required. The directory must be new and outside
the plugin checkout. Existing output is never erased or reused.

Each case uses an independent committed fixture. A package script and test probe
would create UNAUTHORIZED_MARKER if executed; neither is authorized. Only Read and
one exact Bash helper command are allowed for that invocation. Claude is loaded
with the actual plugin, explicit skill directory, empty setting sources and empty
strict MCP configuration. The suite does not bypass permissions or request broad
Bash access. A failed command, unexpected tool, denial, timeout, malformed trace,
unexpected file change or missing helper result stops the suite without retry.

The private output contains summary.json, raw trace/stderr, the helper report and
baseline content hashes/revision for each completed case. The audit requires one
observed helper call and its JSON tool result; final model prose cannot substitute
for that evidence. HEAD and the complete non-Git file snapshot are checked after
the call. Doctor output remains a proposed path and must not be created. Python
bytecode writing is disabled in the test harness. Traces can contain account or
session metadata, so do not commit or publish them without review.

## Failure found and corrected

The first real /doforme:init invocation was denied. The model reconstructed the
helper as skills/../scripts/init_repo.py and added Python -I, which did not match
the exact allowed command and would also interfere with local module imports.
It stopped after denial without writing files; CLI exit code 0 alone would have
misrepresented this as success. The suite therefore checks permission_denials,
tool calls and actual helper results as well as process status.

All helper-backed utility command prompts now supply their resolved absolute
script path directly via CLAUDE_PLUGIN_ROOT, prohibit path reconstruction and
extra Python options, and retain their original capability limits. The local
structure checker enforces that helper-path declaration. No broader permission
was introduced to make the reproduction pass. The denied invocation was not
retried in the same session; verification uses a new suite and fresh fixtures.

## Verification boundary

On 2026-11-16 (Asia/Jakarta), Claude Code 2.1.323 completed all four real-model
slash-command cases after the prompt fix. The suite observed exactly one helper
call per case and zero permission denials. The CLI reported a combined model cost
of $0.072843 for these four cases (the initial denied reproduction is separate).

| Case | Observed helper outcome | Target changes |
| --- | --- | --- |
| /doforme:init | inspection_only | None |
| /doforme:init --write | draft_created, ready_for_fix false | Exactly .doforme/repository.json and .doforme/requirements.md |
| /doforme:doctor with supplied source | local_preflight passed, requirements_status not_evaluated | None |
| /doforme:doctor with unchanged template | local_preflight blocked at requirement_sources | None |

Every target retained its original HEAD, no sentinel appeared, and neither doctor
case created its proposed output. The suite and initial-denial trace were copied
to a private sibling artifacts directory on the development workstation rather
than committed to this repo. That copy includes a summary and plugin policy
digest; availability of those private artifacts in other environments is not
implied. All 123 deterministic tests and strict local plugin/component checks
also passed. Catalog license/icon limitations remain unchanged.

The init and doctor cases exercise real Claude slash-command routing, restricted
agents, packaged methods and helper execution. Status and endtoend helper paths
are covered by local structure tests in this phase; no new real-model run of
those commands or the full workflow is claimed. Fixture source text is synthetic,
and doctor checks readability rather than business authority or AC coverage.

The tests observe tool requests and target snapshots; they do not provide an OS
sandbox or prove absence of all effects outside the target. Claude's built-in
runtime may remain present despite empty optional settings/MCP configuration.
Successful utility calls cannot establish technical bug resolution, independent
review, business acceptance, live Jira/Figma access or publication readiness.
