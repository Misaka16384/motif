from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import sys

from .common import (SKILL_ROOT, TalkError, execution_note, now, python_executable,
                     run_environment, run_logged, save_project, settings, user_home, write_json)

TESTED = {"manim": "0.19.1", "manim-slides": "5.7.0"}
PACKAGES = ["manim", "manim-slides", "python-pptx", "Pillow", "av"]


def _probe(root, config, selected_python=None):
    python = os.path.abspath(os.path.expanduser(selected_python)) if selected_python else python_executable(config)
    env = run_environment(root, config)
    program = """import importlib.metadata as m, json, sys
versions = {}
for name in %r:
    try: versions[name] = m.version(name)
    except m.PackageNotFoundError: versions[name] = None
print(json.dumps({'python':sys.executable,'version':list(sys.version_info[:3]),'packages':versions}))
""" % PACKAGES
    try:
        result = subprocess.run([python, "-c", program], env=env, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise TalkError(f"Cannot inspect Python {python}: {result.stderr.strip()}")
        report = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise TalkError(f"Environment detection failed: {exc}") from exc
    report["tools"] = {name: shutil.which(name, path=env["PATH"]) for name in ("latex", "dvisvgm", "ffmpeg", "ffprobe")}
    report["missing_packages"] = [key for key, value in report["packages"].items() if value is None]
    report["untested_versions"] = {key: value for key, value in report["packages"].items()
                                   if key in TESTED and value and value != TESTED[key]}
    report["missing_external"] = [key for key in ("latex", "dvisvgm") if not report["tools"][key]]
    report["ready"] = (report["version"] >= [3, 10, 0] and not report["missing_packages"]
                       and not report["missing_external"])
    report["checked"] = now()
    report["note"] = "The tested Manim stack uses PyAV. ffmpeg/ffprobe CLI are optional here; LaTeX and dvisvgm are needed for the supplied math scenes. Other versions are reported, not rejected; verify their capabilities with a smoke render."
    return report


def inspect(root, config, selected_python=None, candidates=True):
    source = ("explicit-candidate" if selected_python else
              "project-config" if config.get("environment", {}).get("python") else
              "management-python")
    try:
        report = _probe(root, config, selected_python)
    except TalkError as exc:
        python = selected_python or config.get("environment", {}).get("python") or sys.executable
        env = run_environment(root, config)
        tools = {name: shutil.which(name, path=env["PATH"]) for name in ("latex", "dvisvgm", "ffmpeg", "ffprobe")}
        report = {"python": python, "version": [], "packages": {name: None for name in PACKAGES},
                  "tools": tools, "missing_packages": list(PACKAGES), "untested_versions": {},
                  "missing_external": [name for name in ("latex", "dvisvgm") if not tools[name]],
                  "ready": False, "checked": now(), "error": str(exc)}
    report["selection"] = {"source": source, "note": "Dependency results apply only to the Python shown above, not every environment on this machine. Probing does not bind or modify it."}
    if candidates:
        possibilities = [("project", root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))]
        preferences = settings()
        remembered = preferences.get("shared_python")
        if remembered:
            possibilities.append(("remembered-shared", Path(remembered)))
        active = os.environ.get("VIRTUAL_ENV")
        if active:
            possibilities.append(("active-venv", Path(active) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")))
        conda = os.environ.get("CONDA_PREFIX")
        if conda:
            possibilities.append(("active-conda", Path(conda) / ("python.exe" if os.name == "nt" else "bin/python")))
        manim = shutil.which("manim", path=run_environment(root, config)["PATH"])
        if manim:
            possibilities.append(("path-manim", Path(manim).parent / ("python.exe" if os.name == "nt" else "python")))
        report["reuse_candidates"] = []
        seen = set()
        for kind, path in possibilities:
            identity = os.path.normcase(os.path.abspath(os.path.expanduser(str(path))))
            if identity in seen:
                continue
            seen.add(identity)
            if not path.is_file():
                continue
            try:
                candidate_config = deepcopy(config)
                extra_paths = preferences.get("shared_path", []) if kind == "remembered-shared" else []
                candidate_config.setdefault("environment", {})["path"] = list(dict.fromkeys(extra_paths + config.get("environment", {}).get("path", [])))
                health = _probe(root, candidate_config, str(path))
                report["reuse_candidates"].append({"kind": kind, "python": str(path), "ready": health["ready"],
                                                  "path": candidate_config["environment"]["path"],
                                                  "packages": health["packages"], "missing_external": health["missing_external"]})
            except TalkError as exc:
                report["reuse_candidates"].append({"kind": kind, "python": str(path), "error": str(exc)})
    ready_candidates = [candidate for candidate in report.get("reuse_candidates", []) if candidate.get("ready")]
    candidate = ({"python": report["python"], "path": config.get("environment", {}).get("path", [])}
                 if report["ready"] else ready_candidates[0] if ready_candidates else
                 {"python": "<rendering-python>", "path": []})
    path_args = [argument for directory in candidate.get("path", []) for argument in ("--path", directory)]
    report["reuse_guidance"] = {
        "message": "Selected Python is ready; smoke-test before production." if report["ready"] else
                   "Missing dependencies here do not mean your existing rendering environment is missing. Probe an existing Python or choose a scoped setup plan.",
        "probe_example": ["doctor", "--project", str(root), "--python", candidate["python"], *path_args],
        "reuse_plan_example": ["setup", "--project", str(root), "--reuse", candidate["python"], *path_args],
        "external_tools": "Add --path <tex-bin> when LaTeX/dvisvgm are outside PATH; reuse keeps the selected Python's packages unchanged.",
        "setup_scope": "For a new environment, choose setup --scope project or --scope shared. Setup only executes with --yes after that choice.",
        "discovery_scope": "Candidates are bounded to the project venv, remembered shared environment, active venv/Conda and a PATH Manim launcher; no home/drive scan or automatic binding."
    }
    return report


def configure(root, config, scope, yes=False, reuse=None, base_python=None, paths=()):
    config.setdefault("environment", {})
    if reuse:
        destination = Path(os.path.abspath(os.path.expanduser(reuse)))
        plan = {"action": "reuse", "python": str(destination), "scope": "existing", "path": list(paths)}
    else:
        if scope not in ("project", "shared"):
            raise TalkError("Choose --scope project or shared, or explicitly --reuse an existing Python.")
        directory = root / ".venv" if scope == "project" else user_home() / "environments" / "render-v0.1"
        destination = directory / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        plan = {"action": "install-python-packages", "python": str(destination), "scope": scope,
                "directory": str(directory), "base_python": base_python or sys.executable,
                "requirements": str(SKILL_ROOT / "scripts/requirements.txt"), "path": list(paths),
                "index": "https://pypi.org/simple",
                "external": "Reuse detected LaTeX/dvisvgm or install them separately within the agreed scope; no system package manager is run by this command."}
    if not yes:
        return {"executed": False, "plan": plan, "next": "Confirm the environment scope with the user, then rerun with --yes."}
    log_folder = root / ".build" / "setup"
    if not reuse:
        if not destination.exists():
            run_logged([plan["base_python"], "-m", "venv", plan["directory"]], root, None, log_folder / "venv.log")
        run_logged([str(destination), "-m", "pip", "install", "--index-url", plan["index"],
                    "-r", plan["requirements"]], root, None, log_folder / "packages.log")
    config["environment"].update(python=str(destination), scope=plan["scope"], path=list(paths))
    report = inspect(root, config)
    # Binding an incomplete environment is useful for the next, scoped dependency step.
    save_project(root, config)
    if scope == "shared" and not reuse:
        preferences = settings()
        preferences["shared_python"] = str(destination)
        preferences["shared_path"] = list(paths)
        write_json(user_home() / "settings.json", preferences)
    write_json(log_folder / "environment.json", report)
    execution_note(root, f"Environment scope: `{plan['scope']}`. Interpreter: `{destination}`.\n\n"
                   f"Dependency detection: {'ready' if report['ready'] else 'incomplete'}. Smoke render has not been run by setup.\n\n"
                   "Read `.build/setup/environment.json` for details.")
    return {"executed": True, "plan": plan, "report": report}
