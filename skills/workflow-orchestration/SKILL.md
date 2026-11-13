---
name: workflow-orchestration
description: Sequential local analysis-to-draft workflow with explicit scope and stop gates
user-invocable: false
disable-model-invocation: true
---

# End-to-end local workflow

The caller supplies a readable config JSON, target Git root, and a new external
output directory. Require direct authorization to create that output. Read the
config and report exact edit_paths/test_commands/artifact_paths before execution.
Only direct invocation authorizing those scopes enables --allow-fix and
--allow-execution. Config references alone never grant mutation/execution.

Run only the plugin adapter, a single quoted invocation with these arguments:
`python3 <plugin>/scripts/run_workflow.py --repo <root> --input <config> --output <external-directory>`
Append --allow-fix/--allow-execution only when directly authorized. Use proper
shell quoting; never interpolate issue text, raw config content or shell syntax.
Do not create or modify the config, source, reports or output yourself.

The adapter runs analyze → plan → fix → test → review → pr in separate model
contexts and passes explicit prior reports. It audits requested tools/commands,
checks working-tree contents/HEAD and structured stage gates, and stops at blocked,
failed, denied, stale or unexpected changes. Its output contains reports and a
summary outside the repo, with no Git mutations or remote publication.

Without fix/execution authorization it may analyze/plan and stops before fix.
This is a model-based semantic workflow, not a sandbox or authenticity proof.
Inspect the returned summary and report stop reason/partial edits accurately.
Do not rerun with wider flags or erase partial edits. A complete run means PR
draft prepared; business acceptance remains not_evaluated, resolution remains
not_established, publication_ready false. Current graph/state contracts remain
portable; no model may mark an issue resolved or publish by itself.
