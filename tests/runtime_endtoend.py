"""Opt-in acceptance of the actual /doforme:endtoend slash command."""
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
import run_workflow as WF
from workflow_state import Checkpoints, write_json
from runtime_workflow import prepare, command_spellings, EDIT_PATHS, TEST_COMMAND
from runtime_utilities import private_text


def utility_spellings(arguments):
    spellings = command_spellings(arguments)
    for quote in ("'", '"'):
        parts = []
        for index, value in enumerate(arguments):
            is_path = index == 1 or index > 0 and arguments[index - 1] in ('--repo', '--input', '--profile', '--output')
            if is_path:
                value = ("'" + value.replace("'", "'\\''") + "'") if quote == "'" else (
                    '"' + ''.join('\\' + char if char in '\\"$`' else char for char in value) + '"')
            else:
                value = shlex.quote(value)
            parts.append(value)
        spellings.append(' '.join(parts))
    return list(dict.fromkeys(spellings))


def decode_output(text):
    if isinstance(text, list):
        text = '\n'.join(item.get('text', '') for item in text if item.get('type') == 'text')
    text = text.strip()
    if text.startswith('Exit code 1\n'):
        text = text[len('Exit code 1\n'):].strip()
    objects = []
    decoder = json.JSONDecoder()
    while text:
        value, end = decoder.raw_decode(text)
        objects.append(value)
        text = text[end:].strip()
    if not objects or not isinstance(objects[-1], dict) or 'stages' not in objects[-1]:
        raise ValueError('No observed workflow summary in helper output')
    for event in objects[:-1]:
        if not isinstance(event, dict) or set(event) != {'stage', 'status'}:
            raise ValueError('Ambiguous helper progress output')
    return objects[-1]


def observed_summary(rows, command, preview):
    results = [row for row in rows if row.get('type') == 'result']
    if not results or results[-1].get('is_error') or results[-1].get('permission_denials'):
        raise ValueError('Outer model failed or permission denied; no retry')
    calls, outputs, previews = [], {}, 0
    for row in rows:
        content = row.get('message', {}).get('content', [])
        for block in content if isinstance(content, list) else []:
            if block.get('type') == 'tool_use':
                if block.get('name') == 'Bash':
                    argv = shlex.split(block.get('input', {}).get('command', ''))
                    if argv == command:
                        calls.append(block['id'])
                    elif argv == preview:
                        previews += 1
                    else:
                        raise ValueError('Unexpected utility helper arguments')
                elif block.get('name') != 'Read':
                    raise ValueError('Unexpected outer tool: ' + str(block.get('name')))
            elif block.get('type') == 'tool_result':
                outputs[block['tool_use_id']] = block
    if len(calls) != 1 or previews > 1 or calls[0] not in outputs:
        raise ValueError('Require one workflow invocation and at most one config preview')
    result = outputs[calls[0]]
    summary = decode_output(result.get('content', ''))
    if bool(result.get('is_error')) != (summary['status'] != 'complete'):
        raise ValueError('Helper exit and summary disagree')
    return summary


def run_case(base, case):
    repo, issue, _ = prepare(base, confirmed=case != 'unconfirmed')
    checkpoint = base / 'checkpoint'
    before, revision = WF.snapshot(repo), WF.git(repo, 'rev-parse', 'HEAD')
    write_json(base / 'before.json', {'files': before, 'revision': revision})
    command = ['python3', str(ROOT / 'scripts/run_workflow.py'), '--repo', str(repo),
               '--input', str(issue), '--output', str(checkpoint), '--profile', '.doforme/repository.json']
    authorized = case != 'no_execution_grant'
    if authorized:
        command += ['--allow-fix', '--allow-execution']
    preview = ['python3', str(ROOT / 'scripts/run_workflow.py'), '--repo', str(repo),
               '--input', str(issue), '--profile', '.doforme/repository.json', '--inspect-config']
    authority = ('Authorize edits ONLY pagination.py and test_pagination.py; authorize execution ONLY '
                 + TEST_COMMAND + '; artifacts none.') if authorized else 'No edit or execution authorization is given.'
    prompt = ('/doforme:endtoend --input ' + shlex.quote(str(issue)) + ' --profile .doforme/repository.json --output '
              + shlex.quote(str(checkpoint)) + '; authorize output creation. ' + authority
              + ' Use this exact one workflow invocation without reordering arguments: ' + shlex.join(command)
              + '. If previewing config, use exactly: ' + shlex.join(preview)
              + '. Invoke Bash with timeout 600000; do not use background/polling helpers or retry after denial.')
    spellings = utility_spellings(command) + utility_spellings(preview)
    argv = ['claude', '-p', prompt, '--plugin-dir', str(ROOT), '--add-dir', str(ROOT / 'skills'),
            '--setting-sources', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
            '--no-session-persistence', '--max-turns', '16', '--max-budget-usd', '1',
            '--verbose', '--output-format', 'stream-json', '--tools', 'Read,Bash',
            '--allowedTools', 'Read', *['Bash(' + spelling + ')' for spelling in spellings]]
    stdout_path, stderr_path = base / 'outer.trace.jsonl', base / 'outer.stderr.txt'
    private_text(stdout_path, '')
    private_text(stderr_path, '')
    with stdout_path.open('w') as stdout, stderr_path.open('w') as stderr:
        process = subprocess.Popen(argv, cwd=repo, env=WF.model_environment(), stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=900)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise ValueError('Outer session stopped/timed out; inspect retained fixture and processes')
    if code:
        raise ValueError('Outer Claude session failed')
    rows = [json.loads(line) for line in stdout_path.read_text().splitlines() if line.strip()]
    summary = observed_summary(rows, command, preview)
    state = Checkpoints(checkpoint, resume=True).load()
    if summary != WF.status_checkpoint(repo, checkpoint):
        raise ValueError('Observed helper summary and verified checkpoint disagree')
    expected_stages = list(WF.ORDER) if case == 'confirmed' else ['analyze'] if case == 'unconfirmed' else ['analyze', 'plan']
    if list(state['results']) != expected_stages:
        raise ValueError('Unexpected stage advancement')
    wanted = 'complete' if case == 'confirmed' else 'blocked'
    if summary['status'] != wanted or not summary['fresh']:
        raise ValueError('Unexpected outcome or freshness')
    edits = WF.changed(before, WF.snapshot(repo))
    if edits != (EDIT_PATHS if case == 'confirmed' else set()) or WF.git(repo, 'rev-parse', 'HEAD') != revision:
        raise ValueError('Unexpected target scope or HEAD mutation')
    if case == 'unconfirmed' and state['results']['analyze']['requirements_status'] != 'needs_information':
        raise ValueError('Unconfirmed requirement gate was bypassed')
    write_json(base / 'after.json', WF.snapshot(repo))
    return {'status': 'passed', 'workflow_status': wanted, 'stages': expected_stages,
            'changed_paths': sorted(edits), 'fresh': True, 'permission_denials': 0, 'head_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if not args.live:
        print(json.dumps({'status': 'not_run', 'model_calls': 0, 'cases': ['unconfirmed', 'no_execution_grant', 'confirmed']}))
        return 0
    output = Path(args.output).absolute()
    try:
        if any(path.is_symlink() for path in (output, *output.parents)) or output.resolve().is_relative_to(ROOT):
            raise ValueError('Use a new external, non-symlink acceptance output')
        output.mkdir(mode=0o700)
        summary = {'status': 'running', 'cases': {}, 'policy_digest': WF.policy_digest(), 'remote_actions': 'none'}
        write_json(output / 'summary.json', summary)
        for case in ('unconfirmed', 'no_execution_grant', 'confirmed'):
            base = output / case
            base.mkdir(mode=0o700)
            try:
                summary['cases'][case] = run_case(base, case)
            except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
                summary['cases'][case] = {'status': 'failed', 'reason': str(error)}
                summary['status'] = 'failed'
                write_json(output / 'summary.json', summary)
                print(json.dumps(summary, indent=2))
                return 1
            write_json(output / 'summary.json', summary)
        summary['status'] = 'passed'
        write_json(output / 'summary.json', summary)
        print(json.dumps(summary, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
