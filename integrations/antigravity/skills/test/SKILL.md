---
name: test
description: Independently run the reviewed checks and report AC coverage
disable-model-invocation: true
---

Coordinate **test** in the main conversation. Read `../../references/coordinator.md`
relative to this skill's loaded absolute directory and follow it. The only
execution entry is `../../scripts/antigravity_workflow.py` relative to the same
directory. Resolve its absolute path before invoking it; the project working
directory is not the plugin directory. Plugin commands use `/doforme:test`.
