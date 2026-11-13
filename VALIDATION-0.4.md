# Scoped fix phase — doforme 0.4.0

Local implementation based on milestone 1 commit f4b787b and the preserved,
uncommitted planning/requirement enhancements. Claude Code version: 2.1.323.

## Implemented behavior

- `/doforme:fix` forks `doforme:fixer`, with Read/Glob/Grep/Edit/Write/Bash.
  Analyze and plan keep their Read/Glob/Grep-only capabilities.
- Complete plan v2, confirmed requirement/AC coverage, no material conflicts,
  matching known Git revision, clean tracked baseline, and fresh evidence are
  required. Only explicitly named read-only input reports/snapshots may remain
  untracked. Source/test dirtiness is not silently accepted.
- Direct invocation must authorize exact edit paths and exact test commands.
  Plans and issue content never grant authorization. No automatic installs,
  remote access, Git mutations, publication, or issue closure.
- Regression tests cover only confirmed ACs. Fix records observed red-before /
  green-after results, controls, actual paths changed, and diff boundaries.
- Fix report v1 separates scoped technical completion from pending independent
  review, not_evaluated business acceptance, and not_established resolution.
- The portable graph now implements analyze/plan/fix. Test/review/PR remain
  future stages. There is still no scheduler or persisted workflow state.

## Static checks

Strict plugin/component validation and the local checker passed. Fourteen Python
regression tests passed, including preserving analyze's read-only effect,
preventing fix from skipping plan, and rejecting fixer delegation capabilities.
Distribution license/icon findings remain catalog-only and unresolved.

## Runtime evidence and corrective iteration

Four separate temporary Git targets used synthetic fixture inputs and baseline
commits made by the smoke harness, not by the fixer. PLAN.md was a named untracked
read-only input bound to each test target's HEAD. The permission setup allowed
only exact Edit paths for pagination.py/test_pagination.py, the named unittest
command, and read-only Git inspection. No bypass-permissions mode was used.

| Case | Observed outcome |
| --- | --- |
| No direct edit/command authorization | blocked; no program commands or file edits |
| Known revision deliberately mismatched | blocked; no test execution or edits |
| Unresolved requirement conflict omitted from the plan | blocked on source revalidation; no edits or tests |
| Complete plan plus exact authorized paths and command | AC1/AC2 failed as assertions before the endpoint fix, AC3 control passed; all three passed after the scoped correction; only pagination.py/test_pagination.py changed; HEAD unchanged |

Initial positive execution attempted compound shell commands, including appending
an echo to obtain an exit code. The echo compound command was permission-denied;
the initial final report still marked complete after a plain test run. This did
not satisfy the strict intended stop/command policy. The method was tightened:
one command per Bash invocation including Git, no echo/helper commands, no retry
after a denial, explicit status evidence, and full report sections on blocked
paths. The positive and no-authorization cases were repeated on fresh copies.
This is a documented model-compliance limitation, not proof of OS enforcement.

The repeated positive run used separate exact commands with no permission denials
and observed the intended assertion failures followed by three passing tests.
Its first boundary report checked only the input header; this was tightened to
require full input comparison and an actual patch read. A final fresh-copy run
then inspected `git diff`, read the full new test file, re-read all of PLAN.md,
and recorded input_integrity verified_full_content. Its complete fix report kept
business acceptance not_evaluated, resolution not_established, and review pending.

Independent harness checks compared non-.git file hashes and HEAD for every
case. Negative targets stayed unchanged. In the final positive target only
pagination.py and test_pagination.py differed, no cache/marker artifacts existed,
all report/requirement inputs were unchanged, and HEAD stayed fixed. Trace
inspection confirmed the exact authorized test command ran twice: exit 1 with
two assertion failures and one passing control, then exit 0 with all three OK.
No final positive command contained shell chaining or additional helper programs.

## Boundaries and remaining work

- Fixer has raw file and shell capabilities. Its semantic scope gates are model
  instructions with normal Claude tool permissions, not an OS-enforced sandbox.
  Exact path permission rules do not constrain arbitrary subprocess side effects.
  Test source/config inspection and disposable execution are important limits.
- Actual tests use only Python standard library fixture code and confirmed
  synthetic ACs. No real production repo/business source or UI was validated.
- Dirty baseline, unsafe runner, execution denial, failed post-fix checks,
  symlink/traversal scope, and unexpected outputs have additional manual cases;
  they are not claimed as executed acceptance tests here.
- Neither scoped green tests nor complete fix status implies independent review,
  overall regression coverage, business acceptance, or issue resolution.
- Reports and requirement sources remain read-only inputs. No durable state,
  commit/push/PR, remote mutation, or changes to another real repository's source.
- Implementation work is local and uncommitted; no publication was attempted.
