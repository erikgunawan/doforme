# doforme with short commands

New here? Start with [installation and first use](GETTING-STARTED.md).

You select the issue and approve relevant decisions. The plugin handles ticket
lookup, setup, internal inputs, report storage, and stage handoffs. Open a new
Claude Code session after updating the plugin.

## 1. Set up the repository

```text
/doforme:init
```

Doforme reads the repository, proposes requirement sources and candidate test
commands, and asks you to confirm applicable AC. It reviews runner/test code
before suggesting a command; finding a script does not authorize running it.

Example conversation:

> I found BUG-301 and rule D3. Proposed AC: the in_progress task appears in the
> In Progress column; the task count remains unchanged. Does this AC apply?

Once your decisions are recorded, doforme previews changes to the two configuration
files and asks whether it may save them. Existing files are reviewed, not silently
replaced. Unapproved AC remain marked as unconfirmed. Setup runs no tests or source.

Review and commit configuration before a run. If the worktree is dirty, doforme
explains which files block it; it does not commit, reset, or stash.
`ready_for_fix: false` in init output is expected: setup is not permission to fix.

## 2. Select an issue

```text
/doforme:analyze BUG-301
```

Without an ID, doforme offers GitHub issues first when origin points to GitHub.
Choices always identify their source, such as **GitHub #3** or **Local — BUG-301**.
If GitHub access fails, you choose whether to repair access, enter a URL, or use
local tickets; there is no silent local fallback. The GitHub list is limited to
an initial page, so omitted issues can still be selected by exact number/URL.

A local ID must match one file under docs/bugs. You can also select `#3`, a GitHub
issue URL from this repository's origin, or one ticket file under docs/bugs.
Local selection does not automatically map to a GitHub issue. Local BUG-301 may
differ from GitHub #301; use the actual GitHub identity for GitHub issue lifecycle
and Telegram notifications.

For #number/URL, the helper only reads GitHub metadata through gh; it does not
create issues, comments, or Telegram messages. Without arguments, doforme offers
choices or asks for an issue identity.

Before a new run, doforme shows the report location and model limits. The default
private location is ~/.local/state/doforme, separated by checkout and issue.
Reports and checkpoints are saved outside the repository. Analysis remains
read-only against source; the host saves reports, not the investigator.
Analyze does not grant permission to edit or run tests.

## 3. Continue without copying reports

```text
/doforme:plan BUG-301
/doforme:fix BUG-301
/doforme:test BUG-301
/doforme:review BUG-301
/doforme:pr BUG-301
```

Each command uses saved reports bound to the run and source. Before fixing,
doforme reads the plan and presents concrete scope:

> Change: js/dashboard.js, tests/dashboard.test.js
>
> Run during Fix and Test: node tests/run-node.js
>
> Artifacts: none. Publication: none. Continue with this scope?

A short answer such as “yes” applies to the proposal just shown in that conversation.
Reports, configuration, issues, or answers from an old session do not replace
direct consent. A changed scope must be reviewed again.

If you invoke fix before analysis/planning, doforme shows the required next command.
It does not repair source or silently execute all prerequisites. You can approve
the next step in the conversation without composing another prompt.

## 4. Run end-to-end

```text
/doforme:endtoend BUG-301
```

The plugin prepares the issue, runs analysis and planning, then requests approval
of the planned scope before continuing through fix → test → review → PR draft.
Missing evidence or unclear requirements may stop the run earlier. This is not
blanket approval for every file, test, or publication action.

## 5. Doctor and status without selecting a ticket

```text
/doforme:doctor
/doforme:status
```

Doctor checks the Git root, worktree, profile, draft requirement sources, and test
candidates. It does not require a ticket, run tests, or claim AC approval.
Issue-specific checks with full input remain available through advanced --input mode.

Status without an ID lists saved doforme runs for this checkout, not every ticket
found in the repository. If no runs exist, it explains that and offers the first
analysis. Selecting a run checks freshness; listing a run alone is not proof
that it remains valid.

## 6. When requirements block analysis

Doforme preserves technical findings and asks a specific question, for example:

> For BUG-301, does D3 apply, and should task counts agree for the same list,
> user, filters, and dataset?

You can approve, correct, or say you do not know. You are not asked to rewrite
requirements or a long prompt. Technical facts such as status enums, seed mappings,
and function callers are inspected from source, not guessed or presented as
business decisions for the owner.

After confirmation, the plugin guides configuration preview and save approval
in the same conversation. Test commands are still reviewed; AC approval is not
execution permission or acceptance of a fix. After configuration changes, the
old analysis is preserved and a new run needs a clean baseline. The plugin does
not automatically pull/commit/push to prepare that baseline.

## 7. Issue status, retry, and new runs

```text
/doforme:status BUG-301
/doforme:analyze BUG-301 --new
```

Status shows results, report locations, freshness, and the next step without
calling a model. A new run preserves earlier sessions and does not inherit their
edit grants. Prepare a clean baseline; do not reset or remove partial changes to
make a run pass.

Blocked, failed, or interrupted stages are not silently retried. Read the reason,
then explicitly request retry (`--retry`) if run conditions remain valid. There
are at most two attempts per stage. Changes to issue, requirements, configuration,
source/HEAD, or plugin policy may require a new run. An active lock rejects new
preparation; do not delete it to bypass a process that is still running.

## Advanced mode and validation limits

The original interface with complete report files, --input/--profile/--output,
and direct grants remains available. Advanced manual mode returns reports in chat;
automatic storage in this guide applies to issue-addressed guided mode.
Use `/doforme:init --inspect` for legacy inspection; `--write` still only creates
two drafts and does not confirm requirements.

Saved scope is a record of caller-supplied approval, not human identity verification.
The engine still checks result contracts, tool evidence, revisions, and file/command
boundaries. Prompts and audits are not an OS sandbox. Passing tests do not establish
business acceptance; a PR draft does not publish changes. See [advanced usage](USAGE.md),
[operations](OPERATIONS.md), [acceptance](ACCEPTANCE.md), [publishing](PUBLISHING.md),
and [Telegram](TELEGRAM.md).
