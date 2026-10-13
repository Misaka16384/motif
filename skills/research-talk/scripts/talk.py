#!/usr/bin/env python3
"""Portable, local CLI. Discovery and setup do not import Manim."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from talklib.common import TalkError, load_project, settings, user_home, write_json
from talklib import project, environment, build


def parser():
    result = argparse.ArgumentParser(description="Discover, prepare, render and export local research-talk projects.")
    commands = result.add_subparsers(dest="command", required=True)
    discovery = commands.add_parser("discover", help="Find marked projects in bounded roots and the local registry")
    discovery.add_argument("--root", action="append", default=[])
    discovery.add_argument("--depth", type=int, default=4)
    discovery.add_argument("--limit", type=int, default=100)
    initializer = commands.add_parser("init", help="Create a new project without overwriting anything")
    initializer.add_argument("directory")
    initializer.add_argument("--name", default="Research Talk")
    initializer.add_argument("--no-register", action="store_true")
    roots = commands.add_parser("roots", help="Show or add project search roots")
    roots.add_argument("--add", action="append", default=[])
    for name in ("status", "doctor", "setup", "render", "check", "preview", "export", "smoke", "unlock"):
        command = commands.add_parser(name)
        command.add_argument("--project", default=".")
        if name in ("render", "check", "preview", "export"):
            command.add_argument("--profile", default="preview")
        if name in ("render", "check", "preview"):
            command.add_argument("--scene", action="append", default=[])
        if name in ("render", "smoke"):
            command.add_argument("--force", action="store_true")
            command.add_argument("--allow-low-memory", action="store_true")
        if name == "setup":
            command.add_argument("--scope", choices=["project", "shared"])
            command.add_argument("--reuse", help="Explicit existing rendering Python; does not install into it")
            command.add_argument("--base-python", help="Python used to create the chosen isolated venv")
            command.add_argument("--path", action="append", default=[], help="Approved external tool binary directories")
            command.add_argument("--yes", action="store_true", help="Execute the previously agreed setup plan")
        if name == "doctor":
            command.add_argument("--python", help="Probe a candidate Python without binding it")
            command.add_argument("--path", action="append", default=[])
        if name == "preview":
            command.add_argument("--sample", choices=["last", "all"], default="last")
        if name == "check":
            command.add_argument("--strict-layout", action="store_true")
        if name == "export":
            command.add_argument("--format", choices=["html", "pptx", "both"], default="html")
            command.add_argument("--one-file", action="store_true")
        if name == "unlock":
            command.add_argument("--yes", action="store_true", help="Confirm recorded parent/child processes have stopped")
    return result


def dispatch(args):
    if args.command == "discover":
        if not 0 <= args.depth <= 12 or not 1 <= args.limit <= 500:
            raise TalkError("Discovery depth must be 0..12 and limit 1..500.")
        return project.discover(args.root, args.depth, args.limit), 0
    if args.command == "init":
        return project.initialize(args.directory, args.name, not args.no_register), 0
    if args.command == "roots":
        data = settings()
        for root in args.add:
            value = str(Path(root).expanduser().resolve())
            if not Path(value).is_dir():
                raise TalkError(f"Search root does not exist: {value}")
            if value not in data.setdefault("roots", []):
                data["roots"].append(value)
        if args.add:
            write_json(user_home() / "settings.json", data)
        return data, 0
    root, config = load_project(args.project)
    if args.command == "status":
        return project.status(root), 0
    if args.command == "doctor":
        config.setdefault("environment", {}).setdefault("path", []).extend(args.path)
        report = environment.inspect(root, config, args.python)
        return report, 0 if report["ready"] else 2
    if args.command == "setup":
        result = environment.configure(root, config, args.scope, args.yes, args.reuse, args.base_python, args.path)
        return result, 0 if not result["executed"] or result["report"]["ready"] else 2
    if args.command == "render":
        return build.render(root, config, args.profile, args.scene, args.force, args.allow_low_memory), 0
    if args.command == "check":
        result = build.check(root, config, args.profile, args.scene)
        return result, 2 if not result["ok"] else (3 if args.strict_layout and result["layout_findings"] else 0)
    if args.command == "preview":
        return build.preview(root, config, args.profile, args.sample, args.scene), 0
    if args.command == "export":
        formats = ("html", "pptx") if args.format == "both" else (args.format,)
        return build.export(root, config, args.profile, formats, args.one_file), 0
    if args.command == "smoke":
        rendering = build.render(root, config, "smoke", force=args.force, allow_low_memory=args.allow_low_memory)
        output = build.export(root, config, "smoke", ("html", "pptx"))
        return {"render": rendering, "export": output,
                "limits": "Formula compilation, scene rendering, media metadata and export packaging were exercised. Actual browser/PowerPoint playback needs its own check."}, 0
    if args.command == "unlock":
        if not args.yes:
            raise TalkError("Inspect status and recorded processes first; --yes confirms they have stopped.")
        lock = root / ".build" / "operation.lock"
        lock.unlink(missing_ok=True)
        return {"lock_removed": str(lock), "next": "Inspect the last running scene and resume explicitly."}, 0
    raise TalkError("Unknown command")


def main(argv=None):
    try:
        result, code = dispatch(parser().parse_args(argv))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except KeyboardInterrupt:
        print("Interrupted; inspect project status and logs before resuming.", file=sys.stderr)
        return 130
    except (TalkError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
