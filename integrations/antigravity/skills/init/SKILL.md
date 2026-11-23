---
name: init
description: Set up confirmed requirements and reviewed repository defaults through explicit previews
disable-model-invocation: true
---

Coordinate **init** in the main conversation. Read `../../references/coordinator.md`
relative to this skill's loaded absolute directory and follow it. The only
execution entry is `../../scripts/antigravity_workflow.py` relative to the same
directory. Resolve its absolute path before invoking it; the project working
directory is not the plugin directory. Plugin commands use `/doforme:init`.
