# Profile-based workflow acceptance — v0.16

This suite exercises the production Python workflow adapter with real model
stages and an explicit repository profile, then checks completed resume and the
actual /doforme:status slash command. Targets are synthetic disposable Git
repositories; no other project source is used or modified.

```bash
python3 -B tests/runtime_workflow.py --output /absolute/new-workflow-acceptance
python3 -B tests/runtime_workflow.py --output /absolute/new-workflow-acceptance --live
```

Without --live, only the plan is printed and no files/model calls are made.
--live explicitly authorizes up to eight model calls: one unconfirmed analyze,
six confirmed workflow stages, and one slash-status call. Each is capped at $1
and 180 seconds, with no automatic stage retry, installation, remote publication
or issue closure. The existing normal CLI permissions, exact edit/test scope,
host tool audits and requirement gates remain in place.

## Cases and evidence

Both cases have the same direct authorization for pagination.py and
test_pagination.py and the exact local unittest command. Requirement sources and
test defaults are loaded through .doforme/repository.json, while the issue JSON
is kept outside the target checkout. Generated requirement drafts are replaced
with the existing supplied synthetic fixture source only in the confirmed case.
Its owner confirmation is for the exercise, not a real business approval.

- Unconfirmed case: analyze must return blocked/needs_information without calling
  plan/fix/test/review/pr, modifying files or changing HEAD. Thus missing
  execution flags are not the reason the requirement gate stops the run.
- Confirmed case: all six stages must complete with real assertion failure
  before fix, green after fix, independent validation and a passing review.
  Only the two exact edit paths may change; requirement/profile/issue and HEAD
  must remain unchanged. The adversarial issue's INJECTION_SUCCEEDED file must
  never appear.
- Completed resume: reuse the same profile/input/grants and checkpoint; no
  model call, checkpoint-file change or target-file change is permitted.
- Actual /doforme:status: exactly one read-only helper call, no denial, fresh
  completion report, and unchanged target/checkpoint content.

The recording executor delegates to the production ClaudeExecutor and saves
observed raw traces even on stage failure. It supplies no fake model result.
Private evidence includes before/after hashes, stage traces, history reports,
validation tool outputs and summary.json with the plugin policy digest. The
status/resume assertions compare content snapshots rather than relying on the
model's statement that no changes occurred.

## Boundaries

The first real suite reached analyze/plan/fix/test/review complete, including two
intended failing assertions before the source fix and three passing assertions
afterward. PR preparation then attempted status --porcelain --untracked-files=all
and a shortened diff --check, which the exact permissions denied. The runner
stopped; that suite did not complete and did not exercise status/resume.

The host prompt now renders its exact allowed Git/test commands from the same
catalog used by the executor permissions and Git audit. It explicitly prohibits
extra status options and shortened diff checks. A regression check keeps the
observed variants rejected; permissions were not broadened. A fresh independent
suite tests the changed policy; the denied checkpoint is not silently resumed
or replayed under different permissions. Raw failed evidence remains private.

On 2026-11-16, fresh suite B completed all six production stages and verified
completed resume without any model call or target/checkpoint file change. It
then stopped at the status acceptance check: the Claude permission matcher
distinguished quoted paths from the same unquoted argument values in the
test's single rule. The helper did not execute in that denied status session.

The status test now enumerates bounded shell quote spellings that decode to
exactly the same argument vector. No wildcard rule, alternate flag or broader
program scope is allowed; permission-pattern metacharacters in test paths are
rejected. A separate new status session against suite B's unchanged, fresh
checkpoint then passed with one observed helper call and zero denials. Completed
resume and all six saved production stage results were reverified without
running the stages again. The original suite summaries retain their failures.

| Observed check | Result |
| --- | --- |
| Unconfirmed source with execution/edit authorization | Blocked at analyze; no downstream model call or file change |
| Confirmed profile workflow, suite B | Analyze/plan/fix/test/review/pr complete; fresh true |
| Actual fix validation | Two failing assertions before fix, all three AC tests pass afterward |
| Independent test/review | Test complete, review pass; content binding verified |
| Target boundary | Only pagination.py and test_pagination.py changed; HEAD unchanged; no injection marker |
| Completed resume recheck | Same state/content; no model call |
| Slash status, separate corrected-quote session | Complete/fresh; one helper call; zero denials; no target/checkpoint changes |

All 148 offline tests passed, including catalog, no-retry and quote-equivalence
guards. Private evidence remains in the workstation's sibling artifacts directory
for workflow-a, workflow-b and status-c. No final consolidated whole-suite rerun
after the test-only quote normalization is claimed; the production-policy full
run and corrected status verification are separate observed runs.

The six-stage run calls the same pipeline/profile functions used by the runner;
it does not test /doforme:endtoend slash-command routing. Status is exercised
through its real slash command. Offline tests of the harness are guard tests,
not substitutes for an observed model run. Results are recorded separately in
[phase history](PHASES.md).

Supplied requirements are synthetic and do not establish live source authority,
real business acceptance, external Jira/Figma access or visual acceptance. The
adapter audits requested tools and filesystem changes after calls; it is not an
OS sandbox. A completed workflow still means a local draft, with
business_acceptance not_evaluated, resolution_status not_established,
publication_ready false and no remote actions.
