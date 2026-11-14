"""Regression checks: python -m unittest discover -s reel-edit/tests -v"""
import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from reel_edit import components as c
from reel_edit.project import load


class TextDefaults(unittest.TestCase):
    def test_text_helpers_are_white_pills_in_the_safe_box(self):
        # the default look since 10 Nov 2026: hook, takeaway and CTAs are white pills at the top
        values = [c.hook_card('A clear hook'), c.takeaway(None, 'One point'),
                  c.takeaway([('Good UI', 'good')], c.hl('Clarity'), 'Helpful', color='#f00'),
                  c.follow_card('Build'), c.send_card('Share'), c.keyword_card('START', 'Get it'),
                  c.top_pill('Supabase', c.icon('database', 60, '#fff'), after=c.tag('1+ year'))]
        for html, kind, options in values:
            self.assertEqual(kind, 'overlay')
            self.assertGreaterEqual(options['top'], c.SAFE_T)
            self.assertIn('class="pill', html)
            self.assertNotIn('class="card"', html)
        self.assertEqual(c.hook_card('A clear hook')[2]['motion'], 'cut')   # there on frame one

    def test_outlined_hook_is_still_available(self):
        html, kind, options = c.hook_card('Old look', style='outline')
        self.assertIn('class="text-overlay"', html)
        self.assertEqual(options['motion'], 'cut')

    def test_graphic_motion_remains_available(self):
        self.assertEqual(c.overlay('graphic')[2]['motion'], 'ease')
        self.assertEqual(c.overlay('text', top=0, motion='cut')[2]['top'], 0)
        with self.assertRaises(ValueError):
            c.overlay('text', motion='bounce')

    def test_light_screens_give_one_face_square_when_adjacent(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, 'edit.py').write_text(
                'from reel_edit.components import *\nVIDEO="unused.mp4"\nCAPTIONS=[]\n'
                'VISUALS={"a": light(panel("A")), "b": light(panel("B")), "c": light(panel("C")), "p": top_pill("X")}\n'
                'TIMELINE=[("a",1,3),("b",3,5),("p",5,6),("c",7,9)]\nZOOM=[(0,2,"hook")]\nRISER=True\n', encoding='utf-8')
            with patch('reel_edit.project.probe_duration', return_value=10):
                p = load(td)
            self.assertEqual([w["window"] for w in p.face_card], [(1, 5), (7, 9)])
            self.assertEqual(p.face_card[0]["box"], c.FACE_BOX)
            x, y, w, h = p.face_card[0]["crop"]
            self.assertAlmostEqual(w / h, c.FACE_BOX[2] / c.FACE_BOX[3], places=2)   # no squashing
            self.assertFalse(hasattr(p, "riser"))   # the riser is gone (user's call, 10 Nov 2026)

    def test_face_box_is_a_vertical_rectangle_by_default(self):
        # the face is always a vertical rectangle on a split (user's call, 14 Nov 2026)
        x, y, w, h = c.FACE_BOX
        self.assertGreater(h, w)
        self.assertEqual(y + h, c.SAFE_B)
        self.assertEqual(c.PANEL_BOX[1] + c.PANEL_BOX[3] + 45, y)

    def test_layouts_carry_their_options(self):
        self.assertEqual(c.light(c.panel("A"))[2]["layout"], "light")
        self.assertEqual(c.light(c.panel("A"), layout="blur")[2]["layout"], "blur")
        self.assertIn('class="light clear"', c.light("x", layout="blur")[0])
        self.assertEqual(c.hard("x")[2]["layout"], "hard")
        self.assertEqual(c.light("x", layout="hard")[2]["layout"], "hard")
        self.assertEqual(c.corner("<b>x</b>")[2]["layout"], "corner")
        clip = c.corner("demo.mp4")
        self.assertEqual((clip["mode"], clip["layout"], clip["face"]), ("corner", "corner", True))
        self.assertEqual(c.top_screen("demo.mp4")["mode"], "top")
        self.assertTrue(c.cutout("x")[2]["cutout"])
        self.assertEqual(c.float_card("x")[1], "overlay")
        with self.assertRaises(ValueError):
            c.light("x", layout="flipped")
        x, y, w, h = c.CORNER_BOX
        self.assertGreater(x, c.SAFE_L)   # inside the safe edges, not in the far corner
        self.assertGreater(y, c.SAFE_T)

    def test_different_face_boxes_link_instead_of_growing_back(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, 'edit.py').write_text(
                'from reel_edit.components import *\nVIDEO="unused.mp4"\nCAPTIONS=[]\n'
                'VISUALS={"a": light(panel("A")), "b": light(panel("B"), layout="blur"), "h": hard("H"), "k": corner("<b>K</b>")}\n'
                'TIMELINE=[("a",1,3),("b",3,5),("h",5,7),("k",8,9)]\n', encoding='utf-8')
            with patch('reel_edit.project.probe_duration', return_value=10):
                p = load(td)
            self.assertEqual([w["window"] for w in p.face_card], [(1, 5), (5, 7), (8, 9)])   # light + blur share a box
            self.assertTrue(p.face_card[0].get("to_next"))
            self.assertEqual(p.face_card[1]["from_prev"]["box"], c.FACE_BOX)
            self.assertEqual(p.face_card[1]["box"], (0, c.HARD_Y, c.W, c.H - c.HARD_Y))
            self.assertEqual(p.face_card[1]["radius"], 0)
            self.assertEqual(p.face_card[2]["box"], c.CORNER_BOX)
            self.assertNotIn("from_prev", p.face_card[2])
            for fc in p.face_card:
                x, y, w, h = fc["crop"]
                self.assertAlmostEqual(w / h, fc["box"][2] / fc["box"][3], places=2)   # no squashing

    def test_brand_fonts_and_palette_survive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(SKILL / 'scripts/reel_edit', root / 'scripts/reel_edit',
                            ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'brand.json').write_text(json.dumps({'fonts': {'latin': 'Test Latin', 'arabic': 'Test Arabic'},
                                                        'colors': {'primary': '#123456'}}), encoding='utf-8')
            code = "import sys,json;sys.path.insert(0,'scripts');from reel_edit.components import CSS,caption_css,BLUE;print(json.dumps([CSS,caption_css('ar'),BLUE]))"
            css, captions, blue = json.loads(subprocess.check_output([sys.executable, '-c', code], cwd=root))
            self.assertIn("'Test Latin'", css)
            self.assertIn("'Test Arabic', 'Test Latin'", captions)
            self.assertEqual(blue, '#123456')
            self.assertIn('font-weight:700', captions)

    def test_arabic_numbers_and_english_stay_ltr(self):
        tree = ast.parse((SKILL / 'scripts/render.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'wrap')
        env = {'re': re, 'p': type('P', (), {'lang': 'ar'})()}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<caption-wrap>', 'exec'), env)
        for token in ['5,000', '$53,000', '100%', "you're", 'report.pdf']:
            result = env['wrap']('هيدا ' + token + ' واضح')
            self.assertIn('<bdi class="en" dir="ltr">' + token + '</bdi>', result)


if __name__ == '__main__':
    unittest.main()
