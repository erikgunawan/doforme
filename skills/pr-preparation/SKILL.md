---
name: pr-preparation
description: Prepare an evidence-backed draft PR while keeping publication and business acceptance explicit
user-invocable: false
disable-model-invocation: true
---

# PR preparation — report contract v1

Read [template](references/pr-template.md),
[requirements](../bug-resolution/references/requirements.md), and
[snapshot binding](../bug-testing/references/snapshot.md).

Every Bash call contains exactly one read-only Git command. Never append
echo/printf, shell operators or another command to capture status. Use the tool's
success/failure result. Any permission denial blocks preparation immediately;
do not retry an alternate form or label the draft ready after a denial.

1. Require explicit complete plan v2, fix/test v1 complete, and review v1 complete
   with verdict pass for the same issue/repo/revision. Require material AC coverage,
   scoped green validation and no unresolved P0-P2 findings or requirement gaps.
   Missing/blocked/changes_requested review blocks preparation; do not invent
   a favorable review. Prior conversation is not automatically available.
2. Recheck actual root/HEAD, dirty path scope, diff, full untracked new files,
   material requirement and source bindings using separate read-only Git commands
   allowed in the review method. No other program execution. Changed snapshots
   since test/review block even if HEAD is unchanged. Bind current prepared draft
   to the reviewed content and name exact artifact references.
3. Produce an accurate title and body: concrete symptom, agreed requirement,
   behavior after the change, minimal scope, AC→test results and exact validation
   commands/exit evidence, risks, unrun checks, source/provenance limitations,
   AI review vs pending human review and business acceptance. Do not call static
   reasoning a test run or broaden scoped green checks to full regression proof.
4. An issue reference can be local/unknown. Never invent GitHub issue numbers,
   repository access, branch names, commits or URLs. For a verified issue number,
   use a non-closing reference such as Refs #N; never Fixes/Closes/Resolves magic
   issue-closing text. Describe pending owner acceptance explicitly.
5. This stage prepares a draft only: publication_ready no; remote_created false;
   issue_closed false. Business acceptance remains not_evaluated unless an explicit
   owner acceptance artifact is supplied and read; even then publication remains
   out of scope. Report content readiness separately from publication. A prepared
   draft can request human/owner validation; it cannot label the issue resolved.
6. Keep every report section on blocked cases, with no fabricated PR content.
   pr_status complete means a locally prepared proposal, not a published PR.
   No writes/state, downstream invocation, test rerun, or network action.
