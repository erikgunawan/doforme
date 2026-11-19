# Installing and using doforme

This guide helps you install the plugin, prepare a repository, and handle your
first issue. See [guided usage](GUIDED-USAGE.md) for conversation details and stop conditions.

## 1. Install once for all projects

You need Git, Python 3.9+, and Claude Code with active model access. The runner
uses a POSIX environment. To read GitHub issues, install GitHub CLI (`gh`) with
access to the project repository. Model calls use your account and run limits.

```bash
git clone https://github.com/erikgunawan/doforme.git "$HOME/doforme"
claude plugin marketplace add "$HOME/doforme"
claude plugin install doforme@doforme-marketplace --scope user
```

Use a GitHub account with repository access. Open a new session from your project:

```bash
cd /absolute/path/to/project
claude
```

The plugin is available at user scope; you do not need plugin flags every time
you open a session. Adjust the path if your plugin checkout is not ~/doforme.
See [installation](INSTALLATION.md) for prerequisites and troubleshooting.

## 2. Prepare the repository

```text
/doforme:doctor
/doforme:init
```

Doctor checks repository readiness without asking for a ticket. Init reads
candidate requirement sources and test code, asks you to confirm relevant AC,
and previews configuration changes before requesting permission to save them.

Review and commit approved configuration before starting a run that requires a
clean baseline. Setup does not automatically pull, commit, push, or run tests.
Discovering a script does not authorize executing it.

## 3. Choose an issue and workflow

To select an available GitHub issue:

```text
/doforme:analyze
```

GitHub issues from the repository origin are offered first, with clear source
labels. You can enter a number/URL directly or choose a local ticket.

The following examples use GitHub issue #3. Replace it with the actual number:

```text
/doforme:analyze #3
/doforme:plan #3
/doforme:fix #3
/doforme:test #3
/doforme:review #3
/doforme:pr #3
```

Keep the same issue identity between stages. For a local ticket, an ID such as
BUG-301 finds one file under docs/bugs. Local IDs are not automatically mapped to
GitHub numbers. Guided reports are saved automatically outside the checkout.

To run end-to-end:

```text
/doforme:endtoend #3
```

Doforme may run through planning first, then show the proposed edit files, test
commands, and artifacts. Your confirmation is required before changes or execution
within that scope. Unclear requirements or missing evidence can stop the run and
prompt a follow-up question.

## 4. Inspect progress or start a new run

```text
/doforme:status
/doforme:status #3
/doforme:analyze #3 --new
```

Status without an ID lists saved runs for this checkout. Status with an issue
checks that run. A new run preserves earlier reports and does not inherit earlier
edit grants. Requirement, source, or plugin-policy changes may require a new
analysis session.

If blocked, read the reason and answer the relevant question. Do not modify a
report or force resume to obtain a different verdict. See [guided usage](GUIDED-USAGE.md)
for retries and scope approval, or [advanced usage](USAGE.md) for explicit inputs and paths.

## 5. Review, acceptance, and notifications

The PR stage produces a local draft. Publication, human review, CI, QA/UAT, merge,
and issue closure follow the project's permissions and process. Passing tests
and a complete workflow establish technical results within the tested scope;
the requirement owner still decides business acceptance.

For notifications, follow [Telegram template installation](INSTALLATION.md#4-optional-install-the-telegram-template)
in the project repository and [Telegram lifecycle configuration](TELEGRAM.md).
Telegram is optional. A new-issue notification does not automatically run Claude
or repair source code.

## Updating the plugin

From a clean plugin checkout:

```bash
git -C "$HOME/doforme" pull --ff-only
claude plugin update doforme@doforme-marketplace --scope user
```

Restart Claude after updating. Read [CHANGELOG](../CHANGELOG.md) for change history.
See [operations](OPERATIONS.md) for execution and isolation limits. The plugin
uses the [MIT license](../LICENSE).
