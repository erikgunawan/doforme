"""Local sequential workflow adapter. No remote publication or Git mutations."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_state import Checkpoints, atomic_text, digest, write_json

PLUGIN = Path(__file__).resolve().parents[1]
ORDER = ('analyze', 'plan', 'fix', 'test', 'review', 'pr')
AGENTS = ('investigator', 'planner', 'fixer', 'tester', 'reviewer', 'pr-preparer')
SKILLS = ('bug-resolution', 'bug-planning', 'bug-fixing', 'bug-testing', 'bug-review', 'pr-preparation')
SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {
    'stage': {'enum': list(ORDER)},
    'status': {'enum': ['complete', 'blocked', 'failed']},
    'verdict': {'enum': ['valid_bug', 'not_a_bug', 'duplicate', 'needs_information', 'pass', 'changes_requested', 'blocked', 'not_applicable']},
    'requirements_status': {'enum': ['verified_for_scope', 'needs_information', 'conflict', 'not_applicable']},
    'technical_validation': {'enum': ['passed_scoped', 'failed', 'not_run']},
    'business_acceptance': {'enum': ['not_evaluated']},
    'resolution_status': {'enum': ['not_established']},
    'revision': {'type': 'string'},
    'report': {'type': 'string', 'minLength': 1},
}}
SCHEMA['required'] = list(SCHEMA['properties'])


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()


def safe_path(repo, name):
    if not isinstance(name, str) or not name or name.startswith('-'):
        raise ValueError('Invalid relative path')
    path = Path(name)
    if path.is_absolute() or any(p.startswith('.env') or p in ('..', '.git', '.aws', '.ssh', '.claude', '.github', '.agents', '.codex', '.npmrc', '.pypirc', 'credentials.json', '.credentials') for p in path.parts):
        raise ValueError('Protected or escaping path: ' + name)
    if re.search(r'[\x00-\x1f*?\[\]!]', name) or path.suffix in ('.pem', '.key'):
        raise ValueError('Ambiguous or secret path: ' + name)
    for parent in [repo / path, *(repo / path).parents]:
        if parent == repo.parent:
            break
        if parent.is_symlink():
            raise ValueError('Symlink path: ' + name)
    resolved = (repo / path).resolve()
    if not resolved.is_relative_to(repo):
        raise ValueError('Escaping path: ' + name)
    return resolved


def config_checked(repo, config):
    expected = {'issue_ref', 'issue_text', 'requirements', 'edit_paths', 'test_commands', 'artifact_paths', 'timeout_seconds', 'max_turns', 'max_budget_usd'}
    if set(config) - expected or not isinstance(config.get('issue_text'), str) or not config['issue_text'].strip():
        raise ValueError('Config requires issue_text and only documented keys')
    if not isinstance(config.get('issue_ref'), str) or not config['issue_ref'].strip():
        raise ValueError('Config requires issue_ref')
    config = dict(config)
    for key in ('requirements', 'edit_paths', 'test_commands', 'artifact_paths'):
        config.setdefault(key, [])
        if not isinstance(config[key], list) or any(not isinstance(x, str) for x in config[key]) or len(set(config[key])) != len(config[key]):
            raise ValueError('Invalid config list: ' + key)
    for key in ('requirements', 'edit_paths', 'artifact_paths'):
        for name in config[key]:
            path = safe_path(repo, name)
            if key == 'requirements' and not path.is_file():
                raise ValueError('Requirement source unavailable: ' + name)
            if key != 'requirements' and path.exists() and not path.is_file():
                raise ValueError('Scope must contain exact file paths, not directories')
    if set(config['requirements']) & set(config['edit_paths'] + config['artifact_paths']):
        raise ValueError('Requirement sources must remain read-only')
    for command in config['test_commands']:
        if not command.strip() or re.search(r'[;&|`$<>\n\r\x00]', command):
            raise ValueError('Unsafe compound test command')
        argv = shlex.split(command)
        executable = next((part for part in argv if '=' not in part), '')
        if not executable or Path(executable).name in ('sh', 'bash', 'zsh', 'curl', 'wget', 'sudo', 'git', 'gh', 'pip', 'pip3', 'npm', 'npx'):
            raise ValueError('Use a reviewed direct local runner, not shell/network/install wrappers')
    for key, default, low, high in [('timeout_seconds', 180, 10, 600), ('max_turns', 45, 1, 100), ('max_budget_usd', 1.0, .01, 10)]:
        config.setdefault(key, default)
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError('Invalid bounded option: ' + key)
    if not isinstance(config['max_turns'], int) or not isinstance(config['timeout_seconds'], int):
        raise ValueError('Timeout and turns must be integers')
    return config


def snapshot(repo):
    """Bounded full file scan, excluding Git metadata; fail on symlinks."""
    result = {}
    total = 0
    for directory, folders, files in os.walk(repo, followlinks=False):
        folders[:] = sorted(x for x in folders if x != '.git')
        for name in [*folders, *files]:
            if (Path(directory) / name).is_symlink():
                raise ValueError('Symlink in target; use an isolated regular-file checkout')
        for name in sorted(files):
            path = Path(directory) / name
            relative = str(path.relative_to(repo))
            if relative == '.git':
                continue
            size = path.stat().st_size
            total += size
            if len(result) >= 20000 or total > 100_000_000:
                raise ValueError('Target exceeds bounded snapshot size; use a smaller isolated checkout')
            raw = path.read_bytes()
            result[relative] = {'sha256': hashlib.sha256(raw).hexdigest(), 'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(), 'mode': path.stat().st_mode & 0o777}
    return result


def changed(before, after):
    return {p for p in set(before) | set(after) if before.get(p) != after.get(p)}


def envelope_checked(stage, result, revision):
    if not isinstance(result, dict) or set(result) != set(SCHEMA['required']):
        raise ValueError('Missing/unknown structured result fields')
    for key, rule in SCHEMA['properties'].items():
        if 'enum' in rule and result[key] not in rule['enum']:
            raise ValueError('Invalid result enum: ' + key)
    if result['stage'] != stage or not isinstance(result['report'], str) or not result['report'].strip() or len(result['report']) > 1_000_000:
        raise ValueError('Invalid stage/report')
    if result['revision'] != revision:
        raise ValueError('Result is not bound to the verified revision')
    if result['status'] == 'complete':
        if result['requirements_status'] != 'verified_for_scope':
            raise ValueError('Material requirements not verified')
        if stage == 'analyze' and result['verdict'] != 'valid_bug':
            raise ValueError('Analyze cannot advance a non-bug')
        if stage == 'review' and result['verdict'] != 'pass':
            raise ValueError('Review cannot advance without verdict pass')
        if stage in ('fix', 'test') and result['technical_validation'] != 'passed_scoped':
            raise ValueError('Scoped technical checks have not passed')
    return result


def audit_calls(repo, rows, stage, config):
    readonly = [('git', 'rev-parse', '--show-toplevel'), ('git', 'rev-parse', 'HEAD'), ('git', 'status', '--porcelain'), ('git', 'diff'), ('git', 'diff', '--check')]
    for row in rows:
        for item in row.get('message', {}).get('content', []):
            if item.get('type') != 'tool_use':
                continue
            name, data = item.get('name'), item.get('input', {})
            if name in ('StructuredOutput', 'structured_output'):
                continue
            if name in ('Edit', 'Write'):
                relative = str((repo / data.get('file_path', '')).resolve().relative_to(repo))
                if stage != 'fix' or relative not in config['edit_paths']:
                    raise ValueError('Unscoped edit tool call')
                safe_path(repo, relative)
            elif name == 'Bash':
                command = data.get('command', '')
                if re.search(r'[;&|`$<>\n\r]', command):
                    raise ValueError('Compound shell call rejected by audit')
                parts = tuple(shlex.split(command))
                hashes = parts[:4] == ('git', 'hash-object', '--no-filters', '--') and len(parts) > 4
                if hashes:
                    for path in parts[4:]:
                        safe_path(repo, path)
                validation = stage in ('fix', 'test') and command in config['test_commands']
                if not (parts in readonly or hashes or validation):
                    raise ValueError('Unscoped program call: ' + command)
            elif name in ('Read', 'Glob', 'Grep'):
                path = data.get('file_path') or data.get('path')
                if path:
                    resolved = (repo / path).resolve()
                    if not (resolved.is_relative_to(repo) or resolved.is_relative_to(PLUGIN / 'skills')):
                        raise ValueError('Read/search outside target or plugin skills')
                    if resolved.is_relative_to(repo):
                        relative = str(resolved.relative_to(repo))
                        metadata = relative == '.git/HEAD' or relative.startswith('.git/refs/')
                        if relative != '.' and not metadata:
                            safe_path(repo, relative)
            else:
                raise ValueError('Unexpected tool call: ' + str(name))


def validation_evidence(rows, config):
    calls = {}
    evidence = []
    for row in rows:
        for part in row.get('message', {}).get('content', []):
            if part.get('type') == 'tool_use' and part.get('name') == 'Bash':
                calls[part['id']] = part.get('input', {}).get('command')
            command = calls.get(part.get('tool_use_id'))
            if part.get('type') == 'tool_result' and command in config['test_commands']:
                error = part.get('is_error')
                output = part.get('content', '')
                if not isinstance(error, bool) or not isinstance(output, str):
                    raise ValueError('Validation tool result has no observed status/output')
                code = re.search(r'^Exit code ([0-9]+)', output)
                exit_code = int(code.group(1)) if code else 0 if not error else None
                environment_error = bool(re.search(r'ModuleNotFoundError|ImportError|command not found|No such file|timed out', output, re.I))
                assertion_failure = error and exit_code is not None and exit_code > 0 and not environment_error and bool(re.search(r'AssertionError|FAILED|\bFAIL\b|not ok|assertion', output, re.I))
                evidence.append({'command': command, 'exit_code': exit_code, 'success': not error,
                                 'assertion_failure': assertion_failure, 'output': output[:100000],
                                 'output_truncated': len(output) > 100000})
    return evidence


def validation_checked(rows, stage, config):
    if stage not in ('fix', 'test'):
        return []
    evidence = validation_evidence(rows, config)
    outcomes = {command: [] for command in config['test_commands']}
    for item in evidence:
        outcomes[item['command']].append(item)
    if not outcomes or any(not items or not items[-1]['success'] or items[-1]['exit_code'] != 0 for items in outcomes.values()):
        raise ValueError('No actual final successful tool result for every authorized validation command')
    if stage == 'fix' and not any(item['assertion_failure'] for items in outcomes.values() for item in items[:-1]):
        raise ValueError('No observed assertion red-before/green-after tool results for fix')
    return evidence


def parse_result_text(text):
    """Accept one complete JSON object, optionally after a short progress prefix."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate structured result key')
            result[key] = value
        return result
    if not isinstance(text, str):
        raise ValueError('Result text missing')
    text = text.strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4].strip()
    start = text.find('{')
    if start < 0 or start > 2000:
        raise ValueError('No complete structured result object')
    result, end = json.JSONDecoder(object_pairs_hook=unique).raw_decode(text, start)
    if text[end:].strip() or not isinstance(result, dict):
        raise ValueError('Extra or ambiguous content after structured result')
    return result


def model_environment(source=None):
    environment = dict(os.environ if source is None else source)
    for key in list(environment):
        if key == 'CLAUDECODE' or key.startswith(('GITHUB_', 'GH_', 'TELEGRAM_', 'ACTIONS_')):
            environment.pop(key, None)
    return environment


class ClaudeExecutor:
    def __call__(self, stage, repo, prompt, config):
        tools = ['Read', 'Glob', 'Grep', 'Bash(git rev-parse --show-toplevel)', 'Bash(git rev-parse HEAD)', 'Bash(git status --porcelain)', 'Bash(git diff)', 'Bash(git diff --check)', 'Bash(git hash-object --no-filters -- *)']
        if stage == 'fix':
            tools += ['Edit(/' + path + ')' for path in config['edit_paths']]
        if stage in ('fix', 'test'):
            tools += ['Bash(' + command + ')' for command in config['test_commands']]
        denials = ['Read(**/.env*)', 'Read(**/.aws/**)', 'Read(**/.ssh/**)', 'Read(**/*.pem)', 'Read(**/*.key)', 'Read(**/.npmrc)', 'Read(**/.pypirc)', 'Read(**/credentials.json)']
        command = ['claude', '-p', prompt, '--agent', 'doforme:' + AGENTS[ORDER.index(stage)], '--plugin-dir', str(PLUGIN), '--add-dir', str(PLUGIN / 'skills'), '--setting-sources', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--no-session-persistence', '--max-turns', str(config['max_turns']), '--max-budget-usd', str(config['max_budget_usd']), '--verbose', '--output-format', 'stream-json', '--settings', json.dumps({'permissions': {'deny': denials}}), '--allowedTools', *tools]
        environment = model_environment()
        process = subprocess.Popen(command, env=environment, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=config['timeout_seconds'])
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
            raise ValueError('Model stage timed out; inspect partial edits before retry')
        rows = []
        for line in stdout.splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
        self.last_trace = rows
        results = [row for row in rows if row.get('type') == 'result']
        if process.returncode or not results or results[-1].get('is_error') or results[-1].get('permission_denials'):
            raise ValueError('Model stage failed or permission denied; no automatic retry')
        result = results[-1].get('structured_output')
        if result is None:
            try:
                result = parse_result_text(results[-1].get('result', ''))
            except ValueError:
                raise ValueError('No structured result; upgrade CLI or inspect provider support')
        return result, rows



def graph_checked(graph=None):
    if graph is None:
        graph = json.loads((PLUGIN / 'skills/bug-resolution/references/workflow.json').read_text())
    if graph.get('contract_version') != 2 or graph.get('persistence') != 'host_checkpoint' or graph.get('automatic_transitions') is not False:
        raise ValueError('Unsupported workflow graph contract')
    if set(graph.get('nodes', {})) != set(ORDER):
        raise ValueError('Unexpected workflow stage set')
    for index, stage in enumerate(ORDER):
        node = graph['nodes'][stage]
        expected = [] if index == 0 else [ORDER[index - 1]]
        effect = 'mutation' if stage == 'fix' else 'execution' if stage == 'test' else 'read_only'
        if not node.get('implemented') or node.get('requires') != expected or node.get('effect') != effect:
            raise ValueError('Unsupported or bypassed workflow dependency/effect')
    return graph


def policy_digest():
    values = {}
    for folder in ('commands', 'agents', 'skills', 'scripts'):
        for path in sorted((PLUGIN / folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                values[str(path.relative_to(PLUGIN))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest(values)


def compact(state, fresh=None):
    if fresh is None:
        try:
            repo = Path(state['repository'])
            fresh = state['workspace'] == snapshot(repo) and state['revision'] == git(repo, 'rev-parse', 'HEAD') and state['policy_digest'] == policy_digest()
        except (ValueError, OSError, KeyError, subprocess.SubprocessError):
            fresh = False
    return {'status': state['status'], 'repository': state['repository'], 'revision': state['revision'],
            'stages': {key: value['status'] for key, value in state['results'].items()},
            'next_stage': next((stage for stage in ORDER if state['results'].get(stage, {}).get('status') != 'complete'), None),
            'fresh': fresh, 'reason': state.get('reason'), 'partial_changed_paths': state.get('partial_changed_paths', []),
            'requires_manual_recovery': state.get('requires_manual_recovery', False),
            'publication_ready': False, 'business_acceptance': 'not_evaluated', 'resolution_status': 'not_established', 'remote_actions': 'none'}


def status_checkpoint(repo, output):
    repo = Path(repo).resolve()
    store = Checkpoints(output, resume=True)
    state = store.load()
    if state.get('repository') != str(repo):
        raise ValueError('Checkpoint belongs to another repository')
    for stage, record in state.get('artifact_index', {}).items():
        if store.result(record['filename'], record['digest']) != state['results'].get(stage):
            raise ValueError('Checkpoint artifact changed')
    for record in state.get('validation_artifacts', {}).values():
        store.result(record['filename'], record['digest'])
    fresh = state.get('workspace') == snapshot(repo) and state.get('revision') == git(repo, 'rev-parse', 'HEAD') and state.get('policy_digest') == policy_digest()
    return compact(state, fresh)


def pipeline(repo, config, output, allow_fix=False, allow_execution=False, executor=None, resume=False, retry=False):
    repo, output = Path(repo).resolve(), Path(output).absolute()
    if output.resolve().is_relative_to(repo) or output.resolve().is_relative_to(PLUGIN) or repo.is_relative_to(output.resolve()):
        raise ValueError('Output must be outside target and plugin directories')
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
        raise ValueError('Start at the target Git root')
    graph_checked()
    config = config_checked(repo, config)
    revision = git(repo, 'rev-parse', 'HEAD')
    if not resume and git(repo, 'status', '--porcelain'):
        raise ValueError('Initial target must be clean, including untracked files')
    grants = {'allow_fix': allow_fix, 'allow_execution': allow_execution}
    store = Checkpoints(output, resume=resume)
    with store.locked():
        if resume:
            state = store.load()
            if state.get('repository') != str(repo) or state.get('revision') != revision:
                raise ValueError('Stale repository/revision checkpoint')
            if state.get('config_digest') != digest(config) or state.get('policy_digest') != policy_digest() or state.get('grants') != grants:
                raise ValueError('Config, plugin policy, or direct authorization changed; start a new run')
            if digest(json.loads((store.root / 'input.json').read_text())) != state.get('config_digest'):
                raise ValueError('Saved config content changed')
            if state.get('workspace') != snapshot(repo):
                raise ValueError('Target content changed since checkpoint; no automatic resume')
            if state.get('requires_manual_recovery'):
                raise ValueError('Partial edits require manual recovery/review before a new run')
            results = state.get('results', {})
            if set(results) != set(ORDER[:len(results)]) or set(state.get('artifact_index', {})) != set(results):
                raise ValueError('Noncontiguous or missing prerequisite artifacts')
            incomplete = False
            for stage in ORDER[:len(results)]:
                record = state['artifact_index'][stage]
                actual = store.result(record['filename'], record['digest'])
                if actual != results[stage]:
                    raise ValueError('Checkpoint result changed')
                envelope_checked(stage, actual, revision)
                if incomplete:
                    raise ValueError('Checkpoint advances past a non-complete predecessor')
                if stage in ('fix', 'test') and actual['status'] == 'complete':
                    evidence_record = state.get('validation_artifacts', {}).get(stage)
                    if not evidence_record:
                        raise ValueError('Validation evidence artifact missing')
                    store.result(evidence_record['filename'], evidence_record['digest'])
                incomplete = actual['status'] != 'complete'
            if state['status'] == 'complete' or (state['status'] in ('blocked', 'failed', 'running') and not retry):
                return state
        else:
            state = {'state_version': 1, 'repository': str(repo), 'revision': revision,
                     'config_digest': digest(config), 'policy_digest': policy_digest(), 'grants': grants,
                     'workspace': snapshot(repo), 'artifact_index': {}, 'validation_artifacts': {}, 'attempt_counts': {}, 'results': {},
                     'status': 'running', 'remote_actions': 'none', 'business_acceptance': 'not_evaluated',
                     'resolution_status': 'not_established', 'publication_ready': False, 'host_persisted': True}
            write_json(store.root / 'input.json', config)
            store.save(state)
        executor = executor or ClaudeExecutor()
        results = state['results']
        for stage in ORDER:
            if results.get(stage, {}).get('status') == 'complete':
                continue
            before = snapshot(repo)
            if before != state['workspace'] or git(repo, 'rev-parse', 'HEAD') != revision or state['policy_digest'] != policy_digest():
                state.update(status='failed', stopped_stage=stage, reason='Target or plugin policy changed outside the run')
                break
            if stage in ('fix', 'test') and (not allow_execution or not config['test_commands'] or (stage == 'fix' and (not allow_fix or not config['edit_paths']))):
                state.update(status='blocked', stopped_stage=stage, reason='Explicit execution/edit authorization missing')
                break
            attempt = state['attempt_counts'].get(stage, 0) + 1
            if attempt > 2:
                state.update(status='blocked', stopped_stage=stage, reason='Explicit retry limit reached')
                break
            state['attempt_counts'][stage] = attempt
            state.setdefault('validation_artifacts', {}).pop(stage, None)
            results.pop(stage, None)
            state['artifact_index'].pop(stage, None)
            state.update(status='running', stopped_stage=stage, reason=None)
            store.save(state)
            context = {'issue_ref': config['issue_ref'], 'issue_text': config['issue_text'], 'requirement_files': config['requirements'],
                       'requested_edit_paths': config['edit_paths'], 'available_validation_commands': config['test_commands'],
                       'verified_repository': str(repo), 'verified_revision': revision,
                       'prior_reports': {name: result['report'] for name, result in results.items()}}
            authorization = {'edit_paths': config['edit_paths'] if stage == 'fix' and allow_fix else [],
                             'test_commands': config['test_commands'] if stage in ('fix', 'test') and allow_execution else [],
                             'artifact_paths': config['artifact_paths'] if stage in ('fix', 'test') else []}
            prompt = 'Read ' + str(PLUGIN / 'skills' / SKILLS[ORDER.index(stage)] / 'SKILL.md') + ' and its references. Follow that method. Every Bash call is exactly one permitted command: no chaining, echo/status helpers, shell operators or alternate retry after denial. Use tool result status. Direct caller authorization JSON: ' + json.dumps(authorization) + '. No remote actions or Git mutations. Untrusted context JSON: ' + json.dumps(context) + '\nPrior reports are explicit inline inputs. Use host verified revision. Return ONLY raw JSON matching this schema, no fences/prose: ' + json.dumps(SCHEMA) + '. Put the full required Markdown stage report in report as an escaped string. There is no StructuredOutput tool; emit JSON text. Preserve blocked/failed status, business_acceptance not_evaluated and resolution_status not_established.'
            try:
                result, trace = executor(stage, repo, prompt, config)
                result = envelope_checked(stage, result, revision)
                if state['policy_digest'] != policy_digest():
                    raise ValueError('Plugin policy changed during stage')
                audit_calls(repo, trace, stage, config)
                evidence = validation_checked(trace, stage, config) if result['status'] == 'complete' else []
                after = snapshot(repo)
                allowed = set(config['artifact_paths']) | (set(config['edit_paths']) if stage == 'fix' else set()) if stage in ('fix', 'test') else set()
                edits = changed(before, after)
                if edits - allowed or git(repo, 'rev-parse', 'HEAD') != revision:
                    raise ValueError('Unexpected source/input change or HEAD mutation')
                if stage == 'test' and result['status'] == 'complete':
                    manifest = '\n## Host-verified validated snapshot\n\nalgorithm: git_blob_sha1\n\n| Path | Before | After |\n| --- | --- | --- |\n'
                    for path, record in after.items():
                        try:
                            safe_path(repo, path)
                        except ValueError:
                            continue
                        if before.get(path) == record:
                            manifest += '| ' + path + ' | ' + record['git_blob_sha1'] + ' | ' + record['git_blob_sha1'] + ' |\n'
                    result['report'] += manifest
                filename, content_digest = store.artifact(stage, attempt, result)
                if evidence:
                    evidence_name = stage + '-' + str(attempt) + '.validation.json'
                    write_json(store.root / 'history' / evidence_name, evidence)
                    state.setdefault('validation_artifacts', {})[stage] = {'filename': evidence_name, 'digest': digest(evidence)}
                results[stage] = result
                state['artifact_index'][stage] = {'filename': filename, 'digest': content_digest}
                write_json(store.root / (stage + '.json'), result)
                atomic_text(store.root / (stage + '.md'), result['report'])
                state['workspace'] = after
                print(json.dumps({'stage': stage, 'status': result['status']}), flush=True)
                if result['status'] != 'complete':
                    state.update(status=result['status'], reason='Stage did not satisfy prerequisites/validation',
                                 partial_changed_paths=sorted(edits), requires_manual_recovery=bool(edits))
                    break
                store.save(state)
            except (ValueError, OSError) as error:
                try:
                    partial = sorted(changed(before, snapshot(repo)))
                except (ValueError, OSError):
                    partial = ['unreadable or symlinked target; inspect manually']
                state.update(status='failed', stopped_stage=stage, reason=str(error), partial_changed_paths=partial,
                             requires_manual_recovery=bool(partial))
                if getattr(executor, 'last_trace', None):
                    write_json(store.root / (stage + '.trace.json'), executor.last_trace)
                break
        else:
            state.update(status='complete', reason=None, publication_ready=False)
        store.save(state)
        write_json(store.root / 'summary.json', compact(state))
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--input')
    parser.add_argument('--output', required=True)
    parser.add_argument('--allow-fix', action='store_true')
    parser.add_argument('--allow-execution', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--retry', action='store_true')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        if args.status:
            print(json.dumps(status_checkpoint(args.repo, args.output), indent=2))
            return 0
        if not args.input:
            raise ValueError('--input is required for execution/resume')
        if args.retry and not args.resume:
            raise ValueError('--retry requires --resume')
        result = pipeline(args.repo, json.loads(Path(args.input).read_text()), args.output, args.allow_fix, args.allow_execution, resume=args.resume, retry=args.retry)
        print(json.dumps(compact(result), indent=2))
        return 0 if result['status'] == 'complete' else 1
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
