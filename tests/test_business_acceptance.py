"""Content/coverage guards using synthetic checkpoints, not real owner approvals."""
import hashlib
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
import business_acceptance as ACCEPT
import run_workflow as WF
from workflow_state import digest


class BusinessAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'target'
        self.repo.mkdir()
        (self.repo / 'source.py').write_text('synthetic source\n')
        (self.repo / 'REQ.md').write_text('Synthetic owner confirmation for exercise only.\nAC1: Expected first result.\nAC2: Expected second result.\n')
        for command in (['git', 'init', '-q'], ['git', 'add', '.'],
                        ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic baseline']):
            subprocess.run(command, cwd=self.repo, capture_output=True, check=True)
        self.output = self.base / 'workflow'
        config = {'issue_ref': 'synthetic', 'issue_text': 'Fixture only', 'requirements': ['REQ.md'],
                  'edit_paths': ['source.py'], 'test_commands': ['python3 -m unittest']}
        with contextlib.redirect_stdout(io.StringIO()):
            self.state = WF.pipeline(self.repo, config, self.output, True, True, executor=self.executor)
        self.criteria = self.base / 'criteria.json'
        self.criteria_data = {'contract_version': 1, 'criteria': [
            {'id': 'AC1', 'statement': 'Expected first result.', 'source_path': 'REQ.md', 'confirmation_reference': 'synthetic owner paragraph'},
            {'id': 'AC2', 'statement': 'Expected second result.', 'source_path': 'REQ.md', 'confirmation_reference': 'synthetic owner paragraph'}]}
        self.criteria.write_text(json.dumps(self.criteria_data))
        self.bound = ACCEPT.binding(self.repo, self.output, self.criteria)
        self.evidence = self.base / 'synthetic-uat.txt'
        self.evidence.write_text('Synthetic human UAT notes, not real business approval.\n')
        self.attestation = {'contract_version': 1, 'binding_digest': digest(self.bound),
            'owner': {'name': 'Synthetic Owner', 'role': 'Fixture reviewer', 'authority_reference': 'Exercise-only role assignment'},
            'recorded_at': '2026-11-16T09:00:00+07:00', 'decision_reference': 'Synthetic supplied decision artifact',
            'evidence_files': [{'id': 'U1', 'path': str(self.evidence), 'sha256': hashlib.sha256(self.evidence.read_bytes()).hexdigest()}],
            'criteria': [{'id': 'AC1', 'decision': 'accepted', 'reason': 'Synthetic inspected outcome', 'evidence_refs': ['U1']},
                         {'id': 'AC2', 'decision': 'accepted', 'reason': 'Synthetic inspected outcome', 'evidence_refs': ['U1']}]}
        self.decision_path = self.base / 'decision.json'

    def executor(self, stage, repo, prompt, config):
        traces = []
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
                'revision': WF.git(repo, 'rev-parse', 'HEAD'), 'report': 'Synthetic checkpoint report covers AC1 and AC2; this is not a real test run.'}, traces

    def inspect(self):
        self.decision_path.write_text(json.dumps(self.attestation))
        return ACCEPT.inspect(self.repo, self.output, self.criteria, self.decision_path)

    def test_missing_human_artifact_never_infers_acceptance(self):
        report = ACCEPT.inspect(self.repo, self.output, self.criteria)
        self.assertEqual(report['attestation_status'], 'not_supplied')
        self.assertEqual(report['business_acceptance'], 'not_evaluated')
        self.assertFalse(report['publication_ready'])

    def test_explicit_complete_attestation_is_distinct_from_authenticated_acceptance(self):
        before = WF.snapshot(self.repo), WF.snapshot(self.output)
        report = self.inspect()
        self.assertEqual(report['business_acceptance'], 'attested_accepted')
        self.assertEqual(report['owner_identity_verification'], 'not_verified')
        self.assertEqual(report['owner_authority_verification'], 'not_verified')
        self.assertEqual(report['resolution_status'], 'not_established')
        self.assertFalse(report['publication_ready'])
        self.assertEqual(before, (WF.snapshot(self.repo), WF.snapshot(self.output)))

    def test_rejected_or_pending_decisions_never_appear_accepted(self):
        self.attestation['criteria'][1]['decision'] = 'rejected'
        self.assertEqual(self.inspect()['business_acceptance'], 'attested_rejected')
        self.attestation['criteria'][1]['decision'] = 'pending'
        self.attestation['criteria'][1]['evidence_refs'] = []
        self.assertEqual(self.inspect()['business_acceptance'], 'attested_pending')

    def test_changed_source_with_same_head_invalidates_attestation(self):
        (self.repo / 'source.py').write_text('changed after review\n')
        with self.assertRaisesRegex(ValueError, 'fresh workflow'):
            self.inspect()

    def test_changed_ac_manifest_invalidates_old_binding(self):
        self.criteria_data['criteria'][0]['confirmation_reference'] = 'different supplied decision'
        self.criteria.write_text(json.dumps(self.criteria_data))
        with self.assertRaisesRegex(ValueError, 'does not bind'):
            self.inspect()

    def test_missing_and_unknown_ac_coverage_are_rejected(self):
        for rows in ([self.attestation['criteria'][0]], [*self.attestation['criteria'],
                     {'id': 'AC3', 'decision': 'accepted', 'reason': 'not in scope', 'evidence_refs': ['U1']}]):
            self.attestation['criteria'] = rows
            with self.assertRaisesRegex(ValueError, 'coverage'):
                self.inspect()

    def test_source_criteria_cannot_be_invented_or_omitted(self):
        self.criteria_data['criteria'][0]['statement'] = 'Invented business rule'
        self.criteria.write_text(json.dumps(self.criteria_data))
        with self.assertRaisesRegex(ValueError, 'same exact source AC entry'):
            ACCEPT.binding(self.repo, self.output, self.criteria)

    def test_swapped_ac_statements_cannot_reuse_another_entry_in_same_source(self):
        first, second = self.criteria_data['criteria']
        first['statement'], second['statement'] = second['statement'], first['statement']
        self.criteria.write_text(json.dumps(self.criteria_data))
        with self.assertRaisesRegex(ValueError, 'same exact source AC entry'):
            ACCEPT.binding(self.repo, self.output, self.criteria)

    def test_ambiguous_or_multiline_ac_entries_fail_closed(self):
        for source in ('AC1: First.\nAC1: Second.\n',
                       'AC1: First.\n    Additional condition.\n',
                       '| AC1 | First. |\n',
                       '**AC1:** First.\n'):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'entry'):
                ACCEPT.source_ac_entry(source, 'AC1')
        self.assertEqual(ACCEPT.source_ac_entry('- AC1: Exact condition.\n\nNotes.\n', 'AC1'), 'Exact condition.')

    def test_acceptance_requires_local_hashed_evidence_not_link_only(self):
        self.attestation['evidence_files'][0]['path'] = 'https://example.invalid/approval'
        with self.assertRaisesRegex(ValueError, 'absolute local files'):
            self.inspect()
        self.attestation['evidence_files'] = []
        with self.assertRaisesRegex(ValueError, 'hashed evidence'):
            self.inspect()

    def test_changed_uat_evidence_invalidates_supplied_hash(self):
        self.evidence.write_text('Changed supplied notes\n')
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            self.inspect()

    def test_unknown_trust_and_publication_claims_are_rejected(self):
        self.attestation['business_acceptance'] = 'accepted'
        with self.assertRaisesRegex(ValueError, 'unknown attestation fields'):
            self.inspect()
        self.attestation.pop('business_acceptance')
        self.attestation['owner']['verified'] = True
        with self.assertRaisesRegex(ValueError, 'unknown owner claimant fields'):
            self.inspect()

    def test_tampered_workflow_report_is_not_accepted(self):
        (self.output / 'review.md').write_text('changed review\n')
        with self.assertRaisesRegex(ValueError, 'Displayed report differs'):
            self.inspect()

    def test_cli_is_read_only_and_returns_binding_without_an_owner(self):
        before = WF.snapshot(self.repo), WF.snapshot(self.output)
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/business_acceptance.py'),
                                 '--repo', str(self.repo), '--workflow', str(self.output), '--criteria', str(self.criteria)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['business_acceptance'], 'not_evaluated')
        self.assertEqual(before, (WF.snapshot(self.repo), WF.snapshot(self.output)))


if __name__ == '__main__':
    unittest.main()
