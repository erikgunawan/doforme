"""Ensure the checker rejects privilege broadening and broken packaged resources."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_plugin", ROOT / "scripts/check_plugin.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "plugin"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def replace(self, path, before, after):
        target = self.root / path
        target.write_text(target.read_text().replace(before, after))

    def test_current_plugin(self):
        CHECKER.check(self.root)

    def test_shell_capability_rejected(self):
        self.replace("agents/investigator.md", "Read, Glob, Grep", "Read, Glob, Grep, Bash")
        with self.assertRaisesRegex(ValueError, "only Read"):
            CHECKER.check(self.root)

    def test_main_context_bypass_rejected(self):
        self.replace("commands/analyze.md", "context: fork", "context: inline")
        with self.assertRaisesRegex(ValueError, "restricted investigator"):
            CHECKER.check(self.root)

    def test_missing_report_resource_rejected(self):
        (self.root / "skills/bug-resolution/references/report-template.md").unlink()
        with self.assertRaisesRegex(ValueError, "missing or escaping"):
            CHECKER.check(self.root)

    def test_shell_injection_in_command_rejected(self):
        with (self.root / "commands/analyze.md").open("a") as target:
            target.write("\n!`echo unexpected`\n")
        with self.assertRaisesRegex(ValueError, "dynamic shell"):
            CHECKER.check(self.root)

    def test_planner_write_capability_rejected(self):
        self.replace("agents/planner.md", "Read, Glob, Grep", "Read, Glob, Grep, Write")
        with self.assertRaisesRegex(ValueError, "only Read"):
            CHECKER.check(self.root)

    def graph(self):
        return json.loads((self.root / "skills/bug-resolution/references/workflow.json").read_text())

    def test_graph_cycle_rejected(self):
        graph = self.graph()
        graph["nodes"]["analyze"]["requires"] = ["plan"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            CHECKER.check_graph(graph)

    def test_unknown_prerequisite_rejected(self):
        graph = self.graph()
        graph["nodes"]["plan"]["requires"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "Unknown prerequisite"):
            CHECKER.check_graph(graph)

    def test_automatic_transition_rejected(self):
        graph = self.graph()
        graph["automatic_transitions"] = True
        with self.assertRaisesRegex(ValueError, "automatic transitions"):
            CHECKER.check_graph(graph)

    def test_plan_cannot_skip_analysis(self):
        graph = self.graph()
        graph["nodes"]["plan"]["requires"] = []
        with self.assertRaisesRegex(ValueError, "analyze-to-plan"):
            CHECKER.check_graph(graph)

    def test_legacy_result_contract_rejected(self):
        graph = self.graph()
        graph["nodes"]["analyze"]["result_contract"] = "analysis_v1"
        with self.assertRaisesRegex(ValueError, "v2 result contracts"):
            CHECKER.check_graph(graph)

    def test_fix_cannot_skip_plan(self):
        graph = self.graph()
        graph["nodes"]["fix"]["requires"] = ["analyze"]
        with self.assertRaisesRegex(ValueError, "plan-to-fix"):
            CHECKER.check_graph(graph)

    def test_analyze_cannot_be_mutating(self):
        graph = self.graph()
        graph["nodes"]["analyze"]["effect"] = "mutation"
        with self.assertRaisesRegex(ValueError, "Unexpected effect"):
            CHECKER.check_graph(graph)

    def test_fixer_cannot_delegate(self):
        self.replace("agents/fixer.md", "Read, Glob, Grep, Edit, Write, Bash",
                     "Read, Glob, Grep, Edit, Write, Bash, Agent")
        with self.assertRaisesRegex(ValueError, "fixer must have only"):
            CHECKER.check(self.root)


if __name__ == "__main__":
    unittest.main()
