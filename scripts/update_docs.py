"""Generate command documentation and content-bound change history at commit time."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
from check_plugin import frontmatter
from repo_policy import SAFE_GIT_PREFIX, git_environment

MANAGED = ('docs/changes.json', 'CHANGELOG.md', 'docs/REFERENCE.md')


def git(root, *args):
    return subprocess.check_output([*SAFE_GIT_PREFIX, *args], cwd=root,
                                   env=git_environment(), text=True)


def text_at(root, path, ref=None):
    if ref is None:
        return (root / path).read_text(encoding='utf-8')
    return git(root, 'show', f'{ref}:{path}')


def manifest(root, ref=None):
    return json.loads(text_at(root, '.claude-plugin/plugin.json', ref))


def file_map(root, ref=None):
    if ref == '':
        rows = git(root, 'ls-files', '--stage', '-z').split('\0')
    else:
        rows = git(root, 'ls-tree', '-r', '-z', ref or 'HEAD').split('\0')
    result = {}
    for row in filter(None, rows):
        metadata, name = row.split('\t', 1)
        fields = metadata.split()
        if ref == '':
            mode, blob, stage = fields
            if stage != '0':
                raise ValueError('Resolve index conflicts before updating documentation')
        else:
            mode, _, blob = fields
        result[name] = {'mode': mode, 'blob': blob}
    return result


def changed_files(root, base, head=None):
    if base is None:
        names = list(file_map(root, head))
    else:
        args = ['diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z']
        args += ['--cached', base] if head is None else [base, head]
        names = git(root, *args, '--').split('\0')
    return sorted(name for name in names if name and name not in MANAGED)


def changes(root, base, head=None):
    tree = file_map(root, '' if head is None else head)
    return {name: tree.get(name) for name in changed_files(root, base, head)}


def record(base, version, summary, date, files):
    identity = json.dumps({'base_commit': base, 'changes': files}, sort_keys=True).encode()
    return {'id': hashlib.sha256(identity).hexdigest(), 'base_commit': base,
            'date': date, 'version': version, 'summary': summary, 'changes': files}


def history_checked(data):
    if not isinstance(data, dict) or set(data) != {'schema_version', 'entries'} or data['schema_version'] != 1:
        raise ValueError('Unsupported change history format')
    if not isinstance(data['entries'], list):
        raise ValueError('History entries must be a list')
    ids = set()
    for entry in data['entries']:
        if not isinstance(entry, dict) or set(entry) != {'id', 'base_commit', 'date', 'version', 'summary', 'changes'}:
            raise ValueError('Invalid history entry')
        if not all(isinstance(entry[key], str) and entry[key].strip() for key in ('id', 'date', 'version', 'summary')):
            raise ValueError('History entry metadata is incomplete')
        if entry['base_commit'] is not None and not re.fullmatch(r'[0-9a-f]{40,64}', entry['base_commit']):
            raise ValueError('Invalid history base revision')
        if not isinstance(entry['changes'], dict) or not entry['changes']:
            raise ValueError('History must identify changed files')
        for name, value in entry['changes'].items():
            if name in MANAGED or Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('Invalid history path')
            if value is not None and (not isinstance(value, dict) or set(value) != {'mode', 'blob'} or
                                      not re.fullmatch(r'[0-9a-f]{40,64}', value['blob']) or
                                      not re.fullmatch(r'[0-7]{6}', value['mode'])):
                raise ValueError('Invalid file content identity')
        expected = record(entry['base_commit'], entry['version'], entry['summary'], entry['date'], entry['changes'])
        if expected['id'] != entry['id'] or entry['id'] in ids:
            raise ValueError('Changed or duplicated history identity')
        ids.add(entry['id'])
    return data


def bootstrap(root):
    entries = []
    for commit in git(root, 'rev-list', '--reverse', 'HEAD').splitlines():
        parents = git(root, 'show', '-s', '--format=%P', commit).split()
        base = parents[0] if parents else None
        files = changes(root, base, commit)
        if files:
            entries.append(record(base, manifest(root, commit)['version'],
                                  git(root, 'show', '-s', '--format=%s', commit).strip(),
                                  git(root, 'show', '-s', '--format=%as', commit).strip(), files))
    return {'schema_version': 1, 'entries': entries}


def escape(value):
    return (str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('`', "'").replace('|', '\\|').replace('\n', ' ').replace('\r', ' '))


def reference(root, staged=False):
    ref = '' if staged else None
    plugin = manifest(root, ref)
    paths = sorted(name for name in file_map(root, '') if name.startswith('commands/') and name.endswith('.md')) if staged else sorted(
        path.relative_to(root).as_posix() for path in (root / 'commands').glob('*.md'))
    lines = ['# Referensi command doforme', '', '<!-- Generated by scripts/update_docs.py; do not edit. -->', '',
             f"Versi plugin: **{plugin['version']}**.", '',
             '| Command | Kegunaan | Agent | Input |', '| --- | --- | --- | --- |']
    for name in paths:
        if staged:
            # Same deliberately flat frontmatter format as the local validator.
            body = text_at(root, name, '')
            fields = dict(line.split(':', 1) for line in body.split('\n---\n', 1)[0][4:].splitlines())
            fields = {key: value.strip() for key, value in fields.items()}
        else:
            fields = frontmatter(root / name)
        command = Path(name).stem
        values = (f'/doforme:{command}', fields['description'], fields.get('agent', 'guided coordinator'), fields.get('argument-hint', ''))
        lines.append('| ' + ' | '.join(escape(value) for value in values) + ' |')
    lines += ['', 'Referensi ini dibuat dari manifest dan frontmatter command. Ini bukan bukti',
              'bahwa fitur telah diuji melalui model atau memenuhi requirement bisnis.', '',
              'Panduan: [instalasi](INSTALLATION.md), [penggunaan](USAGE.md),',
              '[perubahan](../CHANGELOG.md), dan [kontribusi](../CONTRIBUTING.md).', '']
    return '\n'.join(lines)


def changelog(data):
    lines = ['# Riwayat perubahan', '', '<!-- Generated by scripts/update_docs.py; do not edit. -->', '',
             'Riwayat awal diimpor dari metadata Git. Entri berikutnya dibuat saat commit',
             'dari file yang di-stage; ringkasan otomatis tidak menyimpulkan perilaku fitur.',
             'Versi yang sama dapat memuat beberapa perubahan dan bukan berarti release/tag.',
             'Hasil pengujian dan batas kemampuan dicatat terpisah di [riwayat fase](docs/PHASES.md).', '']
    for entry in reversed(data['entries']):
        lines += [f"## {escape(entry['date'])} — v{escape(entry['version'])}", '',
                  escape(entry['summary']), '', f"Change ID: `{entry['id'][:12]}`.", '',
                  'File: ' + ', '.join('`' + escape(name) + '`' for name in entry['changes']) + '.', '']
    return '\n'.join(lines)


def rendered(root, data, staged=False):
    return {'docs/changes.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n',
            'CHANGELOG.md': changelog(data), 'docs/REFERENCE.md': reference(root, staged)}


def safe_managed(root):
    for name in MANAGED:
        path = root / name
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError('Managed documentation path must not contain symlinks')


def sync(root, summary=None, import_history=False):
    safe_managed(root)
    # Never overwrite unstaged edits to generated files or an untracked owner file.
    tracked = file_map(root, '')
    for name in MANAGED:
        path = root / name
        if path.exists() and (name not in tracked or path.read_text() != text_at(root, name, '')):
            raise ValueError('Review/stage managed documentation before updating: ' + name)
    if (root / MANAGED[0]).exists():
        data = history_checked(json.loads(text_at(root, MANAGED[0], '')))
        if MANAGED[0] in file_map(root, 'HEAD'):
            prior = history_checked(json.loads(text_at(root, MANAGED[0], 'HEAD')))
            if data['entries'][:len(prior['entries'])] != prior['entries']:
                raise ValueError('Existing committed history must remain unchanged')
    elif import_history:
        data = bootstrap(root)
    else:
        raise ValueError('Missing history; initial setup requires --bootstrap')
    base = git(root, 'rev-parse', 'HEAD').strip()
    files = changes(root, base)
    if files:
        pending = bool(data['entries'] and data['entries'][-1]['base_commit'] == base)
        old = data['entries'][-1] if pending else None
        message = summary or (old['summary'] if old else 'Update staged files: ' + ', '.join(files))
        entry = record(base, manifest(root, '')['version'], message,
                       datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat(), files)
        if pending:
            data['entries'][-1] = entry
        else:
            data['entries'].append(entry)
    history_checked(data)
    for name, content in rendered(root, data, staged=True).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    git(root, 'add', '--', *MANAGED)
    return data


def check(root):
    safe_managed(root)
    data = history_checked(json.loads((root / MANAGED[0]).read_text()))
    for name, expected in rendered(root, data).items():
        if (root / name).read_text() != expected:
            raise ValueError('Generated documentation is stale: ' + name)
    for name in ('docs/INSTALLATION.md', 'docs/USAGE.md', 'CONTRIBUTING.md'):
        if not (root / name).is_file():
            raise ValueError('Required documentation is missing: ' + name)


def verify_range(root, base):
    current = history_checked(json.loads((root / MANAGED[0]).read_text()))
    if re.fullmatch(r'0{40,64}', base):
        previous, base = {'entries': []}, None
    else:
        base = git(root, 'rev-parse', '--verify', '--end-of-options', base + '^{commit}').strip()
        tree = file_map(root, base)
        previous = history_checked(json.loads(text_at(root, MANAGED[0], base))) if MANAGED[0] in tree else {'entries': []}
    count = len(previous['entries'])
    if current['entries'][:count] != previous['entries']:
        raise ValueError('Existing history was rewritten; preserve prior entries')
    latest = {}
    for entry in current['entries'][count:]:
        latest.update(entry['changes'])
    actual = changes(root, base, 'HEAD')
    missing = [name for name, content in actual.items() if name not in latest or latest[name] != content]
    if missing:
        raise ValueError('Changes missing current history content: ' + ', '.join(missing))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--sync', action='store_true', help='Update and stage only managed docs from staged changes')
    mode.add_argument('--check', action='store_true', help='Read-only generated document checks')
    parser.add_argument('--bootstrap', action='store_true', help='Import initial history from existing Git commits')
    parser.add_argument('--summary', help='Owner-written summary for the current staged change')
    parser.add_argument('--base', help='Also verify history coverage against this Git revision')
    args = parser.parse_args()
    if (args.bootstrap or args.summary) and not args.sync or args.base and not args.check:
        parser.error('--bootstrap/--summary require --sync; --base requires --check')
    root = Path(__file__).resolve().parents[1]
    try:
        if args.sync:
            sync(root, args.summary, args.bootstrap)
        else:
            check(root)
            if args.base:
                verify_range(root, args.base)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    print('PASS: documentation/history ' + ('updated and staged' if args.sync else 'verified'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
