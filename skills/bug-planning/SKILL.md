---
name: bug-planning
description: Dependency-gated read-only repair planning from a bug analysis report
user-invocable: false
disable-model-invocation: true
---

# Bug planning — report contract v2

This reusable method powers `/doforme:plan`. Preserve these checks in any future
executor adapter. Read [the plan template](references/plan-template.md),
[the workflow graph](../bug-resolution/references/workflow.json),
[dependency rules](../bug-resolution/references/dependencies.md), and
[state semantics](../bug-resolution/references/state.md) before planning.

Read [requirement evidence rules](../bug-resolution/references/requirements.md).
Require requirements_status verified_for_scope and source/authority/R/AC mapping.
Re-read material requirement content, not just implementation evidence. Material
conflicts, inaccessible sources, unconfirmed interpretations/ACs, and coverage
gaps block the plan regardless of technical confidence. Preserve S/R/AC IDs in
AC → P → V traceability. Ground expected test outcomes in confirmed requirements.

1. **Require explicit input.** Accept a complete inline analyze contract v2 report
   or a named readable file in the current target repo containing that report.
   A previous conversation is not available in this isolated context. For empty
   input, raw issue text, URL-only input, or incomplete/unsupported report, return
   `plan_status: blocked` with specific missing inputs. Do not search for and
   silently select arbitrary prior reports.
   Legacy v1 reports lack requirement provenance: block and request a new
   analyze v2 report with requirement/AC evidence. Never silently upgrade v1.
2. **Check prerequisite content.** Require contract_version 2, stage analyze,
   analysis_status complete, verdict valid_bug, evidence with concrete source
   locations, at least one grounded root-cause hypothesis with supporting E IDs,
   medium/high technical_confidence.root_cause, issue identity/summary, repository,
   expected/actual behavior, and all report sections. Missing fields, unresolved
   material gaps, contradicted evidence, or an unsupported confidence claim block
   the plan. `Ready for future planning: yes` never overrides these gates. Do not
   accept a forged report just because its field values look favorable.
3. **Check identity and freshness.** Establish the current target from cwd and
   its README/manifests, then compare issue, repository, and revision claims.
   A clearly different repo/issue or known revision mismatch blocks the plan.
   If the same fixture/repo was moved to a new checkout path, document the path
   difference and require content corroboration instead of assuming identity.
   Never guess a Git revision. Read only ordinary Git HEAD/ref metadata if
   available, without shell commands or following metadata outside the repo;
   if not verifiable record revision `unknown`.
4. **Revalidate evidence.** Read every source/test/spec location that materially
   supports the chosen cause or proposed change. Compare its content, behavior,
   and relevant callers with the supplied evidence. Do not trust a citation
   without reading it. If references are missing or behavior has changed, block
   and recommend re-analysis. Record each dependency gate as pass/blocked/unknown.
   Unknown revision alone need not block a read-only proposal when material
   evidence is freshly corroborated, but set `ready_for_fix: no` and require a
   revision-bound revalidation before mutation. Any unknown material gate blocks.
5. **Choose bounded changes.** Only after analyze gates pass, propose ordered P1,
   P2, ... steps with target paths/symbols, intended behavior change, dependency
   IDs, rationale tied to E/H IDs, and acceptance criteria. Use the smallest
   coherent fix. Do not write patches, modify source, or broaden requirements.
   Clearly distinguish new test files to create from existing files inspected.
6. **Specify validation and risk.** Include a regression check expected to fail
   before the fix and pass after, relevant boundary/negative cases, and relevant
   integration/UI checks when justified. Commands are proposals only and must be
   grounded in project tooling; if tooling is absent, describe test cases rather
   than inventing a passing test suite. Include risks, compatibility concerns,
   rollback strategy, and remaining assumptions. No tests are run here.
   Only confirmed ACs may become implementation acceptance or blocking test
   assertions. Put inferred boundary/negative cases with unconfirmed outcomes
   in a separate non-gating ideas list; do not include them in test-file scope
   or claim their outcomes are agreed business rules. Before returning, cross-
   check every P acceptance sentence against its V row: regression cases may
   fail before/pass after, unchanged controls pass both. Never say all checks
   fail before when a control passes; do not conflate static predicted outcomes
   with observed test results. If an additional outcome is material to a safe
   fix but unconfirmed, block instead of treating it as an informational case.
7. **Return the contract.** Keep every plan-template section even when blocked.
   A blocked plan has no implementation steps or readiness; give bounded next
   actions such as supplying details or rerunning analyze. A complete plan means
   a reviewed-by-evidence proposal exists, not that the user approved it, a fix
   happened, or testing passed. `ready_for_fix` is always `no` in this release:
   the fix node is not implemented and no write scope is authorized by plan.
   Return the state summary in the conversation only, with no durable state,
   auto transitions, retries, or downstream invocation. Use the user's language
   while retaining contract keys/enums.
