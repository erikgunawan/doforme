# Requirement source snapshots — phase 20 foundation

This helper imports explicitly selected text exports from business documents,
Jira, Figma, repository specifications, or user confirmations. It preserves original
content with provenance and hashes without changing the source. It does not fetch
URLs, connect accounts, call models, execute source, automatically confirm requirements,
or validate visuals.

Live-source integration remains incomplete: actual document/ticket/frame URLs,
access rights, pilot-source needs, and service accounts were not supplied. This
local helper is usable now; do not describe it as successful live Jira/Figma/Docs integration.

## Explicit manifest

Save exports as regular UTF-8 text files in the target repository. The manifest
may be outside the checkout, such as `/absolute/inputs/sources.json`:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "source_id": "S1",
      "kind": "jira",
      "path": "requirements/BUG-123-export.md",
      "origin": "https://example.atlassian.net/browse/BUG-123",
      "origin_locator": "description and acceptance criteria",
      "version": "owner-supplied export; updated time not verified",
      "source_accessed_at": "unknown"
    }
  ]
}
```

Supported kinds: business_document, jira, figma, repository_spec, and
user_confirmation. origin and origin_locator are caller-supplied metadata, not
proof that the helper read a remote system. Omitted version remains unknown.
Optional source_accessed_at accepts a caller-supplied timezone-aware ISO timestamp;
the helper does not invent a remote access time.

```bash
python3 -B /absolute/doforme/scripts/requirement_sources.py --repo /absolute/target --manifest /absolute/inputs/sources.json --output /absolute/snapshots/bug-123
```

The repository must be the selected Git root. Output must be a new directory
outside target and plugin checkouts, with an existing parent. Directories use mode
700 and files mode 600; existing files are not overwritten. A write failure may
leave a partial snapshot, disclosed for manual review rather than silently deleted.

## Output contents

- S1.txt, S2.txt, and so on: unchanged UTF-8 bytes of the read exports.
- sources.json: supplied origin/locator, actual local locations/line ranges read,
  version, SHA-256, byte length, and UTC import timestamp.
- authority remains unconfirmed, freshness unknown, requirements_status
  needs_information, business_acceptance not_evaluated, and remote_actions none.

Import time differs from remote source access/update time. Hashes detect changed
snapshot bytes; they do not establish owner identity, export authenticity, or
latest remote version. Instructions inside text remain untrusted data and are
never executed. A user_confirmation source does not automatically authenticate
the requirement owner's identity.

Review sources and metadata together before placing approved copies in the target
repository for requirements configuration. The helper does not edit profiles,
automatically add sources, stage files, or commit. Owner-applicability evidence,
conflicts, and AC must still be supplied and checked during analyze/plan. Export
snapshots are not implementation-acceptance evidence.

## Limits and checks

The manifest is limited to 1 MB, each source to 1 MB, total content to 4 MB, and
source count to 16. Source IDs and canonical paths must be unique. Files must be
regular, non-symlink, nonempty UTF-8 text. Traversal, credential sources, FIFO/special
files, duplicate JSON keys, authority-granting fields, and credential-bearing origin
URLs are rejected. No automatic source precedence exists between documents, Jira,
and Figma. Text-only Figma imports support textual claims only; pixels, layout,
and visual interactions are not tested.

Local validation uses temporary Git repositories and synthetic exports, covering
bytes/hashes, schemas, scope, permissions, special files, partial failures, and the
actual CLI. These tests do not contact Jira, Figma, Google Docs, or GitHub and do
not establish live account or business integration.
