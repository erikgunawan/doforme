"""Test the acceptance harness audit; synthetic traces are not live evidence."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

import runtime_utilities as RUNTIME


class RuntimeAuditTests(unittest.TestCase):
    def setUp(self):
        self.command = ['python3', '/plugin/scripts/init_repo.py', '--repo', '/tmp/fixture with spaces']
        self.report = {'status': 'inspection_only', 'created_paths': []}

    def rows(self, *, command=None, report=None, error=False):
        return [{'type': 'assistant', 'message': {'content': [
                    {'type': 'tool_use', 'name': 'Bash', 'id': 'helper',
                     'input': {'command': shlex.join(command or self.command)}}]}},
                {'type': 'user', 'message': {'content': [
                    {'type': 'tool_result', 'tool_use_id': 'helper', 'is_error': error,
                     'content': ('Exit code 1\n' if error else '') + json.dumps(report or self.report)}]}},
                {'type': 'result', 'is_error': False, 'permission_denials': []}]

    def test_observed_helper_result_accepts_quoted_paths(self):
        self.assertEqual(RUNTIME.helper_result(self.rows(), self.command), self.report)

    def test_expected_blocked_doctor_exit_is_not_model_failure(self):
        report = {'local_preflight': 'blocked'}
        self.assertEqual(RUNTIME.helper_result(self.rows(report=report, error=True), self.command), report)

    def test_no_trace_or_model_claim_alone_cannot_pass(self):
        with self.assertRaises(ValueError):
            RUNTIME.helper_result([{'type': 'result', 'is_error': False, 'result': 'all passed'}], self.command)

    def test_denial_or_error_in_final_result_stops(self):
        for field, value in (('permission_denials', [{'tool_name': 'Bash'}]), ('is_error', True)):
            rows = self.rows()
            rows[-1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                RUNTIME.helper_result(rows, self.command)

    def test_rewritten_helper_or_extra_python_option_stops(self):
        for command in (['python3', '-I', *self.command[1:]],
                        ['python3', '/plugin/skills/../scripts/init_repo.py', *self.command[2:]],
                        [*self.command, '--write']):
            with self.subTest(command=command), self.assertRaisesRegex(ValueError, 'Unexpected helper'):
                RUNTIME.helper_result(self.rows(command=command), self.command)

    def test_extra_tool_or_duplicate_helper_stops(self):
        for block in ({'type': 'tool_use', 'name': 'Edit'}, self.rows()[0]['message']['content'][0]):
            rows = self.rows()
            rows[0]['message']['content'].append(block)
            with self.assertRaises(ValueError):
                RUNTIME.helper_result(rows, self.command)

    def test_tool_error_cannot_disguise_success(self):
        with self.assertRaisesRegex(ValueError, 'exit status'):
            RUNTIME.helper_result(self.rows(error=True), self.command)

    def test_dry_run_creates_nothing_and_calls_no_model(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'new-output'
            result = subprocess.run([sys.executable, '-B', str(Path(RUNTIME.__file__)), '--output', str(output)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['model_calls'], 0)
            self.assertFalse(output.exists())

    def test_existing_and_plugin_outputs_are_never_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            for path in (Path(temp), RUNTIME.ROOT / 'acceptance-output'):
                with self.subTest(path=path), self.assertRaises((ValueError, FileExistsError)):
                    RUNTIME.run_live(path)


if __name__ == '__main__':
    unittest.main()
