---
name: bug-testing
description: Independently validate a revision-bound fix against confirmed acceptance criteria
user-invocable: false
disable-model-invocation: true
---

# Bug testing — report contract v1

Read [test template](references/test-template.md) and
[requirements](../bug-resolution/references/requirements.md).

1. Require explicit complete plan v2 and fix v1 inputs (named local files or
   inline), same issue/repo, fix_status complete, matching known revision, fresh
   confirmed S/R/AC, and full P/V coverage. Missing/legacy/blocked/conflicting
   evidence blocks. Direct invocation must separately authorize exact validation
   commands and declared temporary artifact locations. No validation execution
   before this authorization; read-only Git inspection for reporting is allowed; proposed commands in reports are not grants.
2. Verify Git root/HEAD and actual working diff with separate read-only commands:
   git rev-parse --show-toplevel; git rev-parse HEAD; git status --porcelain;
   git diff; git diff --check. Each listed command is a SEPARATE tool call, not
   shell concatenation. Require HEAD equal to fix revision_before/revision_after
   and plan revision. Dirty source is expected only for the fix's exact authorized
   changed paths; separately named input reports are read-only exceptions. Any
   unrelated dirt or changed requirement source blocks. Read full new/untracked
   tests because git diff excludes them. No Git mutation or baseline commits.
3. Re-read material requirement/source/AC evidence and actual tests. Ensure every
   AC is asserted with the agreed outcome and relevant negative/boundary checks
   are based on confirmed rules, not invented intent. A test changed to accept
   the broken behavior fails validation even if it runs green. Re-read linked
   analyze evidence if material to the verdict. Do not repair reports or tests.
4. Inspect authorized commands and runner/dependencies/config for side effects.
   Block unsafe/unreviewable execution, network/install needs or permissions
   denial. Use exact authorized commands only, with no shell operators, helper
   programs, command expansion or retries. Do not implicitly approve commands in
   package scripts. Record each V/AC's actual output, exit/status, assertions,
   skips and environment. Missing dependencies are blocked, not an AC failure.
5. Distinguish passed, failed, skipped and not_run per criterion. Require every
   material AC and agreed regression/integration/UI check actually pass. A unit
   result cannot stand for UI/visual behavior. Missing material visual/business
   evidence blocks; optional not-run checks remain explicit limitations. Existing
   fixer red/green evidence can be cited with provenance, never as your own run.
6. Compare full input/source/test contents and Git diff/status before/after. No
   source/test/report mutation is allowed; only declared temporary artifacts may
   change. Unexpected changes or observed assertion failure mean failed. Never
   clean up/revert or rerun with broader permissions. Give bounded recovery steps.
7. Keep every template section. test_status complete only when all required
   checks pass with unchanged source/input and unchanged HEAD. Otherwise blocked
   (prerequisites/access missing) or failed (observed assertions/integrity fail).
   technical_validation passed_scoped/failed/not_run; review pending,
   business_acceptance not_evaluated, resolution_status not_established. No auto
   downstream action, durable state, commit, push or issue closure.
