# doforme roadmap status

## Runtime preview update — 2026-11-23

Version 0.28 adds a separately built native Antigravity CLI preview for doctor,
saved status, read-only analysis and planning. It reuses the graph/checkpoint
engine with a provider adapter, pre-tool read boundary, retained audit evidence
and runtime-bound resume checks. Fix/testing/publication remain unavailable in
that runtime. See [ANTIGRAVITY.md](ANTIGRAVITY.md) for installation and limits,
and [PHASES.md](PHASES.md) for actual fixture-model observations. This does not
complete the outstanding real KlikDown pilot or business acceptance gates.

## Earlier phase baseline

Status as of 2026-11-16. Versions mark development checkpoints, not proof that all
live/production conditions for a phase have been met. Factual phase 1–16 history
is in [PHASES.md](PHASES.md) and [CHANGELOG](../CHANGELOG.md).

| Phase | Available result | Outstanding conditions |
| --- | --- | --- |
| 17 — endtoend slash command | Three real Claude checks passed: requirement-blocked, no-execution-grant, and six-stage completion on a fixture | Not a real-issue pilot; runs used exported, frozen policy |
| 18 — acceptance | Human-decision validator bound to source/AC/content/checkpoint; swapped-AC regression fixed | No real owner UAT/attestation; identity/authority is not authenticated; pre-commit only |
| 19 — real pilot | Input, scope, execution, and evidence checklists prepared | Pilot repository/issue/owner AC and permission to edit another repository not yet supplied; pilot not run |
| 20 — requirement sources | Local export snapshots with hashes/provenance and unconfirmed authority | Source URLs/accounts/permissions unavailable; no successful live Docs/Jira/Figma connector claimed |
| 21 — operations | Bounded POSIX executor, timeout/output cap/cleanup/environment filtering; one real Claude probe passed | No validated OS sandbox, CPU/memory/network isolation, or broad scale/provider testing |
| 22 — PR publication | GET preview and explicit draft POST adapter with digest/receipt; byte-identical commit handoff tested | No owner-selected proposal/head/base or live remote PR created/validated |
| 23 — integration | Offline diagnosis and real GitHub metadata: intake/analysis/Telegram not configured | Events, owner sources, secrets/config/recipient/send authorization unavailable; nothing activated or sent |
| 24 — release candidate | Reproducible packager/verifier from a clean commit; hashes and explicit release gates | License/owner decision, pilot/live/isolation gates outstanding; not stable/v1.0 |

## Outstanding owner decisions

- A real pilot repository and issue, applicable sources/AC, environment, exact
  scope, and edit permission when using a repository other than doforme.
- Document/Jira/Figma URLs and authorized access; a snapshot does not automatically
  establish authority or remote freshness.
- Integration activation, model authentication on the runner, notification targets,
  and permission for send tests. Do not send credentials through issues/history.
- A reviewed branch/PR proposal if publication is desired.
- Distribution license selection and a stable-release decision from the owner.
- A suitable backend/deployment host for isolation and provider/scale testing.

Work dependent on those decisions remains pending rather than assumed complete.
A passing roadmap checkpoint or fixture test does not itself create notifications,
PRs, merges, tags, or releases.

Guides: [pilot](PILOT.md), [acceptance](ACCEPTANCE.md), [sources](SOURCES.md),
[operations](OPERATIONS.md), [publishing](PUBLISHING.md),
[integrations](INTEGRATION-READINESS.md), and [release candidate](RELEASE-CANDIDATE.md).

Version 0.25 added [Telegram lifecycle configuration](TELEGRAM.md) for target
repositories. It supports new-bug and owner-attested resolution notifications,
without treating closure/passing tests as automatic acceptance. At that checkpoint,
the template had not been installed or delivered to a real chat; the operator,
secret, recipient, and live-verification conditions above still applied.
