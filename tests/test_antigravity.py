"""Antigravity contract fixtures are synthetic, not successful model runs."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import antigravity_runtime as A
import build_antigravity as B
import run_workflow as W
import guided_workflow as G
from execution_runtime import ExecutionResult
import test_workflow as F


def events(path, result=None):
    return [{'event': 'init', 'init': {'agent': A.AGENT, 'tools': list(A.TOOLS)}},
            {'event': 'step_update', 'step_update': {'step_type': 'tool', 'state': 'DONE',
                'step_index': 1, 'tool_name': 'view_file', 'tool_info': {
                    'name': 'view_file', 'parameters': {'AbsolutePath': str(path)}, 'output': 'fixture'}}},
            {'event': 'result', 'result': {'status': 'SUCCESS', 'structured_output': result or {}}}]


def audited(rows):
    receipts = []
    for row in rows:
        step = row.get('step_update', {})
        if step.get('step_type') == 'tool' and step.get('state') == 'DONE':
            receipts.append({'step': step['step_index'], 'call': A.canonical_call(step['tool_name'], step['tool_info']['parameters']), 'decision': 'allow'})
    return [{'antigravity_raw': rows, 'guard_receipts': receipts}, *A.normalize(rows)]


class AntigravityTests(unittest.TestCase):
    setUp = F.WorkflowTests.setUp
    executor = F.WorkflowTests.executor

    def test_unknown_write_shell_message_and_delegation_tools_rejected(self):
        for name in ('run_command', 'write_to_file', 'send_message', 'invoke_subagent', 'future_tool'):
            rows = events(self.repo / 'source.py')
            rows[1]['step_update'].update(tool_name=name)
            rows[1]['step_update']['tool_info']['name'] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                A.normalize(rows)

    def test_missing_paths_errors_incomplete_and_unknown_events_fail_closed(self):
        variants = []
        rows = events('source.py'); rows[1]['step_update']['tool_info']['parameters'] = {}; variants.append(rows)
        rows = events('source.py'); rows[1]['step_update']['tool_info']['error'] = {'type': 'permission'}; variants.append(rows)
        rows = events('source.py'); rows[1]['step_update']['state'] = 'ACTIVE'; variants.append(rows)
        rows = events('source.py'); rows[1]['step_update']['subagent_info'] = {'subagents': [{}]}; variants.append(rows)
        rows = events('source.py'); rows[-1]['result']['status'] = 'ERROR'; variants.append(rows)
        rows = events('source.py'); rows.insert(1, {'event': 'future'}); variants.append(rows)
        variants += [events('source.py')[1:], events('source.py')[:-1]]
        for rows in variants:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                A.normalize(rows)

    def test_active_and_done_are_one_call_but_changed_parameters_rejected(self):
        rows = events(self.repo / 'source.py')
        active = copy.deepcopy(rows[1]); active['step_update']['state'] = 'ACTIVE'
        rows.insert(1, active)
        self.assertEqual(len(A.normalize(rows)), 1)
        rows[2]['step_update']['tool_info']['parameters']['AbsolutePath'] = '/elsewhere'
        with self.assertRaisesRegex(ValueError, 'changed'):
            A.normalize(rows)

    def test_native_reads_remain_subject_to_shared_scope_and_secret_audit(self):
        for path in ('/outside/private.txt', str(self.repo / '.env'), str(self.repo / '.git/config')):
            rows = events(path)
            with self.subTest(path=path), self.assertRaises(ValueError):
                W.audit_calls(self.repo, A.normalize(rows), 'analyze', self.config)
        rows = events(self.repo / 'source.py')
        W.audit_calls(self.repo, A.normalize(rows), 'analyze', self.config)

    def test_normalized_trace_cannot_hide_raw_call(self):
        rows = events(self.repo / 'source.py')
        trace = audited(rows)
        A.check_normalized_trace(trace)
        with self.assertRaises(ValueError):
            A.check_normalized_trace(trace[:1])

    def test_guard_rejects_mutations_secrets_escape_and_symlinks_before_execution(self):
        skills = ROOT / 'skills'
        for name, params in [('run_command', {'CommandLine': 'echo unsafe'}),
                             ('read_file', {'Path': '/outside/private.txt'}),
                             ('read_file', {'Path': str(self.repo / '.env')})]:
            with self.subTest(name=name, params=params), self.assertRaises(ValueError):
                A.guard_call(name, params, self.repo, skills)
        link = self.repo / 'link'; link.symlink_to(self.repo / 'source.py')
        with self.assertRaises(ValueError):
            A.guard_call('read_file', {'Path': str(link)}, self.repo, skills)
        A.guard_call('read_file', {'Path': str(self.repo / 'source.py')}, self.repo, skills)
        A.guard_call('view_file', {'AbsolutePath': str(skills / 'bug-resolution/SKILL.md')}, self.repo, skills)

    def test_every_tool_requires_one_matching_pre_execution_receipt(self):
        rows = events(self.repo / 'source.py')
        trace = audited(rows)
        for receipts in ([], trace[0]['guard_receipts'] * 2,
                         [{**trace[0]['guard_receipts'][0], 'decision': 'deny'}],
                         [{**trace[0]['guard_receipts'][0], 'call': {'tool': 'Read', 'field': 'file_path', 'path': '/other'}}]):
            changed = copy.deepcopy(trace); changed[0]['guard_receipts'] = receipts
            with self.subTest(receipts=receipts), self.assertRaises(ValueError):
                A.check_normalized_trace(changed)

    def test_cli_catalog_is_not_mistaken_for_effective_tool_allowlist(self):
        rows = events(self.repo / 'source.py')
        rows[0]['init']['tools'].append('run_command')
        A.check_normalized_trace(audited(rows))
        rows[1]['step_update']['tool_name'] = 'run_command'
        rows[1]['step_update']['tool_info']['name'] = 'run_command'
        with self.assertRaises(ValueError):
            A.normalize(rows)

    def test_guard_script_is_inert_outside_worker_and_records_worker_decisions(self):
        import subprocess
        bundle = self.base / 'bundle'; B.build(bundle)
        helper = bundle / 'scripts/antigravity_guard.py'
        env = dict(os.environ); env.pop('DOFORME_AGY_GUARD', None)
        plain = subprocess.run([sys.executable, '-B', str(helper)], input='', text=True,
                               capture_output=True, env=env, check=True)
        self.assertEqual(json.loads(plain.stdout)['decision'], 'allow')
        receipts = self.base / 'receipts'; receipts.mkdir()
        env['DOFORME_AGY_GUARD'] = json.dumps({'repo': str(self.repo), 'skills': str(ROOT / 'skills'), 'receipts': str(receipts)})
        for name, args, expected in [('read_file', {'Path': str(self.repo / 'source.py')}, 'allow'),
                                      ('run_command', {'CommandLine': 'echo unsafe'}, 'deny')]:
            result = subprocess.run([sys.executable, '-B', str(helper)], input=json.dumps({
                'stepIdx': 1, 'toolCall': {'name': name, 'args': args}}), text=True, capture_output=True, env=env, check=True)
            self.assertEqual(json.loads(result.stdout)['decision'], expected)
        self.assertEqual(len(list(receipts.glob('*.json'))), 2)

    def test_executor_uses_native_schema_denies_and_no_other_provider_auth(self):
        expected, _ = self.executor('analyze', self.repo, '', self.config)
        rows = events(self.repo / 'source.py', expected)
        stdout = '\n'.join(json.dumps(row) for row in rows)
        execution = ExecutionResult(0, stdout, '', len(stdout))
        def observed_process(*args, **kwargs):
            policy = json.loads(kwargs['env']['DOFORME_AGY_GUARD'])
            Path(policy['receipts'], 'observed.json').write_text(json.dumps(audited(rows)[0]['guard_receipts'][0]))
            return execution
        with patch.object(A, 'run_process', side_effect=observed_process) as process, patch.dict(
                os.environ, {'ANTHROPIC_API_KEY': 'sentinel'}):
            actual, trace = A.AntigravityExecutor()('analyze', self.repo, 'fixture',
                {**self.config, 'timeout_seconds': 30})
        self.assertEqual(actual, expected)
        A.check_normalized_trace(trace)
        argv = process.call_args.args[0]
        self.assertEqual(argv[0], 'agy')
        self.assertNotIn('--json-schema', argv)
        self.assertNotIn('--dangerously-skip-permissions', argv)
        self.assertNotIn('ANTHROPIC_API_KEY', process.call_args.kwargs['env'])
        settings = json.loads(argv[argv.index('--settings') + 1])
        self.assertIn('write_file(*)', settings['permissions']['deny'])
        self.assertIn('command(*)', settings['permissions']['deny'])
        self.assertEqual(process.call_args.kwargs['timeout_seconds'], 30)

    def test_missing_structured_output_and_non_json_output_fail(self):
        for stdout in ('not json', '\n'.join(json.dumps(row) for row in events('source.py')[:-1] + [
                {'event': 'result', 'result': {'status': 'SUCCESS', 'response': 'tests passed'}}])):
            with patch.object(A, 'run_process', return_value=ExecutionResult(0, stdout, '', len(stdout))), self.assertRaises(ValueError):
                A.AntigravityExecutor()('analyze', self.repo, '', {'timeout_seconds': 30})

    def test_version_gate_rejects_unreviewed_major_minor_and_old_versions(self):
        for version in ('1.5.13', '1.6.0', '2.0.0', 'not a version'):
            with patch.object(A, 'run_process', return_value=ExecutionResult(0, version, '', 10)), self.assertRaises(ValueError):
                A.runtime_identity()
        with patch.object(A, 'run_process', return_value=ExecutionResult(0, '1.5.14\n', '', 7)), patch.object(A, 'installation_identity', return_value='fixture'):
            self.assertEqual(A.runtime_identity()['cli_version'], '1.5.14')

    def test_pipeline_refuses_later_stages_and_grants_before_execution(self):
        for flags in ({}, {'stop_after': 'fix'}, {'stop_after': 'plan', 'allow_fix': True},
                      {'stop_after': 'analyze', 'allow_execution': True}):
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, 'read-only'):
                W.pipeline(self.repo, self.config, self.base / 'out', runtime='antigravity', executor=self.executor, **flags)
        self.assertFalse(self.calls)
        self.assertFalse((self.base / 'out').exists())

    def test_runtime_binding_and_persisted_raw_audit(self):
        def native(stage, repo, prompt, config):
            result, _ = self.executor(stage, repo, prompt, config)
            rows = events(repo / 'source.py', result)
            return result, audited(rows)
        identity = {'name': 'antigravity', 'adapter_version': 1, 'cli_version': '1.5.14'}
        out = self.base / 'out'
        with patch.object(A, 'runtime_identity', return_value=identity):
            state = W.pipeline(self.repo, self.config, out, executor=native, runtime='antigravity', stop_after='plan')
            self.assertEqual(state['status'], 'paused')
            self.assertEqual(list(state['results']), ['analyze', 'plan'])
            self.assertTrue(W.compact(state)['runtime_limit_reached'])
            self.assertTrue(W.status_checkpoint(self.repo, out)['fresh'])
            with self.assertRaisesRegex(ValueError, 'Runtime'):
                W.pipeline(self.repo, self.config, out, executor=self.executor, resume=True)
            with patch.object(A, 'runtime_identity', return_value={**identity, 'cli_version': '1.5.15'}), self.assertRaisesRegex(ValueError, 'Runtime'):
                W.pipeline(self.repo, self.config, out, executor=native, resume=True, runtime='antigravity', stop_after='plan')
        record = state['runtime_traces']['analyze']
        (out / 'history' / record['filename']).write_text('[]')
        with self.assertRaises(ValueError):
            W.status_checkpoint(self.repo, out)

    def test_plain_response_must_be_one_unambiguous_json_object(self):
        result, _ = self.executor('analyze', self.repo, '', self.config)
        rows = events(self.repo / 'source.py')
        rows[-1]['result'] = {'status': 'SUCCESS', 'response': json.dumps(result)}
        A.check_normalized_trace(audited(rows))
        W.parse_result_text(rows[-1]['result']['response'])
        with self.assertRaises(ValueError):
            W.parse_result_text(json.dumps(result) + '\n' + json.dumps(result))

    def test_installed_guard_must_match_reviewed_bytes_before_model_calls(self):
        install = self.base / 'install'; install.mkdir()
        source = self.base / 'expected.py'; source.write_text('reviewed')
        with self.assertRaises(ValueError):
            A.installation_identity(install, {'guard.py': source})
        (install / 'guard.py').write_text('reviewed')
        identity = A.installation_identity(install, {'guard.py': source})
        self.assertEqual(len(identity), 64)
        (install / 'guard.py').write_text('changed')
        with self.assertRaises(ValueError):
            A.installation_identity(install, {'guard.py': source})

    def test_guided_rejects_mutation_runtime_before_session_creation(self):
        for stage in ('fix', 'test', 'review', 'pr', 'endtoend'):
            with self.assertRaisesRegex(ValueError, 'read-only'):
                G.run(self.repo, 'BUG-1', stage, root=self.base / 'state', runtime='antigravity')
        self.assertFalse((self.base / 'state').exists())

    def test_package_hides_claude_components_and_preserves_engine(self):
        output = self.base / 'bundle'
        B.build(output)
        self.assertEqual(len(list((output / 'skills').glob('*/SKILL.md'))), 4)
        self.assertEqual([p.name for p in (output / 'agents').glob('*.md')], ['doforme-reader.md'])
        self.assertFalse((output / 'commands').exists())
        self.assertEqual((output / 'engine/scripts/run_workflow.py').read_bytes(), (ROOT / 'scripts/run_workflow.py').read_bytes())
        self.assertNotIn('CLAUDE_PLUGIN_ROOT', ''.join(p.read_text() for p in (output / 'skills').rglob('*.md')))
        with self.assertRaises(ValueError):
            B.build(output)

    def test_package_refuses_source_tree_and_symlink_outputs(self):
        with self.assertRaises(ValueError):
            B.build(ROOT / 'must-not-create')
        link = self.base / 'link'; link.symlink_to(self.base / 'missing')
        with self.assertRaises(ValueError):
            B.build(link)

    def test_explicit_stop_is_a_successful_cli_exit(self):
        with patch.object(sys, 'argv', ['run_workflow.py', '--repo', str(self.repo), '--input', 'fixture.json',
                '--output', str(self.base / 'out'), '--runtime', 'antigravity', '--stop-after', 'plan']), \
                patch('repo_profile.load', return_value=self.config), \
                patch.object(W, 'pipeline', return_value={'status': 'paused'}), \
                patch.object(W, 'compact', return_value={'status': 'paused'}), \
                patch.object(W.signal, 'signal'):
            self.assertEqual(W.main(), 0)

    def test_build_excludes_untracked_files_and_rejects_tracked_secret_paths(self):
        import shutil
        import subprocess
        source = self.base / 'source-plugin'
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        subprocess.run(['git', 'init', '-q'], cwd=source, check=True)
        subprocess.run(['git', 'add', '.'], cwd=source, check=True)
        (source / 'scripts/untracked-private.json').write_text('{"synthetic":"not a credential"}')
        with patch.object(B, 'ROOT', source):
            bundle = self.base / 'tracked-bundle'; B.build(bundle)
            self.assertFalse((bundle / 'engine/scripts/untracked-private.json').exists())
            (source / 'scripts/.env').write_text('SYNTHETIC_TEST_ONLY=not-a-secret\n')
            subprocess.run(['git', 'add', '-f', 'scripts/.env'], cwd=source, check=True)
            with self.assertRaisesRegex(ValueError, 'Protected'):
                B.build(self.base / 'secret-bundle')


if __name__ == '__main__':
    unittest.main()
