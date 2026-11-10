# THE REFERENCE FOR THE DEFAULT LOOK: light mode (set 10 Nov 2026). Copy its structure, not its content.
# A story reel: the hook and every name as white pills at the top, a light screen with the face in a
# square for each thing worth seeing (a real DM, two sets of items, a real site recording), the CTA as a
# pill, one accent-colored key term in some captions, soft pops and whooshes from AUTO_SFX.
# Assets (the takes, the B-roll, the site recording) lived in the reel folder.

import re
from pathlib import Path
from reel_edit.components import *

WORK = Path(__file__).resolve().parent
FOLDER = WORK.parents[2] / 'Reels Edit/Clothing Brand Story Website'
VIDEO = str(WORK / 'master.mp4')
OUTPUT = str(FOLDER / 'Clothing Brand Story Website - edited.mp4')
CAPTION_LANG = 'ar'
FACE = (720, 960)
PUNCH = [(42.52, 43.80)]           # [hard zoom] "the website does the job"
YOUTUBE_END = 50.10

SITE_CLIP = str(FOLDER / 'mild-panic-site.mp4')
SCROLL_CLIP = str(FOLDER / 'Phone Scrolling On Desk.MOV')
IG = lambda s=64, c="#fff": brand_logo("instagram", s, c)

# ---- the DM, shown as a chat (in a real reel: the real messages, the other side's name left out)
ME = 'Do you have a website where I can see everything?'
THEM = 'Not yet, we can send you photos of the collection'
Q2 = 'Which piece did you like?'
A2 = 'Nothing specific, I wanted to browse it all with prices'
Q3 = 'We can send you some options'
A3 = 'No need, thank you'


def bubble(text, mine, show=True):
    side = 'flex-end' if mine else 'flex-start'
    bg, fg = (BRIGHT, '#fff') if mine else (SURFACE, INK)
    who = 'Me' if mine else 'The brand'
    return (f'<div style="display:flex;flex-direction:column;align-items:{side};width:100%;margin:10px 0;visibility:{"visible" if show else "hidden"}">'
            f'<div style="font-size:30px;font-weight:700;color:{MUTED};margin:0 14px 8px">{who}</div>'
            f'<div style="max-width:900px;padding:24px 34px;border-radius:34px;background:{bg};color:{fg};'
            f'font-size:42px;font-weight:600;line-height:1.3">{text}</div></div>')


def chat(n):
    pairs = {1: [(ME, True, True), (THEM, False, False)], 2: [(ME, True, True), (THEM, False, True)],
             3: [(Q2, False, True), (A2, True, True)], 4: [(Q3, False, True), (A3, True, True)]}[n]
    head = heading('Instagram DM', tile(IG(46), 76), 46)
    return light(panel(head + '<div style="width:1060px">' + ''.join(bubble(t, m, s) for t, m, s in pairs) + '</div>', dots=True))


def boxes(items, n, bad):
    ic = (lambda: icon("x", 54, RED)) if bad else (lambda: icon("check", 54, BRIGHT))
    row = ''.join(box(t, ic(), w=360, h=380, size=50, dim=i >= n) for i, t in enumerate(items))
    return f'<div class="row" style="gap:30px">{row}</div>'


MISSING = ['No website', 'No collection', 'No prices']
MUST = ['Simple', 'A clear CTA', 'Good design']

VISUALS = {
    'hook': hook_card("Why I didn't buy<br>from this brand"),
    'scroll': broll(SCROLL_CLIP, mode="full", start=4.0, motion="cut"),
    'ad': top_pill('New clothing brand', IG(), after=tag('Ad', dot=False)),
    'c1': chat(1), 'c2': chat(2), 'c3': chat(3), 'c4': chat(4),
    't1': top_pill("I didn't buy", icon("shopping-bag", 60, "#fff")),
    'x1': light(panel(heading('Why I left', icon('circle-help', 60, BRIGHT), 64) + boxes(MISSING, 1, True))),
    'x2': light(panel(heading('Why I left', icon('circle-help', 60, BRIGHT), 64) + boxes(MISSING, 2, True))),
    'x3': light(panel(heading('Why I left', icon('circle-help', 60, BRIGHT), 64) + boxes(MISSING, 3, True))),
    't2': top_pill('Collection + prices', icon("tag", 60, "#fff"), sub='first'),
    't3': top_pill('The website does the job', icon("globe", 60, "#fff")),
    't4': top_pill('Not any website', icon("globe", 60, "#fff")),
    'm1': light(panel(heading('A website that sells', tile(icon("globe", 50, "#fff"), 88), 62) + boxes(MUST, 1, False))),
    'm2': light(panel(heading('A website that sells', tile(icon("globe", 50, "#fff"), 88), 62) + boxes(MUST, 2, False))),
    'm3': light(panel(heading('A website that sells', tile(icon("globe", 50, "#fff"), 88), 62) + boxes(MUST, 3, False))),
    'sitebg': light(panel('', bare=True)),
    'site': screen(SITE_CLIP),
    'cta': keyword_card('WEBSITE', 'and I\u2019ll reach out'),
}

TIMELINE = [
    ('hook', 0.00, 6.50),
    ('scroll', 7.76, 12.00),
    ('ad', 9.58, 14.14),
    ('c1', 15.04, 18.82),
    ('c2', 18.82, 22.33),
    ('c3', 22.33, 25.14),
    ('c4', 25.14, 29.50),
    ('t1', 30.06, 31.62),
    ('x1', 31.62, 32.80),
    ('x2', 32.80, 33.76),
    ('x3', 33.76, 35.50),
    ('t2', 36.22, 41.00),
    ('t3', 41.00, 43.82),
    ('t4', 43.82, 45.48),
    ('m1', 45.48, 46.56),
    ('m2', 46.56, 48.18),
    ('m3', 48.18, 50.10),
    ('sitebg', 51.24, 54.12),
    ('site', 51.24, 54.12),
    ('cta', 54.12, 56.00),
]

CAPTIONS = [
    (0.00, 'لقيت brand تياب جديدة'),
    (1.48, 'على *Instagram*'),
    (2.30, 'وحكيتهم حتى اشتري'),
    (3.50, 'بس فلّيت'),
    (4.24, 'من دون ما اشتري شي'),
    (5.22, 'ومن ورا شغلة وحدة'),
    (6.52, 'من شي 3-4 أيام'),
    (7.76, 'كنت عم بعمل scroll'),
    (8.58, 'على Instagram'),
    (9.58, 'وطلعلي دعاية'),
    (10.58, 'لـ *new clothing brand*'),
    (12.00, 'وعجبني الـ style'),
    (13.06, 'تبع الكنزة'),
    (14.14, 'فـ I DMed them'),
    (15.04, 'وسألتهم إذا في *website*'),
    (16.22, 'حتى شوف كل الـ collection'),
    (17.54, 'والـ prices'),
    (18.36, 'بس قالولي لا'),
    (19.40, 'بس فينا نبعتلك الصور'),
    (21.26, 'وإنت بتنقّي شو بيعجبك'),
    (22.33, 'بس أنا ما كنت عارف'),
    (23.12, 'شو بدّي'),
    (23.60, 'simply عجبني الـ style'),
    (25.14, 'قلت بشوف الـ collections'),
    (26.26, 'والـ prices'),
    (27.12, 'وإذا في شي عجبني'),
    (28.12, 'ساعتها بشتريه'),
    (29.50, 'فكرمال هيك'),
    (30.06, 'I ended up'),
    (30.60, 'not buying anything'),
    (31.62, 'لأنّو ما في محل'),
    (32.80, 'فيني شوف الـ collections'),
    (33.76, 'والـ *prices*'),
    (34.38, 'بطريقة بسيطة'),
    (35.50, 'ومش بس أنا'),
    (36.22, 'أكترية العالم'),
    (37.02, 'قبل ما يشتروا'),
    (37.90, 'بيحبّوا يشوفوا'),
    (38.60, 'الـ collection والـ prices'),
    (39.76, 'قبل ما ياخدوا قرار'),
    (41.00, 'فإذا ما كان'),
    (41.60, 'بقلب المحل'),
    (42.52, 'الـ *website* does the job'),
    (43.82, 'ومش أي website'),
    (44.88, 'لازم يكون'),
    (45.48, 'بسيط'),
    (46.10, 'with a *clear CTA*'),
    (47.34, 'وأهم شي'),
    (47.96, 'يكون الـ *design* حلو'),
    (49.08, 'حتى يجذب الزبون'),
    (50.10, 'فإذا عم تبيع online'),
    (51.24, 'وبدّك'),
    (51.60, 'website يعلّيلك'),
    (52.54, 'الـ *conversion*'),
    (53.18, 'متل هيدا'),
    (54.12, 'comment *website*'),
    (55.08, 'وأنا بتواصل معك'),
]
