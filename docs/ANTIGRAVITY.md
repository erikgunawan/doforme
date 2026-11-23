# Antigravity CLI preview

This experimental adapter supports **doctor, saved status, analyze and plan**.
Claude Code remains the full workflow runtime. Antigravity cannot fix, run tests,
review a fix, prepare a PR or run end-to-end in this release. Guided repository
setup writes are not exposed by the Antigravity package.

## Install

Prerequisites: a POSIX host (Linux/macOS), Python 3.9+, Git, an existing Antigravity CLI sign-in, and CLI
`>=1.5.14,<1.6.0`. GitHub issue discovery additionally uses an authenticated `gh`.
The adapter uses existing CLI sign-in; it does not log in or copy credentials.

Build a separate native package from your doforme clone. Choose a **new** output
directory outside the source checkout; the builder refuses overwrites:

The builder includes tracked source paths using their current working-tree bytes,
excludes untracked files, and rejects protected paths and symlinks. Contributors
must stage newly added implementation files before building. This is a development
preview export, not a clean-commit release attestation.

```bash
cd /absolute/path/to/doforme
python3 -B scripts/build_antigravity.py --output /tmp/doforme-antigravity-preview
agy plugin validate --strict /tmp/doforme-antigravity-preview
agy plugin install /tmp/doforme-antigravity-preview
```

Start a fresh `agy` session in your project. Check `/skills` and `/agents` to
confirm the four skills and `doforme-reader` are loaded. Do not install the
original GitHub URL or import the Claude package as a substitute for this build:
conversion alone does not select the audited Antigravity adapter. Rebuild and
reinstall after updating doforme. Marketplace publication is not implemented.

The build copies the shared engine and methods under `engine/`, keeping Claude
commands and mutation-capable agents outside native component discovery. Native
components contain four explicit skills, one worker and a scoped PreToolUse guard. Source methods
are maintained once; exported copies are build artifacts, not another codebase.

## Use

```text
/doforme-doctor
/doforme-status
/doforme-analyze #3
/doforme-plan #3
```

Select the actual GitHub issue number/URL, or explicitly choose a local bug ID.
They are separate identities. The coordinator previews preparation and execution
before requesting confirmation. Preparation only saves private session inputs.
No project source/configuration is written. Supply existing, reviewed requirement
files; owner applicability/AC must be established in those sources. Empty drafts
and unresolved business decisions block planning. No direct test command is run.

Status lists saved runs without fetching issues. Doctor checks the repository and
CLI without selecting an issue or calling a model. An existing Claude session must
be kept separate: explicitly prepare a new session before selecting another runtime.
Runtime changes never migrate reports, grants or business acceptance.

The advanced host entry point also accepts an explicit runtime/stopping stage:

```bash
python3 -B scripts/run_workflow.py --repo /absolute/project \
  --input /absolute/issue-input.json --output /absolute/private-run \
  --runtime antigravity --stop-after plan
```

This requires the native worker to be installed and loaded by `agy`. It starts a
fresh run unless `--resume` is explicitly supplied. `--allow-fix`,
`--allow-execution`, a missing stopping stage, and stages after plan are rejected
before the model runs. Refer to [USAGE.md](USAGE.md) for the shared input contract.

## Evidence and limits

The host retains its graph, report schema, requirement checks, revision/content
checks, per-stage snapshots, private checkpoints and explicit retry rules. Runtime
name, adapter version, CLI version and installed worker/guard policy hashes are
bound to checkpoints. The host rejects missing or stale installed guard files
before calling the model.
Original Antigravity events, pre-execution guard receipts and normalized audit calls are saved and hashed;
unknown tools/events, missing paths, incomplete calls, denied/failed tools, and
missing or ambiguous JSON results fail closed. The adapter parses exactly one
terminal response object and applies the shared host schema; it does not rely on
the CLI schema flag to establish report validity. Status verifies the saved audit artifacts.

The worker requests a read/search-only tool allowlist and disables inherited
MCP and shell execution. Customizations remain enabled so the bundled guard runs;
existing user rules/hooks can also participate. CLI 1.5.14 reports the full platform tool
catalog in its init event, so that catalog is not treated as proof of restriction.
A bundled PreToolUse guard checks every actual worker call before execution:
only reviewed file reads, searches and directory listings inside the target or
supplied methods are allowed. The observed `read_file(Path)` alias is supported
alongside `view_file(AbsolutePath)`. Writes, commands, messages, delegation, web,
secrets, symlinks and escaping paths are rejected. Content searches must target
one reviewed file so a broad directory search cannot include hidden secrets. Matching guard receipts must
cover every observed tool call. Session deny rules also forbid writes, commands,
MCP and web actions. The guard is active only in host-marked worker children; it
returns `allow` in ordinary sessions without changing their normal permissions. These controls and post-execution
audits are **not OS isolation**, authenticated human identity or proof that inherited
platform configuration can never affect execution. A rejected audit cannot undo
an operation that already occurred. Use trusted local repositories and review the
effective runtime behavior before broader use.

The host enforces timeout and output capture limits. Antigravity does **not**
provide equivalent verified flags for doforme's `max_budget_usd` or `max_turns`;
those settings are explicitly reported as **not enforced** in its execution preview.
Model use consumes the selected account's quota. No bypass-permissions flag is used.
Static analysis is not runtime reproduction, and plan completion does not establish
business acceptance, issue resolution or Telegram delivery.

## Validation

```bash
python3 -B -m unittest discover -s tests -p test_antigravity.py -q
python3 -B scripts/check_plugin.py
python3 -B scripts/update_docs.py --check
```

Offline fixtures validate adapter contracts, not model quality. Actual CLI/model
observations and outstanding limitations are recorded in [PHASES.md](PHASES.md).

Official references (checked 2026-11-23): [native plugins](https://antigravity.google/docs/build-plugins/),
[installation](https://antigravity.google/docs/cli/plugins/),
[headless event stream](https://antigravity.google/docs/cli/headless/), and
[permissions](https://antigravity.google/docs/permissions).
