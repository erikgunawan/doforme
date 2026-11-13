# Dependency contract v1

`analyze` has no predecessor. Missing issue details/access produce a blocked
report with questions, never guessed inputs or an automatic repair.

Analyze-to-plan and plan-to-fix are enforced by their stage methods. Later
gates remain design only; there is no automatic graph execution.

| Node | Requires |
| --- | --- |
| plan | explicit complete analyze contract v2 report, valid_bug, concrete evidence re-read against current source, same issue/repo, grounded cause hypothesis, medium/high root-cause confidence, resolved material gaps |
| fix | complete plan v2, confirmed S/R/AC coverage, known matching Git revision, clean baseline, fresh sources, direct authorization for exact edit paths and safe validation commands |
| test | complete fix v1 and plan v2, same HEAD and scoped diff, confirmed AC assertion coverage, direct safe command/artifact authorization |
| review | test v1 complete, same HEAD plus matching content binding, confirmed assertions, independent inspection, no material gaps |
| pr | complete review v1 with verdict pass, fresh tested/reviewed bindings, scoped validation; prepares local content only, publication not implemented |

`not_a_bug`, `duplicate`, `needs_information`, blocked analysis, or low cause
confidence stop handoff. New source revision or material issue changes invalidate
prior readiness and require re-analysis. Unknown revision permits only a
read-only plan with corroborated material evidence, never mutation readiness.
Require requirements_status verified_for_scope, readable confirmed applicable
S/R/AC sources, complete material coverage, and no unresolved conflict. Re-read
material requirement snapshots; changed intent requires re-analysis. Legacy v1
reports must be replaced by v2, not silently upgraded. See
[requirements.md](requirements.md). A complete plan is not an approved plan: `ready_for_fix` remains `no` in plan output. Fix checks its own authorization
and prerequisites independently; a supplied readiness flag cannot bypass them.
No retries, automatic transitions,
merge, issue closure, GitHub automation, or Telegram notifications are implemented.

Fix runs only directly authorized local validation; all material ACs need actual
pass evidence and before/after regression results for scoped technical completion.
Business acceptance and independent review remain separate and pending. A fix
result cannot trigger issue closure or publication. See
[fix method](../../bug-fixing/SKILL.md).
