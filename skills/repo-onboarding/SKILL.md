---
name: repo-onboarding
description: Initialize a reusable repo profile without mixing issue scope or granting execution
user-invocable: false
disable-model-invocation: true
---

# Repository onboarding — utility contract v1

Run one properly quoted helper command from the current selected Git root:
`python3 <plugin>/scripts/init_repo.py --repo <current-root>`.
Use the exact absolute helper path rendered in the command invocation. Never
derive it from this skill's location or add Python flags such as -I/-B/-m.
No arguments to `/doforme:init` means this inspection only, with no file creation.
Append --write only for a direct explicit caller request to create configuration.
The entire write scope is `.doforme/repository.json` and `.doforme/requirements.md`.
Do not add files, modify .gitignore/source, or create/commit a Git repository.

The helper reports tooling marker files and declared package script names. It
does not execute scripts or infer command safety from their presence. New profile
test_commands stay empty, issue-specific edit_paths are excluded, requirement
templates are marked unconfirmed, and ready_for_fix stays false. An existing
setup is never overwritten; partial or unsafe paths need manual review.

Explain the actual outcome: inspection_only, draft_created, or already_initialized.
If existing data needs review, do not call it ready. Missing requirement content,
owner applicability and AC confirmation, exact reviewed test commands, and issue
input remain explicit next steps. Re-running init cannot approve business intent.

The repo profile holds reusable defaults and execution limit caps. A separate
issue JSON provides issue_ref, issue_text, and exact edit_paths; it may choose
specific test commands, add requirement sources, or lower limits. It cannot omit
profile requirement sources, raise caps, edit the active profile, or grant
execution. Use the runner with --profile and --input explicitly. No silent profile
discovery is performed. Direct mutation/execution flags are still required.

Return a concise onboarding result with paths created (or none), structural
profile status, observed markers, limitations and next actions. No secret setup,
live Jira/Figma fetch, test run, publication, business acceptance, or resolution.
Use the user's language for the explanation while preserving machine keys.
