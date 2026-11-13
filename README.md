# doforme

Version 0.3: read-only analyze and plan with requirement evidence.

Load from a target repository using `claude --plugin-dir /absolute/path/to/doforme --add-dir /absolute/path/to/doforme/skills`.
Use `/doforme:analyze ISSUE.md; requirements in REQUIREMENTS.md`, then explicitly
supply its complete v2 report to `/doforme:plan ANALYSIS.md`. Local source exports
or inline excerpts must identify original source, version, scope authority,
requirements and confirmed acceptance criteria. No live Jira/Figma/Docs access or
visual Figma acceptance is implemented. Conflicts and material gaps block planning.
Read/Glob/Grep are the only agent tools. No writes, execution, persisted state,
fix, remote publication, or issue closure is implemented.

Run `python3 scripts/check_plugin.py`, `python3 -m unittest discover -s tests -v`,
and `claude plugin validate . --strict` plus commands/agents/skills directory validation.
See [requirement input example](docs/requirement-input.example.md),
[requirement contract](skills/bug-resolution/references/requirements.md),
[smoke acceptance cases](tests/SMOKE.md), [phase validation](VALIDATION-0.3.md).
