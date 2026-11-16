"""Capture explicit local requirement exports; never fetch or approve remote intent."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import parse_qsl, urlsplit

sys.dont_write_bytecode = True
from init_repo import repository_root
from repo_policy import safe_path

PLUGIN = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 4_000_000
KINDS = {'business_document', 'jira', 'figma', 'repository_spec', 'user_confirmation'}
SOURCE_KEYS = {'source_id', 'kind', 'path', 'origin', 'origin_locator', 'version', 'source_accessed_at'}


def regular_bytes(path, limit=MAX_FILE_BYTES):
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError('Source/manifest path must not contain symlinks')
    # Reject special files before opening so a FIFO cannot block inspection.
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('Source/manifest must be a regular file')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            raise ValueError('Source/manifest exceeds regular-file byte limit')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Source/manifest exceeds byte limit')
    return raw


def manifest_read(path):
    def unique(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError('Duplicate JSON field: ' + key)
            data[key] = value
        return data
    result = json.loads(regular_bytes(path).decode('utf-8'), object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError('Manifest must be an object')
    return result


def metadata_text(value, field, limit=2048):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Invalid source metadata: ' + field)
    return value


def origin_checked(value):
    value = metadata_text(value, 'origin')
    # Origins are labels only. Even an HTTPS origin is not opened or authenticated.
    if '://' in value:
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise ValueError('URL origins must be HTTPS labels without credentials')
        sensitive = {'token', 'access_token', 'api_key', 'apikey', 'password', 'secret', 'key'}
        if any(key.lower() in sensitive for key, _ in parse_qsl(parsed.query)):
            raise ValueError('Origin must not contain credential query parameters')
    return value


def sources_checked(repo, manifest):
    if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'sources'} or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1:
        raise ValueError('Unsupported source manifest schema')
    sources = manifest['sources']
    if not isinstance(sources, list) or not 1 <= len(sources) <= 16:
        raise ValueError('Manifest requires between 1 and 16 explicit sources')
    ids, paths, prepared, total = set(), set(), [], 0
    for entry in sources:
        if not isinstance(entry, dict) or set(entry) - SOURCE_KEYS or not {'source_id', 'kind', 'path', 'origin', 'origin_locator'} <= set(entry):
            raise ValueError('Source fields missing/unknown; authority cannot be self-granted')
        ident = entry['source_id']
        if not isinstance(ident, str) or not re.fullmatch(r'S[1-9][0-9]{0,2}', ident) or ident in ids:
            raise ValueError('Source IDs must be unique S1..S999 values')
        if not isinstance(entry['kind'], str) or entry['kind'] not in KINDS:
            raise ValueError('Unsupported source kind')
        path = safe_path(repo, entry['path'])
        name = path.relative_to(repo).as_posix()
        if name in paths:
            raise ValueError('Duplicate canonical source path')
        raw = regular_bytes(path)
        text = raw.decode('utf-8')
        if not text.strip() or '\x00' in text:
            raise ValueError('Source must be nonempty UTF-8 text without NUL bytes')
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise ValueError('Source bundle exceeds total byte limit')
        origin = origin_checked(entry['origin'])
        locator = metadata_text(entry['origin_locator'], 'origin_locator')
        version = metadata_text(entry.get('version', 'unknown'), 'version', 256)
        accessed = entry.get('source_accessed_at', 'unknown')
        if accessed != 'unknown':
            metadata_text(accessed, 'source_accessed_at', 64)
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', accessed):
                raise ValueError('source_accessed_at must be supplied ISO time with timezone or unknown')
            datetime.fromisoformat(accessed.replace('Z', '+00:00'))
        record = {'source_id': ident, 'kind': entry['kind'], 'origin': origin,
                  'origin_locator': locator, 'version': version,
                  'source_accessed_at': accessed, 'metadata_basis': 'caller_supplied_unverified',
                  'access': 'supplied_snapshot', 'read_status': 'read',
                  'read_locator': {'repository_relative_path': name, 'lines': [1, len(text.splitlines())]},
                  'snapshot_file': ident + '.txt', 'sha256': hashlib.sha256(raw).hexdigest(),
                  'byte_length': len(raw), 'source_untrusted': True,
                  'authority': 'unconfirmed', 'freshness': 'unknown', 'confirmation_ref': None}
        prepared.append((record, raw))
        ids.add(ident)
        paths.add(name)
    return prepared


def capture(repo, manifest_path, output):
    repo = repository_root(repo)
    prepared = sources_checked(repo, manifest_read(manifest_path))
    raw_output = Path(output).absolute()
    if any(path.is_symlink() for path in (raw_output, *raw_output.parents)):
        raise ValueError('Snapshot output must not contain symlinks')
    output = raw_output.resolve()
    if output.is_relative_to(repo) or repo.is_relative_to(output) or output.is_relative_to(PLUGIN) or PLUGIN.is_relative_to(output):
        raise ValueError('Snapshot output must be outside target and plugin checkouts')
    if not output.parent.is_dir():
        raise ValueError('Snapshot output parent must already exist')
    # Validate everything before creating output; never reuse an existing bundle.
    output.mkdir(mode=0o700)
    report = {'schema_version': 1, 'status': 'snapshot_ready',
              'snapshot_imported_at_utc': datetime.now(timezone.utc).isoformat(),
              'repository': str(repo), 'sources': [record for record, _ in prepared],
              'requirements_status': 'needs_information', 'business_acceptance': 'not_evaluated',
              'resolution_status': 'not_established', 'network_requests': 0, 'remote_actions': 'none',
              'limitations': ['Import timestamp is not a remote source access/currentness confirmation',
                              'Source metadata and owner identity are not independently authenticated',
                              'Jira/Figma/Docs exports are text only; no live fetch or visual validation',
                              'Owner applicability, conflicts and AC coverage still require explicit review']}
    created = []
    payloads = [(record['snapshot_file'], data) for record, data in prepared]
    payloads.append(('sources.json', (json.dumps(report, indent=2, ensure_ascii=False) + '\n').encode('utf-8')))
    try:
        for name, payload in payloads:
            descriptor = os.open(output / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            created.append(name)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
    except OSError as error:
        raise ValueError('Snapshot creation stopped; retained paths need review: ' + json.dumps(created)) from error
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        report = capture(args.repo, args.manifest, args.output)
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
