# Working on doforme

Every change must keep user documentation and change history current.

- Update docs/INSTALLATION.md and docs/USAGE.md when installation or behavior changes.
- Stage only intended changes, then run `python3 -B scripts/update_docs.py --sync --summary "Clear description of the change"`.
- CHANGELOG.md, docs/REFERENCE.md and docs/changes.json are managed outputs; use the updater instead of editing them directly.
- Run `python3 -B scripts/update_docs.py --check`, `python3 -B scripts/check_plugin.py` and the appropriate offline tests.
- Enable the repository's pre-commit hook as described in CONTRIBUTING.md. It updates/stages only the three managed files and preserves separately staged code.
- Do not replace unrelated hooks, bypass a failed check, invent semantic release notes, silently stage unrelated files, or publish without authorization.
- Generated history records file changes, not technical validation or business acceptance. Keep test evidence and limitations in docs/PHASES.md.
