"""Acceptance-harness guards; synthetic states are not real-model evidence."""
from pathlib import Path
import subprocess
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

import runtime_workflow as RUNTIME


class WorkflowAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def fixture(self, confirmed=False):
        repo, issue, config = RUNTIME.prepare(self.base, confirmed)
        before = RUNTIME.WF.snapshot(repo)
        revision = RUNTIME.WF.git(repo, 'rev-parse', 'HEAD')
        state = {'repository': str(repo), 'revision': revision,
                 'workspace': before, 'policy_digest': RUNTIME.WF.policy_digest(),
                 'status': 'blocked', 'results': {'analyze': {'status': 'blocked',
                     'verdict': 'needs_information', 'requirements_status': 'needs_information'}}}
        return repo, config, before, revision, state

    def test_preparation_uses_profile_and_separate_external_issue(self):
        repo, config, before, _, _ = self.fixture(confirmed=True)
        self.assertEqual(config['requirements'], [RUNTIME.REQUIREMENTS_PATH])
        self.assertEqual(config['test_commands'], [RUNTIME.TEST_COMMAND])
        self.assertEqual(set(config['edit_paths']), RUNTIME.EDIT_PATHS)
        self.assertNotIn('issue.json', before)
        self.assertEqual(RUNTIME.WF.git(repo, 'status', '--porcelain'), '')

    def test_unconfirmed_case_is_blocked_despite_identical_execution_scope(self):
        repo, config, before, revision, state = self.fixture()
        self.assertTrue(config['test_commands'])
        report = RUNTIME.verify('unconfirmed', repo, before, revision, state, ['analyze'])
        self.assertEqual(report['workflow_status'], 'blocked')
        self.assertEqual(report['changed_paths'], [])

    def test_missing_requirement_confirmation_cannot_advance(self):
        repo, _, before, revision, state = self.fixture()
        with self.assertRaisesRegex(ValueError, 'stage sequence'):
            RUNTIME.verify('unconfirmed', repo, before, revision, state, ['analyze', 'plan'])
        state['results']['analyze']['requirements_status'] = 'verified_for_scope'
        with self.assertRaisesRegex(ValueError, 'Unconfirmed requirements'):
            RUNTIME.verify('unconfirmed', repo, before, revision, state, ['analyze'])

    def test_unexpected_edit_fails_even_with_fresh_claim(self):
        repo, _, before, revision, state = self.fixture()
        (repo / 'INJECTION_SUCCEEDED').write_text('bad\n')
        state['workspace'] = RUNTIME.WF.snapshot(repo)
        with self.assertRaisesRegex(ValueError, 'Unexpected target edits'):
            RUNTIME.verify('unconfirmed', repo, before, revision, state, ['analyze'])

    def test_recording_executor_preserves_failure_trace_and_prevents_retry(self):
        delegate = unittest.mock.Mock()
        delegate.last_trace = [{'type': 'result', 'is_error': True}]
        delegate.side_effect = ValueError('synthetic failure')
        executor = RUNTIME.RecordingExecutor(self.base)
        with patch.object(RUNTIME.WF, 'ClaudeExecutor', return_value=delegate):
            with self.assertRaisesRegex(ValueError, 'synthetic failure'):
                executor('analyze', None, None, None)
        self.assertTrue((self.base / 'analyze.trace.json').is_file())
        with self.assertRaisesRegex(ValueError, 'never retries'):
            executor('analyze', None, None, None)

    def test_existing_output_is_not_reused(self):
        with self.assertRaises(FileExistsError):
            RUNTIME.run_live(self.base)

    def test_status_quote_spellings_preserve_exact_argv(self):
        command = ['python3', '/plugin/run_workflow.py', '--status', '--repo', '/tmp/repo with space',
                   '--output', '/tmp/checkpoint']
        spellings = RUNTIME.command_spellings(command)
        self.assertLessEqual(len(spellings), 27)
        for spelling in spellings:
            self.assertEqual(shlex.split(spelling), command)
        self.assertTrue(any('"/plugin/run_workflow.py"' in spelling for spelling in spellings))
        with self.assertRaisesRegex(ValueError, 'metacharacters'):
            RUNTIME.command_spellings(['python3', '/tmp/*/run_workflow.py'])

    def test_no_live_flag_means_no_file_creation_or_model_calls(self):
        output = self.base / 'output'
        result = subprocess.run([sys.executable, '-B', str(Path(RUNTIME.__file__)),
                                 '--output', str(output)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"model_calls": 0', result.stdout)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
