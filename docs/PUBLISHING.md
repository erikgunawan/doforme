# Controlled draft PR publication

`/doforme:pr` still prepares local text only. This separate adapter checks a
proposal against explicitly selected GitHub repository/branches, then creates a
**draft** PR only with a publication flag and caller-reviewed digest. The default
is GET/read-only; it does not create branches or push.

No real PR was created during implementation of this feature. Unit tests use a
mock GitHub client; actual GitHub access/branches and owner review decisions are
still required for live use.

## Prerequisites and commit handoff

- Git, Python, authenticated `gh` for github.com, and an explicit destination repository.
- A complete workflow checkpoint with passing review, valid artifacts/digests,
  unchanged plugin policy, and target content identical to the tested snapshot.
- Target origin must point to the same GitHub repository. Repository input is
  case-insensitive; after verifying GET metadata, the adapter uses GitHub's
  canonical name for binding, subsequent requests, receipts, and URL verification.
  Use two distinct existing branches with no open PR for that head/base.
- The complete remote head tree must match tested snapshot blobs/modes, head must
  descend from the tested baseline, and the base→head diff must be nonempty and
  within edit_paths. Publication does not yet support symlinks, submodules,
  truncated trees, or temporary workflow artifacts.
- Title/body must come from human-reviewed local files. Closing references such
  as Fixes #N, Closes owner/repo#N, or Resolves issue URL are rejected; use
  non-closing references such as Refs #N.

Normal workflows bind baseline HEAD and worktree changes. Committing/pushing the
tested patch changes HEAD. The adapter offers a **separate handoff**: if HEAD
changes, it requires a clean checkout, the tested baseline as an ancestor, and
the entire new commit tree to exactly match tested content. The proposal records
revision_transition with tested_revision and current_revision.

Original checkpoints/reports are not edited or rebound. Normal `/doforme:status`
and resume may still mark the checkpoint stale because HEAD changed. Handoff
only states that the new commit contains identical bytes/modes; it does not claim
old reports were produced on the new commit. Extra changes from commit hooks or
automatic formatting reject the handoff if tested bytes differ. Ignored/untracked
files present in the tested snapshot must also be considered: the adapter requires
a complete remote-tree match, not just two visible source files.

Owners arrange commit/push themselves through the project's procedures, outside
this adapter. To preserve the baseline checkout for audit, an owner may prepare
the commit in a separate worktree; the adapter still verifies the remote tree
against the original snapshot. It never auto-pushes to repair a mismatch.

## Read-only preview

Prepare a one-line title (up to 256 characters) and reviewed body with evidence
and risks. The proposal body automatically states that business acceptance and
issue resolution are not evaluated/established; draft preparation does not approve business behavior.

```bash
python3 -B /absolute/doforme/scripts/publish_pr.py --repo /absolute/target --workflow /absolute/run --repository owner/project --head fix-branch --base main --title-file /absolute/title.txt --body-file /absolute/body.md
```

Review preview, changed_paths, head/base SHA, and revision_transition. The digest
binds outgoing text, remote repository/branches/commits, source, and checkpoint.
Preview uses GitHub GET requests, so it is not offline. It creates no receipt
file or remote write. publication_ready remains false: this is not publication
permission, authenticated human review, business acceptance, or merge/deploy readiness.

## Explicit one-time publication

Only after the caller reviews the proposal and authorizes draft PR creation,
provide a **new** receipt in an existing private directory (mode 700), outside
target, workflow folder, and plugin checkout:

```bash
python3 -B /absolute/doforme/scripts/publish_pr.py --repo /absolute/target --workflow /absolute/run --repository owner/project --head fix-branch --base main --title-file /absolute/title.txt --body-file /absolute/body.md --publish --expected-digest COPY_REVIEWED_PREVIEW_DIGEST --receipt /absolute/private-receipts/new-attempt.json
```

The adapter repeats local/remote verification and rejects changed digests. It
exclusively writes and syncs an attempting receipt before POST. The payload is
sent as JSON stdin to fixed-host `gh api`; issue/body content is not interpolated
into a shell. The adapter uses POST pulls directly rather than `gh pr create`,
avoiding interactive or automatic-push CLI behavior.

| Receipt/status | Action |
| --- | --- |
| draft_created | API confirmed the draft on the reviewed repository/SHA; further human review is still needed |
| created_needs_manual_review | API created a PR but SHA moved during the request; inspect it manually and do not assume valid content binding |
| uncertain | Request/response failed or did not establish the expected draft; a PR may exist, so inspect GitHub before another action |
| remaining attempting | Process stopped after creating the receipt; treat the outcome as unknown |

There is no automatic retry, receipt deletion, PR closure, or remote rollback.
An existing receipt always blocks another POST. This is per-receipt deduplication,
not global exactly-once delivery if operators choose new files or multiple machines.
A duplicate open-PR check also runs, but branches/open PRs may change between GET
and POST. Draft creation here has no atomic head/base SHA pin; response checks
detect races and report them for manual review rather than hiding them.

Only draft PRs are created. There is no merge, auto-merge, branch creation, push,
comment, notification, issue closure, or automatic business acceptance. Exit 0
for created_needs_manual_review does not establish valid binding: consumers must
read status/content_binding. Do not recover from failed/uncertain outcomes by
choosing a new receipt without manual inspection.

## Test limits and references

Local tests commit patches that actually change HEAD, verifying byte-identical
handoff without modifying normal runner checkpoint/freshness. Differently cased
repository inputs are tested through mocked POST responses so valid canonical
URLs are not incorrectly labeled uncertain. Tests also cover remote-tree mismatch,
new source, closing references, stale digests, receipt-before-POST, uncertain
delivery, deduplication, and branch races. Checkpoints/GitHub results are synthetic;
there has been no live publication demonstration.

Official references: [GitHub create pull request](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request),
[branch metadata](https://docs.github.com/en/rest/branches/branches#get-a-branch),
[Git trees](https://docs.github.com/en/rest/git/trees#get-a-tree), and
[gh pr create behavior](https://cli.github.com/manual/gh_pr_create).
