"""Repository setup never executes detected tooling or grants issue permissions."""
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
import init_repo as INIT
import repo_profile as PROFILE


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'target'
        self.repo.mkdir()
        self.command(['git', 'init', '-q'])
        (self.repo / 'source.py').write_text('source\n')
        self.command(['git', 'add', '.'])
        self.command(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                      'commit', '-qm', 'synthetic baseline'])
        self.issue = {'issue_ref': 'BUG-1', 'issue_text': 'Synthetic bug', 'edit_paths': ['source.py']}

    def command(self, command):
        return subprocess.run(command, cwd=self.repo, capture_output=True, text=True, check=True)

    def setup_profile(self):
        INIT.initialize(self.repo, write=True)
        return PROFILE.read_json(self.repo / PROFILE.PROFILE_PATH)

    def test_default_inspection_creates_nothing(self):
        before = self.command(['git', 'status', '--porcelain']).stdout
        report = INIT.initialize(self.repo)
        self.assertEqual(report['status'], 'inspection_only')
        self.assertEqual(report['created_paths'], [])
        self.assertFalse((self.repo / '.doforme').exists())
        self.assertEqual(self.command(['git', 'status', '--porcelain']).stdout, before)

    def test_detected_package_script_is_never_executed_or_approved(self):
        (self.repo / 'package.json').write_text(json.dumps({'scripts': {'test': 'touch UNAUTHORIZED_MARKER'}}))
        report = INIT.initialize(self.repo, write=True)
        self.assertIn('test', report['declared_package_scripts'])
        self.assertFalse((self.repo / 'UNAUTHORIZED_MARKER').exists())
        self.assertEqual(PROFILE.read_json(self.repo / PROFILE.PROFILE_PATH)['test_commands'], [])
        self.assertFalse(report['ready_for_fix'])

    def test_write_creates_only_two_unconfirmed_draft_files(self):
        report = INIT.initialize(self.repo, write=True)
        self.assertEqual(set(report['created_paths']), {PROFILE.PROFILE_PATH, PROFILE.REQUIREMENTS_PATH})
        self.assertTrue(report['requirements_template_exists'])
        self.assertEqual(report['status'], 'draft_created')
        self.assertEqual({path.name for path in (self.repo / '.doforme').iterdir()}, {'repository.json', 'requirements.md'})
        profile = PROFILE.read_json(self.repo / PROFILE.PROFILE_PATH)
        self.assertNotIn('edit_paths', profile)
        self.assertNotIn('issue_ref', profile)
        self.assertIn('UNCONFIRMED', (self.repo / PROFILE.REQUIREMENTS_PATH).read_text())
        self.assertEqual((self.repo / 'source.py').read_text(), 'source\n')

    def test_repeated_write_preserves_owner_changes(self):
        profile = self.setup_profile()
        profile['test_commands'] = ['python3 -m unittest']
        path = self.repo / PROFILE.PROFILE_PATH
        path.write_text(json.dumps(profile))
        before = path.read_bytes()
        report = INIT.initialize(self.repo, write=True)
        self.assertEqual(report['status'], 'already_initialized')
        self.assertEqual(report['created_paths'], [])
        self.assertEqual(path.read_bytes(), before)

    def test_partial_existing_setup_is_not_overwritten(self):
        folder = self.repo / '.doforme'
        folder.mkdir()
        path = folder / 'repository.json'
        path.write_text('{"owner_data":"leave unchanged"}')
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'left unchanged'):
            INIT.initialize(self.repo, write=True)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((folder / 'requirements.md').exists())

    def test_creation_failure_discloses_retained_partial_files(self):
        original = os.open
        def fail_second(path, *args, **kwargs):
            if Path(path).name == 'requirements.md':
                raise OSError('synthetic creation failure')
            return original(path, *args, **kwargs)
        with patch.object(INIT.os, 'open', fail_second), self.assertRaisesRegex(ValueError, 'repository.json'):
            INIT.initialize(self.repo, write=True)
        self.assertTrue((self.repo / PROFILE.PROFILE_PATH).is_file())

    def test_symlink_setup_cannot_write_outside_repo(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.repo / '.doforme').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            INIT.initialize(self.repo, write=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_init_does_not_expand_subdirectory_scope_to_parent(self):
        sub = self.repo / 'sub'
        sub.mkdir()
        with self.assertRaisesRegex(ValueError, 'Git repository root'):
            INIT.initialize(sub, write=True)
        self.assertFalse((self.repo / '.doforme').exists())

    def test_init_never_creates_a_git_repo(self):
        directory = self.base / 'not-git'
        directory.mkdir()
        with self.assertRaisesRegex(ValueError, 'Git repository root'):
            INIT.initialize(directory, write=True)
        self.assertEqual(list(directory.iterdir()), [])

    def test_empty_git_repo_can_get_drafts_without_fake_revision(self):
        directory = self.base / 'empty'
        directory.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=directory, check=True)
        report = INIT.initialize(directory, write=True)
        self.assertEqual(report['revision'], 'unknown')
        self.assertFalse(report['ready_for_fix'])

    def test_profile_cannot_contain_issue_scope_or_authorization(self):
        profile = self.setup_profile()
        for name in ('edit_paths', 'issue_ref', 'allow_fix'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'profile field'):
                PROFILE.compose(self.repo, {**profile, name: []}, self.issue)

    def test_profile_requirements_cannot_be_omitted_by_issue(self):
        profile = self.setup_profile()
        config = PROFILE.compose(self.repo, profile, {**self.issue, 'requirements': []})
        self.assertEqual(config['requirements'], [PROFILE.REQUIREMENTS_PATH])

    def test_issue_cannot_edit_requirement_from_profile(self):
        profile = self.setup_profile()
        with self.assertRaisesRegex(ValueError, 'read-only'):
            PROFILE.compose(self.repo, profile, {**self.issue, 'edit_paths': ['./' + PROFILE.REQUIREMENTS_PATH]})

    def test_issue_uses_defaults_but_can_choose_exact_test_command(self):
        profile = self.setup_profile()
        profile['test_commands'] = ['python3 -m unittest']
        self.assertEqual(PROFILE.compose(self.repo, profile, self.issue)['test_commands'], profile['test_commands'])
        issue = {**self.issue, 'test_commands': ['python3 -m unittest -v tests.test_one']}
        self.assertEqual(PROFILE.compose(self.repo, profile, issue)['test_commands'], issue['test_commands'])

    def test_issue_may_lower_but_not_raise_profile_caps(self):
        profile = self.setup_profile()
        for name, cap in PROFILE.LIMITS.items():
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'increase repository limit'):
                PROFILE.compose(self.repo, profile, {**self.issue, name: cap * 2})
        self.assertEqual(PROFILE.compose(self.repo, profile, {**self.issue, 'max_budget_usd': .5})['max_budget_usd'], .5)

    def test_profile_version_is_explicit_and_strict(self):
        profile = self.setup_profile()
        for value in (True, 1.0, 2, '1'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'version'):
                PROFILE.compose(self.repo, {**profile, 'profile_version': value}, self.issue)

    def test_loading_profile_is_explicit_and_relative_to_repo(self):
        self.setup_profile()
        issue = self.base / 'issue.json'
        issue.write_text(json.dumps(self.issue))
        self.assertEqual(PROFILE.load(self.repo, issue), self.issue)
        loaded = PROFILE.load(self.repo, issue, PROFILE.PROFILE_PATH)
        self.assertEqual(loaded['requirements'], [PROFILE.REQUIREMENTS_PATH])

    def test_active_profile_cannot_be_an_edit_target(self):
        self.setup_profile()
        issue = self.base / 'issue.json'
        issue.write_text(json.dumps({**self.issue, 'edit_paths': [PROFILE.PROFILE_PATH]}))
        with self.assertRaisesRegex(ValueError, 'Active profile'):
            PROFILE.load(self.repo, issue, PROFILE.PROFILE_PATH)

    def test_inspect_effective_config_cli_does_not_start_workflow(self):
        self.setup_profile()
        issue = self.base / 'issue.json'
        issue.write_text(json.dumps(self.issue))
        before = self.command(['git', 'status', '--porcelain']).stdout
        command = [sys.executable, str(ROOT / 'scripts/run_workflow.py'), '--repo', str(self.repo),
                   '--input', str(issue), '--profile', PROFILE.PROFILE_PATH, '--inspect-config']
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        effective = json.loads(result.stdout)
        self.assertEqual(effective['edit_paths'], ['source.py'])
        self.assertEqual(effective['test_commands'], [])
        self.assertEqual(self.command(['git', 'status', '--porcelain']).stdout, before)

    def test_duplicate_json_key_is_rejected(self):
        path = self.base / 'issue.json'
        path.write_text('{"issue_ref":"one","issue_ref":"two"}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            PROFILE.read_json(path)


if __name__ == '__main__':
    unittest.main()
