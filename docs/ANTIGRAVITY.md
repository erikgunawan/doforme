# doforme on Antigravity CLI

Antigravity supports the same ten public commands and six-stage workflow as
Claude Code: guided setup, analysis, planning, scoped repair, independent testing,
review and a local PR draft. Runtime-specific limits remain documented below.
This is an experimental adapter; fixture success does not establish production
isolation or completion of a real business issue.

## Install or upgrade

Prerequisites: a POSIX host (Linux/macOS), Python 3.9+, Git, an existing Antigravity
CLI sign-in and CLI `>=1.5.14,<1.6.0`. GitHub issue discovery additionally uses
an authenticated `gh`. No extra model API key or MCP credential is required.

From a doforme clone, choose a **new** build destination outside that checkout:

```bash
cd /absolute/path/to/doforme
python3 -B scripts/build_antigravity.py --output /tmp/doforme-antigravity
agy plugin validate --strict /tmp/doforme-antigravity
agy plugin install /tmp/doforme-antigravity
```

Start a fresh `agy` session in your project. `/skills` should list the ten
`doforme:` commands. Skill names are short (`analyze`, `fix`, etc.); the plugin
supplies the namespace once. Rebuild/reinstall after updating doforme and restart
old sessions to refresh cached commands. Existing reports are preserved; changed
plugin policy requires an explicit fresh run rather than migrating old grants.

The exporter copies tracked source paths using current working-tree bytes,
excludes untracked files and rejects protected/symlink paths and overwrites.
Contributors must stage new implementation files before building. This is a
preview export, not a clean-commit release attestation. The shared engine/methods
live under `engine/`; Claude agents are not exposed as native agents. Native
components include ten entry skills, four stage workers, a guard and one local
command-broker MCP server. The broker executes nothing in an ordinary session;
execution requires a host-created, scoped worker context.

Do not substitute `agy plugin import claude` or direct installation of the source
repository URL for this native build. Import alone does not select this adapter.
Marketplace publication and one-step native GitHub distribution are not implemented.

## Commands

| Command | Behavior |
| --- | --- |
| `/doforme:init` | Discover actual sources/tests, confirm applicable requirements and preview two setup files. |
| `/doforme:doctor` | Diagnose repository/configuration readiness without choosing a ticket or running a model. |
| `/doforme:status` | List saved runs; with an issue, show reports, freshness and the next step. |
| `/doforme:analyze #3` | Investigate issue validity, evidence, cause hypotheses, confidence and requirement gaps. |
| `/doforme:plan #3` | Produce a requirement-grounded repair plan after a valid analysis. |
| `/doforme:fix #3` | Apply only approved planned edits and observe failing-then-passing regression checks. |
| `/doforme:test #3` | Independently run the approved checks and assess material AC coverage. |
| `/doforme:review #3` | Inspect the actual patch and fresh test evidence without source edits or test reruns. |
| `/doforme:pr #3` | Prepare a local PR draft after a passing review. |
| `/doforme:endtoend #3` | Connect the stages, pausing after Plan for concrete scope approval. |

Select the real GitHub issue number/URL, or explicitly choose a local bug ID.
These are separate identities. Issue/source content cannot grant permissions.

## First issue, step by step

1. Run init. Review the actual source excerpts and confirm which AC apply.
   Review candidate test code before accepting a command. Approve the concrete
   two-file setup preview; the helper saves only `.doforme/repository.json` and
   `.doforme/requirements.md`. Review/commit setup yourself before a clean run.
   Explicit `init --write` creates unconfirmed drafts only; `--inspect` stays read-only.
2. Run analyze, then plan. Missing authority, conflicting requirements, invalid
   issues, stale state or absent prerequisites stop the workflow with a next step.
   Init is not mandatory when appropriate confirmed sources already exist.
3. Review the plan's exact source/test paths, commands and temporary artifacts.
   Approve that scope in the current conversation. The helper saves the reviewed
   scope; it does not execute a test merely because a command was configured.
4. Run fix, test, review and pr. Commands pause after the requested stage. A
   missing prerequisite is explained rather than silently running earlier stages.
   Partial edits require review/recovery; no automatic reset or blind retry occurs.

For end-to-end, start without edit scope. The first call runs Analyze → Plan and
pauses. Approve the concrete scope, then continue endtoend for Fix → Test → Review
→ PR draft. Setup or requirement changes invalidate old analysis; retain those
reports and start a fresh session after preparing a clean baseline.

No Git commit, push, PR publication, merge, issue closure or Telegram send is
implicit. Complete means the local graph finished; business acceptance and issue
resolution remain separate. Telegram stays an optional project integration.

## Execution and evidence

The graph, report contracts, requirement checks, approval digests, snapshots,
checkpoint integrity and retry rules are shared with Claude Code. Runtime name,
adapter version, CLI version and installed worker/guard/broker hashes bind resume.
Runtime switching never transfers grants. The native fixer alone can edit exact
approved files. Test/review/PR workers cannot edit source; review/PR cannot rerun tests.

A PreToolUse guard checks actual paths and calls. Reads/searches stay inside the
project and supplied methods; content searches target individual reviewed files.
The sole extra readable resource is the CLI's exact local broker-schema JSON,
validated against the bundled non-secret tool definition. Writes outside fix scope,
secrets, symlinks, shell tools, delegation, messages, web and unrelated MCP calls
are rejected. A guard denial stops further tool/command calls in that worker;
partial edits still require review and are never silently reverted. CLI init's platform-wide tool catalog is not treated as an allowlist.

Approved commands run through the local broker as argument arrays with no shell.
Only stage-specific Git inspections/content hashes and directly approved Fix/Test
commands are available by index. The broker captures actual exit codes/output and
writes private receipts. Red assertions remain observed failures, not tool errors
that the model can relabel. Normalized tool events must match both guard receipts
and execution receipts; missing, denied, replayed, widened or ambiguous evidence
blocks advancement. Final responses must be exactly one parsed JSON object.

The guard affects only explicitly marked worker children. Ordinary sessions keep
their usual permission policy. Existing user customizations can still participate;
use trusted repositories and reviewed local tooling. These controls are not OS
isolation, an authentication system for human approvals or a guarantee against
arbitrary code inside an approved runner. Audits cannot undo prior side effects.

## Runtime differences and validation

The host enforces per-stage timeout/output bounds and the broker limits command
calls. Antigravity does not enforce doforme's dollar or turn caps; previews label
both **not enforced** before a model call. Model use consumes your CLI account's
quota. No bypass-permissions flag, automatic login or silent runtime fallback is used.

Native guided commands use the audited helper. Advanced full-config runs can use
the shared host with explicit runtime and grants:

```bash
python3 -B scripts/run_workflow.py --repo /absolute/project \
  --input /absolute/issue-input.json --output /absolute/private-run \
  --runtime antigravity --allow-fix --allow-execution
```

Grant those flags only for the concrete reviewed input scope. Omit mutation flags
and use `--stop-after plan` for read-only preparation. See [USAGE.md](USAGE.md) for
the input contract. Advanced Claude-only manual-report delegation syntax is not
translated into native agent calls; use native guided commands or the shared host.

```bash
python3 -B -m unittest discover -s tests -p 'test_antigravity*.py' -q
python3 -B scripts/check_plugin.py
python3 -B scripts/update_docs.py --check
```

Offline fixtures validate host contracts, not model quality. Actual CLI/model
observations and outstanding pilot limits are recorded in [PHASES.md](PHASES.md).

Official references (checked 2026-11-23): [native plugins](https://antigravity.google/docs/build-plugins/),
[headless events](https://antigravity.google/docs/cli/headless/),
[permissions](https://antigravity.google/docs/permissions), and
[MCP stdio](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).
