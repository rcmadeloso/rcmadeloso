#!/usr/bin/env python3
"""Draws the README pictures by hand, then builds them.

    pip install fonttools pillow
    python3 draw.py

hand.py is the pen and this file lays out each picture: ink panels that are never quite square, caption
boxes, speech bubbles, a torn notebook page, arrows. It writes src/*.svg (all
but hero.svg, which is written by hand) and build.py turns those into assets/.
"""
import html
import math
from pathlib import Path

import build
from hand import INK, Pen, curve, oval, turned

ROOT = Path(__file__).parent
PAPER, GREY, RED, ORANGE = '#fdfdfb', '#c9c9c9', '#d7263d', '#ff7a00'
NB = ' '

# What moves in every picture. The drawings boil like a flip-book: a filter
# nudges every line a hair, four times a second.
CSS = (
    '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'
    '.cap{fill:#fff;stroke:#111;stroke-linejoin:round;paint-order:stroke}'
    '.arrow{animation:nudge 1.6s ease-in-out infinite}'
    '.bob{animation:bob 3.4s ease-in-out infinite}.bob2{animation-delay:-.85s}.bob3{animation-delay:-1.7s}.bob4{animation-delay:-2.55s}'
    '.scribe{stroke-dasharray:100;animation:scribe 7s ease-in-out infinite}'
    '.hl{animation:glow 3.2s ease-in-out infinite}'
    '@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(var(--dx,4px),var(--dy,0))}}'
    '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}'
    '@keyframes scribe{0%{stroke-dashoffset:100}16%,88%{stroke-dashoffset:0;opacity:1}96%,100%{stroke-dashoffset:0;opacity:0}}'
    '@keyframes glow{0%,100%{opacity:1}50%{opacity:.55}}'
    '@media (prefers-reduced-motion:no-preference){.boil{filter:url(#boil)}}'
)
BOIL = ('<filter id="boil" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency=".03" numOctaves="1" seed="2" result="noise">'
        '<animate attributeName="seed" values="2;7;11;16" dur="1s" calcMode="discrete" repeatCount="indefinite"/></feTurbulence>'
        '<feDisplacementMap in="SourceGraphic" in2="noise" scale="2.6" xChannelSelector="R" yChannelSelector="G"/></filter>')


# ------------------------------------------------------------------ the kit


def text(x, y, words, size, font='comicb', anchor='start', fit=None, fill=None, cls=None, stroke=None):
    attrs = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" data-font="{font}"'
    attrs += f' text-anchor="{anchor}"' if anchor != 'start' else ''
    attrs += f' data-fit="{fit}"' if fit else ''
    attrs += f' fill="{fill}"' if fill else ''
    attrs += f' class="{cls}"' if cls else ''
    attrs += f' data-stroke="{stroke}"' if stroke else ''
    return f'<text {attrs}>{html.escape(words, quote=False)}</text>'


def box(pen, x, y, w, h, tilt=0.0, wander=2.5):
    """Four corners that are not quite where a ruler would put them."""
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    corners = [(cx + pen.rng.uniform(-wander, wander), cy + pen.rng.uniform(-wander, wander)) for cx, cy in corners]
    return turned(corners, x + w / 2, y + h / 2, tilt)


def panel(pen, x, y, w, h, tilt=-0.3):
    pen.shape(box(pen, x, y, w, h, tilt), PAPER, 4.6, step=16)


def caption_box(pen, x, y, words, size, tilt=-0.7):
    """A section heading, lettered in a grey box tucked into the corner."""
    w, h = build.advance(words, 'anton', size) + size * 0.9, size * 1.5
    pen.shape(box(pen, x, y, w, h, tilt, 1.5), GREY, 3.6, step=14)
    pen.add(f'<g transform="rotate({tilt} {x + w / 2:.0f} {y + h / 2:.0f})">{text(x + size * 0.45, y + size * 1.12, words, size, "anton")}</g>')
    return w, h


def bubble(pen, x, y, w, h, tail=None):
    """A speech bubble; tail is (edge x, edge y, tip x, tip y)."""
    r = 17
    pts = [(x + r, y), (x + w - r, y), (x + w, y + r), (x + w, y + h - r), (x + w - r, y + h), (x + r, y + h), (x, y + h - r), (x, y + r)]
    pts = [(px + pen.rng.uniform(-2.5, 2.5), py + pen.rng.uniform(-2.5, 2.5)) for px, py in pts]
    pen.shape(curve(pts, closed=True), PAPER, 3.6, step=9)
    if tail:
        ex, ey, tx, ty = tail
        along = (0, 10) if abs(tx - ex) > abs(ty - ey) else (10, 0)
        a, b = (ex - along[0], ey - along[1]), (ex + along[0], ey + along[1])
        inset = (4 if tx < ex else -4, 0) if along[1] else (0, 4 if ty < ey else -4)
        pen.fill([(a[0] + inset[0], a[1] + inset[1]), (tx, ty), (b[0] + inset[0], b[1] + inset[1])], PAPER, step=40, shake=0)
        pen.stroke([a, (tx, ty)], 3.6, taper=False)
        pen.stroke([(tx, ty), b], 3.6, taper=False)


def arrow(pen, points, cls='arrow', style=''):
    """Orange, inked round the outside, pointing where the story goes next."""
    line = curve(points) if len(points) > 2 else points
    (x0, y0), (x1, y1) = line[-2], line[-1]
    length = math.hypot(x1 - x0, y1 - y0) or 1
    dx, dy = (x1 - x0) / length, (y1 - y0) / length
    base = (x1 - dx * 15, y1 - dy * 15)
    start = len(pen.parts)
    pen.stroke(line[:-1] + [base], 11, taper=False, step=9)
    pen.stroke(line[:-1] + [base], 5, taper=False, step=9, colour=ORANGE)
    pen.shape([(x1 + dx * 5, y1 + dy * 5), (base[0] - dy * 12, base[1] + dx * 12), (base[0] + dy * 12, base[1] - dx * 12)], ORANGE, 3.4, step=6)
    inner = ''.join(pen.parts[start:])
    del pen.parts[start:]
    pen.add(f'<g class="{cls}"{f" style={chr(34)}{style}{chr(34)}" if style else ""}>{inner}</g>')


def circled(pen, cx, cy, rx, ry, delay=0.0):
    """A red ring pulled round something, the way you mark a page. It draws itself."""
    pts = []
    for i in range(34):
        a = -2.5 + (math.tau + 0.9) * i / 33
        grow = 1 + 0.05 * i / 33
        pts.append((cx + rx * grow * math.cos(a) + pen.rng.uniform(-1.5, 1.5), cy + ry * grow * math.sin(a) + pen.rng.uniform(-1.2, 1.2)))
    d = 'M' + ' '.join(f'{x:.0f} {y:.0f}' for x, y in curve(pts, per=3))
    pen.add(f'<path class="scribe" d="{d}" pathLength="100" fill="none" stroke="{RED}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" style="animation-delay:{delay}s"/>')


def highlight(pen, x, y, w, h):
    pts = [(x - 4, y + h * 0.5), (x + w * 0.2, y - 1), (x + w * 0.8, y + 1), (x + w + 5, y + h * 0.45), (x + w * 0.8, y + h + 1), (x + w * 0.2, y + h)]
    pen.group('hl', lambda: pen.fill(curve(pts, closed=True), ORANGE, step=6))


def notebook(pen, x, y, w, h, line, first, margin):
    """A page torn out of a ruled notebook: ragged top, grey rules, a red margin."""
    count = 30
    torn = [(x + w * i / count, y + (3 if i % 2 else 11) + pen.rng.uniform(-3, 3)) for i in range(count + 1)]
    page = torn + [(x + w, y + h), (x, y + h)]
    pen.fill(page, '#fff', step=6, shake=0.5)
    ruled = y + first
    while ruled < y + h - 6:
        pen.stroke([(x + 5, ruled + pen.rng.uniform(-1, 1)), (x + w - 5, ruled + pen.rng.uniform(-1, 1))], 1.7, step=60, taper=False, colour=GREY)
        ruled += line
    pen.stroke([(x + margin, y + 14), (x + margin + pen.rng.uniform(-2, 2), y + h - 4)], 2.4, step=60, taper=False, colour=RED)
    pen.ring(page, 2.6, step=7)


def slot(pen, path, x, y, w, h, limit=480):
    """A picture from src/ (the list is in src/memes/README.md), fitted and centred in its box."""
    pen.add(f'<g class="boil"><image href="{{{{img:{path}:{limit}}}}}" x="{x}" y="{y}" width="{w}" height="{h}"/></g>')


def doodle(pen, kind, ox, oy, k=0.72):
    """The little drawings in the starter pack, on a 64 square scaled by k."""
    at = lambda pts: [(ox + px * k, oy + py * k) for px, py in pts]
    line = lambda *pts: pen.stroke(at(pts), 3, step=5, taper=False)
    shape = lambda pts, colour=PAPER, smooth=False: pen.shape(curve(at(pts), closed=True) if smooth else at(pts), colour, 3, step=5)
    if kind == 'ai':  # a robot
        line((32, 18), (32, 11))
        shape(oval(32, 8, 4, 4, 8), smooth=True)
        shape([(8, 28), (13, 28), (13, 40), (8, 40)])
        shape([(51, 28), (56, 28), (56, 40), (51, 40)])
        shape([(13, 18), (51, 18), (51, 50), (13, 50)])
        shape(oval(24, 31, 4.5, 4.5, 8), smooth=True)
        shape(oval(40, 31, 4.5, 4.5, 8), smooth=True)
        line((23, 42), (41, 42))
        for px in (27, 32, 37):
            line((px, 42), (px, 38))
        line((22, 50), (22, 57))
        line((42, 50), (42, 57))
    elif kind == 'core':  # a literal stack: pancakes and butter
        line((5, 55), (59, 55))
        for cy in (46, 37, 28):
            shape(oval(32, cy, 22, 6.5, 12), smooth=True)
        shape([(27, 17), (37, 17), (37, 23), (27, 23)], '#ffd23f')
        line((45, 32), (45, 40))
    elif kind == 'mobile':  # a phone
        shape([(20, 5), (44, 5), (44, 59), (20, 59)])
        line((20, 14), (44, 14))
        line((20, 48), (44, 48))
        shape(oval(32, 53.5, 2.2, 2.2, 6), INK, smooth=True)
    elif kind == 'platforms':  # a gear
        teeth = []
        for i in range(32):
            a = i * math.tau / 32 - math.pi / 2
            radius = 25 if i % 4 < 2 else 19
            teeth.append((32 + radius * math.cos(a), 32 + radius * math.sin(a)))
        shape(teeth, GREY)
        shape(oval(32, 32, 8, 8, 10), smooth=True)
    elif kind == 'languages':  # a speech bubble of code
        shape([(7, 10), (57, 10), (57, 42), (32, 42), (21, 53), (21, 42), (7, 42)])
        line((24, 20), (17, 26), (24, 32))
        line((40, 20), (47, 26), (40, 32))
        line((35, 17), (29, 35))
    elif kind == 'databases':  # a database
        shape([(13, 14), (51, 14), (51, 50), (42, 56), (32, 57), (22, 56), (13, 50)])
        shape(oval(32, 14, 19, 7, 12), smooth=True)
        for cy in (26, 38):
            pen.stroke(curve(at([(13, cy), (22, cy + 6), (32, cy + 7), (42, cy + 6), (51, cy)])), 3, step=5, taper=False)
    elif kind == 'cloud':  # a cloud, raining an arrow
        shape([(17, 47), (48, 47), (57, 40), (55, 30), (47, 27), (42, 17), (31, 13), (22, 18), (19, 25), (11, 30), (9, 40)], smooth=True)
        line((32, 34), (32, 58))
        line((25, 51), (32, 58), (39, 51))


def picture(name, width, height, pen, note):
    body = '\n'.join(pen.parts)
    (ROOT / 'src' / f'{name}.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" stroke-linejoin="miter">\n'
        f'<!-- {note} Drawn by draw.py: change it there, not here. -->\n'
        f'<style>{CSS}</style>\n<defs>{BOIL}</defs>\n'
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>\n<g transform="translate(3 3)">\n{body}\n</g>\n</svg>\n')


# ------------------------------------------------------------------ the pictures

PACK = [  # kind, heading, items
    ('ai', 'AI ENGINEERING', ['Claude Code', 'AI coding agents', 'Custom agent skills', 'Multi-agent orchestrators', 'Agentic workflows', 'MCP (Model Context Protocol)', 'Anthropic Claude API', 'OpenAI API']),
    ('core', 'CORE STACK', ['Laravel', 'Vue.js', 'Inertia.js', 'Nuxt', 'Livewire', 'Alpine.js', 'Tailwind CSS', 'Pinia']),
    ('mobile', 'MOBILE', ['React Native', 'Swift', 'iOS', 'Android']),
    ('platforms', 'PLATFORMS & AUTOMATION', ['Shopify', 'GoHighLevel', 'Zapier', 'n8n', 'Stripe', 'Bitrix24']),
    ('languages', 'LANGUAGES & FRAMEWORKS', ['PHP', 'JavaScript', 'TypeScript', 'Python', 'C#', 'Node.js', 'React', 'Next.js', '.NET']),
    ('databases', 'DATABASES & APIS', ['MySQL', 'PostgreSQL', 'Redis', 'Firebase', 'REST', 'GraphQL', 'WebSockets', 'OAuth 2.0']),
    ('cloud', 'CLOUD & DEVOPS', ['AWS', 'DigitalOcean', 'Cloudflare', 'GCP', 'Docker', 'CI/CD', 'GitLab CI', 'GitHub Actions', 'Laravel Forge']),
]
MARKED = {'Laravel', 'Vue.js'}  # the core of the kit gets the highlighter


def listed(pen, items, x, baseline, width, line, size=19):
    """The items of one group, written along the rules. Returns the lines used."""
    joined = (NB + '· ').join(item.replace(' ', NB) for item in items)
    lines = build.wrap(joined, 'comic', size, width)
    for row, words in enumerate(lines):
        for item in items:
            mark = item.replace(' ', NB)
            if item in MARKED and mark in words:
                before = build.advance(words[:words.index(mark)], 'comic', size)
                highlight(pen, x + before - 2, baseline + row * line - size * 0.82, build.advance(mark, 'comic', size) + 4, size * 1.05)
        pen.add(text(x, baseline + row * line, words, size, 'comic'))
    return len(lines)


def starter_pack():
    pen = Pen('starter-pack')
    line, height = 29, 766
    panel(pen, 6, 6, 828, height - 12, -0.2)
    caption_box(pen, 22, 20, 'THE SENIOR FULL STACK DEV STARTER PACK', 34)
    px, py, pw = 30, 96, 780
    notebook(pen, px, py, pw, height - py - 26, line, 44, 66)
    rule = lambda n: py + 44 + n * line - 7  # the baseline that sits on rule n

    kind, heading, items = PACK[0]
    doodle(pen, kind, px + 10, rule(0) - 30, 0.74)
    pen.add(text(px + 80, rule(0), heading, 25, 'anton'))
    circled(pen, px + 80 + build.advance(heading, 'anton', 25) / 2, rule(0) - 9, build.advance(heading, 'anton', 25) / 2 + 13, 19)
    used = listed(pen, items, px + 80, rule(1), pw - 100, line)
    assert used <= 3, 'AI row needs more rules'

    for index, (kind, heading, items) in enumerate(PACK[1:]):
        row, col = divmod(index, 2)
        top = 5 + row * 5
        x = px + 80 if col == 0 else px + 462
        doodle(pen, kind, x - 70 if col == 0 else x - 56, rule(top) - 30, 0.74)
        pen.add(text(x, rule(top), heading, 23, 'anton'))
        used = listed(pen, items, x, rule(top + 1), 300 if col == 0 else 292, line)
        assert used <= 3, f'{heading} needs more rules'
    picture('starter-pack', 846, height, pen, 'The tech stack as a starter pack, written on a torn notebook page.')


STRIP = [  # the picture, what he says, the shout under it
    ('memes/ship-1-plan.png', 'I write the plan and the guardrails.', None),
    ('memes/ship-2-build.png', 'Agents build it with my custom skills.', None),
    ('memes/ship-3-review.png', 'Reviewer agents try to break it.', 'Y U NO PASS'),
    ('memes/ship-4-ship.png', 'I verify, test and ship.', 'SHIP IT'),
]


def ship():
    pen = Pen('ship')
    w, h, gap_x, gap_y, top = 388, 204, 40, 40, 112
    width, height = 846, top + 2 * h + gap_y + 16
    caption_box(pen, 14, 12, 'HOW I SHIP IN 2026', 40)
    pen.add(text(16, 98, 'Agents do the heavy lifting. I own the architecture, the standards and the final review.', 19, 'comic', fit=800))
    for index, (image, says, shout) in enumerate(STRIP):
        row, col = divmod(index, 2)
        x, y = 12 + col * (w + gap_x), top + row * (h + gap_y)
        frame = box(pen, x, y, w, h, (-0.35, 0.45, 0.3, -0.25)[index])
        pen.fill(frame, PAPER, step=16)
        slot(pen, image, x + 12, y + 14, 178, h - 28)
        pen.ring(frame, 4.6, step=16)
        lines = build.wrap(says, 'comicb', 19, 150)
        bh = len(lines) * 24 + 26
        by = y + 22 + (0 if shout else 18)
        start = len(pen.parts)
        bubble(pen, x + 202, by, 174, bh, (x + 203, by + bh / 2, x + 180, by + bh / 2 + 6))
        for n, words in enumerate(lines):
            pen.add(text(x + 216, by + 33 + n * 24, words, 19))
        inner = ''.join(pen.parts[start:])
        del pen.parts[start:]
        pen.add(f'<g class="bob bob{index + 1}">{inner}</g>')
        if shout:
            pen.add(text(x + 289, y + h - 22, shout, 31, 'anton', 'middle', cls='cap', stroke='0.15'))
    mid = top + h / 2
    arrow(pen, [(12 + w + 5, mid), (12 + w + gap_x - 3, mid)])
    arrow(pen, [(12 + w + 5, mid + h + gap_y), (12 + w + gap_x - 3, mid + h + gap_y)])
    below = top + h
    arrow(pen, [(646, below + 3), (630, below + 19), (420, below + 21), (226, below + 19), (204, below + gap_y - 3)], style='--dx:0px;--dy:4px')
    picture('ship', width, height, pen, 'How I ship in 2026, as a four-panel strip.')


def outro():
    pen = Pen('outro')
    height = 286
    panel(pen, 6, 6, 828, height - 12, 0.25)
    slot(pen, 'memes/say-hi.png', 32, 54, 202, 176)
    pen.add(text(133, 46, 'Y U NO', 38, 'anton', 'middle', cls='cap', stroke='0.15'))
    pen.add(text(133, 266, 'SEND ME AN EMAIL', 30, 'anton', 'middle', fit=228, cls='cap', stroke='0.15'))
    pen.stroke([(262, 16), (260, height - 18)], 4, step=30, taper=False)
    caption_box(pen, 284, 22, 'SAY HI', 42)
    pen.add(text(286, 116, 'Web, mobile, AI and automation, from requirements to deployment.', 20, 'comic', fit=530))
    pen.add(text(286, 142, 'One email away.', 20, 'comic'))
    email, size = 'job@rcmadeloso.com', 44
    span = build.advance(email, 'anton', size)
    pen.add(text(300, 208, email, size, 'anton'))
    circled(pen, 300 + span / 2, 192, span / 2 + 20, 31)
    pen.add(text(286, 256, 'Ramil Christopher Madeloso · Dumaguete, PH · Remote', 16, 'comic'))
    picture('outro', 846, height, pen, 'The sign-off: why u no send me an email.')


def faces():
    """The portrait and the four strip faces on one sheet, for the fold-out in the README."""
    pen = Pen('faces')
    panel(pen, 6, 6, 828, 232, 0.2)
    caption_box(pen, 22, 20, 'ONE SPRINT, FIVE FACES', 30)
    for index, (name, label) in enumerate((('portrait.png', 'the estimate'), ('memes/ship-1-plan.png', 'the plan'), ('memes/ship-2-build.png', 'the build'),
                                           ('memes/ship-3-review.png', 'the review'), ('memes/ship-4-ship.png', 'the release'))):
        x = 24 + index * 161
        slot(pen, name, x + 4, 66, 142, 138)
        pen.add(text(x + 75, 226, label, 18, anchor='middle'))
    picture('faces', 846, 250, pen, 'The five pictures side by side.')


def doodles(out):
    """The starter-pack drawings as files of their own, for the site."""
    out.mkdir(parents=True, exist_ok=True)
    for kind, *_ in PACK:
        pen = Pen('doodle-' + kind)
        doodle(pen, kind, 0, 0, 1)
        (out / f'{kind}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{"".join(pen.parts)}</svg>\n')


def buttons():
    for name, words, width, inked in (('portfolio', 'Portfolio', 115, True), ('email', 'Email me', 122, False),
                                      ('linkedin', 'LinkedIn', 117, False), ('resume', 'Download resume', 190, False)):
        pen = Pen('btn-' + name)
        pen.shape(box(pen, 4, 4, width - 14, 36, 0, 1.6), INK if inked else PAPER, 3.6, step=10)
        pen.add(text((width - 6) / 2, 28.5, words, 18, anchor='middle', fill=PAPER if inked else None))
        picture('btn-' + name, width, 50, pen, f'The {words} button.')


if __name__ == '__main__':
    starter_pack()
    ship()
    outro()
    faces()
    buttons()
    build.build()
