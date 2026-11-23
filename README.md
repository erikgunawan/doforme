# doforme

**Turn a bug report into a fix your team can review.**

A Claude Code plugin that connects issue investigation, business requirements,
scoped repairs, independent testing, and review—through to a local PR draft.
Bring the issue. Review the plan. Approve the scope. Keep the evidence.

[Get started](docs/GETTING-STARTED.md) · [Explore the workflow](docs/HOW-IT-WORKS.md) · [Antigravity preview](docs/ANTIGRAVITY.md) · [MIT license](LICENSE)

[![Animated illustration of doforme moving from issue selection through analysis, plan approval, repair, testing, review, and a PR draft](docs/media/workflow-preview.gif)](docs/WORKFLOW-PREVIEW.md)

*An illustrated walkthrough with example data. Your approval connects the plan to
code changes; your team's delivery process takes the draft through acceptance.*

## What you get

| Capability | Why it helps |
| --- | --- |
| **Guided setup and short commands** | Start from an issue ID or URL. Doforme handles setup questions, internal inputs, and report handoffs. |
| **Antigravity CLI preview** | Reuse requirement-grounded analysis and planning with a native read-only package. |
| **Evidence before edits** | Investigate issue validity, trace symptoms to source, and separate root-cause hypotheses from facts. |
| **Requirements that shape the repair** | Connect confirmed business rules and AC to the plan and test coverage. Use repository specs or supplied business/Jira/Figma exports. |
| **A scope you can approve** | Review exact files and test commands before the fixer changes code. Clarify ambiguous requirements in the same conversation. |
| **Independent testing and review** | Separate stages inspect behavior, the diff, and evidence before producing a reviewable PR draft. |
| **Progress that stays with the issue** | Saved reports and checkpoints make results, blockers, and next steps visible. New runs preserve previous reports. |
| **GitHub and local ticket support** | GitHub-first selection clearly labels each source. Local tickets support labs and offline work. |
| **Optional Telegram updates** | Notify your team about new bugs and owner-attested resolution through a separate project integration. |

## See how end-to-end connects

![Complete doforme workflow: issue and confirmed requirements, six gated stages, then the team's publication, review, CI, QA/UAT, merge, and closure process](docs/media/workflow-overview.svg)

The runner prepares a local PR draft. Your team controls publication, review, and
business acceptance. Telegram resolution updates require the relevant merged PR,
required checks, and owner evidence.

## Work at your pace

**Review each stage.** Investigate first, inspect the plan, then continue through
fix, test, review, and draft preparation using the same issue identity.

**Run end-to-end.** Let the coordinator connect the stages, pause for scope
approval after planning, and surface missing requirements or evidence when needed.

[Install and try your first issue](docs/GETTING-STARTED.md) ·
[Watch the illustrated workflow](docs/WORKFLOW-PREVIEW.md) · [Change history](CHANGELOG.md)
