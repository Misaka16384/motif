from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import uuid

try:
    import tomllib
except ImportError:
    from .vendor import tomli as tomllib

SKILL_ROOT = Path(__file__).resolve().parents[2]
PROJECT_MARKER = "created_by: research-talk"


class TalkError(Exception):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def user_home():
    override = os.environ.get("RESEARCH_TALK_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "research-talk"
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "research-talk"


def read_json(path, default=None):
    if not Path(path).exists():
        return default
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise TalkError(f"Cannot read {path}: {exc}") from exc


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, data):
    atomic_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def settings():
    return read_json(user_home() / "settings.json", {"schema": 1, "projects": [], "roots": []})


def register(project):
    data = settings()
    paths = data.setdefault("projects", [])
    value = str(Path(project).resolve())
    if value not in paths:
        paths.append(value)
    write_json(user_home() / "settings.json", data)


def within(root, candidate):
    root, candidate = Path(root).resolve(), Path(candidate).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise TalkError(f"Path escapes the project: {candidate}") from exc
    return candidate


def marked(root):
    path = Path(root) / "PROJECT.md"
    if not path.is_file():
        return False
    try:
        header = path.read_text(encoding="utf-8").split("---", 2)
        return len(header) == 3 and header[0].strip() == "" and PROJECT_MARKER in header[1].splitlines()
    except (OSError, UnicodeError):
        return False


def load_project(root):
    root = Path(root).expanduser().resolve()
    if not marked(root):
        raise TalkError(f"Not a research-talk project: {root}. Read PROJECT.md or use init for a new directory.")
    try:
        data = tomllib.loads((root / "talk.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TalkError(f"Invalid talk.toml: {exc}") from exc
    if data.get("schema") != 1 or data.get("created_by") != "research-talk":
        raise TalkError("Unsupported or unmarked project configuration.")
    names = set()
    scenes = data.get("scenes", [])
    if not scenes:
        raise TalkError("talk.toml must contain at least one scene.")
    for scene in scenes:
        name = scene.get("name", "")
        if not name.isidentifier() or name in names:
            raise TalkError(f"Scene names must be unique Python identifiers: {name!r}")
        names.add(name)
        source = within(root, root / scene.get("file", ""))
        if not source.is_file() or source.suffix != ".py":
            raise TalkError(f"Missing Python scene source: {source}")
        for dependency in scene.get("depends", []):
            if not within(root, root / dependency).is_file():
                raise TalkError(f"Missing declared dependency: {dependency}")
    for name, profile in data.get("profiles", {}).items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise TalkError("Profile names must be simple directory names.")
        for key in ("width", "height"):
            value = profile.get(key)
            if type(value) is not int or value <= 0 or value % 2:
                raise TalkError(f"{name}.{key} must be a positive even integer.")
        if not isinstance(profile.get("fps"), (int, float)) or profile["fps"] <= 0:
            raise TalkError(f"{name}.fps must be positive.")
    if not data.get("profiles"):
        raise TalkError("No rendering profiles configured.")
    pace = data.get("visual", {}).get("pace", 0.7)
    if not isinstance(pace, (float, int)) or pace <= 0:
        raise TalkError("visual.pace must be positive.")
    return root, data


def toml_text(data):
    """Write the small project configuration using the TOML data model."""
    lines = []

    def scalar(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, (int, float)):
            return repr(value)
        if isinstance(value, list):
            return "[" + ", ".join(scalar(item) for item in value) + "]"
        raise TalkError(f"Unsupported configuration value: {type(value).__name__}")

    def table(values, prefix=()):
        for key, value in values.items():
            if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
                raise TalkError(f"Unsupported configuration key: {key}")
            if not isinstance(value, dict) and not (isinstance(value, list) and value and isinstance(value[0], dict)):
                lines.append(f"{key} = {scalar(value)}")
        for key, value in values.items():
            path = (*prefix, key)
            if isinstance(value, dict):
                lines.extend(["", "[" + ".".join(path) + "]"])
                table(value, path)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value:
                    lines.extend(["", "[[" + ".".join(path) + "]]"])
                    table(item, path)
    table(data)
    return "\n".join(lines) + "\n"


def save_project(root, data):
    atomic_text(Path(root) / "talk.toml", toml_text(data))


def run_environment(root, data):
    env = os.environ.copy()
    paths = [str(Path(item).expanduser().resolve()) for item in data.get("environment", {}).get("path", [])]
    python = data.get("environment", {}).get("python", "")
    if python:
        paths.insert(0, str(Path(python).parent))
    env["PATH"] = os.pathsep.join(paths + [env.get("PATH", "")])
    env["PYTHONPATH"] = os.pathsep.join([str(root / "anim"), env.get("PYTHONPATH", "")])
    visual = data.get("visual", {})
    for key, fallback in (("pace", 0.7), ("background", "#000000"), ("foreground", "#FFFFFF"), ("seed", 0)):
        env["RESEARCH_TALK_" + key.upper()] = str(visual.get(key, fallback))
    return env


def python_executable(data):
    import sys
    value = data.get("environment", {}).get("python", "") or sys.executable
    # Resolving a venv's bin/python symlink would select the system interpreter.
    path = Path(os.path.abspath(os.path.expanduser(value)))
    if not path.is_file():
        raise TalkError(f"Configured Python does not exist: {path}")
    return str(path)


def run_logged(argv, cwd, env, log, on_start=None):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps({"argv": [str(x) for x in argv], "cwd": str(cwd), "started": now()}, ensure_ascii=False) + "\n")
        stream.flush()
        process = subprocess.Popen([str(x) for x in argv], cwd=cwd, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=(os.name != "nt"))
        if on_start:
            on_start(process.pid)
        try:
            result = process.wait()
        except BaseException:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            process.wait()
            raise
        if result:
            tail = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-12:])
            raise TalkError(f"Command failed (exit {result}); log: {log}\n{tail}")
    return result


@contextlib.contextmanager
def project_lock(root):
    path = root / ".build" / "operation.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise TalkError(f"Project operation locked: {path}. Inspect status and active processes; use unlock --yes only after they have stopped.") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "started": now()}, stream)
        yield
    finally:
        path.unlink(missing_ok=True)


def execution_note(root, message):
    path = root / "PROJECT.md"
    begin, end = "<!-- research-talk:execution -->", "<!-- /research-talk:execution -->"
    text = path.read_text(encoding="utf-8")
    block = f"{begin}\n## Latest execution (tool maintained)\n\nUpdated: {now()}\n\n{message}\n{end}"
    if begin in text and end in text:
        start, finish = text.index(begin), text.index(end) + len(end)
        text = text[:start] + block + text[finish:]
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    atomic_text(path, text)
