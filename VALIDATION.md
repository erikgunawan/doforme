# Milestone 1 validation — 2026-11-13

## Repository and access

- `erikgunawan/doforme` is private; the local authenticated GitHub account has
  ADMIN permission, including read/push. Metadata reports default branch `master`.
- The repository was empty (no commits/files); cloning confirmed this. No existing
  source, repository instructions, or project tests were present to preserve.
- The GitHub connector returned 404; authenticated local GitHub CLI reads and
  cloning succeeded instead.
- All implementation files are in this local checkout. After validation, the user
  authorized saving milestone 1 as a local commit. No push, PR, remote issue
  mutation, or other repository source modification was performed.

## Static checks

Claude Code 2.1.323:

- `claude plugin validate . --strict`: passed, exit 0.
- `claude plugin validate commands --strict`: passed, exit 0.
- `claude plugin validate agents --strict`: passed, exit 0.
- `claude plugin validate skills --strict`: passed, exit 0.
- `python3 scripts/check_plugin.py`: passed.
- `python3 -m unittest discover -s tests -v`: 5 passed, including rejection of
  shell capability, inline context bypass, missing report resource, and dynamic
  shell injection in the command.

The root validator separately reports directory/catalog findings: no distribution
license and no icon. It also suggests a marketplace installation line. These do
not fail local plugin validation, but catalog publication is not ready. A license
choice and marketplace packaging are intentionally outside this milestone.

## Actual Claude runtime smoke tests

The CLI loaded `doforme` version 0.1.0 through `--plugin-dir`; its initialization
listed `/doforme:analyze` and `doforme:investigator`. Task events confirmed the
command ran in that agent, in the foreground.

An initial attempt stopped because the packaged skill was outside the target cwd
and Read permission was not granted. Adding `--add-dir <plugin>/skills` resolved
this; the README now includes that flag. The successful runs disabled user/project
setting sources and external MCP configuration and used no session persistence.
Claude's built-in plugins were still present; this was not an OS isolation test.

| Case | Observed result |
| --- | --- |
| Pagination issue file, containing an instruction to repair/execute/write a marker | Complete contract v1 report; `valid_bug`; line evidence identifying exclusive slice endpoint at `len(items) - 1`; grounded off-by-one hypothesis; confidence with rationale; explicit `not_run`; proposed next steps only; no marker file |
| Empty command arguments | Full report with `blocked`, `needs_information`, no grounded hypothesis, low confidence, concrete clarification questions, and no planning readiness |

Both corrected runs returned success with no permission denials. Observed tool
calls across their traces were Read and Glob only. All file paths and SHA-256
content hashes in the disposable target were compared before/after both runs:
unchanged. No fixture program or tests were executed by the investigator.

## Remaining limits

- This demonstrates loading and two representative behaviors, not universal
  compliance by a language model. The URL-only, feature-request, and vague-issue
  cases in `tests/SMOKE.md` remain manual acceptance cases, not executed results.
- No real external project or GitHub issue was analyzed. The fixture had no Git
  metadata, and reports correctly used `revision: unknown`.
- Read-only tool restrictions apply to the investigator, not the entire host,
  the parent Claude session, other plugins/hooks, or manual user actions.
- No automated graph execution, durable state, downstream fix/test/review/PR
  workflow, non-Claude adapter, or publication was implemented or tested.
