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
}


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
    if graph.get("contract_version") != 1 or graph.get("persistence") != "none" or graph.get("automatic_transitions") is not False:
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
            label = "analyze-to-plan" if stage in ("analyze", "plan") else "plan-to-fix" if stage == "fix" else "fix-to-test"
            raise ValueError(f"The {label} dependency must be preserved")
        if nodes[stage].get("result_contract") != spec[4]:
            raise ValueError("Requirement-aware v2 result contracts and declared stage contracts are required")


def check(root):
    root = Path(root).resolve()
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    if manifest["name"] != "doforme":
        raise ValueError("Plugin namespace must be doforme")
    if set(manifest) - {"name", "version", "description", "author", "repository", "keywords"}:
        raise ValueError("Review new manifest capabilities before accepting them")
    components = [(name, spec[0], spec[1]) for name, spec in STAGES.items()]
    for command_name, agent_name, skill_name in components:
        command_path = root / f"commands/{command_name}.md"
        command = frontmatter(command_path)
        required = {"context": "fork", "agent": f"doforme:{agent_name}",
                    "disable-model-invocation": "true", "background": "false"}
        if any(command.get(key) != value for key, value in required.items()):
            raise ValueError(f"{command_name} must run explicitly in the restricted {agent_name}")
        if set(command) - {*required, "description", "argument-hint"}:
            raise ValueError("Review new command capabilities")
        agent = frontmatter(root / f"agents/{agent_name}.md")
        expected_tools = STAGES[command_name][2]
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
        resource = "${CLAUDE_PLUGIN_ROOT}/skills/" + skill_name + "/SKILL.md"
        if "$ARGUMENTS" not in body or resource not in body:
            raise ValueError(f"{command_name} must forward input and resolve its packaged skill")
    graph = json.loads((root / "skills/bug-resolution/references/workflow.json").read_text())
    check_graph(graph)
    if {name for name, node in graph["nodes"].items() if node["implemented"]} != {c[0] for c in components}:
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
