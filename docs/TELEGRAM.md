# Repository configuration: new and resolved bugs → Telegram

Install this configuration in the target application repository, such as a KlikDown
sandbox. It supports manual and doforme end-to-end fixes. Notifications do not run
Claude, repair source, create PRs, close issues, or activate lab hooks. No model
API key is required for notifications.

**Telegram is entirely optional.** Without this workflow, token/chat ID, or with
DOFORME_NOTIFY_TELEGRAM empty/false, every manual and end-to-end plugin stage remains
available; only notifications are absent. Init, doctor, analyze, plan, fix, test,
review, draft PR, status, and resume need no Telegram credentials. Installation
summary: [plugin installation](INSTALLATION.md#4-optional-install-the-telegram-template).

## Status definitions

| Event | Telegram |
| --- | --- |
| New issue labeled bug, or bug label added to an open issue | New bug; not declared resolved |
| Passing tests, PR draft, unmerged PR, or closed issue without owner evidence | No resolution claim |
| Issue closed as completed, PR merged at matching SHA, required checks passed, owner approver declaration and QA/UAT evidence available | Owner-attested resolution with PR/commit/evidence |
| Issue reopened | Old evidence is insufficient for another resolution; new evidence/declaration required |

Business acceptance comes from the operator-designated GitHub account's declaration,
not AI inference or test status. The workflow verifies account, PR, SHA, checks,
and comment references; it does not inspect screenshot pixels, establish complete
requirement coverage, or authenticate business roles beyond that account list.
The owner attests the PR-to-bug and source/AC relationship. Results are labeled
owner-attested accepted, not AI-proven acceptance.

## 1. Install three files

Start at the KlikDown Git checkout root. Use doforme 0.25+ and review before copying:

```bash
DOFORME="$HOME/doforme"
mkdir -p .github/workflows .github/scripts
cp -i "$DOFORME/integrations/telegram_bugs.py" .github/scripts/doforme_telegram.py
cp -i "$DOFORME/integrations/telegram-bugs.yml.example" .github/workflows/doforme-telegram.yml
cp -i "$DOFORME/integrations/klikdown-tests.yml.example" .github/workflows/tests.yml
```

Use new paths or deliberately merge existing files; do not overwrite someone
else's workflow/CI. Other repositories need project-appropriate test commands.
KlikDown CI runs node tests/run-node.js without npm install or secrets. The selected
runner's Node must meet the project's Node 20+ requirement. BUG-303 regression tests
still need adding and registration; a passing baseline does not prove correct rendering.

Commit/push these files to the application's default branch. Templates in doforme
are outside active workflows, so pushing doforme sends no notifications. Issue/
comment workflows must exist on the default branch to receive those events.
The Telegram-secret job does not check out PR branches.

## 2. Set repository secrets

GitHub → application repository → Settings → Secrets and variables → Actions → Secrets:

| Secret | Value |
| --- | --- |
| TELEGRAM_BOT_TOKEN | Operator-owned bot token from BotFather |
| TELEGRAM_CHAT_ID | Operator-selected destination chat/group ID |

For a private chat, open the bot and press Start. For a group, add the bot and
ensure it can send. Obtain chat ID through reviewed Telegram APIs/tools; avoid
putting tokens in browser URLs, screenshots, issues, Git files, or public conversations.
Do not send tokens to a coding agent/chat. GitHub Actions supplies GITHUB_TOKEN;
this workflow needs no PAT.

## 3. Set repository variables

On the same Actions settings page, select Variables:

| Variable | Example | Purpose |
| --- | --- | --- |
| DOFORME_NOTIFY_TELEGRAM | true | Delivery opt-in; empty/false disables it |
| DOFORME_BUG_LABEL | bug | Required issue label |
| DOFORME_RESOLUTION_APPROVERS | erikgunawan | GitHub usernames authorized to attest accepted QA/UAT; newline- or comma-separated |
| DOFORME_REQUIRED_CHECKS | tests | Required check-job names; one per line |

The approver list is the operator's authority decision. Secrets alone do not
activate delivery. Select the right destinations/accounts and review private-issue
information access before enabling it. Restrict changes to variables, workflows,
and notifier code according to repository policy.

## 4. Test new-bug notifications

1. Ensure Actions is enabled and the workflow is on the default branch.
2. Create a new practice issue, such as BUG-303, labeled bug. Alternatively add
   bug to an open issue.
3. Check Actions → doforme bug Telegram and the destination chat.

Notifications contain repository, issue number, title, and URL. Issue bodies are
not executed or interpolated into shell commands. PRs and PR comments are not
processed as bug issues. Existing issues are not automatically sent retroactively.

## 5. Fix manually or end-to-end, then perform QA

Use either doforme route normally. After fixing/reviewing, commit/push a branch,
create a PR, and merge through human decisions. Use references such as Refs #1
if issue closure should wait until QA. The GitHub issue number may differ from
the BUG-303 code in its title.

Wait for tests on the merge commit/default branch to pass. The owner performs
QA/UAT on that exact merge commit, including D6/regression and KlikDown browser
checks. Do not assume BUG-301/302 are also resolved. Do not declare accepted if
material coverage gaps remain.

## 6. Record evidence and the resolution decision

An approver listed in the variable writes a QA/UAT comment on the issue:

```text
QA/UAT BUG-303 on merge commit <FULL_40_CHARACTER_SHA>:
- D6 and sorting AC: actual outcome ...
- Regression test: ...
- Browser/screenshot/report: ...
- BUG-301/302 remain outside scope; limitations ...
Acceptance decision for the stated scope: accepted.
```

Include complete SHA, actual evidence, and the true decision; do not copy placeholders
as though tested. Copy that QA/UAT comment's permalink.

The approver then creates a **new comment** on the same issue with this format
(only this fenced block). Replace issue/PR numbers, SHA, and permalink with actual
values. Do not edit old approval comments; create a new one if something changes.

````text
```doforme-resolution
{
  "issue": 1,
  "pr": 12,
  "merge_commit": "FULL_40_CHARACTER_SHA",
  "qa": "passed",
  "business_acceptance": "accepted",
  "evidence_url": "https://github.com/OWNER/REPO/issues/1#issuecomment-ACTUAL_ID",
  "source_refs": [
    "docs/rules/dashboard.md:D6",
    "docs/bugs/BUG-303-urutan-deadline-terbalik.md:Kriteria penerimaan"
  ]
}
```
````

Source references retain the target repository's original filenames/headings.
Both comments must be from an approver, unedited, after merge and after the most
recent reopen, if any. The declaration references a PR merged into the default
branch, exactly matching SHA, and an evidence comment on the same issue. Required
checks on that SHA must be completed/success from GitHub Actions.

Close the issue as completed. If the PR already closed it automatically, a new
declaration comment triggers another check. Once all gates pass, Telegram receives
an owner-attested resolution update.

Example message content, rendered in English:

```text
✅ Bug resolved — owner-attested
OWNER/REPO #1
BUG-303 — reversed deadline order
PR: .../pull/12
Commit: <sha>
Approver: <username>
QA/required checks: passed; acceptance: owner-attested accepted
Evidence: <QA/UAT permalink>
```

If closure preceded completed checks, use Actions → doforme bug Telegram → Run
workflow → issue_number to recheck. This does not bypass evidence/approval or
resend a previously recorded attempt.

## Delivery, receipts, and limits

The workflow persists an attempt artifact **before** contacting Telegram, then
rechecks current state/approval/checks before POST. Repeated events stop while
the receipt artifact exists. Resolved keys use closure IDs so additional comments
do not repeatedly notify the same closure. Per-issue concurrency prevents two
simultaneous send jobs; it does not guarantee FIFO order.

A timeout/crash after receipt storage may mean delivery happened or did not.
There is no automatic retry. Inspect chat and artifacts before manual recovery.
Artifacts follow repository retention; deleted/expired receipts can remove
deduplication. This is not permanent exactly-once delivery. GitHub changes after
the final recheck can race POST; messages record verified decisions/commits,
not atomic transactions across services.

The notifier only reads GitHub metadata and POSTs to a fixed Telegram API host,
with no redirects/parse_mode/link previews, package installs, source execution,
push, issue closure, or bot comments. Raw issue bodies/tokens are not archived.
The standalone helper runs in Python isolated mode (-I -B), preventing module
shadowing from the project/PYTHONPATH. Default-branch helper code must still be
operator-reviewed. Corporate identity/authority, semantic UAT correctness, and
deployment requirements remain the owner's process responsibility; labels and
passing tests do not replace them.

## Implementation status

At this feature's implementation checkpoint, configuration/templates and unit
tests existed but were not installed in KlikDown or sent to a real chat: target
repository, token, and recipient had not been supplied. Testing used fake APIs/
senders and claimed no live delivery. Legacy issue_intake.py notification defaults
remain separate and new-issue-only; use this template for the documented resolution gates.

Official references: [issue/comment events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[check runs](https://docs.github.com/en/rest/checks/runs),
[artifact metadata](https://docs.github.com/en/rest/actions/artifacts),
and [Telegram sendMessage](https://core.telegram.org/bots/api#sendmessage).
