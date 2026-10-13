from __future__ import annotations

import ctypes
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET
import zipfile

from .common import (SKILL_ROOT, TalkError, execution_note, now, project_lock,
                     python_executable, read_json, run_environment, run_logged,
                     within, write_json)
from .project import lint_sources
from .pptx_autoplay import normalize_pptx, validate_slide


def free_memory_mb():
    if os.name == "nt":
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        *[(name, ctypes.c_ulonglong) for name in
                          ("total_phys", "avail_phys", "total_page", "avail_page", "total_virtual", "avail_virtual", "extended")]]
        memory = Memory()
        memory.length = ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            return memory.avail_phys / 1024 ** 2
    elif hasattr(os, "sysconf"):
        try:
            return os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024 ** 2
        except (ValueError, OSError):
            pass
    return None


def profile_directory(root, profile):
    return root / ".build" / profile


def scene_fingerprint(root, config, scene, profile):
    scene_sources = {root / item["file"] for item in config["scenes"]}
    # Shared helpers count for every scene; imports from other scene modules or data
    # files must be listed explicitly in depends.
    shared = set((root / "anim").rglob("*.py")) - scene_sources
    files = sorted(shared | {root / scene["file"]} | {root / p for p in scene.get("depends", [])})
    digest = hashlib.sha256()
    digest.update(json.dumps({"profile": config["profiles"][profile], "visual": config.get("visual", {}),
                              "python": python_executable(config), "toolkit": "0.1.0"}, sort_keys=True).encode())
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def segment_files(root, profile, scene):
    folder = profile_directory(root, profile) / "slides"
    path = folder / (scene["name"] + ".json")
    document = read_json(path)
    if not document or not document.get("slides"):
        raise TalkError(f"No slide segments for {scene['name']}: {path}")
    files = []
    for segment in document["slides"]:
        for key in ("file", "rev_file"):
            value = segment.get(key)
            if not isinstance(value, str):
                raise TalkError(f"Missing {key} in {path}")
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = path.parent.parent / candidate
            candidate = within(root, candidate)
            if not candidate.is_file() or candidate.stat().st_size == 0:
                raise TalkError(f"Missing or empty media: {candidate}")
            files.append(candidate)
    return document, list(dict.fromkeys(files))


def media_request(root, config, profile, mode, request):
    folder = profile_directory(root, profile) / "inspection"
    folder.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    input_path, output_path = folder / (token + "-request.json"), folder / (token + "-result.json")
    write_json(input_path, request)
    run_logged([python_executable(config), str(SKILL_ROOT / "scripts/media_helper.py"), mode,
                "--input", input_path, "--output", output_path], root, run_environment(root, config), folder / (mode + ".log"))
    return read_json(output_path)


def verify_scene(root, config, scene, profile, probe=True):
    metadata, files = segment_files(root, profile, scene)
    expected = config["profiles"][profile]
    if metadata.get("resolution") != [expected["width"], expected["height"]]:
        raise TalkError(f"{scene['name']} slide metadata does not match profile {profile}.")
    stats = [{"path": str(p), "size": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns} for p in files]
    previous = state_for(root, profile).get("scenes", {}).get(scene["name"], {})
    if probe and previous.get("state") == "success" and previous.get("file_stats") == stats:
        media = previous.get("media", [])
    else:
        media = media_request(root, config, profile, "probe", {"files": [str(p) for p in files], "decode": True}) if probe else []
    for item in media:
        if (item["width"], item["height"]) != (expected["width"], expected["height"]) or abs(item["fps"] - expected["fps"]) > 0.02:
            raise TalkError(f"Wrong video dimensions/fps: {item}")
        if item["duration"] <= 0:
            raise TalkError(f"Empty video duration: {item['path']}")
        if item.get("cadence_errors") or not item.get("decoded_frames", 0):
            raise TalkError(f"Decoded frame cadence is invalid: {item}")
    return {"beats": len(metadata["slides"]), "files": [str(p) for p in files],
            "file_stats": stats, "media": media, "verified": now()}


def validate_selection(config, selected):
    unknown = set(selected) - {s["name"] for s in config["scenes"]}
    if unknown:
        raise TalkError(f"Unknown scene selection: {sorted(unknown)}")


def state_for(root, profile):
    return read_json(profile_directory(root, profile) / "status.json",
                     {"schema": 1, "profile": profile, "scenes": {}, "exports": []})


def write_state(root, profile, state):
    state["updated"] = now()
    write_json(profile_directory(root, profile) / "status.json", state)


def render(root, config, profile="preview", selected=(), force=False, allow_low_memory=False):
    if profile not in config["profiles"]:
        raise TalkError(f"Unknown profile: {profile}")
    validate_selection(config, selected)
    findings = lint_sources(root, config)
    if findings:
        raise TalkError(f"Source errors: {json.dumps(findings, ensure_ascii=False)}")
    from .environment import inspect
    health = inspect(root, config)
    if not health["ready"]:
        raise TalkError(f"Rendering environment is incomplete. Run doctor/setup: {json.dumps(health, ensure_ascii=False)}")
    folder = profile_directory(root, profile)
    folder.mkdir(parents=True, exist_ok=True)
    state = state_for(root, profile)
    spec = config["profiles"][profile]
    results = []
    with project_lock(root):
        for scene in config["scenes"]:
            if selected and scene["name"] not in selected:
                continue
            fingerprint = scene_fingerprint(root, config, scene, profile)
            previous = state["scenes"].get(scene["name"], {})
            if not force and previous.get("state") == "success" and previous.get("fingerprint") == fingerprint:
                try:
                    verify_scene(root, config, scene, profile, probe=False)
                    results.append({"scene": scene["name"], "state": "reused"})
                    continue
                except TalkError:
                    pass
            free = free_memory_mb()
            minimum = spec.get("min_free_memory_mb")
            if minimum is not None and free is not None and free < minimum and not allow_low_memory:
                execution_note(root, f"Rendering paused before `{scene['name']}`: free memory {free:.0f} MiB is below the configured {minimum} MiB threshold. No automatic restart.\n\nResume only after explicit user direction and checking active processes.")
                raise TalkError(f"Low free memory: {free:.0f} MiB < {minimum}. Rendering was not started. Close other workloads or explicitly choose --allow-low-memory.")
            record = {"state": "running", "fingerprint": fingerprint, "started": now(),
                      "free_memory_mb": free, "log": str(folder / "logs" / (scene["name"] + ".log"))}
            state["scenes"][scene["name"]] = record
            write_state(root, profile, state)
            qa_path = folder / "layout" / (scene["name"] + ".json")
            qa_path.unlink(missing_ok=True)
            env = run_environment(root, config)
            env["MOTIF_QA_FILE"] = str(qa_path)
            env["RESEARCH_TALK_QA_FILE"] = str(qa_path)  # Previously copied starters.
            argv = [python_executable(config), "-m", "manim_slides", "--silent", "render", "--CE",
                    f"--resolution={spec['width']},{spec['height']}", f"--fps={spec['fps']}",
                    "--media_dir", str(folder / "media"), "--progress_bar", "none",
                    str(root / scene["file"]), scene["name"]]
            started = time.monotonic()
            try:
                def process_started(pid):
                    record["child_pid"] = pid
                    write_state(root, profile, state)
                run_logged(argv, folder, env, record["log"], process_started)
                record.update(verify_scene(root, config, scene, profile))
                record.update(state="success", finished=now(), elapsed_seconds=round(time.monotonic() - started, 2))
                results.append({"scene": scene["name"], "state": "rendered", "seconds": record["elapsed_seconds"]})
            except BaseException as exc:
                record.update(state="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", finished=now(), error=str(exc))
                execution_note(root, f"Rendering `{scene['name']}` ({profile}) {record['state']}.\n\nLog: `{record['log']}`.\n\nCompleted scenes remain recorded. Inspect active processes before any restart.")
                raise
            finally:
                write_state(root, profile, state)
        execution_note(root, f"Rendered/checked profile `{profile}`: {spec['width']} × {spec['height']} at {spec['fps']} fps.\n\n"
                       f"This operation covered {len(results)} scene(s). Full-deck freshness is checked separately before export.\n\n"
                       f"Execution record: `.build/{profile}/status.json`. No player test is implied.")
    return {"profile": profile, "results": results, "status": str(folder / "status.json")}


def check(root, config, profile="preview", selected=()):
    validate_selection(config, selected)
    if profile not in config["profiles"]:
        raise TalkError(f"Unknown profile: {profile}")
    state = state_for(root, profile)
    findings = lint_sources(root, config)
    scenes, layouts = [], []
    for scene in config["scenes"]:
        if selected and scene["name"] not in selected:
            continue
        record = state["scenes"].get(scene["name"], {})
        if record.get("state") != "success" or record.get("fingerprint") != scene_fingerprint(root, config, scene, profile):
            findings.append({"scene": scene["name"], "issue": "Missing, failed, interrupted, or stale managed render"})
            continue
        try:
            scenes.append(dict(scene=scene["name"], **verify_scene(root, config, scene, profile)))
        except TalkError as exc:
            findings.append({"scene": scene["name"], "issue": str(exc)})
        layout = read_json(profile_directory(root, profile) / "layout" / (scene["name"] + ".json"), {})
        layouts.extend(dict(scene=scene["name"], **finding) for finding in layout.get("findings", []))
    report = {"profile": profile, "ok": not findings, "media_findings": findings,
              "layout_findings": layouts, "scenes": scenes,
              "limits": "Layout sampling is diagnostic, not proof of readability; player testing and scientific review are separate."}
    write_json(profile_directory(root, profile) / "check.json", report)
    return report


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references, self.remote = [], []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ("src", "href", "data-src") or not value or value.startswith(("#", "data:", "mailto:", "javascript:")):
                continue
            parsed = urlparse(value)
            if parsed.scheme in ("http", "https"):
                if tag in ("script", "link", "video", "source", "img"):
                    self.remote.append(value)
            elif not parsed.scheme and parsed.path:
                self.references.append(unquote(parsed.path))


def validate_html(path):
    parser = LocalReferences()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    missing = [value for value in parser.references if not (Path(path).parent / value).is_file()]
    if missing or parser.remote:
        raise TalkError(f"HTML is incomplete or not offline: missing={missing}, remote={parser.remote}")
    return {"local_references": len(parser.references), "offline": True,
            "player_tested": False}


def validate_pptx(path, expected_beats=None):
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise TalkError(f"Corrupt PPTX member: {corrupt}")
        names = archive.namelist()
        slides = [name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        videos = [name for name in names if name.startswith("ppt/media/") and name.endswith(".mp4")]
        for name in names:
            if name.endswith(".xml") or name.endswith(".rels"):
                ET.fromstring(archive.read(name))
        if not slides or not videos or (expected_beats is not None and len(slides) != expected_beats):
            raise TalkError(f"PPTX slide/video count mismatch: {len(slides)} slides, {len(videos)} videos; expected {expected_beats} beats")
        autoplay = 0
        for name in slides:
            document = ET.fromstring(archive.read(name))
            validate_slide(archive, name, document)
            autoplay += 1
        return {"slides": len(slides), "embedded_videos": len(videos), "timed_video_slides": autoplay,
                "autoplay_method": "native-slide-entry-media-command", "player_tested": False, "editable_formulas": False}


def export(root, config, profile="preview", formats=("html",), one_file=False):
    with project_lock(root):
        report = check(root, config, profile)
        if not report["ok"]:
            raise TalkError("Export refused: render/check the current complete scene list first. See check.json.")
        token = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        staging = root / "deck" / ("." + profile + "-" + token)
        destination = root / "deck" / (profile + "-" + token)
        staging.mkdir(parents=True, exist_ok=False)
        folder = profile_directory(root, profile)
        scenes = [s["name"] for s in config["scenes"]]
        beats = sum(item["beats"] for item in report["scenes"])
        if "pptx" in formats:
            for scene in report["scenes"]:
                for clip in scene["media"]:
                    if clip["codec"] != "h264" or clip["pixel_format"] != "yuv420p":
                        raise TalkError(f"Office/WPS export needs H.264/yuv420p media: {clip['path']}. Render compatible clips first.")
        outputs = {}
        try:
            for format_name in formats:
                if format_name not in ("html", "pptx"):
                    raise TalkError("Supported export formats: html, pptx")
                target = staging / ("talk." + format_name)
                argv = [python_executable(config), "-m", "manim_slides", "--silent", "convert",
                        "--folder", str(folder / "slides"), "--to", format_name]
                if format_name == "html":
                    argv += ["--offline", "-cslide_number=true"]
                    if one_file:
                        argv.append("--one-file")
                else:
                    spec = config["profiles"][profile]
                    argv += [f"-cwidth={spec['width']}", f"-cheight={spec['height']}", "-cauto_play_media=true"]
                argv += [*scenes, str(target)]
                run_logged(argv, folder, run_environment(root, config), staging / (format_name + ".log"))
                if not target.is_file() or target.stat().st_size == 0:
                    raise TalkError(f"Converter returned without a usable output: {target}")
                if format_name == "html":
                    outputs[format_name] = validate_html(target)
                else:
                    normalization = normalize_pptx(target)
                    outputs[format_name] = dict(validate_pptx(target, beats), **normalization)
            write_json(staging / "validation.json", {"profile": profile, "scenes": scenes, "beats": beats, "outputs": outputs})
            # Commit a new release directory only after every requested output passes.
            # Old releases remain intact, including the paths of their assets.
            os.replace(staging, destination)
        except BaseException:
            execution_note(root, f"Export failed. Previous releases are unchanged. Inspect staging logs in `{staging}`; do not report it as a usable release.")
            raise
        state = state_for(root, profile)
        entry = {"directory": str(destination), "created": now(), "formats": list(formats), "beats": beats, "verified": "package-and-media", "player_tested": False}
        state.setdefault("exports", []).append(entry)
        write_state(root, profile, state)
        write_json(root / "deck" / ("latest-" + profile + ".json"), entry)
        execution_note(root, f"Latest validated export ({profile}): `{destination}`.\n\n{len(scenes)} scenes / {beats} beats. Formats: {', '.join(formats)}.\n\nPackage and media checks passed. Browser/PowerPoint playback has not been tested by this command.")
    return dict(entry, outputs=outputs)


def preview(root, config, profile="preview", sample="last", selected=()):
    report = check(root, config, profile, selected)
    if not report["ok"]:
        raise TalkError("Preview requires current successful renders; inspect check.json.")
    destination = root / "reviews" / (profile + "-frames")
    items = []
    for scene in config["scenes"]:
        if selected and scene["name"] not in selected:
            continue
        document, _ = segment_files(root, profile, scene)
        base = profile_directory(root, profile)
        for index, segment in enumerate(document["slides"]):
            file = Path(segment["file"])
            if not file.is_absolute():
                file = base / file
            items.append({"scene": scene["name"], "beat": index + 1, "file": str(file),
                          "destination": str(destination / scene["name"] / f"{index + 1:03d}")})
    frames = media_request(root, config, profile, "frames", {"items": items, "sample": sample})
    sheet_items = [{"image": image, "label": f"{item['scene']} / {item['beat']} / {label}"}
                   for item in frames for label, image in item["frames"].items()]
    sheets = []
    # Keep each contact sheet bounded; avoid loading a whole high-resolution deck.
    for index in range(0, len(sheet_items), 24):
        target = destination / f"sheet-{index // 24 + 1:02d}.png"
        sheets.append(media_request(root, config, profile, "sheet",
                                   {"items": sheet_items[index:index + 24], "destination": str(target)}))
    write_json(destination / "frames.json", frames)
    return {"sheets": sheets, "frames": len(sheet_items), "directory": str(destination)}
