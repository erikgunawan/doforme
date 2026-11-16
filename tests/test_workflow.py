"""Deterministic adapter gates; fake executor results are not model evidence."""
import importlib.util
import contextlib
import io
import json
import os
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
                trace += [{"message": {"content": [{"type": "tool_use", "name": "Bash", "id": ident, "input": {"command": command}}]}}, {"message": {"content": [{"type": "tool_result", "tool_use_id": ident, "is_error": error, "content": "Exit code 1\nAssertionError: synthetic mismatch" if error else "3 synthetic checks OK"}]}}]
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

    def test_host_prompt_supplies_the_exact_git_permission_commands(self):
        def inspect_prompt(stage, repo, prompt, config):
            for command in WF.permitted_bash_calls(stage, config):
                self.assertIn(command, prompt)
            return self.executor(stage, repo, prompt, config)
        result = self.run_pipeline(executor=inspect_prompt, allow_fix=True, allow_execution=True)
        self.assertEqual(result['status'], 'complete')
        self.assertNotIn(self.config['test_commands'][0], WF.permitted_bash_calls('pr', self.config))

    def test_observed_pr_command_variants_remain_outside_permission_scope(self):
        for suffix in ('status --porcelain --untracked-files=all', 'diff --check'):
            command = ' '.join(WF.SAFE_GIT_PREFIX) + ' ' + suffix
            rows = [{'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': command}}]}}]
            with self.subTest(command=command), self.assertRaisesRegex(ValueError, 'Unscoped program'):
                WF.audit_calls(self.repo, rows, 'pr', self.config)

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

    def test_unrelated_ci_credentials_not_inherited_by_models(self):
        result = WF.model_environment({"GITHUB_TOKEN": "fake", "TELEGRAM_BOT_TOKEN": "fake", "ACTIONS_RUNTIME_TOKEN": "fake",
                                       "ANTHROPIC_API_KEY": "model-auth", "PATH": "/bin"})
        self.assertNotIn("GITHUB_TOKEN", result)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", result)
        self.assertNotIn("ACTIONS_RUNTIME_TOKEN", result)
        self.assertEqual(result["ANTHROPIC_API_KEY"], "model-auth")

    def test_environment_error_is_not_regression_evidence(self):
        _, rows = self.executor("fix", self.repo, "", self.config)
        rows[1]["message"]["content"][0]["content"] = "Exit code 1\nModuleNotFoundError: missing dependency"
        with self.assertRaisesRegex(ValueError, "assertion red-before"):
            WF.validation_checked(rows, "fix", self.config)

    def test_validation_tool_output_is_preserved_privately(self):
        state = self.run_pipeline(allow_fix=True, allow_execution=True)
        record = state["validation_artifacts"]["fix"]
        path = self.base / "output/history" / record["filename"]
        evidence = json.loads(path.read_text())
        self.assertTrue(evidence[0]["assertion_failure"])
        self.assertEqual(evidence[0]["exit_code"], 1)
        self.assertEqual(evidence[-1]["exit_code"], 0)
        self.assertEqual(evidence[-1]["command"], self.config["test_commands"][0])
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_tampered_validation_evidence_blocks_resume(self):
        state = self.run_pipeline(allow_fix=True, allow_execution=True)
        record = state["validation_artifacts"]["test"]
        path = self.base / "output/history" / record["filename"]
        path.write_text('[]')
        with self.assertRaisesRegex(ValueError, "content changed"):
            WF.pipeline(self.repo, self.config, self.base / "output", True, True,
                        executor=self.executor, resume=True)

    def test_requirement_alias_cannot_be_authorized_for_edit(self):
        self.config["requirements"] = ["./requirements.md"]
        self.config["edit_paths"] = ["requirements.md"]
        with self.assertRaisesRegex(ValueError, "read-only"):
            self.run_pipeline(allow_fix=True, allow_execution=True)
        self.assertEqual(self.calls, [])

    def test_existing_source_cannot_be_declared_as_scratch_artifact(self):
        self.config["artifact_paths"] = ["source.py"]
        with self.assertRaisesRegex(ValueError, "new temporary"):
            self.run_pipeline()

    def test_duplicate_canonical_scope_paths_are_rejected(self):
        self.config["edit_paths"] = ["source.py", "./source.py"]
        with self.assertRaisesRegex(ValueError, "Duplicate canonical"):
            self.run_pipeline()

    def test_completed_non_bug_stops_and_retry_cannot_bypass_triage(self):
        def executor(*args):
            result, rows = self.executor(*args)
            result["verdict"] = "not_a_bug"
            return result, rows
        result = self.run_pipeline(executor)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["results"]["analyze"]["status"], "complete")
        self.assertEqual(self.calls, ["analyze"])
        result = WF.pipeline(self.repo, self.config, self.base / "output", executor=executor,
                             resume=True, retry=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.calls, ["analyze"])
        self.assertIsNone(WF.compact(result)["next_stage"])

    def test_status_rejects_missing_prerequisite_artifact(self):
        self.run_pipeline()
        path = self.base / "output/checkpoint.json"
        state = json.loads(path.read_text())
        del state["artifact_index"]["analyze"]
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, "missing prerequisite"):
            WF.status_checkpoint(self.repo, self.base / "output")

    def test_status_rejects_missing_observed_validation_artifact(self):
        self.run_pipeline(allow_fix=True, allow_execution=True)
        path = self.base / "output/checkpoint.json"
        state = json.loads(path.read_text())
        del state["validation_artifacts"]["fix"]
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, "Validation evidence artifact missing"):
            WF.status_checkpoint(self.repo, self.base / "output")

    def test_status_rejects_modified_display_report(self):
        self.run_pipeline()
        (self.base / "output/analyze.md").write_text("forged displayed report")
        with self.assertRaisesRegex(ValueError, "Displayed report"):
            WF.status_checkpoint(self.repo, self.base / "output")

    def test_snapshot_rejects_named_pipe_without_opening_it(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("requires Unix named pipes")
        os.mkfifo(self.repo / "pipe")
        # Guard the read so an unsafe implementation fails immediately instead of hanging.
        from unittest.mock import patch
        original = Path.read_bytes
        def read(path):
            if path.name == "pipe":
                raise AssertionError("snapshot attempted to open a named pipe")
            return original(path)
        with patch.object(Path, "read_bytes", read), self.assertRaisesRegex(ValueError, "regular file"):
            WF.snapshot(self.repo)

    def test_model_environment_disables_git_helpers_and_redirection(self):
        result = WF.model_environment({"GIT_DIR": "/outside", "GIT_EXTERNAL_DIFF": "untrusted",
                                       "PATH": "/bin"})
        self.assertNotIn("GIT_DIR", result)
        self.assertNotIn("GIT_EXTERNAL_DIFF", result)
        self.assertEqual(result["GIT_CONFIG_KEY_0"], "core.fsmonitor")
        self.assertEqual(result["GIT_CONFIG_VALUE_0"], "false")

    def test_host_git_diff_does_not_execute_repository_diff_helper(self):
        marker = self.base / "external-diff-ran"
        helper = self.base / "diff-helper"
        helper.write_text("#!/bin/sh\ntouch " + str(marker) + "\n")
        helper.chmod(0o700)
        subprocess.run(["git", "config", "diff.external", str(helper)], cwd=self.repo, check=True)
        (self.repo / "source.py").write_text("changed\n")
        diff = WF.git(self.repo, "diff")
        self.assertIn("+changed", diff)
        self.assertFalse(marker.exists())

    def test_host_git_status_does_not_execute_fsmonitor_hook(self):
        marker = self.base / "fsmonitor-ran"
        helper = self.base / "fsmonitor"
        helper.write_text("#!/bin/sh\ntouch " + str(marker) + "\n")
        helper.chmod(0o700)
        subprocess.run(["git", "config", "core.fsmonitor", str(helper)], cwd=self.repo, check=True)
        WF.git(self.repo, "status", "--porcelain")
        self.assertFalse(marker.exists())

    def test_new_artifact_can_survive_an_idempotent_resume(self):
        self.config["artifact_paths"] = ["scratch.log"]
        def executor(*args):
            result, rows = self.executor(*args)
            if args[0] == "fix":
                (self.repo / "scratch.log").write_text("temporary test output\n")
            return result, rows
        self.run_pipeline(executor, allow_fix=True, allow_execution=True)
        self.calls.clear()
        result = WF.pipeline(self.repo, self.config, self.base / "output", True, True,
                             executor=executor, resume=True)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(self.calls, [])

    def test_forged_complete_flag_does_not_establish_workflow_completion(self):
        self.run_pipeline()
        path = self.base / "output/checkpoint.json"
        state = json.loads(path.read_text())
        state["status"] = "complete"
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, "missing successful prerequisite"):
            WF.status_checkpoint(self.repo, self.base / "output")

    def test_review_changes_requested_is_a_blocked_gate(self):
        def executor(*args):
            result, rows = self.executor(*args)
            if args[0] == "review":
                result["verdict"] = "changes_requested"
            return result, rows
        result = self.run_pipeline(executor, allow_fix=True, allow_execution=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["results"]["review"]["status"], "complete")
        self.assertNotIn("pr", self.calls)

    def test_model_cannot_use_git_without_helper_suppression(self):
        row = {"message": {"content": [{"type": "tool_use", "name": "Bash",
               "input": {"command": "git diff --no-ext-diff --no-textconv"}}]}}
        with self.assertRaisesRegex(ValueError, "disable repository helpers"):
            WF.audit_calls(self.repo, [row], "review", self.config)


if __name__ == "__main__":
    unittest.main()
