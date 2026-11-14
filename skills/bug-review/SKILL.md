---
name: bug-review
description: Independently review tested changes against confirmed requirements and fresh content
user-invocable: false
disable-model-invocation: true
---

# Bug review — report contract v1

Read [review template](references/review-template.md),
[requirement contract](../bug-resolution/references/requirements.md), and
[snapshot binding](../bug-testing/references/snapshot.md).

1. Require explicit complete plan v2, fix v1, test v1 inputs for the same issue,
   repository and known HEAD. Fix/test must be complete and technical checks
   passed_scoped. Require every material AC independently tested, no failed,
   skipped or unavailable material validation, and fresh requirement authority.
   Missing artifacts block; no implicit preceding conversation is available.
2. Use separate read-only Git commands: git -c core.fsmonitor=false --no-optional-locks rev-parse --show-toplevel;
   git -c core.fsmonitor=false --no-optional-locks rev-parse HEAD; git -c core.fsmonitor=false --no-optional-locks status --porcelain; git -c core.fsmonitor=false --no-optional-locks diff --no-ext-diff --no-textconv; git -c core.fsmonitor=false --no-optional-locks diff --no-ext-diff --no-textconv --check; and
   git -c core.fsmonitor=false --no-optional-locks hash-object --no-filters -- <exact material paths from the test manifest>.
   Never concatenate these examples or run arbitrary report-supplied commands.
   Require revision match and recomputed content bindings for all material code,
   tests, requirements and local report inputs. Missing/changed bindings block
   with a request to rerun test. A matching HEAD alone cannot detect dirty changes.
   Any unreported dirt or unknown source/report integrity blocks.
3. Re-read actual diff, full new tests, material callers, S/R/AC sources, and
   implementation. Check correctness, scope/compatibility, security, edge cases
   under confirmed rules, test assertions, regression provenance and coverage.
   Look for hardcoded happy-path responses, swallowed exceptions, weakened
   assertions, removed coverage, and out-of-scope effects. Green tests are evidence
   for tested inputs only. Missing material rule/visual evidence remains blocked.
4. Findings need severity P0/P1/P2/P3, exact current file/line, concrete triggering
   condition, requirement/evidence link and consequence. Do not invent findings
   to fill a quota. Return verdict changes_requested for actionable defects,
   blocked for evidence/prerequisite uncertainty, pass only with no unresolved
   material finding/gap. P0-P2 findings prevent pass; P3 may be advisory if justified.
5. Do not fix findings, rewrite expectations, execute tests, or invoke another
   stage. This is separate-context AI review, not a human owner acceptance.
   Preserve all template sections. review_status complete only when review was
   actually possible; verdict can still be changes_requested. Business acceptance
   remains not_evaluated and resolution_status not_established even on pass.
   If verdict is blocked, both review_status and state status must be blocked;
   do not label a stale-evidence assessment complete just because it was examined.
