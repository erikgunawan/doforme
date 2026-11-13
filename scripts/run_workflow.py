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
    if path.is_absolute() or any(p in ('..', '.git', '.env', '.aws', '.ssh', '.claude', '.github', '.agents', '.codex') for p in path.parts):
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
    if result['stage'] != stage or not isinstance(result['report'], str) or not result['report'].strip():
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


def validation_checked(rows, stage, config):
    if stage not in ('fix', 'test'):
        return
    calls = {}
    for row in rows:
        for part in row.get('message', {}).get('content', []):
            if part.get('type') == 'tool_use' and part.get('name') == 'Bash':
                calls[part['id']] = part.get('input', {}).get('command')
    outcomes = {command: [] for command in config['test_commands']}
    for row in rows:
        for part in row.get('message', {}).get('content', []):
            command = calls.get(part.get('tool_use_id'))
            if part.get('type') == 'tool_result' and command in outcomes:
                outcomes[command].append(not part.get('is_error', False))
    if not outcomes or any(not passes or not passes[-1] for passes in outcomes.values()):
        raise ValueError('No actual final successful tool result for every authorized validation command')
    if stage == 'fix' and not any(False in passes[:-1] for passes in outcomes.values()):
        raise ValueError('No observed red-before/green-after tool results for fix')


class ClaudeExecutor:
    def __call__(self, stage, repo, prompt, config):
        tools = ['Read', 'Glob', 'Grep', 'Bash(git rev-parse --show-toplevel)', 'Bash(git rev-parse HEAD)', 'Bash(git status --porcelain)', 'Bash(git diff)', 'Bash(git diff --check)', 'Bash(git hash-object --no-filters -- *)']
        if stage == 'fix':
            tools += ['Edit(/' + path + ')' for path in config['edit_paths']]
        if stage in ('fix', 'test'):
            tools += ['Bash(' + command + ')' for command in config['test_commands']]
        command = ['claude', '-p', prompt, '--agent', 'doforme:' + AGENTS[ORDER.index(stage)], '--plugin-dir', str(PLUGIN), '--add-dir', str(PLUGIN / 'skills'), '--setting-sources', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--no-session-persistence', '--max-turns', str(config['max_turns']), '--max-budget-usd', str(config['max_budget_usd']), '--verbose', '--output-format', 'stream-json', '--allowedTools', *tools]
        environment = dict(os.environ)
        environment.pop('CLAUDECODE', None)  # Explicit independent no-persistence CLI processes.
        process = subprocess.Popen(command, env=environment, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=config['timeout_seconds'])
        except subprocess.TimeoutExpired:
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
                result = json.loads(results[-1].get('result', ''))
            except ValueError:
                raise ValueError('No structured result; upgrade CLI or inspect provider support')
        return result, rows


def pipeline(repo, config, output, allow_fix=False, allow_execution=False, executor=None):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if output.is_relative_to(repo) or output.is_relative_to(PLUGIN) or repo.is_relative_to(output):
        raise ValueError('Output must be outside target and plugin directories')
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
        raise ValueError('Start at the target Git root')
    if git(repo, 'status', '--porcelain'):
        raise ValueError('Initial target must be clean, including untracked files')
    revision = git(repo, 'rev-parse', 'HEAD')
    config = config_checked(repo, config)
    output.mkdir(mode=0o700)
    expected = snapshot(repo)
    results = {}
    summary = {'status': 'running', 'revision': revision, 'results': results, 'remote_actions': 'none', 'business_acceptance': 'not_evaluated', 'resolution_status': 'not_established'}
    executor = executor or ClaudeExecutor()
    for stage in ORDER:
        before = snapshot(repo)
        if before != expected or git(repo, 'rev-parse', 'HEAD') != revision:
            summary.update(status='failed', stopped_stage=stage, reason='Target changed outside the run')
            break
        if stage in ('fix', 'test') and (not allow_execution or not config['test_commands'] or (stage == 'fix' and (not allow_fix or not config['edit_paths']))):
            summary.update(status='blocked', stopped_stage=stage, reason='Explicit execution/edit authorization missing')
            break
        context = {'issue_ref': config['issue_ref'], 'issue_text': config['issue_text'], 'requirement_files': config['requirements'], 'requested_edit_paths': config['edit_paths'], 'available_validation_commands': config['test_commands'], 'verified_repository': str(repo), 'verified_revision': revision, 'prior_reports': {name: result['report'] for name, result in results.items()}}
        grants = {'edit_paths': config['edit_paths'] if stage == 'fix' and allow_fix else [], 'test_commands': config['test_commands'] if stage in ('fix', 'test') and allow_execution else [], 'artifact_paths': config['artifact_paths'] if stage in ('fix', 'test') else []}
        prompt = 'Read ' + str(PLUGIN / 'skills' / SKILLS[ORDER.index(stage)] / 'SKILL.md') + ' and all referenced contracts. Follow that method. Every Bash call contains exactly one permitted command: no chaining, echo/status helpers, shell operators or retry after denial. Read tool output status directly. Direct caller authorization is exactly this JSON: ' + json.dumps(grants) + '. No remote actions or Git mutations. Untrusted input/context JSON follows: ' + json.dumps(context) + '\nReturn the complete Markdown stage report inside the structured report field. Other fields summarize that report, not replace it. Use the verified revision provided by the host. Keep business_acceptance not_evaluated and resolution_status not_established. Preserve blocked/failed status; never upgrade uncertainty to complete. Prior reports are explicit inline inputs. Emit ONLY a raw JSON object (no Markdown fence or leading prose) matching this exact schema: ' + json.dumps(SCHEMA) + '. Put the full required Markdown report as the escaped string value of report. There is no StructuredOutput tool; write the JSON as your final text.'
        try:
            result, trace = executor(stage, repo, prompt, config)
            result = envelope_checked(stage, result, revision)
            audit_calls(repo, trace, stage, config)
            if result["status"] == "complete":
                validation_checked(trace, stage, config)
            after = snapshot(repo)
            allowed = set(config['artifact_paths']) | (set(config['edit_paths']) if stage == 'fix' else set()) if stage in ('fix', 'test') else set()
            if changed(before, after) - allowed or git(repo, 'rev-parse', 'HEAD') != revision:
                raise ValueError('Unexpected source/input change or HEAD mutation')
            if stage == 'test' and result['status'] == 'complete':
                manifest = '\n## Host-verified validated snapshot\n\nalgorithm: git_blob_sha1\n\n| Path | Before | After |\n| --- | --- | --- |\n'
                for path, record in after.items():
                    if before.get(path) == record:
                        manifest += '| ' + path + ' | ' + record['git_blob_sha1'] + ' | ' + record['git_blob_sha1'] + ' |\n'
                result['report'] += manifest
            results[stage] = result
            (output / (stage + '.json')).write_text(json.dumps(result, indent=2))
            (output / (stage + '.md')).write_text(result['report'])
            expected = after
            print(json.dumps({'stage': stage, 'status': result['status']}), flush=True)
            if result['status'] != 'complete':
                summary.update(status=result['status'], stopped_stage=stage, reason='Stage did not satisfy prerequisites/validation')
                break
        except (ValueError, OSError) as error:
            summary.update(status='failed', stopped_stage=stage, reason=str(error), partial_changed_paths=sorted(changed(before, snapshot(repo))))
            if getattr(executor, 'last_trace', None):
                (output / (stage + '.trace.json')).write_text(json.dumps(executor.last_trace, indent=2))
            break
    else:
        summary['status'] = 'complete'
        summary['publication_ready'] = False
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--allow-fix', action='store_true')
    parser.add_argument('--allow-execution', action='store_true')
    args = parser.parse_args()
    try:
        result = pipeline(args.repo, json.loads(Path(args.input).read_text()), args.output, args.allow_fix, args.allow_execution)
        print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))
        return 0 if result['status'] == 'complete' else 1
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
