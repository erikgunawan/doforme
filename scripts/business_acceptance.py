"""Read-only validation of explicit, content-bound human business attestations."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
from repo_policy import safe_path
from repo_profile import read_json
from run_workflow import checkpoint_results_checked, status_checkpoint
from workflow_state import Checkpoints, digest

AC_ID = re.compile(r'\bAC[1-9][0-9]*\b')
AC_ENTRY = re.compile(r'^[ \t]*(?:[-*][ \t]+)?(AC[1-9][0-9]*):[ \t]*(.*?)[ \t]*$')


def regular_path(path, maximum=1_000_000):
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('Acceptance inputs must not contain symlinks')
    if not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('Acceptance input must be a bounded regular file')
    return path


def json_input(path):
    return read_json(regular_path(path))


def exact_fields(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Missing or unknown ' + label + ' fields')


def nonempty(value, label, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError('Missing or oversized ' + label)
    return value


def source_ac_entry(raw, ident):
    """Resolve one unambiguous single-line canonical AC definition, not mentions."""
    lines = raw.splitlines()
    matches = [(index, match.group(2)) for index, line in enumerate(lines)
               if (match := AC_ENTRY.fullmatch(line)) and match.group(1) == ident]
    if len(matches) != 1 or not matches[0][1]:
        raise ValueError('AC source entry is missing, duplicate or unsupported; require one canonical ACn: statement line')
    index, statement = matches[0]
    if index + 1 < len(lines):
        following = lines[index + 1]
        if following.strip() and not AC_ENTRY.fullmatch(following) and not re.match(r'^\s*#{1,6}\s', following):
            raise ValueError('Multiline/ambiguous AC source entry is unsupported; provide a reviewed single-line export')
    return statement


def criteria_checked(repo, config, state, data):
    exact_fields(data, ('contract_version', 'criteria'), 'criteria manifest')
    if type(data['contract_version']) is not int or data['contract_version'] != 1:
        raise ValueError('Unsupported criteria contract')
    criteria = data['criteria']
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= 200:
        raise ValueError('Explicit scoped acceptance criteria are required')
    mentioned = set()
    for stage in ('plan', 'test', 'review'):
        mentioned.update(AC_ID.findall(state['results'][stage]['report']))
    if not mentioned:
        raise ValueError('Current reports have no canonical AC IDs to bind')
    ids = set()
    normalized = []
    for item in criteria:
        exact_fields(item, ('id', 'statement', 'source_path', 'confirmation_reference'), 'criterion')
        ident = item['id']
        if not isinstance(ident, str) or not AC_ID.fullmatch(ident) or ident in ids:
            raise ValueError('Invalid or duplicate AC ID')
        statement = nonempty(item['statement'], 'AC statement')
        confirmation = nonempty(item['confirmation_reference'], 'AC scope confirmation reference')
        source = safe_path(repo, item['source_path'])
        name = source.relative_to(repo).as_posix()
        if name not in config['requirements']:
            raise ValueError('AC source is not a workflow requirement input')
        raw = regular_path(source).read_text(encoding='utf-8')
        if statement != source_ac_entry(raw, ident):
            raise ValueError('AC ID/statement must match the same exact source AC entry')
        ids.add(ident)
        normalized.append({'id': ident, 'statement': statement, 'source_path': name,
                           'confirmation_reference': confirmation})
    if ids != mentioned:
        raise ValueError('Criteria manifest must cover exactly all AC IDs in current plan/test/review reports')
    return sorted(normalized, key=lambda item: int(item['id'][2:]))


def binding(repo, workflow, criteria_path):
    repo = Path(repo).resolve()
    status = status_checkpoint(repo, workflow)
    if status['status'] != 'complete' or status['fresh'] is not True:
        raise ValueError('Acceptance requires a complete, fresh workflow with passing review')
    store = Checkpoints(workflow, resume=True)
    state = store.load()
    checkpoint_results_checked(store, state, state['revision'])
    if state['results']['review']['verdict'] != 'pass':
        raise ValueError('Acceptance requires passing independent review')
    config = json.loads(store.read_text('input.json'))
    data = json_input(criteria_path)
    criteria = criteria_checked(repo, config, state, data)
    result = {'contract_version': 1, 'repository': str(repo), 'revision': state['revision'],
              'workspace_digest': digest(state['workspace']), 'config_digest': state['config_digest'],
              'policy_digest': state['policy_digest'], 'workflow_results_digest': digest(state['results']),
              'validation_artifacts_digest': digest(state['validation_artifacts']),
              'criteria_manifest_digest': digest(data), 'criteria': criteria}
    return result


def attestation_checked(data, bound):
    exact_fields(data, ('contract_version', 'binding_digest', 'owner', 'recorded_at',
                        'decision_reference', 'evidence_files', 'criteria'), 'attestation')
    if type(data['contract_version']) is not int or data['contract_version'] != 1:
        raise ValueError('Unsupported attestation contract')
    if data['binding_digest'] != digest(bound):
        raise ValueError('Attestation does not bind the current workflow, content and AC manifest')
    owner = data['owner']
    exact_fields(owner, ('name', 'role', 'authority_reference'), 'owner claimant')
    for field in owner:
        nonempty(owner[field], 'owner ' + field)
    nonempty(data['decision_reference'], 'decision provenance')
    timestamp = nonempty(data['recorded_at'], 'recorded_at', 80)
    try:
        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('recorded_at must be an ISO timestamp with timezone') from None
    if date.utcoffset() is None:
        raise ValueError('recorded_at must include timezone')
    evidence = data['evidence_files']
    if not isinstance(evidence, list) or len(evidence) > 200:
        raise ValueError('Invalid evidence list')
    evidence_ids = set()
    for item in evidence:
        exact_fields(item, ('id', 'path', 'sha256'), 'acceptance evidence')
        ident = nonempty(item['id'], 'evidence ID', 80)
        if ident in evidence_ids:
            raise ValueError('Duplicate acceptance evidence ID')
        if not isinstance(item['path'], str) or not Path(item['path']).is_absolute():
            raise ValueError('Acceptance evidence paths must be explicit absolute local files, not URLs')
        raw = regular_path(item['path'], 5_000_000).read_bytes()
        if not raw.strip() or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Acceptance evidence is empty or content hash differs')
        evidence_ids.add(ident)
    decisions = data['criteria']
    if not isinstance(decisions, list) or not 1 <= len(decisions) <= 200:
        raise ValueError('Explicit decisions for all ACs are required')
    by_id = {}
    for item in decisions:
        exact_fields(item, ('id', 'decision', 'reason', 'evidence_refs'), 'AC decision')
        ident = item['id']
        if not isinstance(ident, str) or ident in by_id:
            raise ValueError('Invalid or duplicate AC decision ID')
        if item['decision'] not in ('accepted', 'rejected', 'pending'):
            raise ValueError('Invalid human decision')
        nonempty(item['reason'], 'decision reason')
        refs = item['evidence_refs']
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs) or len(refs) != len(set(refs)):
            raise ValueError('Invalid acceptance evidence references')
        if set(refs) - evidence_ids or (item['decision'] != 'pending' and not refs):
            raise ValueError('Accepted/rejected ACs require supplied hashed evidence files')
        by_id[ident] = item['decision']
    if set(by_id) != {item['id'] for item in bound['criteria']}:
        raise ValueError('AC decision coverage differs from bound material criteria')
    outcome = 'rejected' if 'rejected' in by_id.values() else 'pending' if 'pending' in by_id.values() else 'accepted'
    return {'attestation_status': 'valid_for_current_binding', 'business_acceptance': 'attested_' + outcome,
            'decision_by_ac': by_id, 'owner_claimant': owner, 'recorded_at': timestamp,
            'decision_reference': data['decision_reference'], 'evidence_file_count': len(evidence)}


def inspect(repo, workflow, criteria_path, attestation_path=None):
    bound = binding(repo, workflow, criteria_path)
    report = {'contract_version': 1, 'binding': bound, 'binding_digest': digest(bound),
              'attestation_status': 'not_supplied', 'business_acceptance': 'not_evaluated',
              'owner_identity_verification': 'not_verified', 'owner_authority_verification': 'not_verified',
              'resolution_status': 'not_established', 'publication_ready': False,
              'execution': 'not_run', 'created_paths': [], 'remote_actions': 'none',
              'limitations': ['Content binding detects changed inputs; it is not a signature or proof of human identity',
                              'Local evidence is supplied content; its authenticity and semantic business sufficiency are not verified',
                              'Coverage binds canonical AC IDs in current reports, not independently proven completeness of all business requirements',
                              'An attested decision does not authorize publishing, closing issues or changing workflow state']}
    if attestation_path is not None:
        report.update(attestation_checked(json_input(attestation_path), bound))
    # A second freshness check detects ordinary concurrent target/report changes.
    if binding(repo, workflow, criteria_path) != bound:
        raise ValueError('Acceptance binding changed during inspection')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--workflow', required=True)
    parser.add_argument('--criteria', required=True)
    parser.add_argument('--attestation')
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.repo, args.workflow, args.criteria, args.attestation), indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
