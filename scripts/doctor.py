"""Read-only preflight for a fresh local workflow; no model or test execution."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

from check_plugin import check
from init_repo import REQUIREMENTS_DRAFT, repository_root
from repo_policy import config_checked, git, safe_path
from repo_profile import load
from run_workflow import PLUGIN, snapshot


def new_output_checked(repo, output):
    """Inspect the proposed fresh-run destination without creating it."""
    raw = Path(output).absolute()
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError('Output path must not contain symlinks')
    path = raw.resolve()
    if path.is_relative_to(repo) or path.is_relative_to(PLUGIN) or repo.is_relative_to(path):
        raise ValueError('Output must be outside target and plugin directories')
    if path.exists():
        raise ValueError('Fresh-run output must not exist; use status for an existing checkpoint')
    if not path.parent.is_dir():
        raise ValueError('Output parent must already be a directory')
    return str(path)


def requirement_sources_checked(repo, config):
    if not config['requirements']:
        raise ValueError('Supply actual requirement source files; no sources were declared')
    for name in config['requirements']:
        path = safe_path(repo, name)
        if not path.is_file() or path.stat().st_size > 1_000_000:
            raise ValueError('Requirement source must be a regular text file under 1 MB: ' + name)
        text = path.read_text(encoding='utf-8')
        if not text.strip():
            raise ValueError('Requirement source is empty: ' + name)
        if text.strip() == REQUIREMENTS_DRAFT.strip():
            raise ValueError('Unchanged generated requirement draft needs actual source content: ' + name)
    return 'Source files readable; authority, applicability, conflicts and AC coverage remain unevaluated'


def diagnose(repo, issue_path, profile_path=None, output=None):
    checks = []

    def inspect(name, action):
        try:
            detail = action()
            checks.append({'id': name, 'status': 'passed', 'detail': detail})
            return detail
        except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
            checks.append({'id': name, 'status': 'blocked', 'detail': str(error)})
            return None

    def skip(name, reason):
        checks.append({'id': name, 'status': 'not_checked', 'detail': reason})

    inspect('plugin_structure', lambda: (check(PLUGIN), 'Local plugin structure valid')[1])
    root = inspect('repository_root', lambda: str(repository_root(repo)))
    revision = None
    effective = None
    if root is None:
        for name in ('revision', 'clean_worktree', 'bounded_checkout', 'configuration',
                     'requirement_sources', 'edit_scope', 'test_commands', 'output_location'):
            skip(name, 'Selected repository root is unavailable')
    else:
        repo = Path(root)
        revision = inspect('revision', lambda: git(repo, 'rev-parse', '--quiet', '--verify', 'HEAD'))

        def clean():
            if git(repo, 'status', '--porcelain'):
                raise ValueError('Fresh workflow requires a clean checkout, including untracked inputs')
            return 'Clean tracked and untracked baseline'

        inspect('clean_worktree', clean)
        inspect('bounded_checkout', lambda: {'regular_files': len(snapshot(repo)),
                                           'limits': '20000 files / 100 MB; no symlinks or special files'})
        effective = inspect('configuration', lambda: config_checked(repo, load(repo, issue_path, profile_path)))
        # Return check summaries, not duplicated issue text or configuration content.
        if effective is not None:
            checks[-1]['detail'] = 'Explicit input/profile composition validated'
            inspect('requirement_sources', lambda: requirement_sources_checked(repo, effective))
            for name, key, missing in (
                ('edit_scope', 'edit_paths', 'Declare exact issue-specific edit paths before a full workflow'),
                ('test_commands', 'test_commands', 'Supply reviewed direct test commands before a full workflow'),
            ):
                if effective[key]:
                    checks.append({'id': name, 'status': 'passed', 'detail': {'declared_count': len(effective[key]),
                                                                                 'authorization': 'not_granted'}})
                else:
                    checks.append({'id': name, 'status': 'blocked', 'detail': missing})
        else:
            for name in ('requirement_sources', 'edit_scope', 'test_commands'):
                skip(name, 'Configuration is invalid')
        if output is None:
            skip('output_location', 'No destination supplied; fresh-run destination remains unchecked')
        else:
            inspect('output_location', lambda: new_output_checked(repo, output))

    def cli():
        executable = shutil.which('claude')
        if executable is None:
            raise ValueError('Claude CLI was not found on PATH; authentication/model access not checked')
        return 'Claude CLI found on PATH; version, authentication and model access not checked'

    inspect('claude_on_path', cli)
    blockers = [item['id'] for item in checks if item['status'] == 'blocked']
    return {'contract_version': 1, 'local_preflight': 'blocked' if blockers else 'passed',
            'repository': root, 'revision': revision, 'checks': checks, 'blocking_checks': blockers,
            'requirements_status': 'not_evaluated', 'business_acceptance': 'not_evaluated',
            'resolution_status': 'not_established', 'publication_ready': False,
            'execution': 'not_run', 'model_calls': 0, 'created_paths': [], 'remote_actions': 'none',
            'limitations': ['Point-in-time local checks only; workflow revalidates before execution',
                            'No authentication, command execution, semantic requirement or visual acceptance check',
                            'Passing does not authorize edits/tests, approve business requirements or establish resolution',
                            'No output directory or write-permission probe is created'],
            'next_steps': ['Address blocked checks using owner-reviewed changes',
                           'Provide actual source/AC confirmation for analyze and plan',
                           'Review scope and grant execution/mutation explicitly when starting the workflow']}


def main():
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--profile')
    parser.add_argument('--output')
    args = parser.parse_args()
    report = diagnose(args.repo, args.input, args.profile, args.output)
    print(json.dumps(report, indent=2))
    return 0 if report['local_preflight'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
