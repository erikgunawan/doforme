"""Reproducible, verified release candidates from one clean explicit Git revision."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile

from check_plugin import check
from repo_policy import SAFE_GIT_PREFIX, git_environment

MAX_BYTES = 100_000_000
MAX_FILES = 20_000
VERSION = r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?'
DENIED_PARTS = {'.git', '.aws', '.ssh', '.codex', '.agents', '.credentials',
                'artifacts', '.artifacts', 'private-evidence', '.doforme',
                'credentials.json', 'secrets.json', '.npmrc', '.pypirc'}


def unique_json(content):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate candidate JSON field')
            result[key] = value
        return result
    return json.loads(content, object_pairs_hook=pairs)


def stable_gates(files):
    return {'owner_license_present': any(name in files for name in ('LICENSE', 'LICENSE.txt', 'LICENSE.md')),
            'owner_license_approval': 'not_authenticated', 'real_pilot': 'not_established_by_package',
            'live_integrations': 'not_established_by_package', 'os_isolation': 'not_established_by_package',
            'owner_release_approval': 'not_supplied'}


class BoundedArchiveReader:
    def __init__(self, stream):
        self.stream = stream
        self.remaining = MAX_BYTES + MAX_FILES * 2048 + 10240

    def read(self, size=-1):
        amount = self.remaining + 1 if size < 0 else min(size, self.remaining + 1)
        content = self.stream.read(amount)
        self.remaining -= len(content)
        if self.remaining < 0:
            raise ValueError('Candidate decompressed archive exceeds its bound')
        return content


def git(root, *args):
    environment = git_environment()
    environment['GIT_NO_REPLACE_OBJECTS'] = '1'
    return subprocess.check_output([*SAFE_GIT_PREFIX, *args], cwd=root, env=environment)


def safe_name(name):
    if (not isinstance(name, str) or not name or name.startswith('/') or '\\' in name or
            any(ord(char) < 32 or ord(char) == 127 for char in name)):
        raise ValueError('Unsafe candidate path')
    parts = PurePosixPath(name).parts
    if (any(part in ('.', '..') or part in DENIED_PARTS or part.startswith('.env') for part in parts) or
            PurePosixPath(name).suffix in ('.pem', '.key') or
            name.endswith(('.trace.json', '.trace.jsonl', '.stderr.txt', '.log'))):
        raise ValueError('Private/credential/evidence path cannot be packaged: ' + name)
    if PurePosixPath(name).as_posix() != name:
        raise ValueError('Noncanonical candidate path')
    return name


def regular_path(path):
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('Candidate paths must not contain symlinks')
    return path.resolve()


def selected_commit(root, ref):
    root = regular_path(root)
    actual_root = Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    if actual_root != root:
        raise ValueError('Run packaging at the selected Git root')
    if not (re.fullmatch(r'[0-9a-f]{40,64}', ref) or re.fullmatch(r'refs/tags/[A-Za-z0-9][A-Za-z0-9._/-]*', ref)):
        raise ValueError('Select a full commit SHA or refs/tags/name, not a mutable branch/HEAD shortcut')
    commit = git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()
    if commit != git(root, 'rev-parse', 'HEAD').decode().strip():
        raise ValueError('Selected candidate revision must match the checked-out HEAD')
    if git(root, 'status', '--porcelain'):
        raise ValueError('Candidate checkout must be clean, including untracked files')
    return root, commit


def committed_files(root, commit):
    files = {}
    total = 0
    rows = git(root, 'ls-tree', '-r', '-l', '-z', '--full-tree', commit).decode('utf-8').split('\0')
    for row in filter(None, rows):
        metadata, name = row.split('\t', 1)
        mode, kind, blob, size = metadata.split()
        safe_name(name)
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Only regular committed files may be packaged')
        total += int(size)
        if len(files) >= MAX_FILES or total > MAX_BYTES:
            raise ValueError('Candidate exceeds bounded file/byte limits')
        content = git(root, 'cat-file', 'blob', blob)
        if len(content) != int(size):
            raise ValueError('Git blob size changed unexpectedly')
        files[name] = (int(mode[-3:], 8), content)
    return dict(sorted(files.items()))


def validate_contents(files):
    """Use the current trusted structural validator, never archive Python code."""
    with tempfile.TemporaryDirectory(prefix='doforme-candidate-check-') as directory:
        root = Path(directory)
        for name, (mode, content) in files.items():
            safe_name(name)
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(mode)
        check(root)
    plugin = unique_json(files['.claude-plugin/plugin.json'][1].decode('utf-8'))
    if plugin.get('name') != 'doforme' or not re.fullmatch(VERSION, plugin.get('version', '')):
        raise ValueError('Candidate requires the doforme manifest and a canonical version')
    return plugin


def file_manifest(files):
    return {name: {'mode': mode, 'size': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            for name, (mode, content) in files.items()}


def package(root, ref, output):
    root, commit = selected_commit(root, ref)
    output = regular_path(output)
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError('Candidate output must be outside the checkout')
    files = committed_files(root, commit)
    plugin = validate_contents(files)
    version = plugin['version']
    prefix = 'doforme-' + version + '/'
    filename = f'doforme-{version}-{commit[:12]}-candidate.tar.gz'
    epoch = int(git(root, 'show', '-s', '--format=%ct', commit).decode().strip())
    output.mkdir(mode=0o700)  # Exclusive destination; retain partial output if an I/O failure occurs.
    archive = output / filename
    descriptor = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=9) as compressed:
            with tarfile.open(mode='w|', fileobj=compressed, format=tarfile.PAX_FORMAT) as tar:
                for name, (mode, content) in files.items():
                    info = tarfile.TarInfo(prefix + name)
                    info.size, info.mode, info.mtime = len(content), mode, epoch
                    info.uid = info.gid = 0
                    info.uname = info.gname = ''
                    tar.addfile(info, io.BytesIO(content))
    # Detect concurrent checkout changes rather than silently claiming a clean release.
    selected_commit(root, commit)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    metadata = {'contract_version': 1, 'kind': 'release_candidate', 'commit': commit, 'version': version,
                'prefix': prefix, 'archive': filename, 'archive_sha256': digest, 'files': file_manifest(files),
                'stable_ready': False, 'publication_ready': False, 'remote_actions': 'none',
                'stable_gates': stable_gates(files)}
    for path, text in ((output / 'candidate.json', json.dumps(metadata, indent=2) + '\n'),
                       (output / 'SHA256SUMS', digest + '  ' + filename + '\n')):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(text)
    return verify(output)


def verify(folder):
    folder = regular_path(folder)
    metadata_path = folder / 'candidate.json'
    if not metadata_path.is_file() or metadata_path.is_symlink() or metadata_path.stat().st_size > 10_000_000:
        raise ValueError('Candidate metadata unavailable or oversized')
    metadata = unique_json(metadata_path.read_text())
    expected_keys = {'contract_version', 'kind', 'commit', 'version', 'prefix', 'archive',
                     'archive_sha256', 'files', 'stable_ready', 'publication_ready', 'remote_actions', 'stable_gates'}
    if (not isinstance(metadata, dict) or set(metadata) != expected_keys or
            metadata.get('contract_version') != 1 or metadata.get('kind') != 'release_candidate' or
            metadata.get('stable_ready') is not False or metadata.get('publication_ready') is not False or
            metadata.get('remote_actions') != 'none' or not re.fullmatch(VERSION, metadata.get('version', '')) or
            not re.fullmatch(r'[0-9a-f]{40,64}', metadata.get('commit', ''))):
        raise ValueError('Invalid candidate identity or unsupported stable/publication claim')
    filename = metadata.get('archive', '')
    expected_name = f"doforme-{metadata['version']}-{metadata['commit'][:12]}-candidate.tar.gz"
    prefix = 'doforme-' + metadata['version'] + '/'
    if filename != expected_name or metadata.get('prefix') != prefix:
        raise ValueError('Unexpected candidate archive identity')
    archive = folder / filename
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > MAX_BYTES:
        raise ValueError('Candidate archive unavailable or oversized')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != metadata.get('archive_sha256'):
        raise ValueError('Candidate archive hash mismatch')
    sums = folder / 'SHA256SUMS'
    if sums.is_symlink() or not sums.is_file() or sums.read_text() != digest + '  ' + filename + '\n':
        raise ValueError('Candidate checksum file mismatch')
    files, total = {}, 0
    with gzip.open(archive, 'rb') as compressed:
        with tarfile.open(fileobj=BoundedArchiveReader(compressed), mode='r|') as tar:
            for member in tar:
                if not member.name.startswith(prefix) or not member.isfile():
                    raise ValueError('Candidate archive must contain regular files under its prefix')
                name = safe_name(member.name[len(prefix):])
                total += member.size
                if name in files or len(files) >= MAX_FILES or total > MAX_BYTES or member.size < 0:
                    raise ValueError('Duplicate or oversized candidate archive member')
                mode = member.mode & 0o777
                if mode not in (0o644, 0o755) or member.mode != mode:
                    raise ValueError('Unsafe candidate file mode')
                content = tar.extractfile(member).read(member.size + 1)
                if len(content) != member.size:
                    raise ValueError('Candidate member size mismatch')
                files[name] = (mode, content)
    if file_manifest(files) != metadata.get('files'):
        raise ValueError('Candidate contents differ from hash manifest')
    plugin = validate_contents(files)
    if plugin['version'] != metadata['version'] or stable_gates(files) != metadata.get('stable_gates'):
        raise ValueError('Candidate metadata differs from source version or unsupported stable gate claims')
    return {'status': 'verified_candidate', 'commit': metadata['commit'], 'version': metadata['version'],
            'archive': filename, 'archive_sha256': digest, 'file_count': len(files),
            'stable_ready': False, 'publication_ready': False, 'remote_actions': 'none',
            'stable_gates': metadata.get('stable_gates', {})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--ref', help='Full checked-out commit SHA or refs/tags/name; candidate only')
    mode.add_argument('--verify', help='Read-only verification of an existing candidate directory')
    parser.add_argument('--output', help='New private directory outside the checkout')
    args = parser.parse_args()
    if bool(args.output) != bool(args.ref):
        parser.error('--output is required only with --ref')
    try:
        result = package(Path(__file__).resolve().parents[1], args.ref, args.output) if args.ref else verify(args.verify)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, tarfile.TarError, subprocess.SubprocessError) as error:
        print('Candidate stopped; any newly created partial output is retained: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
