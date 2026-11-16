"""Explicitly enable doforme contributor hooks without replacing existing hooks."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def install(root):
    # Respect effective user/system hooks settings; the runtime Git policy normally
    # suppresses those settings and must not be used to inspect an existing hook.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    def run(*args):
        return subprocess.run(['git', '-c', 'core.fsmonitor=false', '--no-optional-locks', *args],
                              cwd=root, env=env, capture_output=True, text=True)
    selected = run('rev-parse', '--show-toplevel')
    if selected.returncode or Path(selected.stdout.strip()).resolve() != root.resolve():
        raise ValueError('Install hooks only at the doforme checkout root')
    existing = run('config', '--get', 'core.hooksPath')
    if existing.returncode not in (0, 1):
        raise ValueError('Cannot inspect effective hook configuration')
    setting = existing.stdout.strip()
    if existing.returncode == 0 and setting != '.githooks':
        raise ValueError('Existing hooksPath preserved; integrate the documentation check manually: ' + setting)
    if existing.returncode == 1:
        location = run('rev-parse', '--git-path', 'hooks/pre-commit')
        if location.returncode:
            raise ValueError('Cannot inspect existing default hook')
        hook = Path(location.stdout.strip())
        if not hook.is_absolute():
            hook = root / hook
        if hook.exists() or hook.is_symlink():
            raise ValueError('Existing pre-commit hook preserved; integrate the documentation check manually')
    helper = root / '.githooks/pre-commit'
    if any(path.is_symlink() for path in (helper, *helper.parents)) or not helper.is_file() or not os.access(helper, os.X_OK):
        raise ValueError('The tracked documentation hook must be a regular executable file')
    result = run('config', '--local', 'core.hooksPath', '.githooks')
    if result.returncode:
        raise ValueError('Cannot set local documentation hook: ' + result.stderr.strip())
    return 'Documentation auto-update enabled for this doforme checkout only'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', required=True)
    parser.parse_args()
    try:
        print(install(Path(__file__).resolve().parents[1]))
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
