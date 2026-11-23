---
name: endtoend
description: Run the gated workflow with explicit scope approval after planning
disable-model-invocation: true
---

Coordinate **endtoend** in the main conversation. Read `../../references/coordinator.md`
relative to this skill's loaded absolute directory and follow it. The only
execution entry is `../../scripts/antigravity_workflow.py` relative to the same
directory. Resolve its absolute path before invoking it; the project working
directory is not the plugin directory. Plugin commands use `/doforme:endtoend`.
