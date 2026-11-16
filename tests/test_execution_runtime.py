"""Real child-process lifecycle checks; no model, network or daemon required."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from execution_runtime import ExecutionError, model_environment, run_process


def running(pid):
    # A killed orphan may briefly remain a zombie until init reaps it. Zombies
    # cannot execute code and should not be mistaken for a surviving child.
    status = Path('/proc') / str(pid) / 'stat'
    if status.exists():
        return status.read_text().split(') ', 1)[1].split()[0] != 'Z'
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


@unittest.skipUnless(os.name == 'posix', 'POSIX process-group lifecycle')
class ExecutionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)

    def run_python(self, source, **kwargs):
        return run_process([sys.executable, '-u', '-c', source], cwd=self.cwd,
                           env=model_environment(), timeout_seconds=kwargs.pop('timeout_seconds', 3), **kwargs)

    def assert_stopped(self, pid):
        end = time.monotonic() + 2
        while running(pid) and time.monotonic() < end:
            time.sleep(.02)
        if running(pid):
            os.kill(pid, signal.SIGKILL)  # Fixture-only emergency cleanup on regression.
            self.fail('Child process survived bounded invocation cleanup')

    def test_stdout_stderr_and_nonzero_exit_are_data(self):
        result = self.run_python("import sys; print('out'); print('err',file=sys.stderr); sys.exit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, 'out\n')
        self.assertEqual(result.stderr, 'err\n')
        self.assertEqual(result.captured_bytes, 8)

    def test_combined_output_budget_stops_flood_and_diagnostics_hide_output(self):
        with self.assertRaises(ExecutionError) as caught:
            self.run_python("import os; os.write(1,b'SENSITIVE_SENTINEL'); os.write(2,b'x'*100000)",
                            output_limit_bytes=1024)
        self.assertEqual(caught.exception.reason, 'output_limit')
        self.assertLessEqual(caught.exception.partial_result.captured_bytes, 1024)
        self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))

    def test_timeout_kills_leader_and_term_ignoring_descendant(self):
        source = ("import subprocess,sys,time,pathlib; "
                  "p=subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)']); "
                  "pathlib.Path('child.pid').write_text(str(p.pid)); time.sleep(30)")
        started = time.monotonic()
        with self.assertRaises(ExecutionError) as caught:
            self.run_python(source, timeout_seconds=.5, termination_grace=.1)
        self.assertEqual(caught.exception.reason, 'timeout')
        self.assertLess(time.monotonic() - started, 3)
        self.assert_stopped(int((self.cwd / 'child.pid').read_text()))

    def test_parent_exit_does_not_leave_closed_pipe_background_child_running(self):
        source = ("import subprocess,sys,pathlib; "
                  "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],"
                  "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
                  "pathlib.Path('child.pid').write_text(str(p.pid))")
        result = self.run_python(source, termination_grace=.1)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.descendants_terminated)
        self.assert_stopped(int((self.cwd / 'child.pid').read_text()))

    def test_parent_exit_with_inherited_open_pipes_remains_bounded(self):
        source = ("import subprocess,sys,pathlib; "
                  "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                  "pathlib.Path('child.pid').write_text(str(p.pid))")
        with self.assertRaises(ExecutionError) as caught:
            self.run_python(source, timeout_seconds=.4, termination_grace=.1)
        self.assertEqual(caught.exception.reason, 'timeout')
        self.assert_stopped(int((self.cwd / 'child.pid').read_text()))

    def test_explicit_cancellation_stops_real_process(self):
        event = threading.Event()
        timer = threading.Timer(.2, event.set)
        timer.start()
        self.addCleanup(timer.cancel)
        with self.assertRaises(ExecutionError) as caught:
            self.run_python("import time; print('started',flush=True); time.sleep(30)",
                            cancelled=event.is_set, termination_grace=.05)
        self.assertEqual(caught.exception.reason, 'cancelled')
        self.assertIn('started', caught.exception.partial_result.stdout)

    def test_interrupt_cleans_real_child_before_returning_safe_error(self):
        # Callback interruption exercises the same cleanup branch as Ctrl-C,
        # after the actual subprocess is spawned, without signalling the test host.
        started = time.monotonic()
        def interrupted():
            if time.monotonic() - started > .2:
                raise KeyboardInterrupt
            return False
        with self.assertRaises(ExecutionError) as caught:
            self.run_python("import os,time,pathlib; pathlib.Path('leader.pid').write_text(str(os.getpid())); time.sleep(30)",
                            cancelled=interrupted, termination_grace=.05)
        self.assertEqual(caught.exception.reason, 'cancelled')
        self.assert_stopped(int((self.cwd / 'leader.pid').read_text()))

    def test_closed_stdout_still_observes_timeout(self):
        with self.assertRaises(ExecutionError) as caught:
            self.run_python('import os,time; os.close(1); os.close(2); time.sleep(30)',
                            timeout_seconds=.25, termination_grace=.05)
        self.assertEqual(caught.exception.reason, 'timeout')

    def test_empty_option_value_is_preserved_without_allowing_empty_executable(self):
        result = run_process([sys.executable, '-c', 'import sys; print(repr(sys.argv[1]))', ''],
                             cwd=self.cwd, env=model_environment(), timeout_seconds=2)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "''")
        with self.assertRaises(ExecutionError):
            run_process(['', '-p'], cwd=self.cwd, env={}, timeout_seconds=1)

    def test_invalid_options_and_start_errors_do_not_echo_arguments(self):
        for value in (0, float('inf'), True):
            with self.subTest(timeout=value), self.assertRaises(ExecutionError):
                self.run_python('pass', timeout_seconds=value)
        with self.assertRaises(ExecutionError) as caught:
            run_process(['/missing/SENSITIVE_SENTINEL'], cwd=self.cwd, env={}, timeout_seconds=1)
        self.assertEqual(caught.exception.reason, 'start_failed')
        self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))


class ModelEnvironmentTests(unittest.TestCase):
    def test_removes_unrelated_credentials_but_keeps_reviewed_model_auth(self):
        supplied = {'PATH': '/usr/bin', 'HOME': '/fixture', 'ANTHROPIC_API_KEY': 'model-auth',
                    'CLAUDE_CODE_OAUTH_TOKEN': 'model-oauth', 'CLAUDECODE': 'nested',
                    'AWS_SECRET_ACCESS_KEY': 'aws', 'GOOGLE_APPLICATION_CREDENTIALS': '/cloud/key',
                    'GH_TOKEN': 'github', 'TELEGRAM_BOT_TOKEN': 'telegram', 'SSH_AUTH_SOCK': '/agent',
                    'DATABASE_PASSWORD': 'db', 'KUBECONFIG': '/kube/config', 'GIT_CONFIG_GLOBAL': '/injected'}
        cleaned = model_environment(supplied)
        for key in ('AWS_SECRET_ACCESS_KEY', 'GOOGLE_APPLICATION_CREDENTIALS', 'GH_TOKEN',
                    'TELEGRAM_BOT_TOKEN', 'SSH_AUTH_SOCK', 'DATABASE_PASSWORD', 'KUBECONFIG', 'CLAUDECODE'):
            self.assertNotIn(key, cleaned)
        self.assertEqual(cleaned['ANTHROPIC_API_KEY'], 'model-auth')
        self.assertEqual(cleaned['CLAUDE_CODE_OAUTH_TOKEN'], 'model-oauth')
        self.assertEqual(cleaned['PATH'], '/usr/bin')
        self.assertEqual(cleaned['GIT_CONFIG_GLOBAL'], os.devnull)
        self.assertEqual(supplied['GH_TOKEN'], 'github')

    def test_operator_can_preserve_exact_cloud_provider_names_explicitly(self):
        cleaned = model_environment({'AWS_ACCESS_KEY_ID': 'required', 'AWS_SECRET_ACCESS_KEY': 'required-secret',
                                     'AWS_SESSION_TOKEN': 'required-token', 'GH_TOKEN': 'not-required'},
                                    preserve_names={'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN'})
        self.assertEqual(cleaned['AWS_SESSION_TOKEN'], 'required-token')
        self.assertNotIn('GH_TOKEN', cleaned)


if __name__ == '__main__':
    unittest.main()
