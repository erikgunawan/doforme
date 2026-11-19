# Explicit business-acceptance evidence

A complete workflow, passing tests, and a passing review are technical evidence,
not business-owner approval. This utility checks a separate human-decision artifact
and binds it to the content actually tested. It does not change checkpoints,
close issues, publish PRs, or grant execution permission.

## 1. Prepare the workflow and reviewed AC list

Use a complete, fresh checkpoint with a passing review. All reports, inputs, and
test evidence must still pass runner integrity checks. After source, requirement,
revision, or policy changes, old acceptance must not be reused.

Prepare a criteria JSON file at an explicitly selected location. This is a
synthetic example; statement must exactly quote a workflow requirement source:

```json
{
  "contract_version": 1,
  "criteria": [
    {
      "id": "AC1",
      "statement": "Expected first result.",
      "source_path": ".doforme/requirements.md",
      "confirmation_reference": "Reference to the owner's decision that this AC applies to the issue"
    }
  ]
}
```

Include exactly all canonical AC IDs such as AC1/AC2 cited in plan/test/review
reports. A supported source locator is exactly one single-line definition
`AC1: complete statement` (optionally `- AC1: ...` or `* AC1: ...`). The statement
field must exactly match the text after the colon for **the same ID entry**, not
text elsewhere in the file. AC2's statement therefore cannot be paired with AC1.
Duplicate entries, tables, bold labels, multiline definitions, or ambiguous layouts
are rejected rather than guessed. Separate subsequent narrative with a blank line;
another AC definition may immediately follow. Supply an owner-reviewed single-line
text export if the original format is unsupported; do not silently simplify business conditions.

Duplicate, missing, or new IDs are rejected. The source must be one of the workflow's
requirement inputs. This check cannot establish that reports/manifests cover every
business requirement outside the declared scope.

## 2. Obtain the human-decision binding

```bash
python3 -B /absolute/doforme/scripts/business_acceptance.py --repo /absolute/target --workflow /absolute/run --criteria /absolute/criteria.json
```

Without --attestation, business_acceptance is always not_evaluated. Output provides
a binding_digest covering repository root, HEAD, the complete worktree manifest,
effective config, plugin policy, workflow results/validation evidence, and AC
manifest. The helper writes no files. To save output, explicitly redirect it from
your shell to a report location you selected.

## 3. The owner prepares decision and UAT evidence

This artifact defines a format, not AI-generated approval. Supply actual identity,
role, provenance, a timezone-aware timestamp, per-AC decisions, and references to
local evidence the owner actually provided:

```json
{
  "contract_version": 1,
  "binding_digest": "COPY_EXACT_BINDING_DIGEST",
  "owner": {
    "name": "Decision maker identity",
    "role": "Decision maker business role",
    "authority_reference": "Reference to the owner's mandate for this scope"
  },
  "recorded_at": "2026-11-16T09:00:00+07:00",
  "decision_reference": "Reference to the decision artifact actually supplied",
  "evidence_files": [
    {
      "id": "U1",
      "path": "/absolute/uat-notes.txt",
      "sha256": "COPY_ACTUAL_SHA256_OF_SUPPLIED_FILE"
    }
  ],
  "criteria": [
    {
      "id": "AC1",
      "decision": "accepted",
      "reason": "Explanation of the owner's inspection for AC1 conditions",
      "evidence_refs": ["U1"]
    }
  ]
}
```

accepted/rejected require at least one reference to a nonempty evidence file with
a matching hash. pending may have no evidence. Every AC still needs an explicit
decision. A URL alone does not replace readable UAT content; evidence files are
limited to 5 MB, JSON/AC source inputs to 1 MB, and symlinks/special files are
rejected. Evidence content/provenance remains supplied evidence, not automatically
authenticated merely because hashes match.

## 4. Validate without changing the workflow

```bash
python3 -B /absolute/doforme/scripts/business_acceptance.py --repo /absolute/target --workflow /absolute/run --criteria /absolute/criteria.json --attestation /absolute/owner-decision.json
```

| Result | Meaning |
| --- | --- |
| not_evaluated | No human artifact was supplied |
| attested_accepted | The artifact claims acceptance of every AC for this binding |
| attested_rejected | At least one AC is rejected in a valid artifact |
| attested_pending | No rejection, but at least one pending AC |
| Error/nonzero | Stale binding, integrity problems, incorrect coverage, unknown fields, missing provenance, or mismatched evidence |

Exit 0 means the artifact's structure/binding is valid, **not** that every AC was
accepted: valid rejected and pending decisions also return 0. Consumers must read
business_acceptance and decision_by_ac rather than relying on exit code alone.

owner_identity_verification and owner_authority_verification remain not_verified.
This utility provides no owner login, digital signatures, organizational mandate
checks, Jira/Docs/Figma authentication, or semantic UAT assessment. A party controlling
both repository and artifacts can fabricate both; hashes detect differences from
the recorded binding, not forgery by someone changing all sources together.

Output is a separate evidence sidecar. The existing runner summary keeps
business_acceptance not_evaluated; the utility does not rewrite technical history.
resolution_status remains not_established and publication_ready false. Publication
approval, an actual resolution decision, and remote actions require separate
policy/authorization. Availability of this validator does not claim real business acceptance.

## Pre-commit boundary

This phase's validator applies only while **both** HEAD and content match the
tested checkpoint, including baseline HEAD plus a worktree patch. Obtain the
binding and validate human decisions before committing/pushing that patch. Even
a byte-identical commit changes HEAD and makes the validator reject the checkpoint
as stale. This is intentional; do not edit revisions/reports or remove gates to
reuse an old artifact.

The publishing adapter has a separate byte-identical commit handoff, but it only
verifies PR-proposal content. It does not migrate or reapprove this phase's human
acceptance. After commit, reusing acceptance requires a new validation/decision
mechanism unsupported by this validator; do not claim new business acceptance
based on a PR draft.

## Testing

Tests use synthetic Git/checkpoints/artifacts, not real owner decisions. They cover
HEAD/content/report binding, association with the same source AC entry (including
swapped-statement rejection), ambiguous/multiline layouts, AC coverage, evidence
hashes, accepted/rejected/pending separation, rejection of false trust fields,
and CLI inspection without target/checkpoint changes. Tests call no model and
send no owner messages.
