"""Exact approved command execution for a host-marked native worker only."""
import json
import os
from pathlib import Path
import shlex
import uuid

from execution_runtime import model_environment, run_process
from repo_policy import SAFE_GIT_PREFIX, config_checked
from workflow_state import write_json

VALIDATION_TOOL = {'name': 'run', 'description': 'Run one host-approved command by its supplied command_index. '
        'Returns actual exit status and captured output; a nonzero test result is data, not tool failure.',
        'inputSchema': {'type': 'object', 'properties': {'command_index': {'type': 'integer', 'minimum': 0}},
                        'required': ['command_index'], 'additionalProperties': False}}


def commands_for(stage, config):
    from run_workflow import permitted_bash_calls
    commands = permitted_bash_calls(stage, config) if stage in ('fix', 'test', 'review', 'pr') else []
    if stage in ('review', 'pr'):
        commands += [shlex.join([*SAFE_GIT_PREFIX, 'hash-object', '--no-filters', '--', path]) for path in config['edit_paths']]
    return commands


def execute(policy, index):
    if type(index) is not int or not isinstance(policy, dict):
        raise ValueError('An exact reviewed command index is required')
    repo = Path(policy['repo']).resolve()
    config = config_checked(repo, policy['config'], allow_existing_artifacts=True)
    commands = commands_for(policy['stage'], config)
    if policy.get('commands') != commands or not 0 <= index < len(commands):
        raise ValueError('Command is outside the reviewed worker scope')
    receipts = Path(policy['receipts'])
    if (not receipts.is_dir() or any(p.is_symlink() for p in (receipts, *receipts.parents)) or
            receipts.stat().st_mode & 0o077 or receipts.is_relative_to(repo)):
        raise ValueError('Execution receipts require a private external directory')
    if (receipts / 'denied').exists():
        raise ValueError('A previous permission denial stopped this worker')
    if len(list(receipts.glob('execution-*.json'))) >= 100:
        raise ValueError('Worker command limit reached; no automatic retry')
    env = model_environment()
    for name in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'DOFORME_AGY_GUARD'):
        env.pop(name, None)
    result = run_process(shlex.split(commands[index]), cwd=repo, env=env,
                         timeout_seconds=config['timeout_seconds'], termination_grace=.1)
    output = result.stdout + ('\n' + result.stderr if result.stderr else '')
    record = {'receipt_id': str(uuid.uuid4()), 'command_index': index, 'command': commands[index],
              'exit_code': result.returncode, 'output': output[:100000],
              'output_truncated': len(output) > 100000}
    write_json(receipts / ('execution-' + record['receipt_id'] + '.json'), record)
    return record
