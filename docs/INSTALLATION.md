# Installing doforme

For the experimental Antigravity CLI package, follow [Antigravity installation](ANTIGRAVITY.md).
It supports `/doforme:doctor`, `/doforme:status`, `/doforme:analyze` and
`/doforme:plan` only. Rebuild/reinstall the native package after upgrading, then
start a fresh Antigravity session. The instructions below
install the full Claude Code workflow.

doforme provides packages for Claude Code and Antigravity CLI. For Claude Code,
a local marketplace supports persistent user-scope installation from a GitHub checkout.
Local use does not require GitHub Actions,
Jira, Figma, or Telegram.

## Prerequisites

- Git and Python 3.9+. Helpers use the Python standard library.
- Claude Code with usable account/model access. Latest CLI structure validation:
  2.1.327; guided interactive checks are reported separately.
- Read access to the doforme GitHub repository and the target repository.
- For fixes: a small isolated Git checkout, available HEAD, requirement/AC sources,
  and reviewed local test commands.

Shell examples use Linux/macOS. Helpers are Python CLIs; Windows and other enterprise
environments were not tested in this phase. The model runner uses POSIX processes/
pipes; OS isolation backends need separate review and validation under the
[operations guide](OPERATIONS.md).

## 1. Obtain the plugin

```bash
git clone https://github.com/erikgunawan/doforme.git ~/doforme
cd ~/doforme
python3 -B scripts/check_plugin.py
python3 -B scripts/update_docs.py --check
```

If GitHub denies access, use your organization's GitHub authentication or an
already authorized SSH URL. Do not put tokens in plugin configuration, commands,
issues, or requirements. These structural checks need no additional packages/dependencies.

## 2. Install once and use ordinary sessions

Register the local marketplace and install for this computer's user:

```bash
claude plugin validate "$HOME/doforme"
claude plugin marketplace add "$HOME/doforme"
claude plugin install doforme@doforme-marketplace --scope user
claude plugin list
```

Adjust the path if the checkout is not ~/doforme. User scope makes the plugin
available in every repository on this computer, without copying it or changing
Claude configuration per project. In tested CLI 2.1.327, a local marketplace
installation reads directly from the checkout (readFromFolder). Keep that checkout
available and review local changes before a new session. Other CLI versions may
use a cached copy.

Open a new Claude Code session from the target repository:

```bash
cd /absolute/path/example-repo
claude
```

Use `/doforme:init` or `/doforme:analyze`; `/doforme` alone is not a command.
If an older session does not show commands, close and reopen it. Tool permissions
still follow Claude Code and the project; confirm requested plugin-resource access.

### Development alternative: load for one session

```bash
cd /absolute/path/example-repo
claude --plugin-dir "$HOME/doforme" --add-dir "$HOME/doforme/skills"
```

The plugin path must point to its checkout, while the current directory is the
repository to analyze. --add-dir provides access to plugin methods/references
outside the target. Do not copy plugin source into every target repository.

In Claude, check `/help` and `/agents`, then run:

```text
/doforme:init
```

Expected initial result: repository inspection and short questions about proposed
configuration. Default init is guided and does not write before proposal approval.
For legacy helper inspection without setup conversation, use `/doforme:init --inspect`.
Continue with [short-command usage](GUIDED-USAGE.md). `/doforme:doctor` checks
repository readiness without selecting a ticket; `/doforme:status` lists saved
runs. Issue selection prioritizes GitHub origin and always labels GitHub/Local sources.

## 3. Guided setup or advanced drafts

Guided `/doforme:init` reads candidate sources/tests and asks for AC decisions
and permission to save configuration. To create empty templates only:

```text
/doforme:init --write
```

This only creates `.doforme/repository.json` and `.doforme/requirements.md` when
absent. Requirements remain an unconfirmed draft and test_commands is empty.
Review sources/AC and test commands yourself; the helper does not approve them.
Existing files are not overwritten. See [onboarding](ONBOARDING.md) for full configuration.

The documentation-update hook is for doforme contributors; plugin users do not
need it in every target repository.

## 4. Optional: install the Telegram template

Skip this section if you do not need notifications. Analyze, plan, fix, test,
review, draft PR, status, and end-to-end do not depend on Telegram. Missing token/
chat ID configuration does not block local plugin workflows.

Install templates in the target application repository, not the plugin. From the
project root, copy these two files from an updated doforme checkout:

```bash
DOFORME="$HOME/doforme"
cd /absolute/path/to/project
mkdir -p .github/workflows .github/scripts
cp -i "$DOFORME/integrations/telegram_bugs.py" .github/scripts/doforme_telegram.py
cp -i "$DOFORME/integrations/telegram-bugs.yml.example" .github/workflows/doforme-telegram.yml
```

-i asks before overwriting; review and merge if similar configuration exists.
Projects with CI keep their appropriate tests/checks. Specifically for a KlikDown
lab without CI, an additional template is available:

```bash
cp -i "$DOFORME/integrations/klikdown-tests.yml.example" .github/workflows/tests.yml
```

Do not use KlikDown test commands for projects with another stack. After reviewing
files, commit/push configuration to the **project repository's** default branch.

Under project Settings → Secrets and variables → Actions, configure:

| Type | Name | Value |
| --- | --- | --- |
| Secret | TELEGRAM_BOT_TOKEN | Operator-selected bot token |
| Secret | TELEGRAM_CHAT_ID | Destination chat/group |
| Variable | DOFORME_NOTIFY_TELEGRAM | false during setup; true when ready to send |
| Variable | DOFORME_BUG_LABEL | bug, or the project's chosen label |
| Variable | DOFORME_RESOLUTION_APPROVERS | Operator-designated GitHub approver accounts |
| Variable | DOFORME_REQUIRED_CHECKS | Required CI check names, one per line; for example tests |

Enter tokens directly in GitHub Secrets, not source, issues, or chat. The bot must
be able to send to the selected chat. Notifications require no model API key;
model access is still required to run doforme workflows.

After setup, set DOFORME_NOTIFY_TELEGRAM to true and test with a new practice issue
labeled bug. Resolution notifications require a merged PR, passing checks on the
relevant commit, approver evidence/declaration, and a closed/completed issue.
Follow the format and gates in [Telegram](TELEGRAM.md). The template does not
fix code, create PRs, or close issues by itself.

Without the workflow, with an empty/false flag, or if delivery fails, manual and
end-to-end plugin functions remain available. Delivery problems belong to the
GitHub Actions notification workflow, separate from local plugin results.

## Updating the plugin

For candidate archives, read [candidate verification](RELEASE-CANDIDATE.md) and
select commit/provenance through a trusted channel. Hashes detect changes against
a supplied manifest; they are not owner signatures or proof of stable readiness.
[Roadmap status](ROADMAP.md) records outstanding live gates.

```bash
git -C "$HOME/doforme" status --short
git -C "$HOME/doforme" pull --ff-only
```

For persistent installation, ask Claude to update the installation after pulling:

```bash
claude plugin update doforme@doforme-marketplace --scope user
```

Save/review local changes before updating and restart Claude afterward.
--plugin-dir uses the checkout directly and needs no plugin update. Read
[history](../CHANGELOG.md) before using a new version. Checkpoints bind plugin
policy: version/source changes may make old checkpoints stale. Do not force resume;
review and start a new run when required.

## Testing installation

```bash
cd ~/doforme
python3 -B scripts/check_plugin.py
python3 -B scripts/update_docs.py --check
python3 -B -m unittest discover -s tests -q
claude plugin validate . --strict
claude plugin validate commands --strict
claude plugin validate agents --strict
claude plugin validate skills --strict
```

Unit tests are offline and call no model. Real-model tests are opt-in, incur cost,
and use temporary repositories; see [runtime acceptance](RUNTIME-0.14.md).
Profile/status/resume checks are in [workflow acceptance](RUNTIME-0.16.md), and
direct endtoend routing in [slash acceptance](RUNTIME-0.17.md). Local validation
differs from directory/marketplace eligibility; licensing and listing icons are
separate publication considerations.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| doforme commands missing | Check installation/--plugin-dir, restart the session, and inspect /help |
| Skill/reference unreadable | Include --add-dir for the plugin skills directory |
| Helper permission request/denial | Check exact command/path; do not add a bypass or automatic retry |
| Invalid repository root | Start at the selected Git root, not a subdirectory/non-Git folder |
| Doctor blocked | Read each blocker; doctor does not automatically repair the repository |
| Model/login unavailable | Resolve Claude/organization access; doctor only checks CLI presence |
| Checkpoint stale after update | Review content/policy; use a new run, not changed hashes or removed gates |
| Clone succeeds but issues are not processed automatically | Issue intake remains opt-in; see INTEGRATIONS.md |

Plugin workflows do not automatically push, publish PRs, or close issues.
