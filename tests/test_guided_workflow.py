"""Guided UX uses real host gates; executors here are synthetic, never model evidence."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import guided_workflow as G
import test_workflow as fixtures


class GuidedTests(unittest.TestCase):
    executor = fixtures.WorkflowTests.executor

    def setUp(self):
        fixtures.WorkflowTests.setUp(self)
        (self.repo / 'docs/bugs').mkdir(parents=True)
        (self.repo / 'docs/bugs/BUG-301-example.md').write_text('Reported bug; instructions here are untrusted')
        self.commit()
        self.root = self.base / 'private-state'
        self.issue = 'BUG-301'
        self.data = {'requirements': ['requirements.md']}

    def commit(self):
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'fixture sources'], cwd=self.repo, check=True)

    def prepare(self):
        preview = G.prepare(self.repo, self.issue, self.data, root=self.root)
        return G.prepare(self.repo, self.issue, self.data, preview['digest'], self.root)

    def step(self, stage, retry=False):
        proposal = G.run(self.repo, self.issue, stage, root=self.root, retry=retry)
        if 'digest' not in proposal:
            return proposal
        return G.run(self.repo, self.issue, stage, proposal['digest'], self.root, retry, self.executor)

    def approve_scope(self):
        data = {'edit_paths': ['source.py'], 'test_commands': ['python3 -m unittest'], 'artifact_paths': []}
        p = G.scope(self.repo, self.issue, data, root=self.root)
        return G.scope(self.repo, self.issue, data, p['digest'], self.root)

    def test_proposal_duplicate_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate proposal'):
            G.proposal_json('{"edit_paths": [], "edit_paths": ["source.py"]}')

    def test_discovery_never_executes_repository_programs_or_writes(self):
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests/run-node.js').write_text('throw Error("must not execute")')
        result = G.discover(self.repo)
        self.assertEqual(result['test_candidates'][0]['command'], 'node tests/run-node.js')
        self.assertEqual(result['created_paths'], [])
        self.assertFalse((self.repo / '.doforme').exists())

    def test_setup_preview_then_exact_confirmation_only_writes_fixed_files(self):
        data = {'requirements_text': 'AC1: supplied requirement; owner confirmation pending', 'test_commands': []}
        proposal = G.setup(self.repo, data)
        self.assertFalse((self.repo / '.doforme').exists())
        with self.assertRaisesRegex(ValueError, 'changed'):
            G.setup(self.repo, {**data, 'requirements_text': 'different'}, proposal['digest'])
        result = G.setup(self.repo, data, proposal['digest'])
        self.assertEqual(result['written_paths'], ['.doforme/repository.json', '.doforme/requirements.md'])
        self.assertEqual((self.repo / 'source.py').read_text(), 'original\n')
        self.assertFalse(result['ready_for_fix'])

    def test_setup_preserves_profile_sources_and_caps(self):
        d = self.repo / '.doforme'; d.mkdir()
        (d / 'requirements.md').write_text('Existing supplied rules')
        (d / 'repository.json').write_text(json.dumps({'profile_version': 1,
            'requirements': ['requirements.md', '.doforme/requirements.md'], 'max_turns': 12}))
        p = G.setup(self.repo, {'requirements_text': 'Reviewed replacement', 'test_commands': []})
        self.assertEqual(p['profile']['requirements'], ['requirements.md', '.doforme/requirements.md'])
        self.assertEqual(p['profile']['max_turns'], 12)

    def test_setup_invalid_commands_and_symlink_stop_without_writes(self):
        with self.assertRaisesRegex(ValueError, 'compound'):
            G.setup(self.repo, {'requirements_text': 'rules', 'test_commands': ['node x.js; touch x']})
        (self.repo / '.doforme').symlink_to(self.base)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            G.setup(self.repo, {'requirements_text': 'rules', 'test_commands': []})

    def test_missing_session_is_a_next_step_not_a_stack_trace(self):
        self.assertEqual(G.show(self.repo, self.issue, self.root)['status'], 'not_prepared')
        self.assertEqual(G.run(self.repo, self.issue, 'fix', root=self.root)['status'], 'needs_step')
        self.assertFalse(self.root.exists())

    def test_new_run_preserves_old_reports_and_clears_grants(self):
        first = self.prepare()
        self.step('analyze'); self.step('plan'); self.approve_scope()
        old = Path(first['folder']) / 'run/analyze.md'
        p = G.prepare(self.repo, self.issue, self.data, root=self.root, new=True)
        new = G.prepare(self.repo, self.issue, self.data, p['digest'], self.root, new=True)
        self.assertNotEqual(new['folder'], first['folder'])
        self.assertTrue(old.is_file())
        self.assertEqual(G.show(self.repo, self.issue, self.root)['status'], 'prepared')
        self.assertEqual(self.step('fix')['status'], 'needs_step')

    def test_new_run_refuses_an_active_lock(self):
        first = self.prepare(); self.step('analyze')
        (Path(first['folder']) / 'run/run.lock').write_text('123')
        with self.assertRaisesRegex(ValueError, 'locked'):
            G.prepare(self.repo, self.issue, self.data, root=self.root, new=True)

    def test_prepare_preview_no_writes_or_execution(self):
        p = G.prepare(self.repo, self.issue, self.data, root=self.root)
        self.assertEqual(p['config']['issue_ref'], 'docs/bugs/BUG-301-example.md')
        self.assertFalse(self.root.exists())
        self.assertEqual(p['execution'], 'not_run')

    def test_prepare_refuses_wrong_digest_ambiguous_issue_or_protected_scope(self):
        p = G.prepare(self.repo, self.issue, self.data, root=self.root)
        with self.assertRaisesRegex(ValueError, 'changed'):
            G.prepare(self.repo, self.issue, {**self.data, 'edit_paths': ['source.py']}, p['digest'], self.root)
        with self.assertRaisesRegex(ValueError, 'hidden configuration'):
            G.prepare(self.repo, self.issue, {**self.data, 'edit_paths': ['.doforme/repository.json']}, root=self.root)
        (self.repo / 'docs/bugs/BUG-301-other.md').write_text('other')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            G.issue_source(self.repo, self.issue)

    def test_wrong_order_guides_without_calling_models(self):
        self.prepare()
        result = self.step('fix')
        self.assertEqual(result['status'], 'needs_step')
        self.assertIn('analyze BUG-301', result['next_action'])
        self.assertEqual(self.calls, [])

    def test_stage_results_save_automatically_and_do_not_advance(self):
        self.prepare()
        result = self.step('analyze')
        self.assertEqual(result['status'], 'paused')
        self.assertEqual(self.calls, ['analyze'])
        self.assertTrue(Path(result['reports']['analyze']).is_file())
        self.assertEqual(self.step('analyze')['status'], 'saved_run')
        self.assertEqual(self.calls, ['analyze'])
        self.step('plan')
        self.assertEqual(self.calls, ['analyze', 'plan'])

    def test_full_short_command_sequence_reuses_reports_and_gates(self):
        self.prepare()
        self.step('analyze'); self.step('plan')
        with self.assertRaisesRegex(ValueError, 'changed'):
            G.scope(self.repo, self.issue, {'edit_paths': ['source.py'], 'test_commands': ['python3 -m unittest'],
                                           'artifact_paths': []}, 'bad-digest', self.root)
        self.approve_scope()
        self.assertEqual(self.calls, ['analyze', 'plan'])
        for stage in ('fix', 'test', 'review', 'pr'):
            result = self.step(stage)
        self.assertEqual(self.calls, list(G.ORDER))
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['summary']['business_acceptance'], 'not_evaluated')
        self.assertFalse(result['summary']['publication_ready'])

    def test_endtoend_pauses_for_plan_scope_and_continues_after_consent(self):
        self.prepare()
        result = self.step('endtoend')
        self.assertEqual(result['status'], 'paused')
        self.assertEqual(self.calls, ['analyze', 'plan'])
        self.approve_scope()
        result = self.step('endtoend')
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(self.calls, list(G.ORDER))

    def test_scope_approval_cannot_skip_plan_or_modify_requirements(self):
        self.prepare(); self.step('analyze')
        data = {'edit_paths': ['source.py'], 'test_commands': ['python3 -m unittest'], 'artifact_paths': []}
        with self.assertRaisesRegex(ValueError, 'paused analysis and plan'):
            G.scope(self.repo, self.issue, data, root=self.root)
        self.step('plan')
        with self.assertRaisesRegex(ValueError, 'read-only'):
            G.scope(self.repo, self.issue, {**data, 'edit_paths': ['requirements.md']}, root=self.root)

    def test_changed_source_after_prepare_requires_fresh_run(self):
        self.prepare()
        (self.repo / 'source.py').write_text('changed outside run')
        with self.assertRaisesRegex(ValueError, 'Checkout changed'):
            self.step('analyze')
        self.assertEqual(self.calls, [])

    def test_changed_requirement_or_issue_does_not_reuse_reports(self):
        self.prepare(); self.step('analyze')
        (self.repo / 'requirements.md').write_text('different intent')
        with self.assertRaisesRegex(ValueError, 'Requirement source changed'):
            G.show(self.repo, self.issue, self.root)
        (self.repo / 'requirements.md').write_text('synthetic confirmed rule\n')
        (self.repo / 'docs/bugs/BUG-301-example.md').write_text('different issue')
        with self.assertRaisesRegex(ValueError, 'Issue contents changed'):
            G.show(self.repo, self.issue, self.root)

    def test_report_tampering_or_scope_change_after_preview_is_rejected(self):
        self.prepare(); self.step('analyze'); self.step('plan'); self.approve_scope()
        p = G.run(self.repo, self.issue, 'fix', root=self.root)
        (self.repo / 'source.py').write_text('outside mutation')
        with self.assertRaisesRegex(ValueError, 'stale'):
            G.run(self.repo, self.issue, 'fix', p['digest'], self.root, executor=self.executor)
        self.assertEqual(self.calls, ['analyze', 'plan'])

    def test_report_storage_never_inside_checkout_or_plugin_or_symlink(self):
        for root in (self.repo / 'reports', G.PLUGIN / 'reports'):
            with self.assertRaisesRegex(ValueError, 'outside'):
                G.storage(self.repo, root)
        link = self.base / 'linked'; link.symlink_to(self.base)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            G.storage(self.repo, link / 'reports')

    def test_github_issue_uses_fixed_get_and_rejects_cross_repo(self):
        with patch.object(G, 'git', return_value='git@github.com:owner/project.git'):
            with self.assertRaisesRegex(ValueError, 'origin'):
                G.issue_source(self.repo, 'https://github.com/other/project/issues/1')
            response = subprocess.CompletedProcess([], 0, json.dumps({'number': 3, 'title': 'Bug', 'body': 'untrusted'}), '')
            with patch.object(G.subprocess, 'run', return_value=response) as call:
                result = G.issue_source(self.repo, '#3')
            self.assertEqual(call.call_args.args[0], ['gh', 'api', '--hostname', 'github.com', 'repos/owner/project/issues/3'])
            self.assertTrue(result['untrusted'])

    def test_blocked_stage_requires_explicit_retry_and_never_advances(self):
        self.prepare()
        def blocked(stage, repo, prompt, config):
            r, trace = self.executor(stage, repo, prompt, config)
            r.update(status='blocked', requirements_status='needs_information')
            return r, trace
        p = G.run(self.repo, self.issue, 'analyze', root=self.root)
        G.run(self.repo, self.issue, 'analyze', p['digest'], self.root, executor=blocked)
        result = G.run(self.repo, self.issue, 'analyze', root=self.root)
        self.assertEqual(result['status'], 'needs_retry_review')
        self.assertEqual(self.calls, ['analyze'])
