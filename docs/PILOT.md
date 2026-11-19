# Pilot on a real repository and issue — phase 19

A real pilot requires an owner-selected target and requirements. The pagination
fixture is not a substitute and must not be reported as a resolved business issue.

## Status during preparation

On 2026-11-16, an open-issue search in erikgunawan/doforme using an authorized
GitHub account returned no results. A metadata search for documents named doforme
in the connected Drive also found none. No pilot repository/issue URL, owner
scope/AC decision, or permission to edit another repository had been provided.
The pilot therefore had not run.

The original instruction limited source changes to doforme. For another target,
the owner must explicitly identify the target and grant edit permission before
writing there. Reading a candidate does not authorize a fix.

## Minimum owner inputs

| Input | Required clarity |
| --- | --- |
| Target | Repository URL, real issue, baseline branch/revision, permitted environment |
| Permission | Exact editable files, test commands, temporary artifacts, and output location |
| Requirements | Source content, origin/locator/version, confirmation of applicability, observable AC |
| Conflicts | Owner decisions on conflicting sources and excluded scope |
| Operations | Available model/dependency access, cost/time caps, isolation decision |
| UAT | Claimed owner identity, per-AC decisions, and actual evidence for tested content |

Do not include credentials in issues, requirements, or manifests. A URL alone
does not provide source content; a screenshot file does not automatically verify
visual or UX requirements.

## Execution after inputs are complete

1. Choose an isolated checkout/worktree with a clean baseline. Do not use someone
   else's worktree changes or automatically reset/stash them.
2. Load the plugin, inspect onboarding, and prepare the repository profile, issue
   input, and applicable source snapshots. Generated drafts do not confer authority.
3. Run doctor and inspect-config. Review exact scope, commands, and output.
4. Run analyze/plan and check source → requirement → AC → test traceability.
   Unclear requirements, conflicts, or material evidence must stop the fix.
5. With direct permission, run fix/test/review/draft. Record observed red/green,
   minimal diffs, content bindings, scope boundaries, and every failure/denial.
6. Obtain owner UAT decisions for tested content/revision. Use content-bound
   acceptance evidence when available; a name in JSON is not identity authentication.
7. PR publication, notifications, and issue closure are separate actions. Do not
   claim resolved merely because the pipeline completes or tests pass.

## Pilot report

Record target/issue/revision, sources and scope confirmation, exact grants,
plugin-policy digest, stages/attempts, observed cost, test evidence, diff/hashes,
owner decisions, and limitations. Keep raw traces and sensitive data private;
repository history contains only safe summaries and appropriate evidence references.

Pilot success means the real issue's behavior matches tested AC and owner decisions
are recorded with clear authentication limits. It does not establish arbitrary-code
safety, support for every repository/framework, or production-scale readiness.
Record failures; do not replace them with synthetic fixture results.
