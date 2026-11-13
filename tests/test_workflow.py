"""Deterministic adapter gates; fake executor results are not model evidence."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow", ROOT / "scripts/run_workflow.py")
WF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WF)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        silence = contextlib.redirect_stdout(io.StringIO())
        silence.__enter__()
        self.addCleanup(silence.__exit__, None, None, None)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "target"
        self.repo.mkdir()
        (self.repo / "source.py").write_text("original\n")
        (self.repo / "requirements.md").write_text("synthetic confirmed rule\n")
        for command in (["git", "init", "-q"], ["git", "add", "."],
                        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "baseline"]):
            subprocess.run(command, cwd=self.repo, check=True)
        self.config = {"issue_ref": "inline", "issue_text": "synthetic bug",
                       "requirements": ["requirements.md"], "edit_paths": ["source.py"],
                       "test_commands": ["python3 -m unittest"], "artifact_paths": []}
        self.calls = []

    def executor(self, stage, repo, prompt, config):
        self.calls.append(stage)
        trace = []
        if stage in ("fix", "test"):
            command = config["test_commands"][0]
            for index, error in enumerate([True, False] if stage == "fix" else [False]):
                ident = "call" + str(index)
                trace += [{"message": {"content": [{"type": "tool_use", "name": "Bash", "id": ident, "input": {"command": command}}]}}, {"message": {"content": [{"type": "tool_result", "tool_use_id": ident, "is_error": error, "content": "synthetic result"}]}}]
        return {"stage": stage, "status": "complete",
                "verdict": "valid_bug" if stage == "analyze" else "pass" if stage == "review" else "not_applicable",
                "requirements_status": "verified_for_scope",
                "technical_validation": "passed_scoped" if stage in ("fix", "test") else "not_run",
                "business_acceptance": "not_evaluated", "resolution_status": "not_established",
                "revision": WF.git(repo, "rev-parse", "HEAD"), "report": "synthetic stage output"}, trace

    def run_pipeline(self, executor=None, **flags):
        return WF.pipeline(self.repo, self.config, self.base / "output", executor=executor or self.executor, **flags)

    def test_sequence_requires_direct_mutation_authorization(self):
        result = self.run_pipeline()
        self.assertEqual(self.calls, ["analyze", "plan"])
        self.assertEqual((result["status"], result["stopped_stage"]), ("blocked", "fix"))

    def test_full_sequence_with_explicit_scope(self):
        result = self.run_pipeline(allow_fix=True, allow_execution=True)
        self.assertEqual(self.calls, list(WF.ORDER))
        self.assertEqual(result["status"], "complete")
        self.assertFalse(result["publication_ready"])

    def test_blocked_analyze_never_runs_plan(self):
        def executor(*args):
            result, rows = self.executor(*args)
            result.update(status="blocked", requirements_status="needs_information")
            return result, rows
        result = self.run_pipeline(executor)
        self.assertEqual(self.calls, ["analyze"])
        self.assertEqual(result["status"], "blocked")

    def test_changes_requested_never_reaches_pr(self):
        def executor(*args):
            result, rows = self.executor(*args)
            if args[0] == "review":
                result["verdict"] = "changes_requested"
            return result, rows
        result = self.run_pipeline(executor, allow_fix=True, allow_execution=True)
        self.assertEqual(result["stopped_stage"], "review")
        self.assertNotIn("pr", self.calls)

    def test_unscoped_edit_stops_after_fix(self):
        def executor(*args):
            result, rows = self.executor(*args)
            if args[0] == "fix":
                (self.repo / "requirements.md").write_text("tampered\n")
            return result, rows
        result = self.run_pipeline(executor, allow_fix=True, allow_execution=True)
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("test", self.calls)
        self.assertEqual(result["partial_changed_paths"], ["requirements.md"])

    def test_dirty_initial_target_rejected(self):
        (self.repo / "source.py").write_text("dirty\n")
        with self.assertRaisesRegex(ValueError, "clean"):
            self.run_pipeline()

    def test_shell_operators_rejected_before_execution(self):
        self.config["test_commands"] = ["python3 -m unittest; echo success"]
        with self.assertRaisesRegex(ValueError, "compound"):
            self.run_pipeline()
        self.assertEqual(self.calls, [])

    def test_secret_or_escaping_edit_scope_rejected(self):
        for name in ("../other.py", ".env", ".env.local", ".git/config", "/tmp/file", "*.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                WF.safe_path(self.repo, name)

    def test_raw_tool_audit_rejects_chained_git(self):
        row = {"message": {"content": [{"type": "tool_use", "name": "Bash",
                "input": {"command": "git diff; echo 0"}}]}}
        with self.assertRaisesRegex(ValueError, "Compound"):
            WF.audit_calls(self.repo, [row], "review", self.config)

    def test_raw_tool_audit_rejects_source_write_during_test(self):
        row = {"message": {"content": [{"type": "tool_use", "name": "Write",
                "input": {"file_path": str(self.repo / "source.py")}}]}}
        with self.assertRaisesRegex(ValueError, "Unscoped"):
            WF.audit_calls(self.repo, [row], "test", self.config)

    def test_wrong_revision_cannot_advance(self):
        result, _ = self.executor("analyze", self.repo, "", self.config)
        result["revision"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "revision"):
            WF.envelope_checked("analyze", result, WF.git(self.repo, "rev-parse", "HEAD"))

    def test_symlink_target_rejected(self):
        (self.repo / "linked").symlink_to(self.base)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            WF.snapshot(self.repo)

    def test_model_claim_cannot_replace_observed_test_results(self):
        with self.assertRaisesRegex(ValueError, "actual final successful"):
            WF.validation_checked([], "test", self.config)

    def test_green_only_does_not_prove_fix_regression(self):
        _, rows = self.executor("test", self.repo, "", self.config)
        with self.assertRaisesRegex(ValueError, "red-before"):
            WF.validation_checked(rows, "fix", self.config)

    def test_completed_resume_is_idempotent(self):
        self.run_pipeline(allow_fix=True, allow_execution=True)
        self.calls.clear()
        result = WF.pipeline(self.repo, self.config, self.base / "output", True, True,
                             executor=self.executor, resume=True)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(self.calls, [])

    def test_resume_rejects_changed_workspace(self):
        self.run_pipeline()
        (self.repo / "source.py").write_text("changed after checkpoint\n")
        with self.assertRaisesRegex(ValueError, "content changed"):
            WF.pipeline(self.repo, self.config, self.base / "output", executor=self.executor, resume=True)

    def test_resume_rejects_tampered_report(self):
        state = self.run_pipeline()
        record = state["artifact_index"]["analyze"]
        path = self.base / "output" / "history" / record["filename"]
        value = json.loads(path.read_text())
        value["report"] = "forged result"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "report content changed"):
            WF.pipeline(self.repo, self.config, self.base / "output", executor=self.executor, resume=True)

    def test_blocked_resume_requires_explicit_bounded_retry(self):
        def executor(*args):
            result, rows = self.executor(*args)
            result.update(status="blocked", requirements_status="needs_information")
            return result, rows
        self.run_pipeline(executor)
        WF.pipeline(self.repo, self.config, self.base / "output", executor=executor, resume=True)
        self.assertEqual(self.calls, ["analyze"])
        WF.pipeline(self.repo, self.config, self.base / "output", executor=executor, resume=True, retry=True)
        result = WF.pipeline(self.repo, self.config, self.base / "output", executor=executor, resume=True, retry=True)
        self.assertEqual(self.calls, ["analyze", "analyze"])
        self.assertIn("retry limit", result["reason"])

    def test_checkpoint_lock_has_one_owner(self):
        store = WF.Checkpoints(self.base / "lock-test")
        with store.locked():
            with self.assertRaisesRegex(ValueError, "locked"):
                with WF.Checkpoints(self.base / "lock-test", resume=True).locked():
                    self.fail("second owner acquired lock")
            self.assertTrue((store.root / "run.lock").exists())
        self.assertFalse((store.root / "run.lock").exists())

    def test_checkpoint_status_does_not_write(self):
        self.run_pipeline()
        path = self.base / "output" / "checkpoint.json"
        before = path.read_bytes()
        info = WF.status_checkpoint(self.repo, self.base / "output")
        self.assertTrue(info["fresh"])
        self.assertEqual(info["next_stage"], "fix")
        self.assertEqual(path.read_bytes(), before)

    def test_partial_edits_cannot_auto_resume(self):
        def executor(*args):
            result, rows = self.executor(*args)
            if args[0] == "fix":
                (self.repo / "source.py").write_text("partial implementation\n")
                result["status"] = "failed"
            return result, rows
        result = self.run_pipeline(executor, allow_fix=True, allow_execution=True)
        self.assertTrue(result["requires_manual_recovery"])
        with self.assertRaisesRegex(ValueError, "manual recovery"):
            WF.pipeline(self.repo, self.config, self.base / "output", True, True,
                        executor=executor, resume=True, retry=True)

    def test_graph_cannot_bypass_plan(self):
        graph = json.loads((ROOT / "skills/bug-resolution/references/workflow.json").read_text())
        graph["nodes"]["fix"]["requires"] = ["analyze"]
        with self.assertRaisesRegex(ValueError, "dependency"):
            WF.graph_checked(graph)

    def test_short_progress_prefix_preserves_exact_json_values(self):
        self.assertEqual(WF.parse_result_text('Review finished.\n{"status":"blocked"}'), {"status": "blocked"})

    def test_multiple_result_objects_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            WF.parse_result_text('{"status":"blocked"}\n{"status":"complete"}')

    def test_duplicate_result_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            WF.parse_result_text('{"status":"blocked","status":"complete"}')

    def test_malformed_checkpoint_does_not_resume(self):
        self.run_pipeline()
        path = self.base / "output" / "checkpoint.json"
        state = json.loads(path.read_text())
        state["results"] = []
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, "Malformed"):
            WF.pipeline(self.repo, self.config, self.base / "output", executor=self.executor, resume=True)


if __name__ == "__main__":
    unittest.main()
