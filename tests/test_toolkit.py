import json
import os
from pathlib import Path
import sys
import tempfile
from fractions import Fraction
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/research-talk/scripts"))
from talklib import build, environment, project
from talklib.common import (TalkError, load_project, project_lock, save_project,
                            python_executable, settings, toml_text, tomllib, write_json)
import media_helper


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.env = patch.dict(os.environ, {"RESEARCH_TALK_HOME": str(self.base / "preferences")})
        self.env.start()
        self.root = self.base / "A talk with spaces"
        project.initialize(self.root, 'A "quoted" title / 学术报告')
        self.root, self.config = load_project(self.root)

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()

    def test_create_is_discoverable_and_never_overwrites(self):
        found = project.discover([self.base])
        self.assertEqual([p["path"] for p in found["projects"]], [str(self.root)])
        original = (self.root / "PROJECT.md").read_bytes()
        with self.assertRaises(TalkError):
            project.initialize(self.root, "overwrite")
        self.assertEqual((self.root / "PROJECT.md").read_bytes(), original)

    def test_discovery_marker_and_depth_are_meaningful(self):
        preferences = settings()
        preferences["projects"] = []
        write_json(self.base / "preferences/settings.json", preferences)
        self.assertFalse(project.discover([self.base], depth=0)["projects"])
        unrelated = self.base / "unrelated"
        unrelated.mkdir()
        (unrelated / "PROJECT.md").write_text("ordinary project", encoding="utf-8")
        self.assertEqual(len(project.discover([self.base], depth=1)["projects"]), 1)

    def test_toml_roundtrip_handles_windows_paths_and_unicode(self):
        self.config["environment"].update(python=r"C:\Some directory\python.exe", path=[r"D:\TeX\bin"])
        self.assertEqual(tomllib.loads(toml_text(self.config)), self.config)

    def test_manifest_rejects_path_escape_and_duplicate_scene_names(self):
        self.config["scenes"][0]["file"] = "../outside.py"
        save_project(self.root, self.config)
        with self.assertRaises(TalkError):
            load_project(self.root)
        self.config["scenes"][0]["file"] = "anim/scenes.py"
        self.config["scenes"][1]["name"] = self.config["scenes"][0]["name"]
        save_project(self.root, self.config)
        with self.assertRaises(TalkError):
            load_project(self.root)

    def test_setup_plan_does_not_mutate_an_environment(self):
        before = (self.root / "talk.toml").read_bytes()
        result = environment.configure(self.root, self.config, "project")
        self.assertFalse(result["executed"])
        self.assertFalse((self.root / ".venv").exists())
        self.assertEqual((self.root / "talk.toml").read_bytes(), before)

    def test_broken_primary_environment_still_discovers_remembered_replacement(self):
        self.config["environment"]["python"] = str(self.root / "missing-python")
        preferences = settings()
        preferences["shared_python"] = sys.executable
        write_json(self.base / "preferences/settings.json", preferences)
        result = environment.inspect(self.root, self.config)
        self.assertFalse(result["ready"])
        self.assertTrue(result["error"])
        self.assertEqual(result["reuse_candidates"][0]["python"], sys.executable)

    def test_concurrent_project_operations_are_refused(self):
        with project_lock(self.root):
            with self.assertRaises(TalkError):
                with project_lock(self.root):
                    pass
        self.assertFalse((self.root / ".build/operation.lock").exists())

    def test_shared_helper_and_declared_data_invalidate_render(self):
        scene = self.config["scenes"][0]
        original = build.scene_fingerprint(self.root, self.config, scene, "preview")
        with (self.root / "anim/talk_style.py").open("a") as output:
            output.write("\n# helper changed\n")
        self.assertNotEqual(original, build.scene_fingerprint(self.root, self.config, scene, "preview"))
        data = self.root / "anim/data.json"
        data.write_text("[1]", encoding="utf-8")
        scene["depends"] = ["anim/data.json"]
        previous = build.scene_fingerprint(self.root, self.config, scene, "preview")
        data.write_text("[2]", encoding="utf-8")
        self.assertNotEqual(previous, build.scene_fingerprint(self.root, self.config, scene, "preview"))

    def test_escaped_latex_control_characters_are_detected(self):
        with (self.root / "anim/scenes.py").open("a") as output:
            output.write("\n# accidental " + chr(12) + "ormula\n")
        self.assertTrue(project.lint_sources(self.root, self.config))

    def test_missing_render_cannot_be_exported(self):
        with self.assertRaises(TalkError):
            build.export(self.root, self.config, "preview", ("html",))
        self.assertFalse(list((self.root / "deck").glob("latest*.json")))

    def test_backend_failure_records_failed_state_not_success(self):
        with patch.object(environment, "inspect", return_value={"ready": True}), \
                patch.object(build, "run_logged", side_effect=TalkError("backend failed")):
            with self.assertRaises(TalkError):
                build.render(self.root, self.config, "preview", ["Translation"])
        record = json.loads((self.root / ".build/preview/status.json").read_text())
        self.assertEqual(record["scenes"]["Translation"]["state"], "failed")
        self.assertFalse((self.root / ".build/operation.lock").exists())

    def test_html_validation_rejects_missing_and_remote_runtime_assets(self):
        html = self.root / "deck/test.html"
        html.write_text('<video src="absent.mp4"></video>', encoding="utf-8")
        with self.assertRaises(TalkError):
            build.validate_html(html)
        html.write_text('<script src="https://example.com/runtime.js"></script>', encoding="utf-8")
        with self.assertRaises(TalkError):
            build.validate_html(html)

    def test_unknown_selection_does_not_pass_an_empty_check(self):
        with self.assertRaises(TalkError):
            build.check(self.root, self.config, "preview", ["Typo"])

    @unittest.skipIf(os.name == "nt", "Creating interpreter symlinks can require Windows privileges")
    def test_venv_interpreter_symlink_is_not_resolved_to_system_python(self):
        link = self.root / "venv-python"
        link.symlink_to(sys.executable)
        self.config["environment"]["python"] = str(link)
        self.assertEqual(python_executable(self.config), str(link))

    def test_zero_delay_onclick_is_not_autoplay(self):
        ns = 'http://schemas.openxmlformats.org/presentationml/2006/main'
        slide = '<p:sld xmlns:p="%s" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:cSld><p:spTree><p:pic><p:nvPicPr><p:cNvPr id="2"/><p:nvPr>VIDEO</p:nvPr></p:nvPicPr></p:pic></p:spTree></p:cSld><p:timing><p:tnLst><p:par><p:cTn id="1" nodeType="tmRoot"><p:childTnLst><p:video><p:cMediaNode><p:cTn id="2"><p:stCondLst><p:cond delay="0" EVENT/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="2"/></p:tgtEl></p:cMediaNode></p:video></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing></p:sld>' % ns
        target = self.root / "deck/condition.pptx"
        def archive(event, video=True):
            with zipfile.ZipFile(target, "w") as package:
                package.writestr("ppt/slides/slide1.xml", slide.replace("EVENT", event).replace("VIDEO", '<a:videoFile r:link="rIdVideo"/>' if video else ""))
                package.writestr("ppt/media/media1.mp4", b"synthetic media; package-only fixture")
                package.writestr("ppt/slides/_rels/slide1.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdVideo" Target="../media/media1.mp4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/video"/></Relationships>')
        archive('evt="onClick"')
        with self.assertRaises(TalkError):
            build.validate_pptx(target, 1)
        archive("")
        with self.assertRaises(TalkError):
            build.validate_pptx(target, 1)
        build.normalize_pptx(target)
        self.assertEqual(build.validate_pptx(target, 1)["timed_video_slides"], 1)
        archive("", video=False)
        with self.assertRaises(TalkError):
            build.validate_pptx(target, 1)

    def test_nominal_fps_and_decoded_cadence_handle_remux_average_rate(self):
        video = SimpleNamespace(duration=324000, time_base=Fraction(1, 90000), width=640, height=360,
                                base_rate=Fraction(15), average_rate=Fraction(405, 28), guessed_rate=Fraction(15),
                                codec_context=SimpleNamespace(name="h264", format=SimpleNamespace(name="yuv420p")))
        class Container:
            streams = SimpleNamespace(video=[video])
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def decode(self, stream):
                return iter(SimpleNamespace(time=index / 15) for index in range(54))
        with patch.dict(sys.modules, {"av": SimpleNamespace(open=lambda path: Container(), time_base=1000000)}):
            result = media_helper.inspect_video("remux.mp4", decode=True)
        self.assertEqual(result["fps"], 15)
        self.assertNotEqual(result["average_fps"], 15)
        self.assertEqual(result["decoded_frames"], 54)
        self.assertEqual(result["cadence_errors"], 0)


if __name__ == "__main__":
    unittest.main()
