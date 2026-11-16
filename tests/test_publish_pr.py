"""Publication gates with actual local commits and mocked GitHub, never a real PR."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import publish_pr as PUB
import run_workflow as WF


class FakeGitHub:
    def __init__(self, state, base_tree, head_sha):
        self.state = state
        self.base_tree = base_tree
        self.head_tree = PUB.tested_workspace(state)
        self.head_sha = head_sha
        self.base_sha = state['revision']
        self.calls = []
        self.fail_post = False
        self.race = False
        self.receipt = None

    def request(self, method, endpoint, payload=None):
        self.calls.append((method, endpoint, payload))
        if method == 'POST':
            if self.receipt is not None:
                assert json.loads(self.receipt.read_text())['status'] == 'attempting'
            if self.fail_post:
                raise ValueError('simulated uncertain response')
            return {'html_url': 'https://github.com/example/project/pull/7', 'number': 7, 'draft': True,
                    'head': {'sha': 'f' * 40 if self.race else self.head_sha}, 'base': {'sha': self.base_sha}}
        if endpoint.lower() == 'repos/example/project':
            return {'full_name': 'example/project'}
        if '/branches/' in endpoint:
            sha = self.head_sha if endpoint.endswith('/fix') else self.base_sha
            return {'commit': {'sha': sha, 'commit': {'tree': {'sha': sha}}}}
        if '/git/trees/' in endpoint:
            tree = self.head_tree if self.head_sha in endpoint else self.base_tree
            return {'truncated': False, 'tree': [{'path': path, 'type': 'blob', **value} for path, value in tree.items()]}
        if '/compare/' in endpoint:
            return {'status': 'ahead', 'merge_base_commit': {'sha': self.state['revision']}}
        if '/pulls?' in endpoint:
            return []
        raise AssertionError(endpoint)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'target'
        self.repo.mkdir()
        (self.repo / 'source.py').write_text('bug\n')
        (self.repo / 'REQ.md').write_text('Synthetic AC1 confirmation\n')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('remote', 'add', 'origin', 'https://github.com/example/project.git')
        self.git('add', '.')
        self.git('commit', '-qm', 'synthetic baseline')
        before = WF.snapshot(self.repo)
        base_tree = {path: {'sha': item['git_blob_sha1'], 'mode': '100644'} for path, item in before.items()}
        self.workflow = self.base / 'workflow'
        config = {'issue_ref': 'synthetic', 'issue_text': 'Synthetic issue', 'requirements': ['REQ.md'],
                  'edit_paths': ['source.py'], 'test_commands': ['python3 -m unittest']}
        with contextlib.redirect_stdout(io.StringIO()):
            self.state = WF.pipeline(self.repo, config, self.workflow, True, True, executor=self.executor)
        # Explicit human handoff: commit tested bytes outside the workflow. This
        # must not silently rebind the checkpoint or normal resume freshness.
        self.git('add', 'source.py')
        self.git('commit', '-qm', 'commit exact tested patch')
        self.client = FakeGitHub(self.state, base_tree, self.git('rev-parse', 'HEAD'))
        self.title = self.base / 'title.txt'
        self.body = self.base / 'body.md'
        self.title.write_text('Correct synthetic source')
        self.body.write_text('Synthetic draft with scoped evidence. Refs #1.\n')
        self.receipts = self.base / 'receipts'
        self.receipts.mkdir(mode=0o700)
        self.receipt = self.receipts / 'attempt.json'

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True).strip()

    def executor(self, stage, repo, prompt, config):
        traces = []
        if stage == 'fix':
            (repo / 'source.py').write_text('fixed\n')
        if stage in ('fix', 'test'):
            for index, error in enumerate([True, False] if stage == 'fix' else [False]):
                ident = 'validation-' + str(index)
                traces += [{'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'id': ident, 'input': {'command': config['test_commands'][0]}}]}},
                           {'message': {'content': [{'type': 'tool_result', 'tool_use_id': ident, 'is_error': error,
                               'content': 'Exit code 1\nAssertionError: synthetic mismatch' if error else 'Synthetic checks passed'}]}}]
        return {'stage': stage, 'status': 'complete',
                'verdict': 'valid_bug' if stage == 'analyze' else 'pass' if stage == 'review' else 'not_applicable',
                'requirements_status': 'verified_for_scope',
                'technical_validation': 'passed_scoped' if stage in ('fix', 'test') else 'not_run',
                'business_acceptance': 'not_evaluated', 'resolution_status': 'not_established',
                'revision': WF.git(repo, 'rev-parse', 'HEAD'), 'report': 'Synthetic AC1 report; no actual business acceptance.'}, traces

    def args(self):
        return self.repo, self.workflow, 'example/project', 'fix', 'main', self.title, self.body

    def preview(self):
        return PUB.preview(*self.args(), client=self.client)

    def publish(self, expected):
        self.client.receipt = self.receipt
        return PUB.publish(*self.args(), expected, self.receipt, client=self.client)

    def test_content_identical_local_commit_handoff_preserves_original_checkpoint(self):
        before = WF.snapshot(self.repo), WF.snapshot(self.workflow)
        self.assertFalse(WF.status_checkpoint(self.repo, self.workflow)['fresh'])
        report = self.preview()
        self.assertEqual(report['preview']['revision_transition']['status'], 'content_identical_commit_handoff')
        self.assertEqual(report['preview']['tested_revision'], self.state['revision'])
        self.assertFalse(report['publication_ready'])
        self.assertEqual(before, (WF.snapshot(self.repo), WF.snapshot(self.workflow)))
        self.assertTrue(all(method == 'GET' for method, _, _ in self.client.calls))
        self.assertFalse(self.receipt.exists())

    def test_repository_casing_is_canonicalized_before_binding_and_publication(self):
        args = (self.repo, self.workflow, 'EXAMPLE/PROJECT', 'fix', 'main', self.title, self.body)
        report = PUB.preview(*args, client=self.client)
        self.assertEqual(report['preview']['repository'], 'example/project')
        self.client.receipt = self.receipt
        result = PUB.publish(*args, report['preview_digest'], self.receipt, client=self.client)
        self.assertEqual(result['status'], 'draft_created')
        self.assertEqual(result['repository'], 'example/project')
        self.assertEqual(result['url'], 'https://github.com/example/project/pull/7')
        posts = [endpoint for method, endpoint, _ in self.client.calls if method == 'POST']
        self.assertEqual(posts, ['repos/example/project/pulls'])

    def test_unpushed_or_wrong_remote_tree_is_blocked(self):
        self.client.head_tree['source.py']['sha'] = 'a' * 40
        with self.assertRaisesRegex(ValueError, 'Remote head tree'):
            self.preview()

    def test_current_source_change_requires_new_workflow(self):
        (self.repo / 'source.py').write_text('different after commit\n')
        with self.assertRaisesRegex(ValueError, 'content or policy changed'):
            self.preview()

    def test_existing_head_base_and_repo_must_be_explicit_correct(self):
        with self.assertRaisesRegex(ValueError, 'distinct'):
            PUB.preview(self.repo, self.workflow, 'example/project', 'main', 'main', self.title, self.body, self.client)
        with self.assertRaisesRegex(ValueError, 'differs from target origin'):
            PUB.preview(self.repo, self.workflow, 'other/project', 'fix', 'main', self.title, self.body, self.client)

    def test_issue_closing_magic_is_rejected_before_network_mutation(self):
        for body in ('Fixes #1', 'Closes: example/project#2', 'Resolves https://github.com/example/project/issues/3'):
            self.body.write_text(body)
            with self.assertRaisesRegex(ValueError, 'issue-closing'):
                self.preview()
        self.assertFalse(any(method == 'POST' for method, _, _ in self.client.calls))

    def test_changed_remote_branch_or_reviewed_body_invalidates_expected_digest(self):
        expected = self.preview()['preview_digest']
        self.client.head_sha = 'd' * 40
        with self.assertRaisesRegex(ValueError, 'changed since caller review'):
            self.publish(expected)
        self.assertFalse(self.receipt.exists())

    def test_explicit_publish_creates_only_draft_after_durable_receipt(self):
        expected = self.preview()['preview_digest']
        result = self.publish(expected)
        self.assertEqual(result['status'], 'draft_created')
        posts = [payload for method, _, payload in self.client.calls if method == 'POST']
        self.assertEqual(len(posts), 1)
        self.assertTrue(posts[0]['draft'])
        self.assertFalse(posts[0]['maintainer_can_modify'])
        self.assertIn('Business acceptance: not evaluated', posts[0]['body'])
        with self.assertRaises(FileExistsError):
            self.publish(expected)
        self.assertEqual(len([m for m, _, _ in self.client.calls if m == 'POST']), 1)

    def test_uncertain_delivery_receipt_prevents_automatic_retry(self):
        expected = self.preview()['preview_digest']
        self.client.fail_post = True
        with self.assertRaisesRegex(ValueError, 'uncertain'):
            self.publish(expected)
        self.assertEqual(json.loads(self.receipt.read_text())['status'], 'uncertain')
        with self.assertRaises(FileExistsError):
            self.publish(expected)

    def test_branch_movement_during_creation_requires_manual_review(self):
        expected = self.preview()['preview_digest']
        self.client.race = True
        result = self.publish(expected)
        self.assertEqual(result['status'], 'created_needs_manual_review')
        self.assertEqual(result['content_binding'], 'changed_during_creation')


if __name__ == '__main__':
    unittest.main()
