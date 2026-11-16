"""Strict observation checks for slash-command acceptance; no real model calls."""
import json
import shlex
import unittest
import runtime_endtoend as R


class SlashAcceptanceTests(unittest.TestCase):
    def test_permission_quote_variants_preserve_all_named_paths(self):
        command = ['python3', '/plugin/run_workflow.py', '--repo', '/tmp/repo', '--input', '/tmp/issue.json',
                   '--profile', '.doforme/repository.json', '--output', '/tmp/output']
        for spelling in R.utility_spellings(command):
            self.assertEqual(shlex.split(spelling), command)

    def test_progress_and_terminal_summary_are_distinguished(self):
        summary = {'status': 'complete', 'stages': {'analyze': 'complete'}}
        text = json.dumps({'stage': 'analyze', 'status': 'complete'}) + '\n' + json.dumps(summary)
        self.assertEqual(R.decode_output(text), summary)
        self.assertEqual(R.decode_output('Exit code 1\n' + json.dumps({'status': 'blocked', 'stages': {}}))['status'], 'blocked')

    def test_final_model_prose_cannot_substitute_for_helper_output(self):
        with self.assertRaises(ValueError):
            R.observed_summary([{'type': 'result', 'is_error': False, 'result': 'complete'}], ['python3'], [])

    def test_unexpected_progress_and_trailing_prose_are_rejected(self):
        for text in ('{"message":"fine"}\n{"status":"complete","stages":{}}',
                     '{"status":"complete","stages":{}} all done'):
            with self.assertRaises(ValueError):
                R.decode_output(text)

    def test_exact_argv_helper_and_expected_blocked_exit_can_be_observed(self):
        command = ['python3', '/plugin/run_workflow.py', '--repo', '/tmp/repo']
        rows = [{'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'id': 'call',
                                         'input': {'command': shlex.join(command)}}]}},
                {'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'call', 'is_error': True,
                                         'content': 'Exit code 1\n{"status":"blocked","stages":{}}'}]}},
                {'type': 'result', 'is_error': False, 'permission_denials': []}]
        self.assertEqual(R.observed_summary(rows, command, [])['status'], 'blocked')
        rows[-1]['permission_denials'] = [{'tool_name': 'Bash'}]
        with self.assertRaises(ValueError):
            R.observed_summary(rows, command, [])


if __name__ == '__main__':
    unittest.main()
