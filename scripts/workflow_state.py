"""Private atomic checkpoint storage. Caller must verify target/config freshness."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic_text(path, text):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing symlink output')
    descriptor, temporary = tempfile.mkstemp(prefix='.checkpoint-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_text(path, json.dumps(value, indent=2) + '\n')


class Checkpoints:
    def __init__(self, root, resume=False):
        raw = Path(root).absolute()
        if any(path.is_symlink() for path in (raw, *raw.parents)):
            raise ValueError('Checkpoint path must not contain symlinks')
        self.root = raw.resolve()
        if not resume:
            self.root.mkdir(mode=0o700)
        elif not self.root.is_dir():
            raise ValueError('Checkpoint directory missing')
        if self.root.stat().st_mode & 0o077:
            raise ValueError('Checkpoint directory must be private (mode 700)')

    @contextmanager
    def locked(self):
        path = self.root / 'run.lock'
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ValueError('Run is locked; do not remove a lock until the owner process has stopped')
        inode = os.fstat(descriptor).st_ino
        try:
            os.write(descriptor, (str(os.getpid()) + '\n').encode())
            yield
        finally:
            os.close(descriptor)
            if path.exists() and not path.is_symlink() and path.stat().st_ino == inode:
                path.unlink()

    def load(self):
        path = self.root / 'checkpoint.json'
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
            raise ValueError('Missing, symlinked or oversized checkpoint')
        state = json.loads(path.read_text())
        if not isinstance(state, dict) or state.get('state_version') != 1:
            raise ValueError('Unsupported checkpoint version')
        for key in ('results', 'artifact_index', 'attempt_counts', 'workspace', 'grants'):
            if not isinstance(state.get(key), dict):
                raise ValueError('Malformed checkpoint field: ' + key)
        for key in ('repository', 'revision', 'config_digest', 'policy_digest'):
            if not isinstance(state.get(key), str) or not state[key]:
                raise ValueError('Malformed checkpoint identity: ' + key)
        if state.get('status') not in ('running', 'complete', 'blocked', 'failed'):
            raise ValueError('Malformed checkpoint status')
        if any(not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 2 for value in state['attempt_counts'].values()):
            raise ValueError('Malformed checkpoint attempt count')
        for record in state['artifact_index'].values():
            if not isinstance(record, dict) or set(record) != {'filename', 'digest'}:
                raise ValueError('Malformed checkpoint artifact')
        return state

    def read_text(self, filename, maximum=5_000_000):
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError('Invalid checkpoint filename')
        path = self.root / filename
        if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
            raise ValueError('Missing, non-regular, symlinked or oversized checkpoint file')
        return path.read_text()

    def save(self, state):
        write_json(self.root / 'checkpoint.json', state)

    def artifact(self, stage, attempt, result):
        if stage not in ('analyze', 'plan', 'fix', 'test', 'review', 'pr') or not isinstance(attempt, int) or attempt < 1:
            raise ValueError('Invalid artifact identity')
        history = self.root / 'history'
        if history.is_symlink():
            raise ValueError('Symlinked history directory')
        history.mkdir(mode=0o700, exist_ok=True)
        filename = stage + '-' + str(attempt) + '.json'
        if (history / filename).exists():
            raise ValueError('Attempt artifact already exists; refusing overwrite')
        write_json(history / filename, result)
        return filename, digest(result)

    def result(self, filename, expected):
        if Path(filename).name != filename or not filename.endswith('.json'):
            raise ValueError('Invalid checkpoint artifact path')
        if (self.root / 'history').is_symlink():
            raise ValueError('Symlinked history directory')
        path = self.root / 'history' / filename
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 5_000_000:
            raise ValueError('Invalid checkpoint artifact')
        result = json.loads(path.read_text())
        if digest(result) != expected:
            raise ValueError('Checkpoint report content changed')
        return result
