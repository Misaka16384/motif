"""Regression cases for slide-entry playback, distinct from click-to-pause."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/research-talk/scripts"))
from talklib.build import validate_pptx
from talklib.common import TalkError
from talklib.pptx_autoplay import normalize_pptx

HEADER = '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" mc:Ignorable="p14">'
SHAPE = '<p:cSld><p:spTree><p:pic><p:nvPicPr><p:cNvPr id="9"/><p:nvPr><a:videoFile r:link="rIdVideo"/></p:nvPr></p:nvPicPr></p:pic></p:spTree></p:cSld>'
RAW = '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" nodeType="tmRoot"><p:childTnLst><p:video><p:cMediaNode><p:cTn id="2"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="9"/></p:tgtEl></p:cMediaNode></p:video></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
REL = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdVideo" Target="../media/media1.mp4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/video"/></Relationships>'


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "clip.pptx"

    def tearDown(self):
        self.temp.cleanup()

    def archive(self, timing=RAW, shape=SHAPE):
        with zipfile.ZipFile(self.path, "w") as package:
            package.writestr("ppt/slides/slide1.xml", HEADER + shape + timing + "</p:sld>")
            package.writestr("ppt/slides/_rels/slide1.xml.rels", REL)
            package.writestr("ppt/media/media1.mp4", b"media-byte-preservation fixture")

    def normalized(self):
        self.archive()
        normalize_pptx(self.path)
        with zipfile.ZipFile(self.path) as package:
            xml = package.read("ppt/slides/slide1.xml").decode()
        return xml[xml.index("<p:timing"):xml.index("</p:timing>") + len("</p:timing>")]

    def test_raw_zero_delay_is_not_a_native_play_effect(self):
        self.archive()
        with self.assertRaises(TalkError):
            validate_pptx(self.path, 1)

    def test_native_effect_with_separate_click_to_pause_is_valid(self):
        self.archive(self.normalized())
        result = validate_pptx(self.path, 1)
        self.assertEqual(result["timed_video_slides"], 1)
        self.assertFalse(result["player_tested"])

    def test_play_on_click_is_not_slide_entry(self):
        timing = self.normalized().replace('nodeType="withEffect"', 'nodeType="clickEffect"')
        self.archive(timing)
        with self.assertRaises(TalkError):
            validate_pptx(self.path, 1)

    def test_missing_wrong_or_delayed_main_sequence_trigger_is_rejected(self):
        good = self.normalized()
        for bad in (good.replace('evt="onBegin"', 'evt="onClick"'),
                    good.replace('<p:tn val="2"/>', '<p:tn val="8"/>'),
                    good.replace('evt="onBegin" delay="0"', 'evt="onBegin" delay="250"')):
            with self.subTest(timing=bad):
                self.archive(bad)
                with self.assertRaises(TalkError):
                    validate_pptx(self.path, 1)

    def test_play_command_cannot_target_another_shape(self):
        good = self.normalized()
        command = '<p:spTgt spid="9"/>'
        # The first target belongs to playFrom, not the later video/pause branch.
        self.archive(good.replace(command, '<p:spTgt spid="99"/>', 1))
        with self.assertRaises(TalkError):
            validate_pptx(self.path, 1)

    def test_play_command_own_clock_cannot_wait_for_a_click_or_delay(self):
        good = self.normalized()
        original = '<p:cTn id="6" dur="1" fill="hold"/>'
        for condition in ('<p:cond evt="onClick" delay="0"/>', '<p:cond delay="250"/>', '<p:cond delay="indefinite"/>'):
            clock = '<p:cTn id="6" dur="1" fill="hold"><p:stCondLst>' + condition + '</p:stCondLst></p:cTn>'
            self.archive(good.replace(original, clock))
            with self.assertRaises(TalkError):
                validate_pptx(self.path, 1)

    def test_main_sequence_cannot_wait_for_its_own_begin(self):
        good = self.normalized()
        main = '<p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
        circular = '<p:stCondLst><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst>'
        self.archive(good.replace(main, main + circular))
        with self.assertRaises(TalkError):
            validate_pptx(self.path, 1)

    def test_an_additional_wmv_video_is_not_ignored_or_rewritten(self):
        good = self.normalized()
        picture = SHAPE[SHAPE.index('<p:pic>'):SHAPE.index('</p:pic>') + len('</p:pic>')]
        second = picture.replace('id="9"', 'id="40"').replace('rIdVideo', 'rIdOther')
        shape = SHAPE.replace('</p:spTree>', second + '</p:spTree>')
        with zipfile.ZipFile(self.path, "w") as package:
            package.writestr("ppt/slides/slide1.xml", HEADER + shape + good + "</p:sld>")
            relation = '<Relationship Id="rIdOther" Target="../media/other.wmv" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/video"/>'
            package.writestr("ppt/slides/_rels/slide1.xml.rels", REL.replace('</Relationships>', relation + '</Relationships>'))
            package.writestr("ppt/media/media1.mp4", b"mp4 fixture")
            package.writestr("ppt/media/other.wmv", b"other video")
        original = self.path.read_bytes()
        with self.assertRaises(TalkError):
            normalize_pptx(self.path)
        with self.assertRaises(TalkError):
            validate_pptx(self.path, 1)
        self.assertEqual(original, self.path.read_bytes())

    def test_normalization_preserves_media_relationships_namespaces_and_is_repeatable(self):
        self.archive()
        with zipfile.ZipFile(self.path) as package:
            preserved = {name: package.read(name) for name in package.namelist() if name != "ppt/slides/slide1.xml"}
        normalize_pptx(self.path)
        normalize_pptx(self.path)
        validate_pptx(self.path, 1)
        with zipfile.ZipFile(self.path) as package:
            for name, value in preserved.items():
                self.assertEqual(value, package.read(name))
            xml = package.read("ppt/slides/slide1.xml").decode()
            self.assertTrue(xml.startswith(HEADER + SHAPE))

    def test_additional_animation_is_not_discarded(self):
        self.archive(RAW.replace("</p:childTnLst>", "<p:anim/></p:childTnLst>"))
        original = self.path.read_bytes()
        with self.assertRaises(TalkError):
            normalize_pptx(self.path)
        self.assertEqual(hashlib.sha256(original).digest(), hashlib.sha256(self.path.read_bytes()).digest())
