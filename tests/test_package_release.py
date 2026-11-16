"""Real Git snapshots and hostile candidate archives; no publication or model."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_release as RELEASE


class CandidatePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'plugin'
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.commit()
        self.ref = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'synthetic candidate snapshot')

    def candidate(self, name='candidate'):
        output = self.base / name
        result = RELEASE.package(self.repo, self.ref, output)
        return output, result

    def test_same_commit_produces_identical_private_candidate_bytes(self):
        first, result = self.candidate('first')
        second, other = self.candidate('second')
        self.assertEqual(result, other)
        for path in first.iterdir():
            self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(first.stat().st_mode & 0o777, 0o700)
        self.assertFalse(result['stable_ready'])
        self.assertFalse(result['publication_ready'])
        self.assertEqual(result['stable_gates']['real_pilot'], 'not_established_by_package')
        self.assertEqual(self.git('status', '--porcelain').strip(), '')
        with tarfile.open(first / result['archive'], 'r:gz') as archive:
            self.assertTrue(all('.git' not in Path(member.name).parts for member in archive))

    def test_mutable_ref_shortcut_and_old_head_are_rejected(self):
        for ref in ('HEAD', 'master'):
            with self.subTest(ref=ref), self.assertRaisesRegex(ValueError, 'full commit SHA'):
                RELEASE.package(self.repo, ref, self.base / 'out')
        (self.repo / 'README.md').write_text((self.repo / 'README.md').read_text() + '\nfixture\n')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'checked-out HEAD'):
            RELEASE.package(self.repo, self.ref, self.base / 'out')

    def test_explicit_existing_tag_resolves_without_creating_release(self):
        self.git('tag', 'candidate-fixture')
        result = RELEASE.package(self.repo, 'refs/tags/candidate-fixture', self.base / 'out')
        self.assertEqual(result['commit'], self.ref)
        self.assertEqual(self.git('tag').strip(), 'candidate-fixture')
        self.assertEqual(result['remote_actions'], 'none')

    def test_git_replacement_refs_cannot_change_selected_commit_contents(self):
        original = (self.repo / 'README.md').read_bytes()
        blob = self.git('rev-parse', 'HEAD:README.md').strip()
        replacement = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'],
                                              cwd=self.repo, input=b'replaced content\n').decode().strip()
        self.git('replace', blob, replacement)
        output, result = self.candidate()
        with tarfile.open(output / result['archive'], 'r:gz') as archive:
            entry = next(member for member in archive if member.name.endswith('/README.md'))
            self.assertEqual(archive.extractfile(entry).read(), original)

    def test_dirty_and_untracked_files_block_without_copying_them(self):
        path = self.repo / 'README.md'
        original = path.read_bytes()
        path.write_bytes(original + b'\nlocal change\n')
        with self.assertRaisesRegex(ValueError, 'clean'):
            RELEASE.package(self.repo, self.ref, self.base / 'out')
        path.write_bytes(original)
        (self.repo / '.env.private').write_text('SENSITIVE_SENTINEL')
        with self.assertRaisesRegex(ValueError, 'clean') as caught:
            RELEASE.package(self.repo, self.ref, self.base / 'out')
        self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))
        self.assertFalse((self.base / 'out').exists())

    def test_tracked_credentials_and_symlinks_are_rejected(self):
        secret = self.repo / '.env.private'
        secret.write_text('SENSITIVE_SENTINEL')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'Private/credential'):
            RELEASE.package(self.repo, self.git('rev-parse', 'HEAD').strip(), self.base / 'out')
        secret.unlink()
        outside = self.base / 'outside'
        outside.write_text('owner data')
        (self.repo / 'link').symlink_to(outside)
        self.commit()
        with self.assertRaisesRegex(ValueError, 'regular committed'):
            RELEASE.package(self.repo, self.git('rev-parse', 'HEAD').strip(), self.base / 'out')
        self.assertEqual(outside.read_text(), 'owner data')

    def test_existing_and_internal_output_are_not_overwritten(self):
        output, _ = self.candidate()
        before = {path.name: path.read_bytes() for path in output.iterdir()}
        with self.assertRaises(FileExistsError):
            RELEASE.package(self.repo, self.ref, output)
        with self.assertRaisesRegex(ValueError, 'outside'):
            RELEASE.package(self.repo, self.ref, self.repo / 'out')
        self.assertEqual(before, {path.name: path.read_bytes() for path in output.iterdir()})

    def test_archive_and_content_hash_tampering_are_detected(self):
        output, result = self.candidate()
        archive = output / result['archive']
        original = archive.read_bytes()
        archive.write_bytes(original + b'tampered')
        with self.assertRaisesRegex(ValueError, 'archive hash'):
            RELEASE.verify(output)
        archive.write_bytes(original)
        metadata = json.loads((output / 'candidate.json').read_text())
        metadata['files']['README.md']['sha256'] = '0' * 64
        (output / 'candidate.json').write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, 'hash manifest'):
            RELEASE.verify(output)

    def test_claimed_stable_or_owner_approval_is_rejected(self):
        output, _ = self.candidate()
        path = output / 'candidate.json'
        original = path.read_text()
        metadata = json.loads(original)
        metadata['stable_ready'] = True
        path.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, 'stable/publication'):
            RELEASE.verify(output)
        metadata = json.loads(original)
        metadata['stable_gates']['owner_release_approval'] = 'approved'
        path.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, 'stable gate'):
            RELEASE.verify(output)

    def test_archive_traversal_is_rejected_without_extracting(self):
        output, result = self.candidate()
        metadata_path = output / 'candidate.json'
        metadata = json.loads(metadata_path.read_text())
        archive = output / result['archive']
        with tarfile.open(archive, 'w:gz') as tar:
            entry = tarfile.TarInfo(metadata['prefix'] + '../outside')
            entry.size = 3
            tar.addfile(entry, io.BytesIO(b'bad'))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        metadata['archive_sha256'] = digest
        metadata_path.write_text(json.dumps(metadata))
        (output / 'SHA256SUMS').write_text(digest + '  ' + archive.name + '\n')
        with self.assertRaisesRegex(ValueError, 'Private/credential'):
            RELEASE.verify(output)
        self.assertFalse((self.base / 'outside').exists())

    def test_duplicate_json_and_decompressed_stream_bounds(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            RELEASE.unique_json('{"kind":"candidate","kind":"stable"}')
        with patch.object(RELEASE, 'MAX_BYTES', 8), patch.object(RELEASE, 'MAX_FILES', 1):
            reader = RELEASE.BoundedArchiveReader(io.BytesIO(b'x' * 20000))
            with self.assertRaisesRegex(ValueError, 'decompressed'):
                reader.read()


if __name__ == '__main__':
    unittest.main()
