"""Packaged native setup previews must preserve source and execution boundaries."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_antigravity as B
import run_workflow as W
import test_workflow as F


class NativeOnboardingTests(unittest.TestCase):
    setUp = F.WorkflowTests.setUp

    def helper(self, *args):
        bundle = self.base / 'bundle'
        if not bundle.exists():
            B.build(bundle)
        result = subprocess.run([sys.executable, '-B', str(bundle / 'scripts/antigravity_workflow.py'),
            *args, '--repo', str(self.repo)], capture_output=True, text=True, check=False)
        return result.returncode, json.loads(result.stdout)

    def test_plain_init_and_explicit_inspection_are_read_only(self):
        before = W.snapshot(self.repo)
        for args in (('init',), ('init', '--inspect')):
            code, report = self.helper(*args)
            self.assertEqual(code, 0)
            self.assertEqual(report['status'], 'inspection_only')
            self.assertEqual(W.snapshot(self.repo), before)

    def test_explicit_write_creates_only_unconfirmed_drafts_and_preserves_them(self):
        before = W.snapshot(self.repo)
        code, report = self.helper('init', '--write')
        self.assertEqual((code, report['status']), (0, 'draft_created'))
        self.assertFalse(report['ready_for_fix'])
        after = W.snapshot(self.repo)
        self.assertEqual(W.changed(before, after), {'.doforme/repository.json', '.doforme/requirements.md'})
        _, second = self.helper('init', '--write')
        self.assertEqual(second['status'], 'already_initialized')
        self.assertEqual(W.snapshot(self.repo), after)

    def test_setup_requires_exact_current_digest_and_runs_no_tests(self):
        before = W.snapshot(self.repo)
        data = json.dumps({'requirements_text': 'Fixture owner confirmed AC-1: preserve all supplied values.',
                           'test_commands': ['python3 -m unittest']})
        code, preview = self.helper('setup', '--data-json', data)
        self.assertEqual(code, 0)
        self.assertEqual(preview['execution'], 'not_run')
        self.assertEqual(W.snapshot(self.repo), before)
        code, _ = self.helper('setup', '--data-json', data, '--confirm', 'wrong')
        self.assertEqual(code, 2)
        self.assertEqual(W.snapshot(self.repo), before)
        code, saved = self.helper('setup', '--data-json', data, '--confirm', preview['digest'])
        self.assertEqual((code, saved['status']), (0, 'setup_saved'))
        self.assertFalse(saved['ready_for_fix'])
        self.assertEqual(W.changed(before, W.snapshot(self.repo)), {'.doforme/repository.json', '.doforme/requirements.md'})

    def test_draft_flags_cannot_authorize_other_actions_or_override_setup(self):
        before = W.snapshot(self.repo)
        for args in (('analyze', '--write'), ('setup', '--write'), ('init', '--write', '--data-json', '{}')):
            code, _ = self.helper(*args)
            self.assertEqual(code, 2)
            self.assertEqual(W.snapshot(self.repo), before)
