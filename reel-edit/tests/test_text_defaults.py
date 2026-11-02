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
    def test_legacy_helpers_now_choose_stationary_text(self):
        values = [c.hook_card('A clear hook'), c.takeaway(None, 'One point'),
                  c.takeaway([('Good UI', 'good')], c.hl('Clarity'), 'Helpful', color='#f00'),
                  c.follow_card('Build'), c.send_card('Share'), c.keyword_card('START', 'Get it')]
        for html, kind, options in values:
            self.assertEqual(kind, 'overlay')
            self.assertEqual(options['motion'], 'cut')
            self.assertGreaterEqual(options['top'], c.SAFE_T)
            self.assertIn('class="text-overlay"', html)
            self.assertNotIn('class="card"', html)

    def test_graphic_motion_remains_available(self):
        self.assertEqual(c.overlay('graphic')[2]['motion'], 'ease')
        self.assertEqual(c.overlay('text', top=0, motion='cut')[2]['top'], 0)
        with self.assertRaises(ValueError):
            c.overlay('text', motion='bounce')

    def test_hook_zoom_does_not_enable_riser(self):
        with tempfile.TemporaryDirectory() as td:
            base = 'VIDEO="unused.mp4"\nCAPTIONS=[]\nVISUALS={}\nTIMELINE=[]\nZOOM=[(0,2,"hook")]\n'
            for suffix, expected in [('', False), ('RISER=True\n', True)]:
                Path(td, 'edit.py').write_text(base + suffix, encoding='utf-8')
                with patch('reel_edit.project.probe_duration', return_value=3):
                    self.assertEqual(load(td).riser, expected)

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
