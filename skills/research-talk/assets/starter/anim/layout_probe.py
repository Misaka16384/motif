"""End-beat diagnostics. Findings require review, not automatic redesign."""
import json
import os
from pathlib import Path

import numpy as np
from manim.camera.camera import Camera


def snapshot(scene):
    target = Path(os.environ["RESEARCH_TALK_QA_FILE"])
    texts, figures, seen = [], [], set()

    def visible(mob):
        for part in mob.family_members_with_points():
            if hasattr(part, "get_fill_opacity") and np.max(np.asarray(part.get_fill_opacity())) > 0.05:
                return True
            if hasattr(part, "get_stroke_opacity") and np.max(np.asarray(part.get_stroke_opacity())) > 0.05:
                return True
        return False

    def collect(mob):
        if id(mob) in seen:
            return
        seen.add(id(mob))
        if hasattr(mob, "tex_string") or mob.__class__.__name__ in ("Text", "MarkupText", "Paragraph"):
            if visible(mob) and not getattr(mob, "qa_allow_overlap", False):
                texts.append(mob)
            # All descendants of text, including glyph paths, belong to the text layer.
            return
        if len(mob.points) and visible(mob) and not getattr(mob, "qa_ignore", False):
            figures.append(mob)
        for child in mob.submobjects:
            collect(child)

    for mob in scene.mobjects:
        collect(mob)
    camera = scene.camera
    height = 360
    width = max(2, round(height * camera.frame_width / camera.frame_height))
    separate = Camera(pixel_width=width, pixel_height=height,
                      frame_width=camera.frame_width, frame_height=camera.frame_height,
                      frame_center=camera.frame_center.copy(), background_color=camera.background_color,
                      background_opacity=camera.background_opacity)
    separate.frame_height = camera.frame_height
    background = separate.pixel_array[:, :, :3].copy().astype(float)
    separate.capture_mobjects(figures, include_submobjects=False)
    figure_mask = np.max(np.abs(separate.pixel_array[:, :, :3].astype(float) - background), axis=2) > 84
    findings = []
    index = getattr(scene, "_research_talk_snapshot", 0) + 1
    scene._research_talk_snapshot = index
    cx, cy = camera.frame_center[:2]
    for text in texts:
        label = getattr(text, "tex_string", getattr(text, "text", text.__class__.__name__))[:180]
        left, right = text.get_left()[0], text.get_right()[0]
        bottom, top = text.get_bottom()[1], text.get_top()[1]
        if (left < cx - camera.frame_width / 2 - 0.01 or right > cx + camera.frame_width / 2 + 0.01 or
                bottom < cy - camera.frame_height / 2 - 0.01 or top > cy + camera.frame_height / 2 + 0.01):
            findings.append({"snapshot": index, "issue": "text outside the frame", "text": label})
        separate.reset()
        separate.capture_mobjects([text])
        text_mask = np.max(np.abs(separate.pixel_array[:, :, :3].astype(float) - background), axis=2) > 64
        pixels = int(np.count_nonzero(text_mask & figure_mask))
        if pixels >= 8:
            findings.append({"snapshot": index, "issue": "text/figure pixel intersection", "text": label, "pixels": pixels})
    for first in range(len(texts)):
        for second in range(first + 1, len(texts)):
            a, b = texts[first], texts[second]
            overlap_x = min(a.get_right()[0], b.get_right()[0]) - max(a.get_left()[0], b.get_left()[0])
            overlap_y = min(a.get_top()[1], b.get_top()[1]) - max(a.get_bottom()[1], b.get_bottom()[1])
            if overlap_x > 0.03 and overlap_y > 0.03:
                findings.append({"snapshot": index, "issue": "text bounding boxes intersect",
                                 "texts": [getattr(item, "tex_string", getattr(item, "text", "text"))[:100] for item in (a, b)]})
    report = getattr(scene, "_research_talk_layout_report", {"snapshots": 0, "findings": [],
                  "limits": "End-beat samples only. Intentional labels may intersect figures; transient motion and semantic clarity require visual review."})
    report["snapshots"] = index
    report["findings"].extend(findings)
    scene._research_talk_layout_report = report
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
