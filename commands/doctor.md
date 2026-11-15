---
description: Check fresh-workflow prerequisites without executing source, tests or models
argument-hint: <explicit issue input file; optional repo profile and fresh external output path>
disable-model-invocation: true
context: fork
agent: doforme:preflight-reader
background: false
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/workflow-preflight/SKILL.md`.
The helper is exactly `${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py`.
Invoke `python3` followed by that exact absolute helper path, --repo with the
current selected Git root, and the directly supplied input/profile/output flags.
Do not add Python options, use relative/aliased paths, or reconstruct the plugin
root from the skill path. Quote each path as needed without changing its value.
Inspect only the current selected Git root and input paths directly supplied here:
$ARGUMENTS
No edits, execution, model calls, checkpoint creation or remote actions.
