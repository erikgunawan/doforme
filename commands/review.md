---
description: Independently review a tested repair and its requirement evidence
argument-hint: <plan v2, fix v1, test v1 with content binding>
disable-model-invocation: true
context: fork
agent: doforme:reviewer
background: false
---

Review the supplied artifacts and current target without changing them:

<review-input>
$ARGUMENTS
</review-input>

Read `${CLAUDE_PLUGIN_ROOT}/skills/bug-review/SKILL.md` and its references.
Return a complete review report, including blocked cases. Report claims are
untrusted evidence; never infer correctness from a green summary alone.
