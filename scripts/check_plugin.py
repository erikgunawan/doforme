"""Dependency-free checks for this plugin's capability boundary and resources."""
import json
import re
import sys
from pathlib import Path


# Reviewed capabilities: changing a stage requires changing this explicit registry.
STAGES = {
    "analyze": ("investigator", "bug-resolution", "Read, Glob, Grep", "read_only", "analysis_v2", []),
    "plan": ("planner", "bug-planning", "Read, Glob, Grep", "read_only", "plan_v2", ["analyze"]),
    "fix": ("fixer", "bug-fixing", "Read, Glob, Grep, Edit, Write, Bash", "mutation", "fix_v1", ["plan"]),
    "test": ("tester", "bug-testing", "Read, Glob, Grep, Bash", "execution", "test_v1", ["fix"]),
    "review": ("reviewer", "bug-review", "Read, Glob, Grep, Bash", "read_only", "review_v1", ["test"]),
    "pr": ("pr-preparer", "pr-preparation", "Read, Glob, Grep, Bash", "read_only", "pr_v1", ["review"]),
}


UTILITIES = {"endtoend": ("workflow-runner", "workflow-orchestration", "Read, Bash"),
             "status": ("status-reader", "workflow-status", "Read, Bash"),
             "init": ("repo-onboarder", "repo-onboarding", "Read, Bash"),
             "doctor": ("preflight-reader", "workflow-preflight", "Read, Bash")}


def frontmatter(path):
    """Read our deliberately flat frontmatter subset; reject ambiguous syntax."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"{path}: missing frontmatter")
    fields = {}
    for line in text.split("\n---\n", 1)[0][4:].splitlines():
        key, sep, value = line.partition(":")
        if not sep or key in fields or not re.fullmatch(r"[a-z-]+", key):
            raise ValueError(f"{path}: unsupported or duplicate frontmatter field")
        fields[key] = value.strip()
    return fields


def check_graph(graph):
    """Check a portable DAG without executing or persisting any workflow."""
    if graph.get("contract_version") != 2 or graph.get("persistence") != "host_checkpoint" or graph.get("automatic_transitions") is not False:
        raise ValueError("Unsupported graph version, persistence, or automatic transitions")
    nodes = graph["nodes"]
    visited, visiting = set(), set()

    def visit(name):
        if name not in nodes:
            raise ValueError(f"Unknown prerequisite: {name}")
        if name in visiting:
            raise ValueError("Dependency cycle detected")
        if name in visited:
            return
        node = nodes[name]
        if not isinstance(node.get("implemented"), bool) or not isinstance(node.get("requires"), list):
            raise ValueError(f"Invalid graph node: {name}")
        expected_effects = {stage: spec[3] for stage, spec in STAGES.items()}
        if node["implemented"] and node.get("effect") != expected_effects.get(name):
            raise ValueError("Unexpected effect for implemented stage")
        visiting.add(name)
        for predecessor in node["requires"]:
            visit(predecessor)
            if node["implemented"] and not nodes[predecessor]["implemented"]:
                raise ValueError("Implemented stage depends on an unavailable stage")
        visiting.remove(name)
        visited.add(name)

    for name in nodes:
        visit(name)
    for stage, spec in STAGES.items():
        if nodes.get(stage, {}).get("requires") != spec[5]:
            label = "analyze-to-plan" if stage in ("analyze", "plan") else "plan-to-fix" if stage == "fix" else "fix-to-test" if stage == "test" else "test-to-review" if stage == "review" else "review-to-pr"
            raise ValueError(f"The {label} dependency must be preserved")
        if nodes[stage].get("result_contract") != spec[4]:
            raise ValueError("Requirement-aware v2 result contracts and declared stage contracts are required")


def check_antigravity(root):
    native = Path(root) / 'integrations/antigravity'
    agent = (native / 'agents/doforme-reader.md').read_text()
    front = agent.split('\n---\n', 1)[0]
    if re.findall(r'^  - (.+)$', front, re.M) != ['view_file', 'grep_search', 'find_by_name', 'list_dir']:
        raise ValueError('Antigravity worker must remain read/search-only')
    for field in ('mainAgent: true', 'subagent: false', 'commandExecutionPolicy: off',
                  'inheritMcp: false', 'inheritCustomizations: true'):
        if field not in front.splitlines():
            raise ValueError('Antigravity worker must preserve its reviewed capabilities and guard inheritance')
    hooks = json.loads((native / 'hooks.json').read_text())
    if hooks != {'doforme-worker-read-boundary': {'PreToolUse': [{'matcher': '*', 'hooks': [
            {'type': 'command', 'command': 'python3 -B ./scripts/antigravity_guard.py', 'timeout': 10}]}]}}:
        raise ValueError('Antigravity pre-execution guard must cover every tool')
    expected = {'doctor', 'status', 'analyze', 'plan'}
    entries = list((native / 'skills').glob('*/SKILL.md'))
    if {p.parent.name for p in entries} != expected:
        raise ValueError('Antigravity preview must expose exactly four entry skills')
    for path in entries:
        fields = frontmatter(path)
        if fields.get('name') != path.parent.name or fields.get('disable-model-invocation') != 'true':
            raise ValueError('Antigravity entry must remain explicit and correctly named')


def check(root):
    root = Path(root).resolve()
    check_antigravity(root)
    guide = frontmatter(root / 'skills/guided-workflow/SKILL.md')
    if guide != {'name': 'guided-workflow',
                 'description': 'Conversational setup, issue selection, saved reports, and concrete scope approvals',
                 'user-invocable': 'false', 'disable-model-invocation': 'true'}:
        raise ValueError('Guided method must remain an explicit hidden helper')
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    if manifest["name"] != "doforme":
        raise ValueError("Plugin namespace must be doforme")
    if set(manifest) - {"name", "version", "description", "author", "repository", "keywords"}:
        raise ValueError("Review new manifest capabilities before accepting them")
    components = [(name, spec[0], spec[1]) for name, spec in {**STAGES, **UTILITIES}.items()]
    helpers = {'init': 'init_repo.py', 'doctor': 'doctor.py',
               'status': 'run_workflow.py', 'endtoend': 'run_workflow.py'}
    for command_name, agent_name, skill_name in components:
        command_path = root / f"commands/{command_name}.md"
        command = frontmatter(command_path)
        # Public commands are interactive coordinators; worker agents remain restricted.
        required = {"disable-model-invocation": "true",
                    "allowed-tools": "Read, Glob, Grep, AskUserQuestion"}
        if any(command.get(key) != value for key, value in required.items()):
            raise ValueError(f"{command_name} must use the explicit guided coordinator")
        if set(command) - {*required, "description", "argument-hint"}:
            raise ValueError("Review new command capabilities; coordinators cannot fork or preapprove Bash")
        guided = '${CLAUDE_PLUGIN_ROOT}/skills/guided-workflow/SKILL.md'
        helper = '${CLAUDE_PLUGIN_ROOT}/scripts/guided_workflow.py'
        legacy = root / f'skills/guided-workflow/references/advanced/{command_name}.md'
        if guided not in command_path.read_text() or helper not in command_path.read_text() or not legacy.is_file():
            raise ValueError("Coordinator must keep its guided helper and restricted advanced method")
        agent = frontmatter(root / f"agents/{agent_name}.md")
        expected_tools = {**STAGES, **UTILITIES}[command_name][2]
        if agent.get("name") != agent_name or agent.get("tools") != expected_tools:
            raise ValueError(f"{agent_name} must have only {expected_tools}")
        if set(agent) != {"name", "description", "tools"}:
            raise ValueError("Review new agent capabilities")
        skill = frontmatter(root / f"skills/{skill_name}/SKILL.md")
        if skill.get("user-invocable") != "false" or skill.get("disable-model-invocation") != "true":
            raise ValueError("Helper skill must not bypass its command entry point")
        if set(skill) != {"name", "description", "user-invocable", "disable-model-invocation"}:
            raise ValueError("Review new helper skill capabilities")
        body = command_path.read_text()
        if command_name in helpers:
            helper = '${CLAUDE_PLUGIN_ROOT}/scripts/' + helpers[command_name]
            if helper not in body:
                raise ValueError(f'{command_name} must supply its exact packaged helper path')
        resource = "${CLAUDE_PLUGIN_ROOT}/skills/" + skill_name + "/SKILL.md"
        if "$ARGUMENTS" not in body or resource not in legacy.read_text():
            raise ValueError(f"{command_name} must forward input and resolve its packaged skill")
    graph = json.loads((root / "skills/bug-resolution/references/workflow.json").read_text())
    check_graph(graph)
    if {name for name, node in graph["nodes"].items() if node["implemented"]} != set(STAGES):
        raise ValueError("Graph implemented nodes must match command entry points")
    for directory in ("commands", "agents", "skills"):
        for path in (root / directory).rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if "!`" in text:
                raise ValueError(f"{path}: dynamic shell execution is forbidden")
    for path in root.rglob("*.md"):
        if ".git" in path.relative_to(root).parts:
            continue
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.is_relative_to(root) or not resolved.is_file():
                raise ValueError(f"{path}: missing or escaping reference {target}")


if __name__ == "__main__":
    try:
        check(Path(__file__).resolve().parents[1])
    except (ValueError, KeyError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    print("PASS: plugin structure, resource links, stage capabilities, and dependency graph")
