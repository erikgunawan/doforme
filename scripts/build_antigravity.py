"""Build the native Antigravity package outside the source checkout."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from repo_policy import SAFE_GIT_PREFIX, git_environment, safe_path

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    from check_plugin import check_antigravity
    check_antigravity(ROOT)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(ROOT) or ROOT.is_relative_to(output.resolve()):
        raise ValueError('Choose a new output directory outside the source checkout')
    # Validate every source before creating a partial package. Never follow links.
    paths = []
    tracked = subprocess.check_output([*SAFE_GIT_PREFIX, 'ls-files', '-z'], cwd=ROOT,
                                      env=git_environment(), text=True).split('\0')
    for name in sorted(set(filter(None, tracked))):
        if not any(name.startswith(folder + '/') for folder in ('commands', 'agents', 'skills', 'scripts', 'integrations')):
            continue
        path = safe_path(ROOT, name)
        if not path.is_file():
            raise ValueError('Package source must be a regular tracked file')
        paths.append(path)
    required = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'integrations/antigravity').rglob('*')
                if p.is_file() and p.suffix in ('.py', '.md', '.json') and '__pycache__' not in p.parts}
    if not required.issubset(set(tracked)):
        raise ValueError('Stage the intended Antigravity source files before building the preview')
    if any(parent.is_symlink() for parent in output.parents):
        raise ValueError('Symlink in package output')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(mode=0o700)
    for path in paths:
        target = output / 'engine' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        relative = path.relative_to(ROOT / 'integrations/antigravity') if path.is_relative_to(ROOT / 'integrations/antigravity') else None
        if relative is not None and (relative.parts[0] in ('agents', 'skills', 'scripts', 'references') or str(relative) in ('hooks.json', 'mcp_config.json')):
            native_target = output / relative
            native_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, native_target)
    version = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())['version']
    manifest = {'$schema': 'https://antigravity.google/schemas/v1/plugin.json',
                'name': 'doforme', 'displayName': 'doforme', 'version': version,
                'description': 'Guided bug investigation, scoped repairs, independent validation and local PR drafts grounded in requirements.',
                'author': {'name': 'Erik Gunawan'}, 'license': 'MIT',
                'repository': 'https://github.com/erikgunawan/doforme'}
    (output / 'plugin.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copyfile(ROOT / 'LICENSE', output / 'LICENSE')
    guide = (ROOT / 'docs/ANTIGRAVITY.md').read_text()
    for name in ('USAGE', 'PHASES'):
        guide = guide.replace('](' + name + '.md)', '](https://github.com/erikgunawan/doforme/blob/master/docs/' + name + '.md)')
    (output / 'README.md').write_text(guide)
    return {'package': str(output), 'supported_stages': ['analyze', 'plan', 'fix', 'test', 'review', 'pr'],
            'publication': 'none', 'installation': 'not_run'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    try:
        print(json.dumps(build(p.parse_args().output), indent=2))
    except (ValueError, OSError) as error:
        p.exit(2, str(error) + '\n')
