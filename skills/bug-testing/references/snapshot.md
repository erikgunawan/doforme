# Content binding for downstream review

HEAD alone does not identify an uncommitted fix. A complete test report intended
for review must bind every material source/test/requirement and local input report
path to its exact tested contents. Inline reports remain explicit inputs.

Use only the read-only command `git hash-object --no-filters -- <exact paths>`
before and after validation, with separate tool calls and no -w, stdin, filters,
shell expansion/operators or option-like paths. Read the files first. Record
one repo-relative path and its corresponding Git blob SHA-1 in output order,
plus algorithm `git_blob_sha1`. These are content identities, not attestations
of authenticity. No object is written to Git. Symlink/escaping/secret paths block.

Include all changed source/new test files, requirement snapshots, issue/spec
inputs and named local plan/fix reports used materially. Unknown/partial manifests
cannot establish downstream freshness. Verify the before and after maps match.
The reviewer recomputes the map against current content and revision. Added
unreported dirt or mismatched/missing material bindings require revalidation.
The reviewer also inspects actual assertions/behavior; hashes never prove that
the tests or requirement claims were correct.
