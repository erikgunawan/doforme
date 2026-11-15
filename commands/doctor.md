---
description: Check fresh-workflow prerequisites without executing source, tests or models
argument-hint: <explicit issue input file; optional repo profile and fresh external output path>
disable-model-invocation: true
context: fork
agent: doforme:preflight-reader
background: false
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/workflow-preflight/SKILL.md`.
Inspect only the current selected Git root and input paths directly supplied here:
$ARGUMENTS
No edits, execution, model calls, checkpoint creation or remote actions.
