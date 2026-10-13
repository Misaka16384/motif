from __future__ import annotations

import ast
import json
from pathlib import Path
import os
import re
import shutil

from .common import (SKILL_ROOT, TalkError, marked, load_project, settings,
                     register, write_json, user_home, now)

SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", ".build", "media", "deck", ".runtime"}


def discover(roots=(), depth=4, limit=100):
    config = settings()
    found, seen, scanned = [], set(), 0

    def add(path):
        path = Path(path).expanduser().resolve()
        if path in seen or not marked(path) or len(found) >= limit:
            return
        seen.add(path)
        state = (path / "PROJECT.md").read_text(encoding="utf-8")
        title = re.search(r'^title:\s*(.+)$', state, re.MULTILINE)
        next_step = re.search(r'^## Next step\s*\n(.*?)(?=^## |\Z)', state, re.MULTILINE | re.DOTALL)
        current = re.search(r'^## Current state\s*\n(.*?)(?=^## |\Z)', state, re.MULTILINE | re.DOTALL)
        found.append({"path": str(path), "title": title.group(1).strip('"') if title else path.name,
                      "current_state": current.group(1).strip()[:900] if current else "Read PROJECT.md",
                      "next_step": next_step.group(1).strip()[:500] if next_step else "Read PROJECT.md"})

    for path in config.get("projects", []):
        add(path)
    search_roots = list(roots) or [Path.cwd()]
    search_roots += config.get("roots", [])
    walked = set()
    for root in search_roots:
        root = Path(root).expanduser().resolve()
        if not root.is_dir() or root in walked:
            continue
        walked.add(root)
        for directory, directories, files in os.walk(root, followlinks=False):
            location = Path(directory)
            level = len(location.relative_to(root).parts)
            directories[:] = [name for name in directories if name not in SKIP and
                              not (location / name).is_symlink() and level < depth]
            scanned += 1
            if "PROJECT.md" in files:
                add(location)
            if scanned >= 2500 or len(found) >= limit:
                directories[:] = []
                break
        if scanned >= 2500 or len(found) >= limit:
            break
    return {"projects": found, "scanned_directories": scanned, "bounded": True,
            "settings": str(user_home() / "settings.json")}


def initialize(path, title, register_project=True):
    path = Path(path).expanduser().resolve()
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise TalkError(f"init requires a new or empty directory; refusing to overwrite {path}")
    if "\n" in title or "\r" in title or not title.strip():
        raise TalkError("Project title must be one nonempty line.")
    path.mkdir(parents=True, exist_ok=True)
    source = SKILL_ROOT / "assets" / "starter"
    shutil.copytree(source, path, dirs_exist_ok=True)
    config = path / "talk.toml"
    config.write_text(config.read_text(encoding="utf-8").replace('"__PROJECT_TITLE__"', json.dumps(title, ensure_ascii=False)), encoding="utf-8")
    state = path / "PROJECT.md"
    content = state.read_text(encoding="utf-8").replace('"__PROJECT_TITLE__"', json.dumps(title, ensure_ascii=False))
    state.write_text(content.replace("__PROJECT_TITLE__", title), encoding="utf-8")
    for name in ("deck", "reviews"):
        (path / name).mkdir(exist_ok=True)
    (path / ".gitignore").write_text(".venv/\n.build/\n__pycache__/\n*.pyc\n", encoding="utf-8")
    load_project(path)
    if register_project:
        register(path)
    return {"project": str(path), "state": str(state), "registered": register_project, "created": now()}


def status(path):
    root, config = load_project(path)
    builds = {}
    for profile in config["profiles"]:
        from .common import read_json
        builds[profile] = read_json(root / ".build" / profile / "status.json", {"scenes": {}, "exports": []})
    from .common import read_json
    return {"project": str(root), "title": config.get("title"),
            "environment": config.get("environment", {}), "scene_order": [s["name"] for s in config["scenes"]],
            "profiles": builds, "lock": read_json(root / ".build" / "operation.lock"),
            "handoff": str(root / "PROJECT.md")}


def lint_sources(root, config):
    findings = []
    files = sorted(set([root / s["file"] for s in config["scenes"]] + list((root / "anim").rglob("*.py"))))
    for path in files:
        text = path.read_text(encoding="utf-8")
        controls = [(i + 1, ord(character)) for i, line in enumerate(text.split("\n"))
                    for character in line if ord(character) < 32 and character not in "\t\r"]
        for line, code in controls:
            findings.append({"file": str(path), "line": line, "issue": f"Control character U+{code:04X}; possible escaped LaTeX corruption"})
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            findings.append({"file": str(path), "line": exc.lineno, "issue": exc.msg})
    return findings
