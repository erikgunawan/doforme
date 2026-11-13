"""Dependency-free checks for this plugin's capability boundary and resources."""
import json
import re
import sys
from pathlib import Path


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


def check(root):
    root = Path(root).resolve()
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    if manifest["name"] != "doforme":
        raise ValueError("Plugin namespace must be doforme")
    if set(manifest) - {"name", "version", "description", "author", "repository", "keywords"}:
        raise ValueError("Review new manifest capabilities before accepting them")
    command = frontmatter(root / "commands/analyze.md")
    required = {"context": "fork", "agent": "doforme:investigator",
                "disable-model-invocation": "true", "background": "false"}
    if any(command.get(key) != value for key, value in required.items()):
        raise ValueError("Analyze must run explicitly in the restricted investigator")
    if set(command) - {*required, "description", "argument-hint"}:
        raise ValueError("Review new command capabilities")
    agent = frontmatter(root / "agents/investigator.md")
    if agent.get("name") != "investigator" or agent.get("tools") != "Read, Glob, Grep":
        raise ValueError("Investigator must have only Read, Glob, Grep")
    if set(agent) != {"name", "description", "tools"}:
        raise ValueError("Review new agent capabilities")
    skill = frontmatter(root / "skills/bug-resolution/SKILL.md")
    if skill.get("user-invocable") != "false" or skill.get("disable-model-invocation") != "true":
        raise ValueError("Helper skill must not bypass the analyze entry point")
    if set(skill) != {"name", "description", "user-invocable", "disable-model-invocation"}:
        raise ValueError("Review new helper skill capabilities")
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
    body = (root / "commands/analyze.md").read_text()
    if "$ARGUMENTS" not in body or "${CLAUDE_PLUGIN_ROOT}/skills/bug-resolution/SKILL.md" not in body:
        raise ValueError("Analyze must forward input and resolve the packaged skill")


if __name__ == "__main__":
    try:
        check(Path(__file__).resolve().parents[1])
    except (ValueError, KeyError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    print("PASS: plugin structure, resource links, and read-only capability boundary")
