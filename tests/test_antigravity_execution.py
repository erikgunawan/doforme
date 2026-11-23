"""Actual local commands plus synthetic stream fixtures; not model quality evidence."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import antigravity_runtime as A
import antigravity_commands as C
import build_antigravity as B
import run_workflow as W
import test_workflow as F


class NativeExecutionTests(unittest.TestCase):
    def setUp(self):
        F.WorkflowTests.setUp(self)
        (self.repo / 'source.py').write_text('def total(values):\n    return len(values) - 1\n')
        (self.repo / 'test_check.py').write_text('import unittest\nfrom source import total\nclass Checks(unittest.TestCase):\n    def test_count(self):\n        self.assertEqual(total([]), 0)\n        self.assertEqual(total([1,2]), 2)\n')
        self.config = W.config_checked(self.repo, {**self.config, 'edit_paths': ['source.py', 'test_check.py'],
            'test_commands': ['python3 -B -m unittest test_check.py'], 'timeout_seconds': 10})
        self.receipts = self.base / 'receipts'; self.receipts.mkdir(mode=0o700)
        self.policy = {'repo': str(self.repo), 'skills': str(W.PLUGIN / 'skills'), 'stage': 'fix',
                       'config': self.config, 'commands': C.commands_for('fix', self.config),
                       'receipts': str(self.receipts)}
        self.index = len(self.policy['commands']) - 1

    def test_broker_observes_real_red_then_green_exit_status(self):
        red = C.execute(self.policy, self.index)
        self.assertEqual(red['exit_code'], 1)
        self.assertIn('AssertionError', red['output'])
        (self.repo / 'source.py').write_text('def total(values):\n    return len(values)\n')
        green = C.execute(self.policy, self.index)
        self.assertEqual(green['exit_code'], 0)
        self.assertEqual(len(list(self.receipts.glob('execution-*.json'))), 2)
        rows = [{'event': 'init', 'init': {'agent': 'doforme-fixer', 'tools': []}}]
        guards = []
        for step, record in enumerate((red, green), 1):
            params = {'command_index': self.index}
            call = A.canonical_call('mcp_doforme_validation_run', params, self.policy)
            guards.append({'step': step, 'call': call, 'decision': 'allow'})
            rows.append({'event': 'step_update', 'step_update': {'step_type': 'tool', 'state': 'DONE',
                'step_index': step, 'tool_name': 'mcp_doforme_validation_run', 'tool_info': {
                    'name': 'mcp_doforme_validation_run', 'parameters': params,
                    'output': 'doforme-command-receipt:' + record['receipt_id']}}})
        rows.append({'event': 'result', 'result': {'status': 'SUCCESS'}})
        header = {k:v for k,v in self.policy.items() if k != 'receipts'}
        trace = [{'antigravity_raw': rows, 'guard_receipts': guards, 'execution_receipts': [red, green],
                  'policy': header}, *A.normalize(rows, header, [red, green])]
        A.check_normalized_trace(trace, 'fix', self.config, self.repo)
        evidence = W.validation_checked(trace, 'fix', self.config)
        self.assertTrue(evidence[0]['assertion_failure'])
        self.assertTrue(evidence[-1]['success'])
        changed = copy.deepcopy(trace); changed[0]['execution_receipts'] = [green]
        with self.assertRaises(ValueError):
            A.check_normalized_trace(changed, 'fix', self.config, self.repo)

    def test_invalid_indexes_and_expanded_command_table_execute_nothing(self):
        for index in (-1, True, 999, '5'):
            with self.subTest(index=index), self.assertRaises(ValueError):
                C.execute(self.policy, index)
        changed = copy.deepcopy(self.policy); changed['commands'].append('git push')
        with self.assertRaises(ValueError):
            C.execute(changed, 0)
        self.assertFalse(list(self.receipts.glob('execution-*.json')))
        (self.receipts / 'denied').touch()
        with self.assertRaisesRegex(ValueError, 'denial'):
            C.execute(self.policy, self.index)
        self.assertFalse(list(self.receipts.glob('execution-*.json')))

    def test_test_review_and_pr_cannot_edit_or_run_unapproved_tests(self):
        for stage in ('test', 'review', 'pr', 'analyze', 'plan'):
            policy = {**self.policy, 'stage': stage, 'commands': C.commands_for(stage, self.config)}
            with self.subTest(stage=stage), self.assertRaises(ValueError):
                A.guard_call('write_to_file', {'TargetFile': str(self.repo / 'source.py')}, self.repo, W.PLUGIN / 'skills', policy)
            if stage != 'test':
                self.assertNotIn(self.config['test_commands'][0], policy['commands'])
                with self.assertRaises(ValueError):
                    A.guard_call('mcp_doforme_validation_run', {'command_index': len(policy['commands'])}, self.repo, W.PLUGIN / 'skills', policy)

    def test_fixer_can_only_write_exact_approved_paths(self):
        A.guard_call('write_to_file', {'TargetFile': str(self.repo / 'source.py')}, self.repo, W.PLUGIN / 'skills', self.policy)
        for path in (self.repo / 'requirements.md', self.repo / '.env', self.base / 'outside.py', self.repo / 'unapproved.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                A.guard_call('write_to_file', {'TargetFile': str(path)}, self.repo, W.PLUGIN / 'skills', self.policy)
        with self.assertRaises(ValueError):
            A.guard_call('run_command', {'CommandLine': 'python3 -B -m unittest test_check.py'}, self.repo, W.PLUGIN / 'skills', self.policy)

    def test_no_provider_or_guard_secrets_are_inherited_by_test_program(self):
        from execution_runtime import ExecutionResult
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'not-a-real-key', 'DOFORME_AGY_GUARD': 'private-policy'}), \
                patch.object(C, 'run_process', return_value=ExecutionResult(0, 'OK', '', 2)) as process:
            C.execute(self.policy, self.index)
        self.assertNotIn('ANTHROPIC_API_KEY', process.call_args.kwargs['env'])
        self.assertNotIn('DOFORME_AGY_GUARD', process.call_args.kwargs['env'])

    def test_only_the_exact_non_secret_broker_schema_is_readable(self):
        schema = self.base / 'metadata.json'
        schema.write_text(json.dumps({'name': C.VALIDATION_TOOL['name'],
            'description': C.VALIDATION_TOOL['description'], 'parameters': C.VALIDATION_TOOL['inputSchema']}))
        with patch.object(A, 'broker_schema_path', return_value=schema):
            A.guard_call('read_file', {'Path': str(schema)}, self.repo, W.PLUGIN / 'skills', self.policy)
            with self.assertRaises(ValueError):
                A.guard_call('read_file', {'Path': str(self.base / 'other.json')}, self.repo, W.PLUGIN / 'skills', self.policy)
            schema.write_text('{"unexpected":"not a tool schema"}')
            with self.assertRaises(ValueError):
                A.guard_call('read_file', {'Path': str(schema)}, self.repo, W.PLUGIN / 'skills', self.policy)

    def test_readonly_trace_survives_scope_approval_but_not_requirement_change(self):
        original = {**self.config, 'edit_paths': [], 'test_commands': [], 'artifact_paths': []}
        policy = {'repo': str(self.repo), 'skills': str(W.PLUGIN / 'skills'), 'stage': 'plan',
                  'config': original, 'commands': []}
        params = {'Path': str(self.repo / 'source.py')}
        rows = [{'event': 'init', 'init': {'agent': A.AGENT, 'tools': []}},
                {'event': 'step_update', 'step_update': {'step_type': 'tool', 'state': 'DONE',
                 'step_index': 1, 'tool_name': 'read_file', 'tool_info': {'name': 'read_file', 'parameters': params, 'output': 'fixture'}}},
                {'event': 'result', 'result': {'status': 'SUCCESS'}}]
        trace = [{'antigravity_raw': rows, 'guard_receipts': [{'step': 1, 'decision': 'allow',
                    'call': A.canonical_call('read_file', params)}], 'execution_receipts': [], 'policy': policy}, *A.normalize(rows, policy)]
        A.check_normalized_trace(trace, 'plan', self.config, self.repo)
        with self.assertRaises(ValueError):
            A.check_normalized_trace(trace, 'plan', {**self.config, 'requirements': []}, self.repo)

    def test_stdio_mcp_handshake_and_no_execution_outside_worker(self):
        bundle = self.base / 'bundle'; B.build(bundle)
        requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                    {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
                    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {'command_index': self.index}}}]
        env = dict(os.environ); env.pop('DOFORME_AGY_GUARD', None)
        script = bundle / 'scripts/antigravity_validation.py'
        result = subprocess.run([sys.executable, '-B', str(script)], input='\n'.join(json.dumps(x) for x in requests)+'\n',
                                text=True, capture_output=True, env=env, check=True)
        responses = [json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual([x['id'] for x in responses], [1,2,3])
        self.assertEqual(responses[0]['result']['protocolVersion'], '2025-06-18')
        self.assertEqual(responses[1]['result']['tools'][0]['name'], 'run')
        self.assertTrue(responses[2]['result']['isError'])
        self.assertFalse(list(self.receipts.glob('execution-*.json')))
        env['DOFORME_AGY_GUARD'] = json.dumps(self.policy)
        result = subprocess.run([sys.executable, '-B', str(script)], input=json.dumps(requests[-1])+'\n',
                                text=True, capture_output=True, env=env, check=True)
        content = json.loads(result.stdout)['result']['content']
        record = json.loads(content[0]['text'])
        self.assertEqual(record['exit_code'], 1)
        self.assertIn(record['receipt_id'], content[-1]['text'])
