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
