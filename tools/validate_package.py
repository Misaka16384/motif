#!/usr/bin/env python3
"""Check the portable skill package, without installing render dependencies."""
import ast
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/research-talk"


def validate():
    issues = []
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "research-talk" or not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        issues.append("Invalid package name/version")
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    header = text.split("---", 2)
    if len(header) != 3 or not re.search(r"^name: research-talk$", header[1], re.MULTILINE) or not re.search(r"^description: .+", header[1], re.MULTILINE):
        issues.append("Missing skill frontmatter")
    if len(text.splitlines()) > 160:
        issues.append("Entrypoint has grown beyond this package's intended concise scope")
    for document in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
        content = document.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", content):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (document.parent / target).resolve()
            if not resolved.is_relative_to(SKILL.resolve()) or not resolved.exists():
                issues.append(f"Broken or escaping reference in {document.name}: {target}")
    for file in ROOT.rglob("*.py"):
        if any(part in (".git", ".build", ".venv", ".runtime", "dist", "__pycache__", "examples") for part in file.relative_to(ROOT).parts):
            continue
        try:
            source = file.read_text(encoding="utf-8")
            ast.parse(source, filename=str(file))
            if any(ord(char) < 32 and char not in "\n\r\t" for char in source):
                issues.append(f"Control characters: {file.relative_to(ROOT)}")
        except (SyntaxError, UnicodeError) as exc:
            issues.append(f"Invalid Python {file.relative_to(ROOT)}: {exc}")
    for name in ("scripts/talk.py", "scripts/media_helper.py", "scripts/requirements.txt", "assets/starter/talk.toml", "assets/starter/PROJECT.md", "scripts/talklib/vendor/tomli/LICENSE"):
        if not (SKILL / name).is_file():
            issues.append(f"Missing resource: {name}")
    tag = __import__("os").environ.get("GITHUB_REF_NAME", "")
    if tag.startswith("v") and tag != "v" + manifest["version"]:
        issues.append("Release tag and manifest version differ")
    return issues


if __name__ == "__main__":
    issues = validate()
    print(json.dumps({"ok": not issues, "issues": issues}, indent=2))
    raise SystemExit(bool(issues))
