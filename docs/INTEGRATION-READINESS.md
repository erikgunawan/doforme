# Integration readiness checks — phase 23 foundation

This helper checks the legacy intake template. For the standalone v0.25 new-bug/
resolved workflow, use [Telegram configuration](TELEGRAM.md); legacy checker output
is not live validation of that newer workflow.

The helper checks GitHub issue-intake and Telegram prerequisites without installing
workflows, changing variables/secrets, running workflows/models, or sending messages.
It is entirely offline by default. Live activation remains incomplete without a
pilot issue, confirmed sources/AC, valid accounts/secrets, and an owner-selected
recipient. No recipient or approval is inferred from configuration.

```bash
python3 -B /absolute/doforme/scripts/integration_readiness.py --repo /absolute/target --repository owner/repo --event /absolute/inputs/issue-event.json --requirement requirements/confirmed-source.md
```

Remote repository name must be explicit, in owner/name format. An optional event
must be an issues.opened snapshot matching the selected repository/issue URL;
event content remains untrusted and does not establish actual live event receipt.
--requirement may be repeated for up to 16 operator-selected local source paths.
Source bodies are neither executed nor treated as permission.

The helper can also inspect GitHub metadata through an already authorized CLI
account, only when --check-remote is supplied directly:

```bash
python3 -B /absolute/doforme/scripts/integration_readiness.py --repo /absolute/target --repository owner/repo --requirement requirements/confirmed-source.md --check-remote
```

This uses gh api GET on github.com for repository workflows, variables, secret
names, and active intake workflow content. It does not read secret values or
show unrelated variables. Metadata is repository-level only; environment or
organization secret applicability is not guessed. Incomplete lists or denied
access yield blocked, not a claim that credentials are absent. --telegram-recipient
accepts an explicit operator-supplied chat ID/name, but the helper cannot prove
it matches the chat secret.

## Status meanings

- not_checked: check not performed or input not supplied.
- not_configured: checked configuration prerequisites are missing.
- configured: configuration/metadata is visible; not execution or delivery evidence.
- blocked: invalid input, incomplete metadata, access failure, or a local workflow
  differing from the checked template that needs review.

live_verification always remains not_checked and ready_to_activate false. Secret
names or an active workflow alone never produce verified_live. Exit 0 means a
report was produced, not that integration is ready to activate. The report does
not declare requirements verified_for_scope or business acceptance.

## Prerequisites and manual activation sequence

1. Select a pilot repository/issue and authorized data; review the event, requirement
   sources, and owner AC confirmation. Do not treat synthetic fixtures as real
   business acceptance.
2. Review the [intake template](../integrations/github-issues.yml.example), then
   place an approved copy at .github/workflows/doforme-intake.yml in a repository
   containing plugin scripts/skills. The readiness helper does not copy it.
3. Start in packet dry-run mode. Inspect an actual issues.opened event, private
   artifacts, and deduplication. workflow_dispatch without an issue is skipped;
   a successful manual job is not live issue-intake evidence.
4. If live analysis is authorized, provide DOFORME_ENABLE_ANALYZE=true, a reviewed
   numeric DOFORME_CLAUDE_VERSION, valid ANTHROPIC_API_KEY, and operator-selected
   DOFORME_TRUSTED_REQUIREMENTS. Secret names alone do not establish model login,
   CLI compatibility, or correct requirements.
5. If notifications are authorized, select a recipient and review permitted data;
   provide DOFORME_NOTIFY_TELEGRAM=true and TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID.
   A test send needs separate authorization and actual delivery evidence. This
   helper does not test bots or send messages to check tokens.
6. Inspect receipts before recovery. Uncertain delivery is not automatically
   retried; local receipts do not provide global deduplication across GitHub reruns.

The template defaults to contents:read and does not enable automatic fixes or
publication. Variable-provided sources must match reviewed --requirement inputs;
variables cannot authorize edits or source execution. The helper checks remote
workflow bytes against the supplied template; it does not claim a complete
security audit of YAML, account policy, or subprocesses.

## Verification

Offline tests use an injected metadata reader and temporary repositories to check
no default GitHub contact, event/repository identity, bounded metadata, workflow/
opt-in/version/source paths, secret names not implying success, and no setup/send/
dispatch. FIFO/symlink sources are rejected before opening. The CLI is report-only;
there is no --activate or --send-telegram. Actual remote metadata checks, when
performed, still differ from live verification.

On 2026-11-16, read-only metadata inspection in erikgunawan/doforme successfully
observed repository configuration. Intake was not installed/active, analysis and
notifications were disabled, CLI version was absent, and the three expected secret
names were not visible at repository level. No event, source, owner AC, or recipient
was supplied for live testing. Sanitized reports were saved privately in workstation
artifacts; they do not establish environment/organization secret state. No credential
value was read, setup changed, workflow dispatched, model called, or message sent.

API-schema validation treats malformed workflow/secret rows as blocked, not missing
configuration. Remote workflow content must be a file at the requested path with
valid base64 before comparison with the template.

Official references: [GitHub secret metadata](https://cli.github.com/manual/gh_secret_list),
[repository workflows](https://docs.github.com/en/rest/actions/workflows), and
[using secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
