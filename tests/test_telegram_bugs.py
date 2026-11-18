"""Lifecycle notification gates use GitHub evidence, never model completion alone."""
import contextlib
import copy
import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('telegram_bugs', ROOT / 'integrations/telegram_bugs.py')
N = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(N)
SHA = 'a' * 40


class FakeGitHub:
    def __init__(self):
        self.issue = {'id': 100, 'number': 1, 'title': 'BUG-303 $(touch SHOULD_NOT_RUN)',
                      'html_url': 'https://github.com/example/lab/issues/1', 'labels': [{'name': 'bug'}],
                      'state': 'closed', 'state_reason': 'completed', 'closed_at': '2026-11-18T10:00:00Z'}
        self.declaration = {'issue': 1, 'pr': 2, 'merge_commit': SHA, 'qa': 'passed',
            'business_acceptance': 'accepted', 'evidence_url': 'https://github.com/example/lab/issues/1#issuecomment-20',
            'source_refs': ['docs/rules/dashboard.md:D6', 'BUG-303 acceptance criteria']}
        self.comments = [{'id': 30, 'user': {'login': 'owner'}, 'created_at': '2026-11-18T09:30:00Z',
                          'updated_at': '2026-11-18T09:30:00Z', 'body': ''}]
        self.timeline = [{'id': 50, 'event': 'closed', 'created_at': '2026-11-18T10:00:00Z'}]
        self.pr = {'merged': True, 'merge_commit_sha': SHA, 'merged_at': '2026-11-18T09:00:00Z',
                   'base': {'ref': 'main', 'repo': {'full_name': 'example/lab'}}}
        self.evidence = {'html_url': self.declaration['evidence_url'], 'user': {'login': 'owner'},
                         'created_at': '2026-11-18T09:15:00Z', 'updated_at': '2026-11-18T09:15:00Z',
                         'body': 'QA passed ACs on merge commit ' + SHA + '; business owner accepts for scope D6.'}
        self.checks = {'total_count': 1, 'check_runs': [{'id': 80, 'name': 'tests', 'head_sha': SHA,
            'app': {'slug': 'github-actions'}, 'status': 'completed', 'conclusion': 'success'}]}
        self.artifacts = {'total_count': 0, 'artifacts': []}
        self.calls = []

    def get(self, path):
        self.calls.append(('GET', path))
        if '/actions/artifacts?' in path:
            return self.artifacts
        if path.endswith('/issues/1'):
            return self.issue
        if path.endswith('/pulls/2'):
            return self.pr
        if path.endswith('/issues/comments/20'):
            return self.evidence
        if '/check-runs?' in path:
            return self.checks
        if path == 'repos/example/lab':
            return {'default_branch': 'main'}
        raise AssertionError('Unexpected API path: ' + path)

    def pages(self, path):
        self.calls.append(('GET', path))
        if path.endswith('/timeline'):
            return self.timeline
        if path.endswith('/comments'):
            self.comments[0]['body'] = '```doforme-resolution\n' + json.dumps(self.declaration) + '\n```'
            return self.comments
        raise AssertionError('Unexpected page path')


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeGitHub()
        self.event = {'action': 'closed', 'repository': {'full_name': 'example/lab'}, 'issue': {'number': 1}}

    def plan(self, **kwargs):
        options = {'owners': 'owner', 'required_checks': ['tests'], 'client': self.client}
        options.update(kwargs)
        return N.plan(self.event, 'example/lab', 'issues', **options)

    def test_complete_owner_evidence_produces_bound_resolved_message(self):
        report = self.plan()
        self.assertEqual(report['status'], 'ready')
        self.assertEqual(report['topic'], 'resolved')
        self.assertEqual(report['key'], 'resolved-100-50')
        self.assertIn('owner-attested accepted', report['text'])
        self.assertEqual(report['resolution']['merge_commit'], SHA)
        self.assertTrue(all(method == 'GET' for method, _ in self.client.calls))

    def test_new_bug_never_needs_or_claims_acceptance(self):
        self.client.issue['state'] = 'open'
        self.event['action'] = 'opened'
        report = self.plan(owners='', required_checks=[])
        self.assertEqual(report['topic'], 'new')
        self.assertIn('belum dinyatakan resolved', report['text'])
        self.assertNotIn('resolution', report)
        self.assertEqual(len(self.client.calls), 1)

    def test_non_bug_and_pull_requests_are_skipped(self):
        self.client.issue['labels'] = []
        self.assertEqual(self.plan()['status'], 'skipped')
        self.event['issue']['pull_request'] = {}
        self.assertEqual(self.plan()['status'], 'skipped')

    def test_labeled_bug_notifies_same_new_key_and_ignores_other_labels(self):
        self.client.issue['state'] = 'open'
        self.event.update(action='labeled', label={'name': 'bug'})
        self.assertEqual(self.plan()['key'], 'new-100')
        self.event['label']['name'] = 'qa:passed'
        self.assertEqual(self.plan()['status'], 'skipped')

    def test_close_not_planned_or_reopen_never_means_resolved(self):
        self.client.issue['state_reason'] = 'not_planned'
        self.assertEqual(self.plan()['status'], 'skipped')
        self.client.issue.update(state='open', state_reason=None)
        self.event['action'] = 'reopened'
        self.assertEqual(self.plan()['status'], 'skipped')

    def test_bare_close_without_trusted_owner_declaration_is_blocked(self):
        self.client.comments[0]['user']['login'] = 'random-user'
        self.assertEqual(self.plan()['status'], 'blocked')
        self.assertEqual(self.plan(owners='')['status'], 'blocked')

    def test_rejected_or_pending_business_acceptance_is_blocked(self):
        for key, value in (('qa', 'failed'), ('business_acceptance', 'pending')):
            with self.subTest(key=key):
                current = copy.deepcopy(self.client.declaration)
                self.client.declaration[key] = value
                self.assertEqual(self.plan()['status'], 'blocked')
                self.client.declaration = current

    def test_wrong_or_unmerged_pr_and_wrong_base_are_blocked(self):
        for change in ({'merged': False}, {'merge_commit_sha': 'b' * 40},
                       {'base': {'ref': 'other', 'repo': {'full_name': 'example/lab'}}}):
            original = copy.deepcopy(self.client.pr)
            self.client.pr.update(change)
            with self.subTest(change=change):
                self.assertEqual(self.plan()['status'], 'blocked')
            self.client.pr = original

    def test_edited_or_pre_merge_approval_is_blocked(self):
        self.client.comments[0]['updated_at'] = '2026-11-18T11:00:00Z'
        self.assertEqual(self.plan()['status'], 'blocked')
        self.client.comments[0].update(created_at='2026-11-18T08:00:00Z', updated_at='2026-11-18T08:00:00Z')
        self.assertEqual(self.plan()['status'], 'blocked')

    def test_reopen_invalidates_old_owner_evidence(self):
        self.client.timeline.insert(0, {'id': 45, 'event': 'reopened', 'created_at': '2026-11-18T09:45:00Z'})
        self.assertEqual(self.plan()['status'], 'blocked')

    def test_evidence_requires_same_issue_owner_and_exact_commit(self):
        self.client.evidence['body'] = 'all good without a revision'
        self.assertEqual(self.plan()['status'], 'blocked')
        self.client.declaration['evidence_url'] = 'https://example.invalid/arbitrary'
        self.assertEqual(self.plan()['status'], 'blocked')

    def test_missing_failed_stale_or_foreign_app_check_blocks(self):
        self.assertEqual(self.plan(required_checks=[])['status'], 'blocked')
        for change in ({'conclusion': 'failure'}, {'status': 'in_progress'}, {'head_sha': 'b' * 40},
                       {'app': {'slug': 'another-app'}}):
            original = copy.deepcopy(self.client.checks)
            self.client.checks['check_runs'][0].update(change)
            with self.subTest(change=change):
                self.assertEqual(self.plan()['status'], 'blocked')
            self.client.checks = original
        self.client.checks['total_count'] = 101
        self.assertEqual(self.plan()['status'], 'blocked')

    def test_latest_check_attempt_must_succeed(self):
        self.client.checks['check_runs'].append({**self.client.checks['check_runs'][0], 'id': 81, 'conclusion': 'failure'})
        self.client.checks['total_count'] = 2
        self.assertEqual(self.plan()['status'], 'blocked')

    def test_receipt_key_is_per_closure_not_per_owner_comment(self):
        first = self.plan()
        self.client.comments[0]['id'] = 31
        self.assertEqual(self.plan()['key'], first['key'])
        name = N.artifact_name(first)
        self.client.artifacts = {'total_count': 1, 'artifacts': [{'name': name, 'expired': False}]}
        self.assertTrue(N.attempted(self.client, 'example/lab', name))

    def test_manual_dispatch_only_rechecks_explicit_issue(self):
        event = {'repository': {'full_name': 'example/lab'}, 'inputs': {'issue_number': '1'}}
        report = N.plan(event, 'example/lab', 'workflow_dispatch', owners='owner', required_checks=['tests'], client=self.client)
        self.assertEqual(report['topic'], 'resolved')
        event['inputs']['issue_number'] = '1; run something'
        with self.assertRaises(ValueError):
            N.plan(event, 'example/lab', 'workflow_dispatch', client=self.client)

    def test_other_repository_and_duplicate_json_are_rejected(self):
        with self.assertRaises(ValueError):
            N.plan(self.event, 'other/lab', 'issues', client=self.client)
        with self.assertRaises(ValueError):
            N.checked_json('{"issue":1,"issue":2}')

    def test_disabled_cli_never_contacts_services_or_creates_output(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'packet'
            with patch.dict(os.environ, {'DOFORME_NOTIFY_TELEGRAM': 'false'}, clear=True), \
                 patch.object(sys, 'argv', ['notify', 'prepare', '--event', '/missing/event.json', '--folder', str(folder)]), \
                 patch.object(N, 'GitHub', side_effect=AssertionError('No network')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(N.main(), 0)
            self.assertFalse(folder.exists())

    def test_standalone_isolated_cli_ignores_project_module_shadowing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'json.py').write_text('raise RuntimeError("Untrusted project module imported")\n')
            folder = root / 'packet'
            result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'integrations/telegram_bugs.py'),
                                     'prepare', '--event', str(root / 'missing.json'), '--folder', str(folder)],
                cwd=root, env={**os.environ, 'DOFORME_NOTIFY_TELEGRAM': 'false', 'PYTHONPATH': str(root)},
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'disabled')
            self.assertFalse(folder.exists())

    def test_send_revalidates_and_stops_if_issue_reopens(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'packet'
            folder.mkdir(mode=0o700)
            N.write_private(folder / 'notification.json', self.plan())
            event = Path(temp) / 'event.json'
            event.write_text(json.dumps(self.event))
            self.client.issue['state'] = 'open'
            env = {'DOFORME_NOTIFY_TELEGRAM': 'true', 'GITHUB_REPOSITORY': 'example/lab',
                   'GITHUB_EVENT_NAME': 'issues', 'DOFORME_RESOLUTION_APPROVERS': 'owner', 'DOFORME_REQUIRED_CHECKS': 'tests'}
            with patch.dict(os.environ, env, clear=True), patch.object(N, 'GitHub', return_value=self.client), \
                 patch.object(N, 'telegram', side_effect=AssertionError('Must not send')), \
                 patch.object(sys, 'argv', ['notify', 'send', '--event', str(event), '--folder', str(folder)]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(N.main(), 1)
            self.assertFalse((folder / 'delivery.json').exists())

    def test_prepare_writes_private_plan_but_never_sends_and_retained_receipt_suppresses_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'packet'
            event = Path(temp) / 'event.json'
            self.event['action'] = 'opened'
            self.client.issue['state'] = 'open'
            event.write_text(json.dumps(self.event))
            env = {'DOFORME_NOTIFY_TELEGRAM': 'true', 'GITHUB_REPOSITORY': 'example/lab', 'GITHUB_EVENT_NAME': 'issues'}
            argv = ['notify', 'prepare', '--event', str(event), '--folder', str(folder)]
            with patch.dict(os.environ, env, clear=True), patch.object(N, 'GitHub', return_value=self.client), \
                 patch.object(N, 'telegram', side_effect=AssertionError('Prepare must not send')), \
                 patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(N.main(), 0)
            self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
            self.assertEqual((folder / 'notification.json').stat().st_mode & 0o777, 0o600)
            notification = N.read_json(folder / 'notification.json')
            self.client.artifacts = {'total_count': 1, 'artifacts': [{'name': N.artifact_name(notification), 'expired': False}]}
            second = Path(temp) / 'second-packet'
            argv[-1] = str(second)
            with patch.dict(os.environ, env, clear=True), patch.object(N, 'GitHub', return_value=self.client), \
                 patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(N.main(), 0)
            self.assertFalse(second.exists())

    def test_send_requires_durable_artifact_and_local_attempt_before_sender(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'packet'
            folder.mkdir(mode=0o700)
            original = self.plan()
            N.write_private(folder / 'notification.json', original)
            event = Path(temp) / 'event.json'
            event.write_text(json.dumps(self.event))
            env = {'DOFORME_NOTIFY_TELEGRAM': 'true', 'GITHUB_REPOSITORY': 'example/lab',
                   'GITHUB_EVENT_NAME': 'issues', 'DOFORME_RESOLUTION_APPROVERS': 'owner', 'DOFORME_REQUIRED_CHECKS': 'tests',
                   'TELEGRAM_BOT_TOKEN': '123:FAKE_SECRET', 'TELEGRAM_CHAT_ID': '-12345'}
            argv = ['notify', 'send', '--event', str(event), '--folder', str(folder)]
            sent = []
            def sender(token, chat, message):
                self.assertTrue((folder / 'delivery.json').is_file())
                self.assertIn('owner-attested', message)
                sent.append(message)
                return 101
            with patch.dict(os.environ, env, clear=True), patch.object(N, 'GitHub', return_value=self.client), \
                 patch.object(N, 'telegram', side_effect=sender), patch.object(sys, 'argv', argv), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(N.main(), 1)  # No durable remote attempt artifact: don't send.
                self.assertEqual(sent, [])
                self.client.artifacts = {'total_count': 1, 'artifacts': [
                    {'name': N.artifact_name(original), 'expired': False}]}
                self.assertEqual(N.main(), 0)
                self.assertEqual(N.main(), 1)  # Local attempt already exists: don't resend.
            self.assertEqual(len(sent), 1)
            self.assertEqual(N.read_json(folder / 'delivered.json')['message_id'], 101)

    def test_source_json_fifo_and_symlink_are_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'event.json'
            path.symlink_to('/missing/event')
            with self.assertRaises(ValueError):
                N.read_json(path)
            path.unlink()
            os.mkfifo(path)
            with self.assertRaises(ValueError):
                N.read_json(path)

    def test_transport_uncertainty_does_not_expose_token(self):
        token = '123:FAKE_SECRET'
        with patch.object(N.urllib.request, 'build_opener') as opener:
            opener.return_value.open.side_effect = OSError('https://api.telegram.org/bot' + token)
            with self.assertRaises(ValueError) as caught:
                N.telegram(token, '-12345', 'example message')
        self.assertNotIn(token, str(caught.exception))


if __name__ == '__main__':
    unittest.main()
