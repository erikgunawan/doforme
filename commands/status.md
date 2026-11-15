---
description: Inspect an explicitly named local checkpoint without running workflow stages
argument-hint: <external checkpoint directory for the current target>
disable-model-invocation: true
context: fork
agent: doforme:status-reader
background: false
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/workflow-status/SKILL.md`.
The helper is exactly `${CLAUDE_PLUGIN_ROOT}/scripts/run_workflow.py`.
Use python3 with this exact absolute helper path; no extra Python options,
relative/aliased paths, or reconstruction of the plugin root from the skill path.
Inspect only the checkpoint directory named in this direct invocation:
$ARGUMENTS
Do not run stages, retry, write state, edit source, or publish anything.
