import json
from copy import deepcopy
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
sys.path.insert(0, str(ROOT / "skills/motif/scripts"))
from talklib import build, common, environment, project
from talklib.common import (TalkError, load_project, project_lock, save_project,
                            python_executable, settings, toml_text, tomllib, write_json)
import media_helper
import talk


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.env = patch.dict(os.environ, {"MOTIF_HOME": str(self.base / "preferences")})
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

    def test_new_motif_projects_and_legacy_projects_are_both_readable(self):
        self.assertEqual(self.config["created_by"], "motif")
        state = self.root / "PROJECT.md"
        self.assertIn("created_by: motif", state.read_text(encoding="utf-8"))
        state.write_text(state.read_text(encoding="utf-8").replace("created_by: motif", "created_by: research-talk", 1), encoding="utf-8")
        self.config["created_by"] = "research-talk"
        save_project(self.root, self.config)
        before = (state.read_bytes(), (self.root / "talk.toml").read_bytes())
        loaded_root, loaded = load_project(self.root)
        self.assertEqual(loaded_root, self.root)
        self.assertEqual(loaded["created_by"], "research-talk")
        self.assertEqual([item["path"] for item in project.discover([self.base])["projects"]], [str(self.root)])
        self.assertEqual((state.read_bytes(), (self.root / "talk.toml").read_bytes()), before)

    def test_motif_home_override_takes_precedence_and_legacy_override_still_works(self):
        current, legacy = self.base / "motif-config", self.base / "old-config"
        with patch.dict(os.environ, {"MOTIF_HOME": str(current), "RESEARCH_TALK_HOME": str(legacy)}):
            self.assertEqual(common.user_home(), current.resolve())
        with patch.dict(os.environ, {"MOTIF_HOME": "", "RESEARCH_TALK_HOME": str(legacy)}):
            self.assertEqual(common.user_home(), legacy.resolve())
        self.assertFalse(current.exists())
        self.assertFalse(legacy.exists())

    def test_existing_default_registry_is_reused_without_moving_settings(self):
        base = self.base / "user-config"
        current, legacy = base / "motif", base / "research-talk"
        preferences = {"schema": 1, "projects": [str(self.root)], "roots": [], "shared_python": "old-python"}
        write_json(legacy / "settings.json", preferences)
        before = (legacy / "settings.json").read_bytes()
        with patch.dict(os.environ, {"MOTIF_HOME": "", "RESEARCH_TALK_HOME": "",
                                     "LOCALAPPDATA": str(base), "XDG_CONFIG_HOME": str(base)}):
            self.assertEqual(common.user_home(), legacy)
            self.assertEqual(settings(), preferences)
            self.assertFalse(current.exists())
            write_json(current / "settings.json", {"schema": 1, "projects": [], "roots": []})
            self.assertEqual(common.user_home(), current)
            self.assertEqual(settings()["projects"], [])
        self.assertEqual((legacy / "settings.json").read_bytes(), before)

    def test_legacy_copied_scenes_receive_visual_and_layout_environment(self):
        self.config["visual"].update(pace=0.4, seed=17, background="#123456", foreground="#FFFFFF")
        env = common.run_environment(self.root, self.config)
        for key, value in self.config["visual"].items():
            if key in ("pace", "seed", "background", "foreground"):
                self.assertEqual(env["MOTIF_" + key.upper()], str(value))
                self.assertEqual(env["RESEARCH_TALK_" + key.upper()], str(value))
        with patch.object(environment, "inspect", return_value={"ready": True}), \
                patch.object(build, "run_logged", side_effect=TalkError("test backend stop")) as backend:
            with self.assertRaises(TalkError):
                build.render(self.root, self.config, "preview", ["Translation"])
        render_env = backend.call_args.args[2]
        self.assertTrue(render_env["MOTIF_QA_FILE"].endswith("Translation.json"))
        self.assertEqual(render_env["MOTIF_QA_FILE"], render_env["RESEARCH_TALK_QA_FILE"])

    def test_execution_note_replaces_legacy_block_instead_of_duplicating_it(self):
        state = self.root / "PROJECT.md"
        with state.open("a", encoding="utf-8") as output:
            output.write("\n<!-- research-talk:execution -->\nold note\n<!-- /research-talk:execution -->\n")
        common.execution_note(self.root, "new note")
        text = state.read_text(encoding="utf-8")
        self.assertNotIn("old note", text)
        self.assertNotIn("research-talk:execution", text)
        self.assertEqual(text.count("<!-- motif:execution -->"), 1)
        common.execution_note(self.root, "latest note")
        text = state.read_text(encoding="utf-8")
        self.assertEqual(text.count("<!-- motif:execution -->"), 1)
        self.assertNotIn("new note", text)
        self.assertIn("latest note", text)

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

    def test_status_is_compact_without_losing_handoff_or_interruption_evidence(self):
        first, second = [scene["name"] for scene in self.config["scenes"]]
        record = {"scenes": {
            first: {"state": "success", "beats": 3, "media": [{"file": "clip.mp4"}] * 100,
                    "file_stats": {"clip.mp4": {"size": 123}}},
            second: {"state": "interrupted", "child_pid": 321, "log": "scene.log", "error": "stopped"},
            "OldScene": {"state": "success", "beats": 99}},
            "exports": [{"directory": "old", "formats": ["html"]},
                        {"directory": "latest", "formats": ["pptx"], "beats": 3,
                         "verified": "package-and-media", "player_tested": False}]}
        path = self.root / ".build/preview/status.json"
        write_json(path, record)
        write_json(self.root / ".build/operation.lock", {"pid": 123})
        before = path.read_bytes()
        summary = project.status(self.root)
        detail = project.status(self.root, verbose=True)
        profile = summary["profiles"]["preview"]
        self.assertEqual(profile["counts"], {"interrupted": 1, "success": 1})
        self.assertEqual(profile["beats"], 3)
        self.assertEqual(profile["recorded_scene_states"], {first: "success", second: "interrupted"})
        self.assertEqual(profile["attention"][second], {"state": "interrupted", "child_pid": 321, "log": "scene.log"})
        self.assertEqual(profile["errors"][second], "stopped")
        self.assertEqual(profile["latest_export"]["directory"], "latest")
        self.assertFalse(profile["latest_export"]["player_tested"])
        self.assertEqual(summary["lock"], {"pid": 123})
        self.assertTrue(summary["current_state"])
        self.assertTrue(summary["next_step"])
        self.assertIn("freshness", summary["detail_hint"])
        self.assertEqual(detail["profiles"]["preview"], record)
        self.assertLess(len(json.dumps(summary)), len(json.dumps(detail)))
        self.assertEqual(path.read_bytes(), before)
        empty = summary["profiles"]["final"]
        self.assertEqual(empty["counts"], {"pending": 2})
        self.assertIsNone(empty["latest_export"])

    def test_status_cli_verbose_flag_preserves_detailed_records(self):
        for verbose in (False, True):
            arguments = ["status", "--project", str(self.root)] + (["--verbose"] if verbose else [])
            with patch.object(project, "status", return_value={"ok": True}) as status_call:
                result, code = talk.dispatch(talk.parser().parse_args(arguments))
            status_call.assert_called_once_with(self.root, verbose=verbose)
            self.assertEqual(code, 0)
            self.assertEqual(result, {"ok": True})

    def test_doctor_distinguishes_interpreter_selection_without_binding_it(self):
        manifest = (self.root / "talk.toml").read_bytes()
        for source, configured, selected in (("management-python", "", None),
                                              ("project-config", "configured-python", None),
                                              ("explicit-candidate", "configured-python", "candidate-python")):
            self.config["environment"]["python"] = configured
            before = deepcopy(self.config)
            with patch.object(environment, "_probe", return_value={"python": selected or configured or sys.executable,
                                                                    "ready": True}):
                result = environment.inspect(self.root, self.config, selected, candidates=False)
            self.assertEqual(result["selection"]["source"], source)
            self.assertIn("not every environment", result["selection"]["note"])
            self.assertIn("smoke-test", result["reuse_guidance"]["message"])
            self.assertEqual(result["reuse_guidance"]["probe_example"][4], result["python"])
            self.assertEqual(self.config, before)
        self.assertEqual((self.root / "talk.toml").read_bytes(), manifest)

    def test_doctor_bounded_candidates_deduplicate_and_keep_required_tool_paths(self):
        venv_suffix = "Scripts/python.exe" if os.name == "nt" else "bin/python"
        project_python = self.root / ".venv" / venv_suffix
        shared_python = self.base / "shared" / venv_suffix
        conda_python = self.base / "conda" / ("python.exe" if os.name == "nt" else "bin/python")
        for candidate in (project_python, shared_python, conda_python):
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.touch()
        preferences = settings()
        preferences.update(shared_python=str(shared_python), shared_path=["shared-tex-bin"])
        write_json(self.base / "preferences/settings.json", preferences)
        self.config["environment"]["path"] = ["project-tool-bin"]
        config_before = deepcopy(self.config)
        settings_before = (self.base / "preferences/settings.json").read_bytes()
        def probe(root, config, selected=None):
            return {"python": selected or sys.executable, "ready": selected == str(shared_python),
                    "packages": {}, "missing_external": []}
        with patch.dict(os.environ, {"VIRTUAL_ENV": str(self.root / ".venv"),
                                     "CONDA_PREFIX": str(self.base / "conda")}), \
                patch.object(environment, "_probe", side_effect=probe), \
                patch.object(environment.shutil, "which", return_value=str(shared_python.parent / "manim")):
            result = environment.inspect(self.root, self.config)
        candidates = result["reuse_candidates"]
        self.assertEqual([candidate["kind"] for candidate in candidates], ["project", "remembered-shared", "active-conda"])
        self.assertFalse(result["ready"])
        self.assertTrue(candidates[1]["ready"])
        required_paths = ["--path", "shared-tex-bin", "--path", "project-tool-bin"]
        self.assertEqual(result["reuse_guidance"]["probe_example"],
                         ["doctor", "--project", str(self.root), "--python", str(shared_python), *required_paths])
        self.assertEqual(result["reuse_guidance"]["reuse_plan_example"],
                         ["setup", "--project", str(self.root), "--reuse", str(shared_python), *required_paths])
        self.assertIn("do not mean", result["reuse_guidance"]["message"])
        self.assertEqual(self.config, config_before)
        self.assertEqual((self.base / "preferences/settings.json").read_bytes(), settings_before)

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

    def test_normalize_html_injects_memory_guard_and_patches_reveal_unload(self):
        html = self.root / "deck/talk.html"
        assets = self.root / "deck/talk_assets"
        assets.mkdir(parents=True, exist_ok=True)
        html.write_text(
            "<html><body><script>Reveal.initialize({\n"
            "  viewDistance: 3,\n"
            "  mobileViewDistance: 2,\n"
            "});</script>\n  </body>\n</html>\n",
            encoding="utf-8",
        )
        reveal = assets / "reveal.js"
        reveal.write_text(
            "n&&(n.style.display=`none`,t(n,`iframe[src]`).forEach(e=>{e.removeAttribute(`src`)}));"
            "let a=B.isActive(),o=a?10:f.viewDistance;g&&(o=a?6:f.mobileViewDistance);",
            encoding="utf-8",
        )
        first = build.normalize_html(html)
        second = build.normalize_html(html)  # idempotent on repeated calls
        self.assertTrue(first["patched_reveal_js"])
        self.assertFalse(second["patched_reveal_js"])
        patched_html = html.read_text(encoding="utf-8")
        patched_reveal = reveal.read_text(encoding="utf-8")
        self.assertIn("viewDistance: 2,", patched_html)
        self.assertIn("mobileViewDistance: 1,", patched_html)
        self.assertEqual(patched_html.count("Motif Memory Guard"), 1)
        self.assertIn("t(n,`video`).forEach", patched_reveal)
        self.assertEqual(patched_reveal.count("n.removeAttribute(`data-loaded`)"), 1)
        self.assertIn("o=a?2:f.viewDistance", patched_reveal)

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
