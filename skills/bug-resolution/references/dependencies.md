# Dependency contract v1

`analyze` has no predecessor. Missing issue details/access produce a blocked
report with questions, never guessed inputs or an automatic repair.

Proposed future gates (not an executable graph):

| Node | Requires |
| --- | --- |
| plan | complete analyze report, valid_bug, concrete evidence, grounded cause hypothesis, medium/high root-cause confidence, resolved material gaps |
| fix | reviewed plan tied to the same issue and revision; explicit write scope |
| test | implemented changes plus validation criteria |
| review | passing relevant validation, documented limitations |
| pr | completed review, repository access, publication authorization |

`not_a_bug`, `duplicate`, `needs_information`, blocked analysis, or low cause
confidence stop handoff. New source revision or material issue changes invalidate
prior readiness and require re-analysis. No retries, automatic transitions,
merge, issue closure, GitHub automation, or Telegram notifications are implemented.
