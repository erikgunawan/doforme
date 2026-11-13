# Dependency contract v1

`analyze` has no predecessor. Missing issue details/access produce a blocked
report with questions, never guessed inputs or an automatic repair.

Analyze-to-plan is enforced by the planning method. Later gates remain design only; there is no automatic graph execution.

| Node | Requires |
| --- | --- |
| plan | explicit complete analyze contract v2 report, valid_bug, concrete evidence re-read against current source, same issue/repo, grounded cause hypothesis, medium/high root-cause confidence, resolved material gaps |
| fix | reviewed plan tied to the same issue and revision; explicit write scope |
| test | implemented changes plus validation criteria |
| review | passing relevant validation, documented limitations |
| pr | completed review, repository access, publication authorization |

`not_a_bug`, `duplicate`, `needs_information`, blocked analysis, or low cause
confidence stop handoff. New source revision or material issue changes invalidate
prior readiness and require re-analysis. Unknown revision permits only a
read-only plan with corroborated material evidence, never mutation readiness.
Require requirements_status verified_for_scope, readable confirmed applicable
S/R/AC sources, complete material coverage, and no unresolved conflict. Re-read
material requirement snapshots; changed intent requires re-analysis. Legacy v1
reports must be replaced by v2, not silently upgraded. See
[requirements.md](requirements.md). A complete plan is not an approved plan: `ready_for_fix` remains `no`; fix is not implemented.
No retries, automatic transitions,
merge, issue closure, GitHub automation, or Telegram notifications are implemented.
