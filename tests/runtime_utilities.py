"""Opt-in real-Claude acceptance checks on disposable repositories only."""
import argparse
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from init_repo import initialize
from repo_policy import git, git_environment
from repo_profile import PROFILE_PATH, REQUIREMENTS_PATH, read_json
from run_workflow import changed, model_environment, parse_result_text, snapshot
from workflow_state import write_json

CASES = ('init_inspect', 'init_write', 'doctor_pass', 'doctor_blocked')


def private_text(path, content):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(content)


def prepare(base, case):
    repo = base / 'target'
    repo.mkdir(mode=0o700)
    for command in (('init', '-q'),):
        git(repo, *command)
    (repo / 'source.py').write_text('original fixture source\n')
    (repo / 'package.json').write_text(json.dumps({'scripts': {'test': 'touch UNAUTHORIZED_MARKER'}}))
    (repo / 'test_probe.py').write_text("from pathlib import Path\nPath('UNAUTHORIZED_MARKER').touch()\n")
    arguments = ['python3', str(ROOT / 'scripts/init_repo.py'), '--repo', str(repo)]
    prompt = '/doforme:init' + (' --write' if case == 'init_write' else ' --inspect')
    if case == 'init_write':
        arguments.append('--write')
    if case.startswith('doctor_'):
        initialize(repo, write=True)
        if case == 'doctor_pass':
            (repo / REQUIREMENTS_PATH).write_text('Synthetic supplied business excerpt. Authority is not evaluated by doctor.\n')
        issue = base / 'issue.json'
        issue_data = {'issue_ref': 'SMOKE-1', 'issue_text': 'Synthetic preflight input',
                      'edit_paths': ['source.py'], 'test_commands': ['python3 test_probe.py']}
        private_text(issue, json.dumps(issue_data))
        arguments = ['python3', str(ROOT / 'scripts/doctor.py'), '--repo', str(repo),
                     '--input', str(issue), '--profile', PROFILE_PATH, '--output', str(base / 'new-output')]
        prompt = '/doforme:doctor ' + shlex.join(arguments[4:])
    git(repo, 'add', '.')
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'synthetic acceptance baseline'], cwd=repo,
                   env=git_environment(), capture_output=True, text=True, check=True)
    return repo, prompt, arguments


def helper_result(rows, expected):
    """Require successful model completion and observed exact helper invocation."""
    results = [row for row in rows if row.get('type') == 'result']
    if not results or results[-1].get('is_error') or results[-1].get('permission_denials'):
        raise ValueError('Model failed or a permission denial occurred; no retry')
    calls, outputs = [], {}
    for row in rows:
        content = row.get('message', {}).get('content', [])
        for block in content if isinstance(content, list) else []:
            if block.get('type') == 'tool_use':
                if block.get('name') == 'Bash':
                    if shlex.split(block['input']['command']) != expected:
                        raise ValueError('Unexpected helper command or Python options')
                    calls.append(block['id'])
                elif block.get('name') != 'Read':
                    raise ValueError('Unexpected tool: ' + str(block.get('name')))
            elif block.get('type') == 'tool_result':
                outputs[block['tool_use_id']] = block
    if len(calls) != 1 or calls[0] not in outputs:
        raise ValueError('Expected exactly one observed helper call and result')
    result = outputs[calls[0]]
    content = result.get('content', '')
    if isinstance(content, list):
        content = '\n'.join(block.get('text', '') for block in content if block.get('type') == 'text')
    report = parse_result_text(content)
    expected_error = report.get('local_preflight') == 'blocked'
    if bool(result.get('is_error')) != expected_error:
        raise ValueError('Helper exit status and reported result disagree')
    return report


def verify(case, repo, before, revision, report):
    after = snapshot(repo)
    if git(repo, 'rev-parse', 'HEAD') != revision:
        raise ValueError('Fixture HEAD changed')
    expected = {PROFILE_PATH, REQUIREMENTS_PATH} if case == 'init_write' else set()
    if changed(before, after) != expected or (repo / 'UNAUTHORIZED_MARKER').exists():
        raise ValueError('Unexpected fixture changes or package/test execution')
    if (repo.parent / 'new-output').exists():
        raise ValueError('Doctor created output')
    if case.startswith('init_'):
        wanted = 'draft_created' if case == 'init_write' else 'inspection_only'
        if report.get('status') != wanted or set(report.get('created_paths', [])) != expected:
            raise ValueError('Unexpected onboarding outcome')
        if report.get('ready_for_fix') is not False or report.get('execution') != 'not_run':
            raise ValueError('Onboarding claimed readiness/execution')
        if case == 'init_write':
            if read_json(repo / PROFILE_PATH)['test_commands'] or 'UNCONFIRMED' not in (repo / REQUIREMENTS_PATH).read_text():
                raise ValueError('Generated defaults inferred test or business approval')
    else:
        wanted = 'passed' if case == 'doctor_pass' else 'blocked'
        if report.get('local_preflight') != wanted or report.get('model_calls') != 0:
            raise ValueError('Unexpected doctor outcome')
        if case == 'doctor_blocked' and 'requirement_sources' not in report.get('blocking_checks', []):
            raise ValueError('Unconfirmed draft did not block')
    if report.get('business_acceptance') != 'not_evaluated' or report.get('remote_actions') != 'none':
        raise ValueError('Unexpected business acceptance or remote action claim')
    return {'outcome': wanted, 'changed_paths': sorted(expected), 'head_unchanged': True,
            'observed_helper_calls': 1, 'permission_denials': 0}


def run_live(output):
    raw = Path(output).absolute()
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError('Output must not contain symlinks')
    output = raw.resolve()
    if output.is_relative_to(ROOT) or ROOT.is_relative_to(output):
        raise ValueError('Acceptance output must be outside the plugin checkout')
    output.mkdir(mode=0o700)  # Never reuse or erase an existing run.
    summary = {'status': 'running', 'cases': {}, 'remote_actions': 'none',
               'business_acceptance': 'not_evaluated', 'six_stage_workflow': 'not_run'}
    write_json(output / 'summary.json', summary)
    for case in CASES:
        base = output / case
        base.mkdir(mode=0o700)
        repo, prompt, arguments = prepare(base, case)
        before, revision = snapshot(repo), git(repo, 'rev-parse', 'HEAD')
        write_json(base / 'before.json', {'files': before, 'revision': revision})
        command = ['claude', '-p', prompt, '--plugin-dir', str(ROOT), '--add-dir', str(ROOT / 'skills'),
                   '--setting-sources', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                   '--no-session-persistence', '--max-turns', '12', '--max-budget-usd', '1',
                   '--verbose', '--output-format', 'stream-json', '--tools', 'Read,Bash',
                   '--allowedTools', 'Read', 'Bash(' + shlex.join(arguments) + ')']
        # Normal permissions; no broad Bash, bypass flag or retry after denial.
        stdout_path, stderr_path = base / 'trace.jsonl', base / 'stderr.txt'
        private_text(stdout_path, '')
        private_text(stderr_path, '')
        try:
            with stdout_path.open('w') as stdout, stderr_path.open('w') as stderr:
                process = subprocess.Popen(command, cwd=repo, env=model_environment(), stdout=stdout,
                                           stderr=stderr, start_new_session=True)
                try:
                    code = process.wait(timeout=180)
                except (subprocess.TimeoutExpired, KeyboardInterrupt):
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    raise ValueError('Acceptance stopped or timed out; no automatic retry')
            if code:
                raise ValueError('Claude CLI failed; inspect the private trace/stderr')
            rows = [json.loads(line) for line in stdout_path.read_text().splitlines() if line.strip()]
            report = helper_result(rows, arguments)
            record = verify(case, repo, before, revision, report)
            write_json(base / 'helper-report.json', report)
            summary['cases'][case] = {'status': 'passed', **record}
        except (ValueError, OSError, KeyError, TypeError) as error:
            summary['cases'][case] = {'status': 'failed', 'reason': str(error)}
            summary['status'] = 'failed'
            write_json(output / 'summary.json', summary)
            return summary  # Stop the suite, never relax permissions or retry.
        write_json(output / 'summary.json', summary)
    summary['status'] = 'passed'
    write_json(output / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if not args.live:
        print(json.dumps({'status': 'not_run', 'cases': CASES, 'model_calls': 0,
                          'note': 'Use --live explicitly; up to four calls, $1 cap and 180s timeout each'}))
        return 0
    try:
        summary = run_live(args.output)
        print(json.dumps(summary, indent=2))
        return 0 if summary['status'] == 'passed' else 1
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
