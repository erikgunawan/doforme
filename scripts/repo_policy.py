"""Shared local Git, path and run-configuration policy; no workflow execution."""
import math
import os
from pathlib import Path
import re
import shlex
import subprocess

SAFE_GIT_PREFIX = ('git', '-c', 'core.fsmonitor=false', '--no-optional-locks')


def git(repo, *args):
    if args and args[0] == 'diff':
        args = ('diff', '--no-ext-diff', '--no-textconv', *args[1:])
    return subprocess.check_output([*SAFE_GIT_PREFIX, *args], cwd=repo, env=git_environment(), text=True).strip()


def git_environment(source=None):
    environment = dict(os.environ if source is None else source)
    for key in list(environment):
        if key.startswith('GIT_'):
            environment.pop(key, None)
    environment.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.fsmonitor',
                       GIT_CONFIG_VALUE_0='false', GIT_OPTIONAL_LOCKS='0',
                       GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    return environment


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


def config_checked(repo, config, *, allow_existing_artifacts=False):
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
        canonical = []
        for name in config[key]:
            path = safe_path(repo, name)
            canonical.append(path.relative_to(repo).as_posix())
            if key == 'requirements' and not path.is_file():
                raise ValueError('Requirement source unavailable: ' + name)
            if key != 'requirements' and path.exists() and not path.is_file():
                raise ValueError('Scope must contain exact file paths, not directories')
            if key == 'artifact_paths' and path.exists() and not allow_existing_artifacts:
                raise ValueError('Artifact scope must name new temporary files, not existing source/input')
        if len(set(canonical)) != len(canonical):
            raise ValueError('Duplicate canonical scope paths: ' + key)
        config[key] = canonical
    if set(config['requirements']) & set(config['edit_paths'] + config['artifact_paths']):
        raise ValueError('Requirement sources must remain read-only')
    if set(config['edit_paths']) & set(config['artifact_paths']):
        raise ValueError('Edit scope and temporary artifacts must be distinct')
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

