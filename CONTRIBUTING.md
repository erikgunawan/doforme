# Documentation and history for every change

These rules apply to development of doforme, not every repository using the
plugin. [AGENTS.md](AGENTS.md) also asks coding agents to follow this workflow.

## Enable automatic updates once per clone

```bash
cd /absolute/path/to/doforme
python3 -B scripts/install_doc_hooks.py --install
```

The installer only sets local core.hooksPath to .githooks. It stops if another
hooksPath or an existing pre-commit hook is present, preserving your configuration.
For an existing hook manager, add these calls to your managed pre-commit hook
without replacing other hooks:

```bash
python3 -B scripts/update_docs.py --sync
python3 -B scripts/update_docs.py --check
```

Git does not enable hooks automatically when cloning; each contributor clone
needs this setup. No model login or additional dependency is required.

## For each change

1. Update the implementation and affected guides: installation in
   docs/INSTALLATION.md, user workflows in docs/USAGE.md, and test evidence in
   docs/PHASES.md.
2. Stage only intended changes. The hook does not stage unrelated source files.
3. Optionally provide a meaningful summary before committing:

```bash
python3 -B scripts/update_docs.py --sync --summary "Describe the change and its effect on users"
```

4. Run checks, then commit normally:

```bash
python3 -B scripts/update_docs.py --check
python3 -B scripts/check_plugin.py
python3 -B -m unittest discover -s tests -q
git commit -m "Describe the change"
```

Pre-commit automatically updates and stages only three managed files:

| File | Source of truth | Update method |
| --- | --- | --- |
| docs/changes.json | Staged files, Git blob/mode, parent revision, Jakarta date, plugin version | Append an entry for each commit change |
| CHANGELOG.md | docs/changes.json; optional English display translations in docs/history-translations.json | Regenerate readable history |
| docs/REFERENCE.md | Staged manifest and command frontmatter | Regenerate version/command/agent/input reference |

Without --summary, history uses the changed-file list rather than guessing feature
behavior or using a commit message unavailable during pre-commit. Explicit summaries
are retained when the hook refreshes the same entry. Review the summary if scope
changes. Re-running the updater before committing refreshes the pending entry
instead of creating duplicates.

Do not edit generated files manually. The updater refuses to overwrite unstaged
local edits to managed files; review them first. Existing committed entries are
preserved. Unstaged source changes are neither included in history nor overwritten.
Narrative documentation remains the author's/reviewer's responsibility: a generator
cannot determine whether new requirement descriptions or instructions are correct.

Historical summaries in another language may have an English display translation
in docs/history-translations.json, keyed by full change ID. Stage that curated
mapping like source; the generator applies it only when rendering CHANGELOG.md.
It does not rewrite the original summaries, IDs, dates, or content bindings in
committed docs/changes.json history. New summaries should be written in English.

## GitHub and stale-document checks

The `.github/workflows/documentation.yml` workflow supports push, pull request,
and workflow_dispatch. It runs on GitHub once pushed and Actions are enabled.
The job uses contents:read, no model or external secret, no bot commits, and no
issue processing.

Checks verify generated docs are synchronized, old history is not rewritten,
and base-to-head changes are covered by new history entries with current Git
blob/mode identities. Listing a filename alone is insufficient if its content
differs. Renames are recorded as delete/add. For multiple commits, squashes, or
merges, coverage checks net base → head changes; it does not prove every intermediate
commit had perfect documentation.

```bash
python3 -B scripts/update_docs.py --check --base origin/master
```

This cannot block a push that already occurred. Owners should make
`Documentation and history / documentation` a required branch status check to
prevent merges on failure. Git hooks can be bypassed, so CI is an additional
check, not a tamper-proof guarantee against someone modifying the checker or workflow.

History conflicts between branches must merge entries while preserving the base's
committed prefix. After resolving code conflicts, stage the resolution and run
the updater to record final content identities. Do not delete history to pass
checks. CI does not silently repair it.

## Initial history and versions

Initial history is imported from existing Git commits, including subject, manifest
version, and changed files; phase 0.2/0.3 reconstruction retains the limitations
in docs/PHASES.md. Importing creates no new test claims. --bootstrap is only for
initial setup when docs/changes.json does not exist; normal checkouts need not
repeat it. The updater does not automatically bump versions or create GitHub tags/releases.

Upstream references: [Git hooks](https://git-scm.com/docs/githooks) and
[workflow permissions/events](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
