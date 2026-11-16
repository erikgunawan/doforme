"""Bounded POSIX child execution. Lifecycle controls are not an OS sandbox."""
from dataclasses import dataclass
import math
import os
import selectors
import signal
import subprocess
import time

from repo_policy import git_environment


@dataclass(frozen=True)
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    captured_bytes: int
    descendants_terminated: bool = False


class ExecutionError(ValueError):
    """Safe diagnostic; partial output is private data and is never interpolated."""
    MESSAGES = {
        'invalid_options': 'Invalid bounded process options',
        'unsupported_platform': 'Bounded process execution currently requires POSIX',
        'start_failed': 'Process could not start; inspect the reviewed local executable',
        'timeout': 'Process deadline exceeded; process group terminated; inspect partial edits',
        'cancelled': 'Process cancelled; process group terminated; inspect partial edits',
        'output_limit': 'Process output limit exceeded; process group terminated; inspect partial edits',
        'cleanup_failed': 'Process cleanup failed; inspect running processes and partial edits manually',
    }

    def __init__(self, reason, partial_result=None):
        self.reason = reason
        self.partial_result = partial_result
        super().__init__(self.MESSAGES[reason])


def model_environment(source=None, *, preserve_names=()):
    """Remove unrelated credentials while preserving explicitly reviewed model auth.

    Cloud-provider deployments can explicitly preserve exact required variable
    names. This is environment hygiene, not filesystem or network isolation.
    """
    environment = dict(os.environ if source is None else source)
    allowed = {'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', *preserve_names}
    prefixes = ('GITHUB_', 'GH_', 'TELEGRAM_', 'ACTIONS_', 'AWS_', 'AZURE_',
                'GOOGLE_', 'GCLOUD_', 'GCP_', 'SSH_', 'DOCKER_', 'KUBERNETES_')
    for key in list(environment):
        upper = key.upper()
        credential = any(word in upper for word in ('TOKEN', 'PASSWORD', 'SECRET', 'CREDENTIAL'))
        credential = credential or upper.endswith(('_API_KEY', '_ACCESS_KEY', '_PRIVATE_KEY'))
        if key == 'CLAUDECODE' or (key not in allowed and (upper.startswith(prefixes) or credential or upper == 'KUBECONFIG')):
            environment.pop(key, None)
    return git_environment(environment)


def _group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _terminate_group(process, grace):
    """Kill same-session descendants even if the original leader already exited."""
    existed = _group_exists(process.pid)
    if existed:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        end = time.monotonic() + grace
        while time.monotonic() < end:
            process.poll()  # Reap the leader; descendant reaping belongs to its parent/init.
            if not _group_exists(process.pid):
                break
            time.sleep(min(.02, max(0, end - time.monotonic())))
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=max(1, grace))
    return existed


def run_process(argv, *, cwd, env, timeout_seconds, output_limit_bytes=16_000_000,
                termination_grace=.25, cancelled=None):
    """Run shell=False with one combined stdout/stderr byte budget and deadline.

    Any deadline, cancellation or output overflow fails closed. No retries occur.
    Child output is returned only as bounded data; diagnostics never echo argv,
    environment values or child stderr. Descendants escaping the session with
    setsid are outside these lifecycle controls; use a real OS boundary for that.
    """
    if os.name != 'posix':
        raise ExecutionError('unsupported_platform')
    if (not isinstance(argv, (list, tuple)) or not argv or not argv[0] or
            any(not isinstance(value, str) or '\0' in value for value in argv) or
            isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or
            not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or
            type(output_limit_bytes) is not int or not 1 <= output_limit_bytes <= 100_000_000 or
            isinstance(termination_grace, bool) or not isinstance(termination_grace, (int, float)) or
            not math.isfinite(termination_grace) or not 0 <= termination_grace <= 5):
        raise ExecutionError('invalid_options')
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, bufsize=0, close_fds=True)
    except OSError:
        raise ExecutionError('start_failed') from None
    streams = {'stdout': bytearray(), 'stderr': bytearray()}
    captured = 0
    selector = selectors.DefaultSelector()
    deadline = time.monotonic() + timeout_seconds

    def result(terminated=False):
        return ExecutionResult(process.returncode if process.returncode is not None else -1,
                               bytes(streams['stdout']).decode('utf-8', errors='replace'),
                               bytes(streams['stderr']).decode('utf-8', errors='replace'),
                               captured, terminated)

    try:
        for name, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or process.poll() is None:
            if cancelled is not None and cancelled():
                raise ExecutionError('cancelled')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ExecutionError('timeout')
            if not selector.get_map():
                time.sleep(min(.05, remaining))
                continue
            for key, _ in selector.select(min(.1, remaining)):
                try:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                room = output_limit_bytes - captured
                streams[key.data].extend(chunk[:room])
                captured += min(len(chunk), room)
                if len(chunk) > room:
                    raise ExecutionError('output_limit')
        # A leader can exit cleanly while background descendants close their pipe
        # handles and keep running. They must not outlive this bounded invocation.
        terminated = _terminate_group(process, termination_grace)
        return result(terminated)
    except (ExecutionError, KeyboardInterrupt) as error:
        reason = error.reason if isinstance(error, ExecutionError) else 'cancelled'
        try:
            _terminate_group(process, termination_grace)
        except (OSError, subprocess.SubprocessError):
            reason = 'cleanup_failed'
        raise ExecutionError(reason, result(True)) from None
    except BaseException:
        try:
            _terminate_group(process, termination_grace)
        finally:
            raise
    finally:
        selector.close()
        for stream in (process.stdout, process.stderr):
            if not stream.closed:
                stream.close()
