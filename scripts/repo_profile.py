"""Compose reusable repository defaults with explicit per-issue input."""
import json
from pathlib import Path

from repo_policy import config_checked, safe_path

PROFILE_PATH = '.doforme/repository.json'
REQUIREMENTS_PATH = '.doforme/requirements.md'
LIMITS = {'timeout_seconds': 180, 'max_turns': 45, 'max_budget_usd': 1.0}
PROFILE_KEYS = {'profile_version', 'requirements', 'test_commands', 'artifact_paths', *LIMITS}
ISSUE_KEYS = {'issue_ref', 'issue_text', 'requirements', 'edit_paths', 'test_commands', 'artifact_paths', *LIMITS}


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError('JSON input must be a regular, non-symlink file under 1 MB')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field: ' + key)
            result[key] = value
        return result
    result = json.loads(path.read_text(), object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError('JSON input must be an object')
    return result


def profile_checked(repo, data, *, allow_existing_artifacts=False):
    if not isinstance(data, dict) or set(data) - PROFILE_KEYS:
        raise ValueError('Unknown profile field; issue data, edit scope and authorization do not belong in a repository profile')
    if type(data.get('profile_version')) is not int or data.get('profile_version') != 1:
        raise ValueError('Unsupported repository profile version')
    defaults = {key: value for key, value in data.items() if key != 'profile_version'}
    validated = config_checked(repo, {'issue_ref': 'profile-validation-only', 'issue_text': 'Validate structure only', **defaults},
                               allow_existing_artifacts=allow_existing_artifacts)
    return {key: validated[key] for key in ('requirements', 'test_commands', 'artifact_paths', *LIMITS)}


def compose(repo, profile, issue, *, allow_existing_artifacts=False):
    if not isinstance(issue, dict) or set(issue) - ISSUE_KEYS:
        raise ValueError('Unknown issue field or authorization flag in input')
    defaults = profile_checked(repo, profile, allow_existing_artifacts=allow_existing_artifacts)
    # Validate the issue independently so limits cannot be bypassed with coercion.
    requested = config_checked(repo, issue, allow_existing_artifacts=allow_existing_artifacts)
    effective = {**defaults, 'issue_ref': requested['issue_ref'], 'issue_text': requested['issue_text'],
                 'edit_paths': requested['edit_paths']}
    for key in ('test_commands', 'artifact_paths'):
        if key in issue:
            effective[key] = requested[key]
    effective['requirements'] = list(dict.fromkeys([*defaults['requirements'], *requested['requirements']]))
    for key in LIMITS:
        if key in issue:
            if requested[key] > defaults[key]:
                raise ValueError('Issue cannot increase repository limit: ' + key)
            effective[key] = requested[key]
    return config_checked(repo, effective, allow_existing_artifacts=allow_existing_artifacts)


def load(repo, issue_path, profile_path=None, *, allow_existing_artifacts=False):
    issue = read_json(issue_path)
    if profile_path is None:
        return issue  # Legacy complete run-config input remains supported.
    repo = Path(repo).resolve()
    relative = Path(profile_path)
    if relative.is_absolute():
        try:
            relative = relative.relative_to(repo)
        except ValueError:
            raise ValueError('Repository profile must be inside the selected repository') from None
    profile = read_json(safe_path(repo, str(relative)))
    effective = compose(repo, profile, issue, allow_existing_artifacts=allow_existing_artifacts)
    protected = {relative.as_posix()}
    issue_file = Path(issue_path).resolve()
    if issue_file.is_relative_to(repo):
        protected.add(issue_file.relative_to(repo).as_posix())
    if protected & set(effective['edit_paths'] + effective['artifact_paths']):
        raise ValueError('Active profile and issue input must remain read-only')
    return effective
