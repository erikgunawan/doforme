# Requirement evidence phase — doforme 0.3.0

Validated on 2026-11-13 with Claude Code 2.1.323.

## Changes

- Analyze/plan report contracts are v2. The portable graph declares analysis_v2
  and plan_v2; graph, requirement, and state vocabulary keep their own version 1.
- Shared requirement contract records source origin/locator/version/access,
  read status, scope authority, and freshness limits. It maps S → R → AC → E/H,
  then AC → proposed P steps → V checks. Interpretations and agent-derived ACs
  require explicit confirmation. No source type wins automatically in a conflict.
- Material missing/partial/unconfirmed sources, uncovered criteria, unresolved
  conflicts, or unavailable visual evidence prevent planning readiness. A high
  technical confidence does not override these gates.
- Plan re-reads requirement snapshots as well as code. Analyze v1 input is
  blocked with a request for re-analysis, not silently migrated.
- Both outputs separate technical confidence and requirement readiness, and
  retain technical_validation not_run, business_acceptance not_evaluated, and
  resolution_status not_established. They cannot mark an issue resolved.

## Checks

- Strict Claude plugin validation passed for root, commands, agents, and skills.
- Eleven Python regression tests passed, including legacy result-contract
  rejection in the graph, dependency graph guards, and restricted agent tools.
- The local structure/resource checker passed. No additional tool capabilities,
  network integrations, or permissions were added to plugin agents.
- Catalog-only license/icon findings and marketplace-install advice remain.

## Actual model checks

Used isolated disposable targets with synthetic requirements and explicit fixture
owner confirmation. These fixtures do not represent real business acceptance.
Runs used explicit skill-directory read access, no external MCP, empty setting
sources, and no session persistence; built-in Claude plugins were still present.

| Case | Observed behavior |
| --- | --- |
| Analyze with only authoritative Jira/Figma URLs; no contents or approved local substitute | blocked, needs_information; URLs recorded unavailable; preserved technical hypothesis without promoting it to confirmed business intent; no visual acceptance claim |
| Plan after a conflicting synthetic Jira excerpt was appended to the requirement snapshot while analysis still claimed no conflicts | blocked; registered competing expectations; requested explicit owner resolution and re-analysis; no implementation steps despite strong technical cause |
| Legacy analyze v1 report | blocked; requested analyze v2; did not manufacture requirement provenance |
| Complete synthetic v2 report with confirmed source and explicit AC1–AC3 | complete; re-read requirements; S/R/AC registry and AC-to-step-to-check coverage; no mutation readiness or business acceptance claim |

Initial positive-plan review exposed inconsistent wording about before-fix test
outcomes and inclusion of unconfirmed boundary ideas in test scope. The method
and template were tightened to separate proposed non-gating ideas from confirmed
acceptance and to cross-check P acceptance against V rows. The positive case was
then repeated successfully: the test-file scope contained AC1–AC3 only, the
regressions were predicted fail-before/pass-after, the unchanged control was
predicted pass-before/pass-after, and additional unconfirmed ideas were excluded
from acceptance/test scope. These were proposals, not executed test outcomes.

All four cases completed successfully with no permission denials. The positive
case was run twice as described. Final observed tools were Read and Glob only;
every target's file paths and SHA-256 hashes matched its pre-run snapshot,
including after the repeated positive run. No fixture program was executed.

## Practical limits

- No live Jira, Figma, Google Docs, or document-rendering integration exists.
  Supported inputs are local readable text/Markdown exports and inline excerpts.
  A URL alone is not source content; snapshots do not prove authenticity or remote
  freshness. Figma text does not establish pixel/layout acceptance.
- No real business source, production issue, actual owner approval, runtime fix,
  executed test result, or end-to-end business acceptance was validated.
- Requirements that are proposed/unconfirmed, partial-source coverage, and
  visual evidence gaps have additional manual cases in tests/SMOKE.md. The
  executed cases above are representative, not universal behavior guarantees.
- Semantic gates are model instructions. The Python checker checks plugin/graph
  structure, not truth of source claims. A malicious or incorrectly prepared
  source can still mislead a model; supplied authority is not authentication.
- Agents remain Read/Glob/Grep only. Host-wide immutability and parent-session
  behavior are outside this boundary. No persistent state, fix execution,
  automatic issue closure, remote mutation, push, or PR was added.
- Work is local and uncommitted on top of milestone 1; the prior planning-phase
  edits are preserved. Distribution license and icon remain undecided.
