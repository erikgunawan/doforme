# doforme

Version 0.2: read-only analyze and plan for evidence-based bug investigation.
Load from a target repository with `claude --plugin-dir /absolute/path/to/doforme --add-dir /absolute/path/to/doforme/skills`.
Run `/doforme:analyze ISSUE.md` and explicitly supply the complete report to
`/doforme:plan ANALYSIS.md`. Commands have separate contexts and do not share
conversation memory. Source evidence, validity, confidence, identity and freshness
are rechecked. Unknown revision permits only a read-only proposal. No fix, shell,
source writes, persistent state, scheduler, GitHub publication or issue closure.
The portable graph describes stage dependencies without automatically executing.

Run `python3 scripts/check_plugin.py`, `python3 -m unittest discover -s tests -v`,
and `claude plugin validate . --strict` plus commands/agents/skills directory validation.
See [phase validation](VALIDATION-0.2.md) and [smoke cases](tests/SMOKE.md).
