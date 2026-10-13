#!/usr/bin/env python3
"""Create a distributable ZIP containing the complete skill and license."""
import argparse
import json
from pathlib import Path
import zipfile

from validate_package import ROOT, validate


def package(output, kind="both"):
    issues = validate()
    if issues:
        raise ValueError("Package invalid: " + "; ".join(issues))
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    outputs = []
    if kind in ("skill", "both"):
        skill_root = ROOT / "skills/motif"
        destination = output / f"motif-skill-{version}.zip"
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(skill_root.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, Path("motif") / path.relative_to(skill_root))
        outputs.append(destination)
    if kind == "skill":
        return outputs
    destination = output / f"motif-plugin-{version}.zip"
    excluded = {".git", "__pycache__", ".build", ".venv", ".runtime", "dist", "examples"}
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or any(part in excluded for part in path.relative_to(ROOT).parts):
                continue
            if path.name == "PROJECT.md" and path.parent == ROOT:
                continue  # Local development handoff, not skill material.
            archive.write(path, Path("motif") / path.relative_to(ROOT))
    outputs.append(destination)
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "dist"))
    parser.add_argument("--kind", choices=["skill", "plugin", "both"], default="both")
    args = parser.parse_args()
    print(json.dumps([str(p) for p in package(args.output, args.kind)], indent=2))
