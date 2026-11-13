# Workflow contract v1

Implemented nodes: `analyze` and `plan`. Analyze input: bug description or readable local issue file
in a target repository. Output: analysis report contract v2 in the conversation. Effects:
read-only inspection; no persisted artifacts. No network or program execution.

Plan input: an explicitly supplied analysis report, not implicit conversation
memory. Plan re-reads material evidence, checks identity/freshness and dependency
gates, then returns a plan contract v2 with a conversation-only state summary.
Plan never invokes fix or writes source/state. Unknown revision remains an explicit
limitation before any future mutation.

The portable [workflow.json](workflow.json) declares the DAG, implemented nodes,
effects, and report contracts. It is metadata consumed by the planning method and
validated locally, not a scheduler. Semantic gates remain in
[dependencies.md](dependencies.md); a graph edge alone never authorizes a stage.

Graph (`fix` onward remains design only):

`analyze → plan → fix → test → review → pr`

`endtoend` would orchestrate nodes rather than duplicate their instructions.
Triage currently lives within analyze's validity assessment. Nodes communicate
through explicit inputs/results, not executor-specific conversation memory.
Future adapters may map these contracts to Claude, Codex, or other executors;
none of those additional adapters or commands are shipped here.

Analyze and plan report contracts are now v2: they require source/requirement/AC
provenance, conflict handling, and coverage. Workflow/state contract versions
remain 1; the DAG and conversation-only persistence semantics are unchanged.
