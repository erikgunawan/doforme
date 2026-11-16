# Reproducible release candidates — stable release remains gated

The packager creates and verifies an explicit **candidate**, not a stable 1.0
release. It creates no Git tag, GitHub release, push, PR or external publication.
The owner still chooses the distribution license and release decision. Candidate
verification cannot establish real pilot/business approval, live integration
readiness or operating-system isolation.

## Build from a clean selected commit

```bash
cd /absolute/path/to/doforme
python3 -B scripts/package_release.py --ref "$(git rev-parse HEAD)" --output /absolute/new-candidate
```

The ref must be the full checked-out commit SHA or an existing `refs/tags/name`
that resolves to that same HEAD. Mutable `HEAD`/branch shortcuts, a selected old
revision, tracked dirt and ordinary untracked files block packaging. The script
does not commit/stash/reset the checkout or create/rewrite tags. Ignored files
such as Python caches are not read because only Git tree blobs are packaged.

Output must be a new directory outside the checkout. It is created private
(directory 700, files 600) and contains:

- A `doforme-VERSION-COMMIT-candidate.tar.gz` archive.
- `candidate.json`: selected commit/version, every file's SHA-256/size/mode,
  archive digest and explicit outstanding stable-release gates.
- `SHA256SUMS`: archive checksum for transport/integrity checks.

Packaging reads committed Git blobs directly, disables Git replacement objects,
and does not copy the working tree or run source/test/package code. No checkout
filters, archive export substitutions or untracked files are used. File ordering,
UID/GID, names, gzip timestamp and archive metadata are deterministic; file mtime
comes from the selected commit. Byte-for-byte reproducibility is tested in the
same Python/zlib environment, not promised across every compression implementation.

Regular files only are accepted. Symlinks, submodules, Git metadata, credential
paths, private evidence/artifact paths and raw trace/log filenames are rejected.
The candidate is bounded to 20,000 files/100 MB of source. Path filtering is not
a complete content secret scanner: a credential committed under an innocent
filename can still require owner review before sharing an artifact.

The current trusted plugin structural checker validates the selected snapshot in
a disposable extraction directory. It reads manifest/resources/contracts without
executing Python from the archive. Missing resources, unsafe paths or malformed
plugin structure block verification. A concurrent HEAD/checkout change stops
packaging rather than claiming a clean release; newly created partial output is
retained for inspection, never silently overwritten or deleted.

## Verify an existing candidate

```bash
python3 -B scripts/package_release.py --verify /absolute/existing-candidate
```

Verification checks archive identity/hash, checksum file, all member hashes/modes,
source-manifest version, bounded decompression, no duplicate/traversing/symlink
members and the local structural contract. It creates only a temporary bounded
inspection directory and does not modify the supplied candidate/source checkout.
Modified metadata cannot label this format stable_ready or publication_ready.

Checksums detect mismatch/corruption relative to the supplied manifest; they are
not a signature or proof of authorship if an attacker can replace archive and
manifest together. Verify the selected commit and provenance through a trusted
channel before distributing or executing a received package.

## Stable release gates remain explicit

Every package result reports stable_ready false and publication_ready false.
The source may contain an owner-selected LICENSE file; this establishes presence,
not authenticated approval or a legal conclusion. The packager does not invent
owner approval, real pilot evidence, live integration validation or OS isolation.
It has no stable-publishing mode and never assigns a license automatically.

A stable release needs separate reviewed evidence and owner decisions for these
conditions. Until then, successfully verified artifacts are useful local test
candidates; they are not a claim that all roadmap phases or v1.0 readiness passed.

## Verification scope

Eleven offline tests used real disposable Git repositories and candidate archives.
They verified reproducible bytes/private modes, exact commit/tag selection,
unchanged checkout, rejection of dirty/untracked/credential/symlink inputs,
protection against Git replacement refs, archive/content-hash tampering, archive
traversal, duplicate metadata, decompression bounds and unsupported stable/owner
approval claims. No real release/tag/publication or owner-license decision was made.
