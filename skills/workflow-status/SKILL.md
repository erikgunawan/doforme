---
name: workflow-status
description: Inspect checkpoint status and freshness without executing or mutating workflow state
user-invocable: false
disable-model-invocation: true
---

# Checkpoint status

Require a directly named external checkpoint folder. Use one quoted invocation:
`python3 <plugin>/scripts/run_workflow.py --status --repo <current-root> --output <folder>`.
Never enable resume/retry/execution, modify metadata, remove locks, or run stages.
The helper checks repository identity, HEAD, content manifest and plugin policy
fingerprint, then reports compact stage status, freshness and next pending stage.
It does not rewrite checkpoint files or imply owner acceptance/publication.
If stale, blocked or failed, show the actual reason and manual recovery need;
do not suggest forcing stale work through a gate. No path means request the
checkpoint location rather than searching arbitrary folders.
