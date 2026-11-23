---
name: analyze
description: Investigate a bug using read-only evidence and requirement checks
disable-model-invocation: true
---

Coordinate **analyze** in the main conversation. Read `../../references/coordinator.md`
relative to this skill's loaded absolute directory and follow it. The only
execution entry is `../../scripts/antigravity_workflow.py` relative to the same
directory. Resolve its absolute path before invoking it; the project working
directory is not the plugin directory. Plugin commands use `/doforme:analyze`.
