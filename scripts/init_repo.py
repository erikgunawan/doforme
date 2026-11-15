"""Inspect repository onboarding; create two draft files only with --write."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from repo_policy import SAFE_GIT_PREFIX, git_environment, safe_path
from repo_profile import LIMITS, PROFILE_PATH, REQUIREMENTS_PATH, profile_checked, read_json

REQUIREMENTS_DRAFT = '''# Requirement sources and acceptance criteria — UNCONFIRMED DRAFT

This generated document is a template, not a business requirement or approval.
Do not claim verified_for_scope until an owner supplies the actual evidence.

## Source registry

| Source ID | Origin / exact locator | Version / updated time | Supplied content | Owner applicability confirmation |
| --- | --- | --- | --- | --- |
| S1 | unknown | unknown | not supplied | unconfirmed |

## Requirements and acceptance criteria

| Requirement ID | Explicit statement / scope / exceptions | Source reference | AC condition and observable outcome | Confirmation reference |
| --- | --- | --- | --- | --- |
| R1 | unknown | S1 (unverified) | unknown | unconfirmed |

## Conflicts and missing information

- Real business source content and scope confirmation are missing.
- Acceptance criteria require explicit owner confirmation.
- A document/Jira/Figma link alone is not readable verified content.
- Visual Figma requirements need appropriate evidence; no visual pass is implied.

Business acceptance: not_evaluated. Resolution: not_established.
'''
MARKERS = {
    'python': ('pyproject.toml', 'requirements.txt', 'pytest.ini', 'setup.cfg', 'tox.ini'),
    'node': ('package.json',), 'go': ('go.mod',), 'rust': ('Cargo.toml',),
    'jvm': ('pom.xml', 'build.gradle', 'build.gradle.kts'),
}


def repository_root(repo):
    raw = Path(repo).absolute()
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError('Repository path must not contain symlinks')
    repo = raw.resolve()
    if not repo.is_dir():
        raise ValueError('Repository directory is unavailable')
    result = subprocess.run([*SAFE_GIT_PREFIX, 'rev-parse', '--show-toplevel'], cwd=repo,
                            env=git_environment(), capture_output=True, text=True)
    if result.returncode or Path(result.stdout.strip()).resolve() != repo:
        raise ValueError('Run init at the selected Git repository root; no Git init or parent expansion is performed')
    return repo


def inspection(repo):
    repo = repository_root(repo)
    def query(*args):
        return subprocess.check_output([*SAFE_GIT_PREFIX, *args], cwd=repo, env=git_environment(), text=True).strip()
    markers = []
    scripts = []
    notes = []
    for kind, paths in MARKERS.items():
        for name in paths:
            path = safe_path(repo, name)
            if not path.is_file():
                continue
            markers.append({'kind': kind, 'path': name, 'basis': 'file presence only'})
            if name == 'package.json':
                try:
                    manifest = read_json(path)
                    declared = manifest.get('scripts', {})
                    if not isinstance(declared, dict) or len(declared) > 200:
                        raise ValueError('Invalid/bounded package script metadata')
                    scripts = [name for name in sorted(declared) if re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}', name)]
                except ValueError:
                    notes.append('package.json could not be inspected; review it manually')
    profile_file = safe_path(repo, PROFILE_PATH)
    requirement_file = safe_path(repo, REQUIREMENTS_PATH)
    profile_status = 'not_created'
    if profile_file.exists():
        try:
            profile_checked(repo, read_json(profile_file))
            profile_status = 'structurally_valid'
        except ValueError:
            profile_status = 'needs_manual_review'
    head = subprocess.run([*SAFE_GIT_PREFIX, 'rev-parse', 'HEAD'], cwd=repo, env=git_environment(), capture_output=True, text=True)
    return {'contract_version': 1, 'repository': str(repo), 'revision': head.stdout.strip() if head.returncode == 0 else 'unknown',
            'worktree_clean': not bool(query('status', '--porcelain')),
            'tooling_markers': markers, 'declared_package_scripts': scripts,
            'tooling_detection_is_authorization': False, 'profile_status': profile_status,
            'profile_path': PROFILE_PATH, 'requirements_template_exists': requirement_file.is_file(),
            'planned_paths': [PROFILE_PATH, REQUIREMENTS_PATH], 'created_paths': [],
            'execution': 'not_run', 'ready_for_fix': False,
            'business_acceptance': 'not_evaluated', 'remote_actions': 'none', 'notes': notes,
            'next_steps': ['Supply real source excerpts and owner-confirmed ACs',
                           'Review direct test commands; detection does not approve package scripts',
                           'Provide a separate issue input with exact issue-specific edit paths',
                           'Review/commit setup files before starting a clean-tree workflow']}


def initialize(repo, write=False):
    report = inspection(repo)
    repo = Path(report['repository'])
    paths = [safe_path(repo, name) for name in report['planned_paths']]
    report['status'] = 'inspection_only'
    if not write:
        return report
    present = [path.exists() for path in paths]
    if all(present):
        if not all(path.is_file() for path in paths):
            raise ValueError('Existing onboarding paths are not regular files; left unchanged')
        report['status'] = 'already_initialized'
        return report  # Never overwrite, even if existing profile requires review.
    if any(present):
        raise ValueError('Existing onboarding files left unchanged; partial setup requires manual review')
    profile = {'profile_version': 1, 'requirements': [REQUIREMENTS_PATH],
               'test_commands': [], 'artifact_paths': [], **LIMITS}
    contents = [json.dumps(profile, indent=2) + '\n', REQUIREMENTS_DRAFT]
    paths[0].parent.mkdir(mode=0o700, exist_ok=True)
    # Exclusive creation protects existing user files; disclose partial creation on a race/failure.
    for path, content in zip(paths, contents):
        try:
            safe_path(repo, path.relative_to(repo).as_posix())
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            report['created_paths'].append(path.relative_to(repo).as_posix())
            with os.fdopen(descriptor, 'w') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as error:
            raise ValueError('Setup stopped; created paths retained for manual review: ' +
                             json.dumps(report['created_paths'])) from error
    created = report['created_paths']
    report = inspection(repo)
    report.update(status='draft_created', created_paths=created)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(initialize(args.repo, args.write), indent=2))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
