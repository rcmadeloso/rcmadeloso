#!/usr/bin/env python3
"""Builds assets/*.svg from src/*.svg.

GitHub shows README pictures as <img>, where an SVG cannot load a web font. So
every <text> in src/ is redrawn here as outlines from the fonts in src/fonts,
and {{portrait:SIZE}} becomes the portrait as an inline PNG.

    pip install fonttools pillow
    python3 build.py

<text> attributes read here (all others pass through to the outline):
  x, y, font-size, text-anchor, letter-spacing
  data-font     anton | comic | comicb (default comicb)
  data-fit      shrink the type until the line is at most this wide
  data-wrap     break into lines at most this wide; data-leading sets the step
  data-stroke   stroke width in em (the meme caption outline)
  data-key      underline the first letter, like a Windows menu access key

Plain text becomes <use> references to one outline per glyph, so a file stays
small however much it says. Stroked captions become a single path instead.
"""
import base64
import html
import io
import re
from pathlib import Path
from xml.dom import minidom

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).parent
FONT_FILES = {'anton': 'Anton-Regular.ttf', 'comic': 'ComicNeue-Regular.ttf', 'comicb': 'ComicNeue-Bold.ttf'}
FONTS = {}
for key, name in FONT_FILES.items():
    font = TTFont(ROOT / 'src/fonts' / name)
    FONTS[key] = (font.getGlyphSet(), font.getBestCmap(), font['hmtx'], font['head'].unitsPerEm)


def num(value):
    return f'{value:.1f}'.rstrip('0').rstrip('.')


# shortcut: no kerning pairs are applied, add uharfbuzz shaping if a pair ever looks loose
def advance(text, font_key, size, spacing=0.0):
    _, cmap, hmtx, upm = FONTS[font_key]
    for ch in text:
        if ord(ch) not in cmap:
            raise SystemExit(f'{FONT_FILES[font_key]} has no glyph for {ch!r} in {text!r}')
    return sum(hmtx[cmap[ord(ch)]][0] * size / upm + spacing for ch in text) - (spacing if text else 0)


def wrap(text, font_key, size, width):
    lines, line = [], ''
    for word in text.split(' '):
        trial = f'{line} {word}'.strip()
        if line and advance(trial, font_key, size) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


GLYPHS = {}  # id -> outline in font units, shared by every <use> in one file


def outline(match):
    attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', match.group(1)))
    text = html.unescape(match.group(2)).strip()
    font_key = attrs.pop('data-font', 'comicb')
    size = float(attrs.pop('font-size'))
    x, y = float(attrs.pop('x', 0)), float(attrs.pop('y', 0))
    anchor = attrs.pop('text-anchor', 'start')
    spacing = float(attrs.pop('letter-spacing', 0))
    fit, wrap_at = attrs.pop('data-fit', None), attrs.pop('data-wrap', None)
    leading = float(attrs.pop('data-leading', size * 1.2))
    stroke_em, key = attrs.pop('data-stroke', None), attrs.pop('data-key', None)

    if fit:
        size = min(size, size * float(fit) / advance(text, font_key, size, spacing))
    lines = wrap(text, font_key, size, float(wrap_at)) if wrap_at else [text]

    glyphs, cmap, hmtx, upm = FONTS[font_key]
    scale = size / upm
    pen = SVGPathPen(glyphs, ntos=num)  # stroked captions: one path, so no outline covers a neighbour
    uses = []
    for row, line in enumerate(lines):
        width = advance(line, font_key, size, spacing)
        cursor = x - {'start': 0, 'middle': width / 2, 'end': width}[anchor]
        baseline = y + row * leading
        for index, ch in enumerate(line):
            name = cmap[ord(ch)]
            step = hmtx[name][0]
            ux, uy = round((cursor - x) / scale), round((y - baseline) / scale)
            if stroke_em:
                glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline)))
            elif not ch.isspace():
                glyph_id = f'{font_key[0] if font_key != "comicb" else "b"}{ord(ch):x}'
                if glyph_id not in GLYPHS:
                    unit_pen = SVGPathPen(glyphs)
                    glyphs[name].draw(unit_pen)
                    GLYPHS[glyph_id] = unit_pen.getCommands()
                uses.append(f'<use href="#{glyph_id}"' + (f' x="{ux}"' if ux else '') + (f' y="{uy}"' if uy else '') + '/>')
            if key and row == 0 and index == 0:
                uses.append(f'<path d="M{ux} {round(-0.14 * upm)}h{step}v{round(-0.1 * upm)}h-{step}z"/>')
            cursor += step * scale + spacing
    rest = ''.join(f' {name}="{value}"' for name, value in attrs.items())
    if stroke_em:
        return f'<path{rest} stroke-width="{num(size * float(stroke_em))}" d="{pen.getCommands()}"/>'
    return f'<g{rest} transform="translate({num(x)} {num(y)}) scale({scale:.5f} -{scale:.5f})">{"".join(uses)}</g>'


PORTRAITS = {}


def portrait(match):
    size = int(match.group(1))
    if size not in PORTRAITS:
        image = Image.open(ROOT / 'src/portrait.png').convert('RGB').resize((size, size), Image.LANCZOS)
        # Snap the paper to pure white and the ink to pure black, so flat areas stay flat and small.
        image = image.point(lambda value: 255 if value >= 236 else 0 if value <= 18 else value)
        buffer = io.BytesIO()
        # Ink, paper, one hoodie tan and their blends: 24 colours keep the edges smooth.
        image.quantize(24, dither=Image.Dither.NONE).save(buffer, 'PNG', optimize=True)
        PORTRAITS[size] = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
    return PORTRAITS[size]


def build():
    out_dir = ROOT / 'assets'
    out_dir.mkdir(exist_ok=True)
    for source in sorted((ROOT / 'src').glob('*.svg')):
        svg = source.read_text()
        svg = re.sub(r'<!--.*?-->\s*', '', svg, flags=re.S)
        GLYPHS.clear()
        svg = re.sub(r'<text\b([^>]*)>([^<]*)</text>', outline, svg)
        defs = ''.join(f'<path id="{glyph_id}" d="{d}"/>' for glyph_id, d in sorted(GLYPHS.items()))
        svg = re.sub(r'(<svg\b[^>]*>)', rf'\1\n<defs>{defs}</defs>', svg, count=1)
        svg = re.sub(r'\{\{portrait:(\d+)\}\}', portrait, svg)
        svg = re.sub(r'\n\s*', '\n', svg).strip() + '\n'
        # Self-check: nothing left that GitHub cannot draw, and the file still parses.
        assert '<text' not in svg and '{{' not in svg, f'{source.name}: unconverted text or placeholder'
        minidom.parseString(svg)
        (out_dir / source.name).write_text(svg)
        print(f'{source.name:24} {len(svg) / 1024:6.1f} KB')


if __name__ == '__main__':
    build()
