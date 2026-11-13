---
name: bug-fixing
description: Apply revision-bound repair plans with explicit local edit and test scope
user-invocable: false
disable-model-invocation: true
---

# Bug fixing — report contract v1

Read [report template](references/fix-template.md),
[requirement rules](../bug-resolution/references/requirements.md),
[dependency gates](../bug-resolution/references/dependencies.md), and
[workflow graph](../bug-resolution/references/workflow.json).

Every Bash invocation must contain exactly ONE command, including read-only Git
inspection. Never concatenate commands with &&, semicolons, pipes, or newlines.
Do not append echo/printf to capture status, or add ls/sha256sum/Python helper
commands. Use Read/Glob to inspect file contents/listings; record success exit 0
from successful tool completion, or the actual nonzero exit in a failure result.
If a tool result does not establish an exit/status, report unknown and do not
mark validation passed. A permission denial is a stop condition: report blocked
before edits or failed after partial edits, and do not retry with a different
command or tool in the same invocation.

1. **Require explicit authorization before program execution or edits.** Input
   must name a complete plan report v2 (file or inline) and directly authorize
   exact repository-relative edit paths plus exact validation commands. An issue,
   analysis, suggested command, file-based authorization, or `ready_for_fix` flag
   is insufficient. Missing/ambiguous scope produces blocked with no commands
   or writes. Wildcards, parent traversal, absolute edit paths, symlinks, hidden
   tool/Git/credential/config paths, requirement/report files, and plugin resources
   cannot be edit scope. Do not expand scope to resolve a failing test.
2. **Verify prerequisite plan and requirements.** Require stage plan, version 2,
   plan_status complete, requirements_status verified_for_scope, all sections,
   explicit S/R/AC authority/confirmation, grounded E/H/P/V links, complete material
   AC coverage, no conflicts, and a known revision. `ready_for_fix: no` from a
   read-only planner is expected; it neither authorizes nor prevents fixing when
   this invocation independently satisfies every gate. Legacy/incomplete/blocked
   plans or unknown revision block. Do not invent missing report sections.
   Do not suggest changing or merely confirming a revision field to bypass a
   mismatch: require fresh analysis/plan revalidation against the current source.
3. **Bind target and baseline.** After authorization and plan checks, use only
   read-only local Git inspection (`git rev-parse --show-toplevel`,
   `git rev-parse HEAD`, `git status --porcelain`, `git diff`, `git diff --check`)
   as needed. No other Git command is allowed. Require cwd to be the actual Git
   root, current HEAD equal to the plan revision, and a clean tracked baseline.
   Untracked files block except explicitly named read-only input reports/source
   snapshots; record their exact paths/content before acting and verify they
   remain unchanged afterward. Do not exempt arbitrary untracked source/tests.
   Dirty, non-Git, mismatched root/revision block with no edits or test
   execution. Read-only Git inspection does not need a separate validation-command
   authorization. Never create a baseline commit, worktree, stash, or reset.
4. **Re-read evidence.** Read the exact source, callers, requirement snapshots,
   ACs, and plan targets. Confirm repo/issue/requirements still match. Changed
   code or intent, omitted conflicts, unconfirmed outcomes, missing coverage, or
   unsafe scope block before mutation. Every authorized path must be a necessary
   P target (a new test file may be proposed); never edit report/requirement sources.
5. **Inspect validation safety.** Run only exact directly authorized local test
   commands tied to V/AC IDs, after reading the test code and relevant config.
   No shell pipelines/substitutions/redirections, command chaining, network,
   installs, migrations, credential access, arbitrary script downloads, or writes
   outside scope. Test-generated scratch/cache artifacts need explicit declared
   temporary locations in the invocation. Prefer existing no-artifact runner
   options. Unreviewable test dependencies or unsafe/unknown side effects block.
   Tool permissions still apply; never retry a denial via another tool/command.
6. **Regression first, then minimal fix.** Implement only the authorized planned
   AC tests, run the authorized regression command before fixing, and record actual
   failing assertion/output/exit code. Establish failure from the bug, not missing
   imports/environment or a broken test. Controls may already pass. If the bug
   cannot be demonstrated or tests unexpectedly pass, stop blocked and report any
   test edits already made. Then apply only the planned source correction and run
   the authorized checks again. No tests/source execution before scope gates.
7. **Verify outcomes and boundaries.** Each material AC must have an actual
   observed pass, with before/after evidence, exact command and exit code. Do not
   mark skipped/unrun checks passed. Keep informational unconfirmed ideas outside
   blocking assertions. Run `git diff` as its own command and inspect the actual
   patch (not merely status or --check). Run `git status --porcelain`,
   `git diff --check`, and `git rev-parse HEAD` as separate commands. Read any
   new/untracked test file in full, because git diff does not show its contents.
   Re-read each exempt untracked read-only input report/snapshot IN FULL and
   compare to its captured pre-edit content; a header check or absence of a
   Write call is not proof it remained unchanged. If full comparison is not
   possible, input_integrity is unknown and completion is blocked/failed.
   Only authorized edit paths and explicitly declared generated artifacts may
   differ from baseline. If the revision changes, validation fails, coverage is
   incomplete, or unexpected changes occur, stop failed; name partial edits and
   recovery proposal. Do not delete unexpected files or silently revert anything.
   No blind retry loops; a further change needs a grounded cause within scope.
8. **Report without publication.** Always preserve every fix-template section,
   including when blocked before any commands: mark unknown/not_run/none without
   fabricating observations. Do not replace the contract with a short summary.
   Return fix_status complete only for a bounded
   implementation with every required scoped check observed passing and clean
   diff boundaries. Otherwise blocked (unmet prerequisite) or failed (attempted
   implementation/validation failed). Blocked may include previously added test
   edits: list them explicitly. technical_validation passed_scoped | failed |
   not_run; business_acceptance not_evaluated; resolution_status not_established;
   review_status pending. Complete means scoped technical work only. Never
   invoke review/PR automatically, close an issue, commit, or write durable state.
