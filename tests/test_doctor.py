"""Preflight diagnoses prerequisites, never executes them or accepts business intent."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import doctor as DOCTOR
import init_repo as INIT


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'target'
        self.repo.mkdir()
        self.git('init', '-q')
        (self.repo / 'source.py').write_text('original\n')
        (self.repo / 'requirements.md').write_text('Synthetic source text; no confirmed authority implied\n')
        (self.repo / 'test_probe.py').write_text("from pathlib import Path\nPath('UNAUTHORIZED_MARKER').touch()\n")
        self.commit()
        self.config = {'issue_ref': 'FIXTURE-1', 'issue_text': 'Synthetic bug',
                       'requirements': ['requirements.md'], 'edit_paths': ['source.py'],
                       'test_commands': ['python3 test_probe.py']}
        self.issue = self.base / 'issue.json'
        self.issue.write_text(json.dumps(self.config))
        cli = patch.object(DOCTOR.shutil, 'which', return_value='/not-executed/claude')
        cli.start()
        self.addCleanup(cli.stop)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'synthetic baseline')

    def diagnose(self, **kwargs):
        self.issue.write_text(json.dumps(self.config))
        return DOCTOR.diagnose(self.repo, self.issue, **kwargs)

    def test_pass_does_not_execute_tests_create_output_or_accept_requirements(self):
        before = DOCTOR.snapshot(self.repo)
        revision = self.git('rev-parse', 'HEAD')
        output = self.base / 'new-output'
        report = self.diagnose(output=output)
        self.assertEqual(report['local_preflight'], 'passed')
        self.assertEqual(report['requirements_status'], 'not_evaluated')
        self.assertEqual(report['business_acceptance'], 'not_evaluated')
        self.assertEqual(report['resolution_status'], 'not_established')
        self.assertEqual(report['created_paths'], [])
        self.assertEqual(report['model_calls'], 0)
        self.assertFalse(report['publication_ready'])
        self.assertFalse(output.exists())
        self.assertEqual(DOCTOR.snapshot(self.repo), before)
        self.assertEqual(self.git('rev-parse', 'HEAD'), revision)
        self.assertNotIn('Synthetic bug', json.dumps(report))

    def test_dirty_checkout_is_reported_without_repair(self):
        (self.repo / 'source.py').write_text('owner changes\n')
        before = DOCTOR.snapshot(self.repo)
        report = self.diagnose()
        self.assertIn('clean_worktree', report['blocking_checks'])
        self.assertEqual(DOCTOR.snapshot(self.repo), before)

    def test_untracked_input_in_checkout_blocks_clean_baseline(self):
        self.issue = self.repo / 'issue.json'
        self.assertIn('clean_worktree', self.diagnose()['blocking_checks'])

    def test_subdirectory_and_non_git_root_do_not_expand_or_initialize(self):
        for directory in (self.repo / 'sub', self.base / 'not-git'):
            directory.mkdir()
            report = DOCTOR.diagnose(directory, self.issue)
            self.assertIn('repository_root', report['blocking_checks'])
            self.assertIsNone(report['repository'])
            self.assertEqual(list(directory.iterdir()), [])

    def test_empty_git_repo_has_no_verified_revision(self):
        empty = self.base / 'empty'
        empty.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=empty, check=True)
        report = DOCTOR.diagnose(empty, self.issue)
        self.assertIn('revision', report['blocking_checks'])
        self.assertIsNone(report['revision'])

    def test_symlink_and_fifo_checkout_block_without_reading_special_file(self):
        path = self.repo / 'unsafe'
        path.symlink_to(self.repo / 'source.py')
        self.assertIn('bounded_checkout', self.diagnose()['blocking_checks'])
        path.unlink()
        os.mkfifo(path)
        self.assertIn('bounded_checkout', self.diagnose()['blocking_checks'])

    def test_absent_or_unsafe_configuration_stops_dependent_checks(self):
        self.config['edit_paths'] = ['../outside']
        report = self.diagnose()
        self.assertIn('configuration', report['blocking_checks'])
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id'] == 'edit_scope'), 'not_checked')
        report = DOCTOR.diagnose(self.repo, self.base / 'missing.json')
        self.assertIn('configuration', report['blocking_checks'])

    def test_missing_scope_commands_and_sources_are_distinct_blockers(self):
        for key in ('requirements', 'edit_paths', 'test_commands'):
            self.config[key] = []
        report = self.diagnose()
        self.assertTrue({'requirement_sources', 'edit_scope', 'test_commands'} <= set(report['blocking_checks']))

    def test_generated_template_blocks_until_actual_source_is_supplied(self):
        INIT.initialize(self.repo, write=True)
        self.commit()
        self.config['requirements'] = []
        report = self.diagnose(profile_path='.doforme/repository.json')
        self.assertIn('requirement_sources', report['blocking_checks'])
        self.assertIn('Unchanged generated', str(report['checks']))
        (self.repo / '.doforme/requirements.md').write_text('Supplied synthetic source excerpt\n')
        self.commit()
        report = self.diagnose(profile_path='.doforme/repository.json')
        self.assertEqual(report['local_preflight'], 'passed')
        self.assertEqual(report['requirements_status'], 'not_evaluated')

    def test_empty_binary_and_oversized_requirement_sources_block(self):
        source = self.repo / 'requirements.md'
        for content in (b'', b'\xff\xfe', b'x' * 1_000_001):
            source.write_bytes(content)
            self.commit()
            report = self.diagnose()
            self.assertIn('requirement_sources', report['blocking_checks'])

    def test_profile_cap_increase_blocks_before_workflow(self):
        INIT.initialize(self.repo, write=True)
        self.commit()
        self.config['max_turns'] = 46
        report = self.diagnose(profile_path='.doforme/repository.json')
        self.assertIn('configuration', report['blocking_checks'])

    def test_profile_is_never_loaded_implicitly(self):
        (self.repo / '.doforme').mkdir()
        (self.repo / '.doforme/repository.json').write_text('not valid JSON')
        self.commit()
        self.assertEqual(self.diagnose()['local_preflight'], 'passed')

    def test_missing_cli_is_blocker_without_auth_attempt(self):
        with patch.object(DOCTOR.shutil, 'which', return_value=None):
            self.assertIn('claude_on_path', self.diagnose()['blocking_checks'])

    def test_output_omission_is_explicitly_not_checked(self):
        report = self.diagnose()
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id'] == 'output_location'), 'not_checked')

    def test_existing_internal_ancestor_and_missing_parent_outputs_block(self):
        existing = self.base / 'existing'
        existing.mkdir()
        for path in (existing, self.repo / 'output', self.base,
                     ROOT / 'output', self.base / 'missing-parent' / 'output'):
            with self.subTest(path=path):
                self.assertIn('output_location', self.diagnose(output=path)['blocking_checks'])
        self.assertEqual(list(existing.iterdir()), [])

    def test_symlink_output_parent_is_rejected(self):
        link = self.base / 'alias'
        link.symlink_to(self.base, target_is_directory=True)
        self.assertIn('output_location', self.diagnose(output=link / 'new')['blocking_checks'])
        self.assertFalse((self.base / 'new').exists())

    def test_cli_emits_structured_pass_and_block_without_executing_fake_claude(self):
        binary = self.base / 'bin'
        binary.mkdir()
        fake = binary / 'claude'
        marker = self.base / 'CLI_WAS_EXECUTED'
        fake.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
        fake.chmod(0o700)
        env = {**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']}
        command = [sys.executable, '-B', str(ROOT / 'scripts/doctor.py'), '--repo', str(self.repo),
                   '--input', str(self.issue), '--output', str(self.base / 'output')]
        good = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['local_preflight'], 'passed')
        (self.repo / 'source.py').write_text('dirty\n')
        blocked = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(blocked.returncode, 1, blocked.stderr)
        self.assertEqual(json.loads(blocked.stdout)['local_preflight'], 'blocked')
        self.assertFalse(marker.exists())
        self.assertFalse((self.repo / 'UNAUTHORIZED_MARKER').exists())
        self.assertFalse((self.base / 'output').exists())

    def test_cli_cannot_enable_execution(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/doctor.py'),
                                 '--repo', str(self.repo), '--input', str(self.issue), '--allow-fix'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.repo / 'UNAUTHORIZED_MARKER').exists())


if __name__ == '__main__':
    unittest.main()
