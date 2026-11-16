# Direct endtoend slash-command acceptance — v0.17

This opt-in suite exercises the real /doforme:endtoend routing and workflow-runner
agent, not a direct call to the Python pipeline. It uses three independent
synthetic Git fixtures: unconfirmed requirements, confirmed requirements without
execution/edit grants, and a fully authorized confirmed workflow.

```bash
python3 -B tests/runtime_endtoend.py --output /absolute/new-slash-acceptance
python3 -B tests/runtime_endtoend.py --output /absolute/new-slash-acceptance --live
```

Without --live no files or model calls occur. Live mode may use three outer
Claude sessions and up to nine inner stage calls, each with a $1 budget cap.
Inner stages retain their 180-second cap. The outer helper invocation has a
600-second Bash timeout and the test process has a 900-second deadline. A timeout
or denial stops the suite without retry; inspect retained processes/artifacts
before any manual recovery. The fixture source and confirmations are synthetic.

The direct caller authorizes only new checkpoint output and, in authorized cases,
pagination.py/test_pagination.py plus the exact unittest command. The outer agent
may use one effective-config preview and one actual adapter invocation, with
bounded equivalent shell quoting but identical arguments. No broad Bash,
permission bypass, push, PR creation, notification or issue closure is permitted.

The observer checks actual tool results, stage progress and terminal summary,
then independently reads the bound checkpoint and target snapshots. Final model
prose cannot stand in for helper output. The unconfirmed case must stop at analyze;
the no-grant case must stop before fix; only the positive case may edit the two
authorized files and complete all six stages. Every case must preserve HEAD.

For concurrent development, run this suite from an immutable exported plugin tree
containing only the phase under test. That prevents unrelated in-progress source
edits from invalidating the workflow policy digest; the resulting evidence belongs
to that exported policy, not to later versions. Private raw traces/checkpoints
remain outside Git. Observed results and any failed attempts are recorded in
[phase history](PHASES.md).

On 2026-11-16 all three real slash-command cases passed on the immutable staged
plugin tree 753290e4d39a8dcb6443c4a448cbd3126c8baf2a. Unconfirmed requirements
stopped at analyze. Confirmed requirements without execution/edit grants completed
analyze/plan and stopped before fix. The authorized case completed all six stages,
changed only pagination.py/test_pagination.py, preserved HEAD and reported fresh
true. Every case had zero permission denials. The same exported tree passed all
153 offline tests and structure/generated-document checks. Private evidence is
retained under the workstation's sibling artifacts doforme-0.17-slash-a folder.
No real pilot, business acceptance, remote PR or integration activation is implied.
