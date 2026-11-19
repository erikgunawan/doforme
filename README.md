# doforme

**From bug report to PR draft, with evidence at every step.**

doforme is a Claude Code plugin that helps teams investigate bugs, plan repairs,
change code within approved scope, and verify the results. One workflow connects
issues, requirements, testing, and review—with important decisions in your hands.

[Installation and usage](docs/GETTING-STARTED.md) ·
[How it works and workflow diagrams](docs/HOW-IT-WORKS.md)

## Features

### Start a conversation, skip the long prompts

Guided setup discovers requirement sources and candidate tests in your repository,
then helps you review acceptance criteria and configuration through short questions.
In guided mode, you do not need to assemble input JSON or copy reports between stages.

### Work with GitHub issues or local tickets

Issue selection prioritizes GitHub when the repository has a GitHub origin.
Every ticket clearly identifies its source. Local tickets support labs and offline workflows.

### Investigate with traceable evidence

Analysis separates facts, reporter assumptions, and root-cause hypotheses. Reports
include issue validity, evidence locations, confidence, and next steps. Initial
investigation reads source without changing code or running tests.

### Ground fixes in business requirements

Use repository specifications, business documents, or exported Jira/Figma
requirements as confirmed references. Acceptance criteria connect expected behavior
to the repair plan and test evidence. When intent is ambiguous, doforme guides
confirmation before proceeding.

### Six stages, one connected workflow

Analyze → Plan → Fix → Test → Review → Draft PR. Specialized roles handle each
stage, with results checked before the next handoff. Run stages individually to
review each decision, or use end-to-end execution with scope approval after planning.

### Review the scope before code changes

See the files to be changed, test commands, and temporary artifacts before approving
them. Independent testing and review check results against scope and evidence.
The PR draft summarizes the work for review before publication.

### Saved reports, visible progress

Reports and checkpoints are saved automatically per issue outside the checkout.
Check repository readiness, inspect saved runs, and continue stages without losing
context. New runs preserve earlier reports for later review.

### Telegram notifications for the bug lifecycle

An optional integration in the project repository sends new-bug notifications and
owner-attested resolution updates. Merged-PR evidence, required checks, and QA/UAT
decisions connect resolution notifications to the relevant changes.

[Get started with doforme](docs/GETTING-STARTED.md) ·
[Change history](CHANGELOG.md) · [MIT license](LICENSE)
