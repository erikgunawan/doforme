# Local phase history and verification

Earlier uncommitted work was reconstructed into coherent cumulative snapshots,
then committed without rewriting milestone 1. The 0.2/0.3 snapshots are phase
reconstructions, not claims of byte-for-byte historical working trees.

| Version | Phase | Local verification |
| --- | --- | --- |
| 0.1 | analyze plugin | existing f4b787b; validation in VALIDATION.md |
| 0.2 | planning and graph foundation | 10 tests; strict component validation |
| 0.3 | business requirement evidence | 11 tests; strict component validation |
| 0.4 | scoped fixes | 14 tests; strict component validation; recorded red/green fixture evidence |
| 0.5 | independent scoped testing | 16 tests; strict component validation; real model test passed AC1–AC3, no-authorization case blocked validation, both targets unchanged |

Version 0.5 model traces had no permission denials. Read-only Git inspection was
used in both cases; only the authorized case executed unittest. Test results do
not establish independent code review or business acceptance. Fixture inputs are
synthetic. No push or remote PR was made. Prior validation documents describe
what was true at the time of their original runs (including then-uncommitted work).


Version 0.6 adds independent review and content binding. Eighteen regression tests
and strict components passed. Actual model checks: matching tested content passed
review; a test file changed after validation was blocked despite the same HEAD.
Both review targets stayed byte-for-byte unchanged with no permission denials or
test execution. The stale report used inconsistent complete/blocked status wording;
the method now explicitly requires blocked status whenever verdict is blocked.
Advance gates must require both completion and verdict pass, never status alone.
Test reports now carry before/after Git blob IDs for every material input so
review can detect dirty-tree changes after testing. Scope authority and snapshots
remain supplied evidence, not authenticated live business acceptance.


Version 0.7 adds PR preparation only (no remote publication). Twenty tests and
strict components passed. Actual model runs prepared an evidence-backed draft
from a passing review and blocked a changes_requested review. The first positive
attempt appended an unauthorized echo helper; the command was denied. The method
was tightened to stop on denial and prohibit helpers; a fresh positive rerun had
no denials. All targets remained unchanged. Drafts retained pending business
acceptance and publication_ready no, with no invented issue number or remote PR.


Version 0.8 adds the sequential local CLI adapter and /endtoend entry point.
Thirty-four deterministic tests passed, including scope/authorization, tool audit,
actual test-result requirements, regression-before-fix evidence, and stop gates.
The first real adapter runs exposed unavailable automatic structured output in
restricted-agent mode and stopped without edits. Explicit raw JSON envelopes with
local validation fixed the protocol: a real missing-requirement run now returned
blocked at analyze with no downstream call. A positive real integration run was
started separately; final results are recorded in the subsequent state phase.
The adapter never publishes remotely, and complete means draft preparation only.


Version 0.9 adds graph v2, atomic private checkpoints, attempt history, single-run
locks, /status, fingerprint-checked resume, bounded explicit retry and partial-
edit recovery stops. Forty-six deterministic tests passed. A real blocked analyze
run persisted a checkpoint; after plugin policy changed, status correctly marked
it stale and resume refused without a model call or checkpoint mutation.
The positive adapter integration reached analyze/plan/fix/test complete with real
regression and independent validation. Review returned a valid pass envelope
preceded by one progress sentence; the strict initial parser stopped. The new
parser accepts exactly one complete JSON object after a short prefix while still
rejecting duplicate keys or multiple objects; the saved actual review trace
passed this parser, envelope validation and read-only audit offline. A fresh full
checkpoint integration is run after freezing this version; its final outcome is
recorded below when complete. No remote publication or business acceptance.
