# Workflow contract v1

Implemented node: `analyze`. Input: bug description or readable local issue file
in a target repository. Output: report contract v1 in the conversation. Effects:
read-only inspection; no persisted artifacts. No network or program execution.

Potential future graph (design only):

`analyze → plan → fix → test → review → pr`

`endtoend` would orchestrate nodes rather than duplicate their instructions.
Triage currently lives within analyze's validity assessment. Nodes communicate
through explicit inputs/results, not executor-specific conversation memory.
Future adapters may map these contracts to Claude, Codex, or other executors;
none of those additional adapters or commands are shipped here.
