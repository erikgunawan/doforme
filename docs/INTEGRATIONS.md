# GitHub issue intake and optional Telegram notifications

The [workflow template](../integrations/github-issues.yml.example) is deliberately
outside `.github/workflows`: committing or pushing this repository does not
activate it. No secret/account was configured and no notification was sent during
implementation. This phase supplies reviewable local integration code, not a
claim of successful live deployment.

## Default behavior

After owner review, copy the template to `.github/workflows/doforme-intake.yml`
in a repository containing this plugin's scripts/skills. It handles issues.opened
only, normalizes event data into a private external packet, and archives the
packet for three days. Manual workflow_dispatch creates a skipped packet because
there is no issue event. No issue body is interpolated into shell commands.
Repository/issue URL and size bounds are checked. Payload content is untrusted,
not requirement authority. Workflow permissions are contents:read only;
checkout credentials are not persisted. Per-issue concurrency limits active runs,
not global exactly-once delivery across separate workflow reruns.

## Optional read-only analysis

Only set repository variable `DOFORME_ENABLE_ANALYZE=true` after review. Supply
an exact reviewed numeric CLI version in `DOFORME_CLAUDE_VERSION` and headless
model access via secret `ANTHROPIC_API_KEY`. The optional installer runs only for
this explicit opt-in and has no model/Telegram secrets in its environment.
The locally tested CLI was 2.1.323; package availability and compatibility must be
verified for the operator's CI environment. No CI job was run in this session.

Optional `DOFORME_TRUSTED_REQUIREMENTS` is a newline-separated list of local
repository text source paths chosen by the operator, never by issue content.
Sources still need explicit applicability/AC confirmation. URL-only/missing
business intent remains blocked. Intake config contains no edit paths, validation
commands or mutation/execution flags: even a valid analysis/plan cannot auto-fix.
Checkpoint/report output remains outside the checkout. Runner/provider calls may
incur costs within configured per-stage limits. Live fix/publication is not enabled.

## Optional new-issue notification

Telegram requires both repository variable `DOFORME_NOTIFY_TELEGRAM=true` and
secrets `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`. Secret presence alone never enables
sending. The script also requires the explicit `--send-telegram` action.
No recipient is inferred. The message contains the issue reference/title and
explicitly does not mark it resolved. Business-acceptance or resolved notifications
are not implemented because those states cannot yet be established automatically.

The helper posts only to Telegram's fixed HTTPS API host, rejects credential URL
injection, disables redirects and link previews, and does not log token-bearing
URLs. A receipt is persisted before delivery. An uncertain delivery or previous
attempt is not automatically retried; the operator must check the recipient before
any manual recovery. This deduplication is per packet directory; separate CI reruns
need an operator-managed durable receipt store for cross-run deduplication.

Tests use fake credentials and injected/mock senders; no HTTP message was sent.
GitHub/Telegram credentials are removed from child model environments. Normal CLI
permissions and scope audits still do not provide OS isolation from subprocesses.
Review artifact contents and repository access policies before enabling archival
or notifications for sensitive issues. Keep packet/checkpoint directories private.

## Local dry-run

```bash
python3 scripts/issue_intake.py --repo /absolute/checkout --event /absolute/event.json --output /absolute/new-packet
```

This writes a packet/input config only and performs no model call or send. Output
must be new and outside the checkout. `--analyze-readonly --packet <folder>` and
`--send-telegram --packet <folder>` are separate opt-in actions; do not execute
them until the relevant operator authorization/configuration is present.

## Verified upstream references

Workflow dependencies are pinned to commits verified against the official tag
refs: [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1)
(`3d3c42e5aac5ba805825da76410c181273ba90b1`) and
[upload-artifact v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2)
(`cf430e030ddbb5b0abf93d22962f4752f3646cd9`). Review/maintain pins and runner
compatibility before activation. The notifier follows
[Telegram sendMessage](https://core.telegram.org/bots/api#sendmessage) without
format parsing or automatic retry. These references establish API/dependency
shape, not proof that this project's workflow has run in GitHub Actions.
