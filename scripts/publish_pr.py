"""Preview a content-bound draft PR; explicit publication never pushes code."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote

sys.dont_write_bytecode = True
from repo_policy import git
from run_workflow import PLUGIN, checkpoint_results_checked, policy_digest, snapshot
from workflow_state import Checkpoints, digest, write_json

CLOSING = re.compile(r'\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+'
                     r'(?:#\d+|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+|https://github\.com/[^\s]+/issues/\d+)', re.I)
NOTICE = ('\n\n---\nPrepared with doforme. Business acceptance: not evaluated. '
          'Issue resolution: not established. Human review and owner acceptance remain pending. '
          'This draft does not authorize merge or issue closure.\n')


class GitHub:
    def request(self, method, endpoint, payload=None):
        command = ['gh', 'api', '--hostname', 'github.com', '--method', method, endpoint]
        if payload is not None:
            command += ['--input', '-']
        result = subprocess.run(command, input=None if payload is None else json.dumps(payload),
                                text=True, capture_output=True, timeout=30)
        if result.returncode or len(result.stdout) > 20_000_000:
            raise ValueError('GitHub request failed or exceeded response limit; no automatic retry')
        return json.loads(result.stdout)


def text_input(path, maximum):
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)) or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('Proposal text must be an explicitly named bounded regular local file')
    text = path.read_text(encoding='utf-8').strip()
    if not text or '\x00' in text or CLOSING.search(text):
        raise ValueError('Empty/invalid proposal or automatic issue-closing reference')
    return text


def remote_tree(client, repository, sha):
    data = client.request('GET', f'repos/{repository}/git/trees/{sha}?recursive=1')
    if not isinstance(data, dict) or data.get('truncated') is not False or not isinstance(data.get('tree'), list):
        raise ValueError('Remote tree is incomplete or unavailable')
    result = {}
    for entry in data['tree']:
        if not isinstance(entry, dict):
            raise ValueError('Malformed remote tree entry')
        if entry.get('type') == 'tree':
            continue
        path = entry.get('path')
        if not isinstance(path, str) or path in result or entry.get('type') != 'blob' or entry.get('mode') not in ('100644', '100755'):
            raise ValueError('Remote tree requires unique regular-file paths')
        if not re.fullmatch(r'[0-9a-f]{40}', entry.get('sha', '')):
            raise ValueError('Unsupported remote blob identity')
        result[path] = {'sha': entry['sha'], 'mode': entry['mode']}
    if len(result) > 20000:
        raise ValueError('Remote tree exceeds supported file count')
    return result


def branch_name(repo, value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,199}', value):
        raise ValueError('Invalid explicit branch name')
    git(repo, 'check-ref-format', '--branch', value)
    return value


def tested_workspace(state):
    return {path: {'sha': info['git_blob_sha1'], 'mode': '100755' if info['mode'] & 0o111 else '100644'}
            for path, info in state['workspace'].items()}


def workflow_handoff(repo, workflow):
    """Separate publication handoff; never rebind normal status/resume freshness."""
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
        raise ValueError('Select the tested Git repository root')
    store = Checkpoints(workflow, resume=True)
    state = store.load()
    if state['repository'] != str(repo) or state['status'] != 'complete':
        raise ValueError('Publication requires the original complete workflow for this target')
    checkpoint_results_checked(store, state, state['revision'])
    if state['policy_digest'] != policy_digest() or state['workspace'] != snapshot(repo):
        raise ValueError('Tested content or policy changed; a new validation workflow is required')
    current = git(repo, 'rev-parse', 'HEAD')
    transition = {'tested_revision': state['revision'], 'current_revision': current,
                  'status': 'unchanged_tested_revision'}
    if current != state['revision']:
        if git(repo, 'status', '--porcelain'):
            raise ValueError('Content-identical commit handoff requires a clean committed checkout')
        git(repo, 'merge-base', '--is-ancestor', state['revision'], current)
        tree = {}
        for line in git(repo, 'ls-tree', '-r', '-z', current).split('\0'):
            if not line:
                continue
            metadata, path = line.split('\t', 1)
            mode, kind, sha = metadata.split()
            if kind != 'blob' or mode not in ('100644', '100755'):
                raise ValueError('Committed handoff requires regular file blobs')
            tree[path] = {'sha': sha, 'mode': mode}
        if tree != tested_workspace(state):
            raise ValueError('Committed tree differs from the exact tested content')
        transition.update(status='content_identical_commit_handoff', baseline_is_ancestor=True)
    return store, state, transition


def preview(repo, workflow, repository, head, base, title_file, body_file, client=None):
    repo = Path(repo).resolve()
    client = client or GitHub()
    if not isinstance(repository, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Select an explicit GitHub owner/repository')
    head, base = branch_name(repo, head), branch_name(repo, base)
    if head == base:
        raise ValueError('Head and base must be distinct existing branches')
    origin = git(repo, 'config', '--get', 'remote.origin.url')
    expected_origins = ('https://github.com/' + repository, 'git@github.com:' + repository)
    if origin.removesuffix('.git').lower() not in tuple(value.lower() for value in expected_origins):
        raise ValueError('Selected GitHub repository differs from target origin')
    store, state, transition = workflow_handoff(repo, workflow)
    config = json.loads(store.read_text('input.json'))
    if config['artifact_paths']:
        raise ValueError('Remove publication ambiguity: workflow temporary artifacts are unsupported for publishing')
    title, body = text_input(title_file, 1024), text_input(body_file, 60_000)
    if len(title) > 256 or '\n' in title or '\r' in title:
        raise ValueError('PR title must be a single line of at most 256 characters')
    body += NOTICE
    metadata = client.request('GET', f'repos/{repository}')
    canonical = metadata.get('full_name') if isinstance(metadata, dict) else None
    if not isinstance(canonical, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', canonical) or canonical.lower() != repository.lower():
        raise ValueError('Remote repository identity differs')
    repository = canonical
    refs = {}
    trees = {}
    for key, branch in (('head', head), ('base', base)):
        detail = client.request('GET', f'repos/{repository}/branches/{quote(branch, safe="")}')
        if not isinstance(detail, dict):
            raise ValueError('Malformed remote branch response')
        sha = detail.get('commit', {}).get('sha', '')
        tree_sha = detail.get('commit', {}).get('commit', {}).get('tree', {}).get('sha', '')
        if not re.fullmatch(r'[0-9a-f]{40}', sha) or not re.fullmatch(r'[0-9a-f]{40}', tree_sha):
            raise ValueError('Existing remote branch commit unavailable')
        refs[key] = sha
        trees[key] = remote_tree(client, repository, tree_sha)
    expected = tested_workspace(state)
    if trees['head'] != expected:
        raise ValueError('Remote head tree does not match the exact tested working content; no push is performed')
    comparison = client.request('GET', f'repos/{repository}/compare/{state["revision"]}...{refs["head"]}')
    if not isinstance(comparison, dict) or comparison.get('status') not in ('ahead', 'identical') or comparison.get('merge_base_commit', {}).get('sha') != state['revision']:
        raise ValueError('Remote head is not a descendant of the tested baseline')
    changed = {path for path in set(trees['head']) | set(trees['base']) if trees['head'].get(path) != trees['base'].get(path)}
    if not changed or changed - set(config['edit_paths']):
        raise ValueError('Remote branch diff is empty or extends beyond tested edit scope')
    query = f'repos/{repository}/pulls?state=open&head={quote(repository.split("/")[0] + ":" + head, safe="")}&base={quote(base, safe="")}'
    existing = client.request('GET', query)
    if not isinstance(existing, list) or existing:
        raise ValueError('An open PR already exists or duplicate check is unavailable')
    bound = {'contract_version': 1, 'repository': repository, 'head': head, 'base': base,
             'head_sha': refs['head'], 'base_sha': refs['base'], 'target_repository': str(repo),
             'tested_revision': state['revision'], 'workspace_digest': digest(state['workspace']),
             'checkpoint_digest': digest(state), 'title': title, 'body': body, 'draft': True,
             'changed_paths': sorted(changed), 'revision_transition': transition}
    _, final_state, final_transition = workflow_handoff(repo, workflow)
    if final_state != state or final_transition != transition:
        raise ValueError('Target or checkpoint changed during preview')
    return {'proposal_status': 'verified_draft_proposal', 'preview': bound, 'preview_digest': digest(bound),
            'publication_ready': False, 'remote_created': False, 'business_acceptance': 'not_evaluated',
            'resolution_status': 'not_established', 'remote_actions': 'read_only',
            'limitations': ['Preview is not publication authorization or proof of human review',
                            'Owner acceptance remains pending; tested source is not a business sign-off',
                            'GitHub branch movement is rechecked before POST and checked in its response; no atomic branch pin is available here']}


def receipt_path(path, repo, workflow):
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError('Receipt path must not contain symlinks')
    resolved = path.resolve()
    for root in (Path(repo).resolve(), Path(workflow).resolve(), PLUGIN):
        if resolved.is_relative_to(root):
            raise ValueError('Receipt must be outside target, workflow and plugin')
    if not path.parent.is_dir() or path.parent.stat().st_mode & 0o077:
        raise ValueError('Receipt parent must be an existing private directory (mode 700)')
    return path


def publish(repo, workflow, repository, head, base, title_file, body_file, expected_digest, receipt, client=None):
    if not isinstance(expected_digest, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_digest):
        raise ValueError('Explicit expected preview digest is required')
    client = client or GitHub()
    report = preview(repo, workflow, repository, head, base, title_file, body_file, client)
    if report['preview_digest'] != expected_digest:
        raise ValueError('Proposal/source/checkpoint/remote branch changed since caller review')
    bound = report['preview']
    repository = bound['repository']
    path = receipt_path(receipt, repo, workflow)
    attempted = {'status': 'attempting', 'preview_digest': expected_digest, 'repository': repository,
                 'head_sha': bound['head_sha'], 'base_sha': bound['base_sha'], 'remote_created': False}
    # Exclusive durable receipt is the deduplication boundary, including uncertain deliveries.
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(json.dumps(attempted, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    try:
        result = client.request('POST', f'repos/{repository}/pulls',
                                {'head': head, 'base': base, 'title': bound['title'], 'body': bound['body'],
                                 'draft': True, 'maintainer_can_modify': False})
        if not isinstance(result, dict):
            raise ValueError('Malformed publication response')
        url = result.get('html_url', '')
        number = result.get('number')
        if not isinstance(number, int) or isinstance(number, bool) or number < 1 or url != f'https://github.com/{repository}/pull/{number}':
            raise ValueError('Publication response does not identify the requested repository PR')
        raced = result.get('head', {}).get('sha') != bound['head_sha'] or result.get('base', {}).get('sha') != bound['base_sha']
        if result.get('draft') is not True:
            raise ValueError('Publication response did not establish a draft PR')
        receipt_data = {**attempted, 'status': 'created_needs_manual_review' if raced else 'draft_created',
                        'remote_created': True, 'url': url, 'number': number,
                        'content_binding': 'changed_during_creation' if raced else 'matched_at_creation',
                        'business_acceptance': 'not_evaluated', 'resolution_status': 'not_established',
                        'publication_ready': False, 'issue_closed': False}
        write_json(path, receipt_data)
        return receipt_data
    except (ValueError, OSError, subprocess.SubprocessError):
        write_json(path, {**attempted, 'status': 'uncertain', 'remote_created': 'unknown'})
        raise ValueError('PR delivery uncertain; inspect the repository and receipt, do not retry automatically') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('repo', 'workflow', 'repository', 'head', 'base', 'title-file', 'body-file'):
        parser.add_argument('--' + flag, required=True)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--expected-digest')
    parser.add_argument('--receipt')
    args = parser.parse_args()
    try:
        values = (args.repo, args.workflow, args.repository, args.head, args.base, args.title_file, args.body_file)
        if args.publish:
            if not args.expected_digest or not args.receipt:
                raise ValueError('--publish requires --expected-digest and --receipt')
            result = publish(*values, args.expected_digest, args.receipt)
        else:
            if args.expected_digest or args.receipt:
                raise ValueError('Publication flags require explicit --publish')
            result = preview(*values)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
