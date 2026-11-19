"""Guided local proposals and issue-addressed runs. Preview first; no remote writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from init_repo import inspection, repository_root
from repo_policy import config_checked, git, safe_path
from repo_profile import LIMITS, PROFILE_PATH, REQUIREMENTS_PATH, compose, read_json
from run_workflow import (PLUGIN, ORDER, compact, pipeline, policy_digest, snapshot,
                          status_checkpoint, checkpoint_results_checked, advance_reason)
from workflow_state import Checkpoints, atomic_text, digest, write_json


def proposal_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate proposal field: ' + key)
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


def checked_text(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 100_000:
        raise ValueError('Expected a regular text source under 100 KB')
    return path.read_text(encoding='utf-8')


def no_symlinks(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Storage path must not contain symlinks')
    return path


def storage(repo, root=None):
    root = no_symlinks(root or Path.home() / '.local/state/doforme')
    for target in (repo, PLUGIN):
        if root.resolve().is_relative_to(target) or target.is_relative_to(root.resolve()):
            raise ValueError('Report storage must be outside project and plugin')
    return root / hashlib.sha256(str(repo).encode()).hexdigest()[:24]


def github_repo(repo):
    remote = git(repo, 'remote', 'get-url', 'origin')
    found = re.fullmatch(r'(?:git@github\.com:|https://github\.com/)([\w.-]+/[\w.-]+?)(?:\.git)?', remote)
    if not found:
        raise ValueError('Use a local issue file or configure an unambiguous GitHub origin')
    return found.group(1)


def issue_source(repo, selector):
    if not isinstance(selector, str) or not selector or len(selector) > 300:
        raise ValueError('Select an issue ID, exact local file, #number, or GitHub issue URL')
    if re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*-\d+', selector):
        folder = safe_path(repo, 'docs/bugs')
        matches = sorted(p for p in folder.glob(selector + '*.md')
                         if re.match(re.escape(selector) + r'(?:[-_.]|$)', p.name))
        if len(matches) != 1:
            raise ValueError('Issue ID must match exactly one docs/bugs file; choose its exact path')
        path = safe_path(repo, matches[0].relative_to(repo).as_posix())
    elif re.fullmatch(r'#[1-9][0-9]*', selector) or selector.startswith('https://github.com/'):
        origin = github_repo(repo)
        if selector.startswith('#'):
            number = selector[1:]
        else:
            found = re.fullmatch(r'https://github\.com/([\w.-]+/[\w.-]+)/issues/([1-9][0-9]*)', selector)
            if not found or found.group(1).lower() != origin.lower():
                raise ValueError('GitHub issue must belong to this checkout origin')
            number = found.group(2)
        # Fixed GitHub GET; no shell, issue creation, comments, or notification.
        result = subprocess.run(['gh', 'api', '--hostname', 'github.com',
                                 'repos/' + origin + '/issues/' + number],
                                capture_output=True, text=True, timeout=20, env=os.environ.copy())
        if result.returncode or len(result.stdout) > 200_000:
            raise ValueError('Cannot read GitHub issue; check access or supply a local issue file')
        data = json.loads(result.stdout)
        if 'pull_request' in data or data.get('number') != int(number):
            raise ValueError('The selected item is not the expected GitHub issue')
        text = str(data.get('title', '')) + '\n\n' + str(data.get('body') or '')
        if len(text) > 100_000:
            raise ValueError('Issue exceeds 100 KB')
        url = 'https://github.com/' + origin + '/issues/' + number
        return {'identity': url, 'text': text, 'local_path': None, 'untrusted': True}
    else:
        path = safe_path(repo, selector)
    return {'identity': path.relative_to(repo).as_posix(), 'text': checked_text(path),
            'local_path': path.relative_to(repo).as_posix(), 'untrusted': True}


def discover(repo):
    report = inspection(repo)
    issues = []
    folder = safe_path(repo, 'docs/bugs')
    for p in sorted(folder.glob('*.md'))[:100]:
        if p.is_file() and not p.is_symlink():
            issues.append(p.relative_to(repo).as_posix())
    sources = []
    for name in ('docs/rules', 'docs/requirements'):
        for p in sorted(safe_path(repo, name).glob('*.md'))[:100]:
            if p.is_file() and not p.is_symlink():
                sources.append(p.relative_to(repo).as_posix())
    candidates = []
    for path, command in [('tests/run-node.js', 'node tests/run-node.js')]:
        if safe_path(repo, path).is_file():
            candidates.append({'command': command, 'review_required': True})
    return {'status': 'inspection_only', 'repository': str(repo), 'onboarding': report,
            'issue_candidates': issues, 'requirement_candidates': sources,
            'test_candidates': candidates, 'next_action': 'Review sources and test code, then preview setup',
            'created_paths': [], 'execution': 'not_run'}


def fingerprints(repo, requirements):
    return {name: hashlib.sha256(checked_text(safe_path(repo, name)).encode()).hexdigest()
            for name in requirements}


def setup(repo, data, confirm=None):
    if not isinstance(data, dict) or set(data) != {'requirements_text', 'test_commands'}:
        raise ValueError('Setup needs only requirements_text and reviewed test_commands')
    text = data['requirements_text']
    if not isinstance(text, str) or not text.strip() or len(text) > 100_000:
        raise ValueError('Supply bounded actual requirement excerpts; do not invent confirmation')
    profile_path = safe_path(repo, PROFILE_PATH)
    before = {name: checked_text(safe_path(repo, name)) if safe_path(repo, name).exists() else None
              for name in (PROFILE_PATH, REQUIREMENTS_PATH)}
    profile = read_json(profile_path) if profile_path.exists() else {
        'profile_version': 1, 'requirements': [REQUIREMENTS_PATH], 'artifact_paths': [], **LIMITS}
    profile['test_commands'] = data['test_commands']
    profile['requirements'] = list(dict.fromkeys([*profile.get('requirements', []), REQUIREMENTS_PATH]))
    # Validate exact commands without requiring the not-yet-created requirement file.
    if set(profile) - {'profile_version', 'requirements', 'test_commands', 'artifact_paths', *LIMITS}:
        raise ValueError('Existing profile needs manual review; unknown fields preserved on disk')
    config_checked(repo, {'issue_ref': 'setup', 'issue_text': 'Structural validation only',
                         **{k: v for k, v in profile.items() if k not in ('profile_version', 'requirements')},
                         'requirements': []})
    if type(profile.get('profile_version')) is not int or profile.get('profile_version') != 1:
        raise ValueError('Unsupported existing profile version')
    for name in profile['requirements']:
        safe_path(repo, name)
    proposal = {'action': 'setup', 'repository': str(repo), 'revision': git(repo, 'rev-parse', 'HEAD'),
                'before': before, 'profile': profile, 'requirements_text': text,
                'writes': [PROFILE_PATH, REQUIREMENTS_PATH], 'execution': 'not_run',
                'business_acceptance': 'not_evaluated'}
    proposal['digest'] = digest(proposal)
    if confirm is None:
        return proposal
    if confirm != proposal['digest']:
        raise ValueError('Setup changed since preview; review the new proposal')
    parent = safe_path(repo, '.doforme')
    parent.mkdir(mode=0o700, exist_ok=True)
    # No repository scripts, source mutation, Git writes, or model calls.
    atomic_text(safe_path(repo, REQUIREMENTS_PATH), text.rstrip() + '\n')
    write_json(profile_path, profile)
    return {'status': 'setup_saved', 'written_paths': proposal['writes'],
            'next_action': 'Review and commit setup files before starting a clean-tree run',
            'ready_for_fix': False, 'execution': 'not_run', 'business_acceptance': 'not_evaluated'}


def locator(repo, issue, root=None):
    source = issue_source(repo, issue)
    key = hashlib.sha256(source['identity'].encode()).hexdigest()[:24]
    return source, storage(repo, root) / key


def prepare(repo, issue, data, confirm=None, root=None, new=False):
    source, base_folder = locator(repo, issue, root)
    no_symlinks(base_folder)
    active_path = base_folder / 'active.json'
    previous = read_json(active_path) if active_path.exists() else None
    if previous and not new:
        raise ValueError('This issue already has saved reports; use show, or explicitly request a new run')
    if new and any(p.exists() for p in base_folder.glob('session-*/run/run.lock')):
        raise ValueError('An issue run is locked; ensure it has stopped before preparing a new run')
    number = 1 + len(list(base_folder.glob('session-*')))
    folder = base_folder / ('session-' + str(number))
    if not isinstance(data, dict) or set(data) - {'edit_paths', 'test_commands', 'artifact_paths', 'requirements', *LIMITS}:
        raise ValueError('Unknown preparation field; issue contents cannot grant permission')
    base = {'issue_ref': source['identity'], 'issue_text': source['text'], **data}
    profile_path = safe_path(repo, PROFILE_PATH)
    profile = read_json(profile_path) if profile_path.is_file() else None
    config = compose(repo, profile, base) if profile else config_checked(repo, base)
    protected = {PROFILE_PATH, REQUIREMENTS_PATH, source['local_path']}
    for name in config['edit_paths'] + config['artifact_paths']:
        if name in protected or any(part.startswith('.') for part in Path(name).parts):
            raise ValueError('Issue inputs and hidden configuration cannot be edit/artifact scope')
    proposal = {'action': 'prepare', 'repository': str(repo), 'revision': git(repo, 'rev-parse', 'HEAD'),
                'workspace_digest': digest(snapshot(repo)), 'policy_digest': policy_digest(), 'config': config,
                'source_hashes': fingerprints(repo, config['requirements']),
                'profile_digest': digest(profile) if profile else None,
                'folder': str(folder), 'previous_active': previous, 'execution': 'not_run'}
    proposal['digest'] = digest(proposal)
    if confirm is None:
        return proposal
    if confirm != proposal['digest']:
        raise ValueError('Issue, source, profile, or scope changed since preview; review again')
    base_folder.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    index = Checkpoints(base_folder, resume=base_folder.exists())
    with index.locked():
        current = read_json(active_path) if active_path.exists() else None
        if current != previous:
            raise ValueError('Active run changed; preview preparation again')
        store = Checkpoints(folder)
        write_json(store.root / 'session.json', proposal)
        write_json(active_path, {'session': folder.name})
    return {'status': 'prepared', 'folder': str(folder), 'config': config,
            'next_action': 'Run analyze; reports will be saved automatically'}


def session(repo, issue, root=None):
    source, base_folder = locator(repo, issue, root)
    no_symlinks(base_folder)
    active = read_json(base_folder / 'active.json')
    if set(active) != {'session'} or not re.fullmatch(r'session-[1-9][0-9]{0,5}', str(active['session'])):
        raise ValueError('Invalid active session pointer')
    folder = base_folder / active['session']
    no_symlinks(folder)
    Checkpoints(folder, resume=True)
    saved = read_json(folder / 'session.json')
    copy = dict(saved)
    expected = copy.pop('digest', None)
    if digest(copy) != expected or saved.get('repository') != str(repo) or saved.get('folder') != str(folder):
        raise ValueError('Session identity/content changed; do not trust the saved reports')
    if source['text'] != saved['config']['issue_text']:
        raise ValueError('Issue contents changed; prepare a fresh run after reviewing the change')
    if saved['source_hashes'] != fingerprints(repo, saved['config']['requirements']):
        raise ValueError('Requirement source changed; prepare a fresh run')
    profile_path = safe_path(repo, PROFILE_PATH)
    current_profile = digest(read_json(profile_path)) if profile_path.is_file() else None
    if saved['profile_digest'] != current_profile:
        raise ValueError('Repository profile changed; prepare a fresh run')
    if saved['policy_digest'] != policy_digest():
        raise ValueError('Plugin changed; prepare a fresh run')
    return folder, saved


def show(repo, issue, root=None):
    _, base_folder = locator(repo, issue, root)
    if not (base_folder / 'active.json').exists():
        return {'status': 'not_prepared', 'next_action': '/doforme:analyze ' + issue,
                'execution': 'not_run', 'created_paths': []}
    folder, saved = session(repo, issue, root)
    run = folder / 'run'
    if not run.exists():
        return {'status': 'prepared', 'folder': str(folder), 'config': saved['config'], 'next_action': 'Run analyze'}
    result = status_checkpoint(repo, run)
    return {'status': 'saved_run', 'folder': str(folder), 'summary': result,
            'reports': {name: str(run / (name + '.md')) for name in ORDER if (run / (name + '.md')).is_file()}}


def scope(repo, issue, data, confirm=None, root=None):
    """Bind the reviewed plan's concrete scope before the first source mutation."""
    folder, saved = session(repo, issue, root)
    if not isinstance(data, dict) or set(data) != {'edit_paths', 'test_commands', 'artifact_paths'}:
        raise ValueError('Review exact edit_paths, test_commands, and artifact_paths')
    store = Checkpoints(folder / 'run', resume=True)
    state = store.load()
    current = status_checkpoint(repo, store.root)
    if not current['fresh'] or state['status'] != 'paused' or set(state['results']) != {'analyze', 'plan'}:
        raise ValueError('Review scope only after a fresh paused analysis and plan, before any fix')
    if any(advance_reason(name, value) for name, value in state['results'].items()):
        raise ValueError('Analysis/plan gates have not passed')
    config = config_checked(repo, {**saved['config'], **data})
    for name in config['edit_paths'] + config['artifact_paths']:
        if name == saved['config']['issue_ref'] or any(p.startswith('.') for p in Path(name).parts):
            raise ValueError('Issue inputs and hidden configuration cannot be edit scope')
    if not config['edit_paths'] or not config['test_commands']:
        raise ValueError('Exact planned files and reviewed test commands are required')
    proposal = {'action': 'scope', 'config': config, 'repository': str(repo),
                'checkpoint_digest': digest(state), 'workspace_digest': digest(snapshot(repo)),
                'plan_digest': state['artifact_index']['plan']['digest'],
                'session_digest': saved['digest'], 'execution': 'not_run',
                'authorization': 'Fix and independent Test for these exact paths/commands only'}
    proposal['digest'] = digest(proposal)
    if confirm is None:
        return proposal
    if confirm != proposal['digest']:
        raise ValueError('Scope or state changed after preview; review again')
    with store.locked():
        latest = store.load()
        if digest(latest) != proposal['checkpoint_digest']:
            raise ValueError('Checkpoint changed during scope review')
        saved['config'] = config
        saved.pop('digest')
        saved['digest'] = digest(saved)
        latest['config_digest'] = digest(config)
        latest['grants'] = {'allow_fix': True, 'allow_execution': True}
        latest['guided_approval'] = {'proposal_digest': confirm, 'plan_digest': proposal['plan_digest'],
                                    'identity': 'caller_attested_not_authenticated'}
        # A partial I/O failure leaves a mismatch which normal readers reject.
        write_json(store.root / 'input.json', config)
        write_json(folder / 'session.json', saved)
        store.save(latest)
    return {'status': 'scope_saved', 'config': config, 'execution': 'not_run',
            'next_action': '/doforme:fix ' + issue}


def run(repo, issue, stage, confirm=None, root=None, retry=False, executor=None):
    if stage not in (*ORDER, 'endtoend'):
        raise ValueError('Unknown stage')
    _, base_folder = locator(repo, issue, root)
    if not (base_folder / 'active.json').exists():
        return {'status': 'needs_step', 'next_action': '/doforme:analyze ' + issue,
                'execution': 'not_run', 'created_paths': []}
    folder, saved = session(repo, issue, root)
    config, output = saved['config'], folder / 'run'
    state = None
    if output.exists():
        state = Checkpoints(output, resume=True).load()
        # This verifies workspace, revision, policy, and report/evidence digests.
        current = status_checkpoint(repo, output)
        if not current.get('fresh'):
            raise ValueError('Run is stale; inspect status before preparing a fresh run')
        results = state['results']
        if stage != 'endtoend':
            if stage in results and results[stage].get('status') == 'complete':
                return show(repo, issue, root)
            for prior in ORDER[:ORDER.index(stage)]:
                if prior not in results or advance_reason(prior, results[prior]):
                    return {'status': 'needs_step', 'next_action': '/doforme:' + prior + ' ' + issue,
                            'message': 'Complete the prerequisite first; no model or test was run'}
        if state['status'] in ('blocked', 'failed', 'running') and not retry:
            return {'status': 'needs_retry_review', 'summary': current,
                    'next_action': 'Read the stop reason; explicit retry is required', 'execution': 'not_run'}
    elif stage not in ('analyze', 'endtoend'):
        return {'status': 'needs_step', 'next_action': '/doforme:analyze ' + issue, 'execution': 'not_run'}
    elif saved['revision'] != git(repo, 'rev-parse', 'HEAD') or saved['workspace_digest'] != digest(snapshot(repo)):
        raise ValueError('Checkout changed since preparation; review a fresh run')
    read_only_first = (stage == 'endtoend' and (not state or 'plan' not in state['results'])
                       and (not config['edit_paths'] or not config['test_commands']))
    needs_mutation = stage in ('fix', 'test', 'endtoend') and not read_only_first
    grants = state['grants'] if state else {'allow_fix': False, 'allow_execution': False}
    proposal = {'action': 'run', 'stage': stage, 'issue': saved['config']['issue_ref'],
                'repository': str(repo), 'revision': git(repo, 'rev-parse', 'HEAD'),
                'workspace_digest': digest(snapshot(repo)), 'session_digest': saved['digest'],
                'checkpoint_digest': digest(state) if state else None,
                'config': config, 'output': str(output), 'retry': retry,
                'allow_fix': grants['allow_fix'] or needs_mutation,
                'allow_execution': grants['allow_execution'] or needs_mutation,
                'model_calls': 'up to six' if stage == 'endtoend' else 'one',
                'stop_after': 'plan' if read_only_first else None if stage == 'endtoend' else stage,
                'publication': 'none', 'business_acceptance': 'not_evaluated'}
    proposal['digest'] = digest(proposal)
    if confirm is None:
        return proposal
    if confirm != proposal['digest']:
        raise ValueError('Run scope/state changed after preview; review the current proposal')
    if needs_mutation and (not config['edit_paths'] or not config['test_commands']):
        return {'status': 'needs_scope', 'execution': 'not_run',
                'next_action': 'Review a fresh preparation with exact file paths and test commands'}
    if state and grants != {'allow_fix': proposal['allow_fix'], 'allow_execution': proposal['allow_execution']}:
        # Consent upgrade is allowed only after a verified, paused, read-only plan.
        store = Checkpoints(output, resume=True)
        with store.locked():
            latest = store.load()
            if digest(latest) != proposal['checkpoint_digest'] or latest['status'] != 'paused' or set(latest['results']) != {'analyze', 'plan'}:
                raise ValueError('Scope approval can only upgrade a paused, completed analysis and plan')
            checkpoint_results_checked(store, latest, latest['revision'])
            if any(advance_reason(name, value) for name, value in latest['results'].items()):
                raise ValueError('Read-only prerequisites do not permit scope approval')
            latest['grants'] = {'allow_fix': proposal['allow_fix'], 'allow_execution': proposal['allow_execution']}
            latest['guided_approval'] = {'proposal_digest': confirm, 'identity': 'caller_attested_not_authenticated'}
            store.save(latest)
    result = pipeline(repo, config, output, allow_fix=proposal['allow_fix'],
                      allow_execution=proposal['allow_execution'], executor=executor,
                      resume=state is not None, retry=retry,
                      stop_after=proposal['stop_after'])
    return {'status': result['status'], 'summary': compact(result),
            'reports': {name: str(output / (name + '.md')) for name in result['results']},
            'folder': str(folder)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'setup', 'prepare', 'show', 'scope', 'run'))
    parser.add_argument('--repo', required=True)
    parser.add_argument('--issue')
    parser.add_argument('--data-json')
    parser.add_argument('--confirm')
    parser.add_argument('--stage', choices=(*ORDER, 'endtoend'))
    parser.add_argument('--storage')
    parser.add_argument('--retry', action='store_true')
    parser.add_argument('--new', action='store_true')
    args = parser.parse_args()
    try:
        repo = repository_root(args.repo)
        if args.data_json and len(args.data_json) > 150_000:
            raise ValueError('Proposal JSON exceeds size limit')
        data = proposal_json(args.data_json) if args.data_json else {}
        if args.action == 'inspect':
            result = discover(repo)
        elif args.action == 'setup':
            result = setup(repo, data, args.confirm)
        else:
            if not args.issue:
                raise ValueError('Choose an issue first; inspect lists local candidates')
            if args.action == 'prepare':
                result = prepare(repo, args.issue, data, args.confirm, args.storage, args.new)
            elif args.action == 'scope':
                result = scope(repo, args.issue, data, args.confirm, args.storage)
            elif args.action == 'show':
                result = show(repo, args.issue, args.storage)
            else:
                result = run(repo, args.issue, args.stage, args.confirm, args.storage, args.retry)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'needs_attention', 'message': str(error),
                          'next_action': 'Explain the concrete missing step; do not widen permission or retry silently'}))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
