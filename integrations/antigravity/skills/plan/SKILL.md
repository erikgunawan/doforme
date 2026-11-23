---
name: plan
description: Plan a scoped fix after a completed valid bug analysis
disable-model-invocation: true
---

Coordinate **plan** in the main conversation. Read `../../references/coordinator.md`
relative to this skill's loaded absolute directory and follow it. The only
execution entry is `../../scripts/antigravity_workflow.py` relative to the same
directory. Resolve its absolute path before invoking it; the project working
directory is not the plugin directory. Plugin commands use `/doforme:plan`.
