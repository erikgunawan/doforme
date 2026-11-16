"""Read-only integration readiness; never activate workflows or send notifications."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
from init_repo import repository_root
from issue_intake import issue_packet
from repo_policy import safe_path
from requirement_sources import manifest_read, regular_bytes

PLUGIN = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = '.github/workflows/doforme-intake.yml'
VARIABLES = ('DOFORME_ENABLE_ANALYZE', 'DOFORME_CLAUDE_VERSION',
             'DOFORME_TRUSTED_REQUIREMENTS', 'DOFORME_NOTIFY_TELEGRAM')
SECRETS = ('ANTHROPIC_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')
MAX_REMOTE_BYTES = 1_000_000


def repository_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value) or any(part in ('.', '..') for part in value.split('/')):
        raise ValueError('Name one explicit GitHub repository as owner/name')
    return value


def workflow_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml', value):
        raise ValueError('Workflow must be one explicit .github/workflows YAML path')
    return value


def gh_read(repository, resource):
    """Fixed-host GET endpoints only. Never return credentials or raw CLI errors."""
    repository_name(repository)
    endpoints = {'workflows': 'actions/workflows?per_page=100',
                 'variables': 'actions/variables?per_page=100',
                 'secrets': 'actions/secrets?per_page=100'}
    if resource.startswith('content:'):
        suffix = 'contents/' + workflow_name(resource[len('content:'):])
    elif resource in endpoints:
        suffix = endpoints[resource]
    else:
        raise ValueError('Unsupported read-only integration resource')
    env = dict(os.environ)
    for name in ('GH_HOST', 'GH_REPO', 'GH_DEBUG', 'GH_FORCE_TTY'):
        env.pop(name, None)
    env['GH_PROMPT_DISABLED'] = '1'
    result = subprocess.run(['gh', 'api', '--hostname', 'github.com', '--method', 'GET',
                             'repos/' + repository + '/' + suffix], env=env,
                            capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('GitHub metadata read failed; account permission/access needs review')
    if len(result.stdout) > MAX_REMOTE_BYTES:
        raise ValueError('GitHub metadata exceeds inspection limit')
    data = json.loads(result.stdout.decode('utf-8'))
    if not isinstance(data, dict):
        raise ValueError('GitHub metadata response must be an object')
    return data


def listed(data, key):
    if not isinstance(data, dict):
        raise ValueError('GitHub listing must be an object')
    entries = data.get(key)
    total = data.get('total_count')
    if not isinstance(entries, list) or type(total) is not int or total != len(entries) or not 0 <= total <= 100:
        raise ValueError('GitHub listing is malformed or incomplete; no automatic pagination')
    return entries


def diagnose(repo, repository, event=None, requirements=(), recipient=None,
             workflow=DEFAULT_WORKFLOW, check_remote=False, reader=None):
    repo = repository_root(repo)
    repository = repository_name(repository)
    workflow = workflow_name(workflow)
    if recipient is not None and not re.fullmatch(r'-?[0-9]+|@[A-Za-z0-9_]{5,}', recipient):
        raise ValueError('Telegram recipient must be an explicitly supplied chat ID/name')
    checks = []
    missing = []

    def add(name, state, detail):
        checks.append({'id': name, 'state': state, 'detail': detail})

    template = regular_bytes(PLUGIN / 'integrations/github-issues.yml.example')
    template_hash = hashlib.sha256(template).hexdigest()
    add('template', 'configured', {'sha256': template_hash, 'automatic_activation': False,
                                  'review_basis': 'shipped example only; owner review still required'})
    active = repo / workflow
    if active.exists() or active.is_symlink():
        try:
            raw = regular_bytes(active)
            add('local_workflow', 'configured' if raw == template else 'blocked',
                {'path': workflow, 'matches_template': raw == template,
                 'sha256': hashlib.sha256(raw).hexdigest()})
        except (ValueError, OSError) as error:
            add('local_workflow', 'blocked', str(error))
    else:
        add('local_workflow', 'not_configured', {'path': workflow})
        missing.append('Operator-reviewed intake workflow in target .github/workflows')
    if event is None:
        add('issue_event', 'not_checked', 'No explicit event snapshot supplied')
        missing.append('Actual issue event/target selected by owner')
    else:
        try:
            packet = issue_packet(manifest_read(event), repository)
            state = 'configured' if packet['status'] == 'intake_ready' else 'blocked'
            add('issue_event', state, {'packet_status': packet['status'],
                                      'source_untrusted': True, 'live_event_verified': False})
        except (ValueError, OSError, KeyError, TypeError) as error:
            add('issue_event', 'blocked', str(error))
    names = []
    try:
        if len(requirements) > 16:
            raise ValueError('At most 16 trusted source paths can be inspected')
        for name in requirements:
            path = safe_path(repo, name)
            raw = regular_bytes(path)
            text = raw.decode('utf-8')
            if not text.strip() or '\x00' in text:
                raise ValueError('Trusted source must be nonempty UTF-8 text without NUL bytes')
            canonical = path.relative_to(repo).as_posix()
            if canonical in names:
                raise ValueError('Duplicate canonical trusted source')
            names.append(canonical)
        add('trusted_sources', 'configured' if names else 'not_checked',
            {'declared_paths': names, 'authority': 'unconfirmed', 'business_acceptance': 'not_evaluated'})
    except (ValueError, OSError) as error:
        add('trusted_sources', 'blocked', str(error))
    missing.append('Owner confirmation of source applicability and acceptance criteria')
    if recipient is None:
        missing.append('Explicit Telegram recipient and authorization for a live test send')
    add('telegram_recipient', 'configured' if recipient is not None else 'not_checked',
        {'explicitly_supplied': recipient is not None, 'matches_secret_value': 'not_checked'})
    remote = {'configuration': 'not_checked', 'github_intake': 'not_checked',
              'analysis': 'not_checked', 'telegram': 'not_checked'}
    if check_remote:
        read = reader or gh_read
        try:
            workflows = listed(read(repository, 'workflows'), 'workflows')
            variables = listed(read(repository, 'variables'), 'variables')
            secrets = listed(read(repository, 'secrets'), 'secrets')
            for item in workflows:
                if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not item['path'] or not isinstance(item.get('state'), str) or not item['state']:
                    raise ValueError('Malformed workflow metadata')
            values = {}
            for item in variables:
                if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not isinstance(item.get('value'), str):
                    raise ValueError('Malformed variable metadata')
                if item['name'] in VARIABLES:
                    if item['name'] in values:
                        raise ValueError('Duplicate integration variable')
                    values[item['name']] = item['value']
            secret_names = set()
            for item in secrets:
                if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not item['name'] or item['name'] in secret_names:
                    raise ValueError('Malformed/duplicate secret metadata')
                secret_names.add(item['name'])
            matching = [item for item in workflows if item['path'] == workflow]
            workflow_active = len(matching) == 1 and matching[0].get('state') == 'active'
            remote_workflow_matches = False
            if workflow_active:
                content = read(repository, 'content:' + workflow)
                if (content.get('type') != 'file' or content.get('path') != workflow or
                        content.get('encoding') != 'base64' or not isinstance(content.get('content'), str)):
                    raise ValueError('Remote workflow content unavailable')
                decoded = base64.b64decode(content['content'].replace('\n', '').replace('\r', '').encode(), validate=True)
                if len(decoded) > MAX_REMOTE_BYTES:
                    raise ValueError('Remote workflow content exceeds inspection limit')
                remote_workflow_matches = decoded == template
            valid_toggles = all(values.get(key, 'false') in ('true', 'false') for key in ('DOFORME_ENABLE_ANALYZE', 'DOFORME_NOTIFY_TELEGRAM'))
            if not valid_toggles:
                raise ValueError('Integration opt-in variables must be explicit true/false values')
            trusted_match = values.get('DOFORME_TRUSTED_REQUIREMENTS', '').splitlines() == names
            analysis = (workflow_active and remote_workflow_matches and values.get('DOFORME_ENABLE_ANALYZE') == 'true'
                        and bool(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', values.get('DOFORME_CLAUDE_VERSION', '')))
                        and 'ANTHROPIC_API_KEY' in secret_names and trusted_match)
            telegram = (workflow_active and remote_workflow_matches and values.get('DOFORME_NOTIFY_TELEGRAM') == 'true'
                        and {'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'} <= secret_names)
            remote.update(configuration='observed', github_intake='configured' if workflow_active and remote_workflow_matches else 'not_configured',
                          analysis='configured' if analysis else 'not_configured', telegram='configured' if telegram else 'not_configured')
            add('remote_configuration', 'configured', {'workflow_active': workflow_active,
                'workflow_matches_reviewed_template': remote_workflow_matches,
                'analysis_enabled': values.get('DOFORME_ENABLE_ANALYZE') == 'true',
                'cli_version_is_exact': bool(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', values.get('DOFORME_CLAUDE_VERSION', ''))),
                'trusted_paths_match_explicit_inputs': trusted_match,
                'telegram_enabled': values.get('DOFORME_NOTIFY_TELEGRAM') == 'true',
                'secret_names_present': {name: name in secret_names for name in SECRETS},
                'secret_values_read': False})
        except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
            remote['configuration'] = 'blocked'
            add('remote_configuration', 'blocked', 'Remote metadata incomplete/inaccessible/invalid; no secrets or workflow settings changed')
    else:
        add('remote_configuration', 'not_checked', 'Use --check-remote for explicit read-only GitHub metadata checks')
    add('github_intake_live', 'not_checked', 'No hosted issue intake event was executed or independently verified')
    add('analysis_live', 'not_checked', 'No hosted model call/dependency installation was run')
    add('telegram_delivery_live', 'not_checked', 'No API send, recipient ownership or delivery was verified')
    return {'contract_version': 1, 'repository': repository, 'target': str(repo),
            'activation': 'not_performed', 'remote_configuration': remote, 'checks': checks,
            'missing_inputs': missing, 'live_verification': 'not_checked', 'ready_to_activate': False,
            'business_acceptance': 'not_evaluated', 'resolution_status': 'not_established',
            'messages_sent': 0, 'workflow_dispatches': 0, 'settings_changed': False,
            'remote_actions': 'read_only_metadata' if check_remote else 'none',
            'limitations': ['Configured does not establish successful live execution or delivery',
                            'Repository-level metadata only; environment/organization secret applicability is not inferred',
                            'Secret names do not prove valid credentials or recipient binding',
                            'Owner must authorize actual activation, account/source scope and any send separately']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--event')
    parser.add_argument('--requirement', action='append', default=[])
    parser.add_argument('--telegram-recipient')
    parser.add_argument('--workflow', default=DEFAULT_WORKFLOW)
    parser.add_argument('--check-remote', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(diagnose(args.repo, args.repository, args.event, args.requirement,
                                  args.telegram_recipient, args.workflow, args.check_remote), indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
