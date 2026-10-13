"""Native slide-entry playback for this toolkit's one-video-per-beat exports.

The timing template reproduces an author-tested PowerPoint-normalized export.
Only timing is replaced; all other XML bytes, namespaces and media are retained.
This is a structural check, not evidence of playback on an untested player.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
import posixpath
import re
import shutil
import uuid
import xml.etree.ElementTree as ET
import zipfile

from .common import SKILL_ROOT, TalkError

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P14 = "{http://schemas.microsoft.com/office/powerpoint/2010/main}"


def video_shapes(archive, slide_name, document):
    relations = {}
    rel_name = "ppt/slides/_rels/" + Path(slide_name).name + ".rels"
    if rel_name in archive.namelist():
        for relation in ET.fromstring(archive.read(rel_name)):
            target = posixpath.normpath(posixpath.join("ppt/slides", relation.get("Target", "")))
            if relation.get("TargetMode") != "External" and target in archive.namelist() and target.startswith("ppt/media/") and target.endswith(".mp4"):
                relations[relation.get("Id")] = (target, relation.get("Type", ""))
    pictures = [picture for picture in document.findall(".//" + P + "pic")
                if picture.find(".//" + A + "videoFile") is not None]
    if len(pictures) != 1:
        return set()  # Count unsupported/external video shapes too, not just MP4s.
    ids = set()
    for picture in pictures:
        identity = picture.find(P + "nvPicPr/" + P + "cNvPr")
        video = picture.find(".//" + A + "videoFile")
        embedded = picture.find(".//" + P14 + "media")
        if identity is None or video is None or not identity.get("id"):
            continue
        target = relations.get(video.get(R + "link"))
        destination = relations.get(embedded.get(R + "embed")) if embedded is not None else None
        if target and target[1].endswith("/video") and (embedded is None or destination and destination[0] == target[0]):
            ids.add(identity.get("id"))
    return ids


def _starts_with_slide(command, parents):
    behavior_clock = command.find(P + "cBhvr/" + P + "cTn")
    if behavior_clock is None:
        return False
    for condition in behavior_clock.findall(P + "stCondLst/" + P + "cond"):
        if condition.get("delay") != "0" or condition.get("evt") or list(condition):
            return False
    ancestors, node = [], parents.get(command)
    while node is not None:
        ancestors.append(node)
        node = parents.get(node)
    clocks = [node for node in ancestors if node.tag == P + "cTn"]
    main = [node for node in clocks if node.get("nodeType") == "mainSeq"]
    if len(main) != 1 or not any(node.get("nodeType") == "tmRoot" for node in clocks):
        return False
    if not any(node.get("nodeType") == "withEffect" for node in clocks):
        return False
    if any(node.get("nodeType") in ("clickEffect", "interactiveSeq") for node in clocks):
        return False
    began_with_main = False
    for clock in clocks:
        conditions = clock.findall(P + "stCondLst/" + P + "cond")
        if not conditions:
            continue
        activated = False
        for condition in conditions:
            if condition.get("delay") == "0" and not condition.get("evt") and not list(condition):
                activated = True
            elif condition.get("evt") == "onBegin" and condition.get("delay") == "0":
                if clock is main[0] or clock.get("nodeType") == "tmRoot":
                    return False  # A sequence cannot require its own start first.
                children = list(condition)
                if len(children) != 1 or children[0].tag != P + "tn" or children[0].get("val") != main[0].get("id"):
                    return False
                began_with_main = activated = True
            elif not (condition.get("delay") == "indefinite" and not condition.get("evt") and not list(condition)):
                return False
        if not activated:
            return False
    return began_with_main


def validate_slide(archive, name, document):
    ids = video_shapes(archive, name, document)
    if len(ids) != 1:
        raise TalkError(f"Expected one embedded video shape per beat: {name}")
    video_id = next(iter(ids))
    clock_ids = [clock.get("id", "") for clock in document.findall(".//" + P + "cTn")]
    if any(not re.fullmatch(r"[1-9]\d*", value) for value in clock_ids) or len(set(clock_ids)) != len(clock_ids):
        raise TalkError(f"Missing or duplicate timing node IDs: {name}")
    targets = [node.find(P + "cMediaNode/" + P + "tgtEl/" + P + "spTgt")
               for node in document.findall(".//" + P + "video")]
    if len(targets) != 1 or targets[0] is None or targets[0].get("spid") != video_id:
        raise TalkError(f"Video timing targets the wrong shape: {name}")
    parents = {child: parent for parent in document.iter() for child in parent}
    commands = [command for command in document.findall(".//" + P + "cmd")
                if command.get("type") == "call" and command.get("cmd") == "playFrom(0.0)"]
    if len(commands) != 1:
        raise TalkError(f"Missing unique native slide-entry media-play effect: {name}")
    target = commands[0].find(P + "cBhvr/" + P + "tgtEl/" + P + "spTgt")
    if target is None or target.get("spid") != video_id or not _starts_with_slide(commands[0], parents):
        raise TalkError(f"Media-play effect needs a click, delay or wrong target: {name}")


def normalize_pptx(path):
    """Normalize only disposable, freshly converted single-video slide exports."""
    path = Path(path)
    template = (SKILL_ROOT / "assets/pptx/autoplay-timing.xml").read_bytes().strip()
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    replacements = {}
    try:
        with zipfile.ZipFile(path) as source:
            for name in source.namelist():
                if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                    continue
                data = source.read(name)
                document = ET.fromstring(data)
                ids = video_shapes(source, name, document)
                if len(ids) != 1 or not re.fullmatch(r"[1-9]\d*", next(iter(ids), "")):
                    raise TalkError(f"Cannot normalize a non-single-video slide: {name}")
                timing = document.find(P + "timing")
                if timing is None or not re.search(rb'xmlns:p=[\'"]http://schemas.openxmlformats.org/presentationml/2006/main[\'"]', data):
                    raise TalkError(f"Unsupported converter XML/timing: {name}")
                videos = timing.findall(".//" + P + "video")
                media_target = videos[0].find(P + "cMediaNode/" + P + "tgtEl/" + P + "spTgt") if len(videos) == 1 else None
                if media_target is None or media_target.get("spid") != next(iter(ids)):
                    raise TalkError(f"Refusing to replace other video timing: {name}")
                for node in timing.iter():
                    if node.tag in {P + item for item in ("anim", "animClr", "animEffect", "animMotion", "animRot", "animScale", "set", "audio")} or (node.tag == P + "cmd" and node.get("cmd") not in ("playFrom(0.0)", "togglePause")):
                        raise TalkError(f"Refusing to replace additional slide animations: {name}")
                value = template.replace(b"__VIDEO_SHAPE_ID__", next(iter(ids)).encode("ascii"))
                # Replace just this element. A whole-tree round trip would rewrite
                # namespace prefixes used by Office's compatibility extensions.
                patched, count = re.subn(rb"<p:timing(?:\s[^>]*)?>.*?</p:timing\s*>", lambda _: value, data, flags=re.DOTALL)
                if count != 1:
                    raise TalkError(f"Cannot locate unique converter timing block: {name}")
                validate_slide(source, name, ET.fromstring(patched))
                replacements[name] = patched
            if not replacements:
                raise TalkError("No video slides to normalize")
            with zipfile.ZipFile(temporary, "w") as target:
                for member in source.infolist():
                    entry = copy.copy(member)
                    if member.filename in replacements:
                        target.writestr(entry, replacements[member.filename])
                    else:
                        with source.open(member) as reader, target.open(entry, "w") as writer:
                            shutil.copyfileobj(reader, writer, length=1024 * 1024)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"normalized_slides": len(replacements), "method": "native-slide-entry-media-command", "player_tested": False}
