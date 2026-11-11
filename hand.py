"""A pen that draws by hand, on a 512 by 512 sheet.

Nothing here is a clean vector line. An ink line is a filled shape whose two
edges wander a little and whose weight changes along the way, set down in short
straight steps on whole numbers. Hatching is a zigzag pulled across with a
plain stroke. Colours are flat. One seed gives one drawing, so a picture comes
out the same on every build.

    pen = Pen('my-drawing')
    pen.shape(curve([(100, 100), (200, 90), (210, 200), (95, 210)], closed=True), '#fff', 9)
    pen.stroke(curve([(120, 150), (150, 140), (180, 152)]), 7)
    svg = pen.svg()
"""
import math
import random
import zlib

INK = '#111'


def curve(points, closed=False, per=10):
    """A smooth line through the points (Catmull-Rom), as many small steps."""
    pts, n, out = list(points), len(points), []
    at = (lambda i: pts[i % n]) if closed else (lambda i: pts[max(0, min(n - 1, i))])
    for i in range(n if closed else n - 1):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = at(i - 1), at(i), at(i + 1), at(i + 2)
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * (2 * x1 + (x2 - x0) * t + (2 * x0 - 5 * x1 + 4 * x2 - x3) * t2 + (3 * x1 - x0 - 3 * x2 + x3) * t3),
                0.5 * (2 * y1 + (y2 - y0) * t + (2 * y0 - 5 * y1 + 4 * y2 - y3) * t2 + (3 * y1 - y0 - 3 * y2 + y3) * t3),
            ))
    if not closed:
        out.append(pts[-1])
    return out


def oval(cx, cy, rx, ry, count=14, turn=0.0):
    """Points round an oval, for curve(..., closed=True)."""
    return [(cx + rx * math.cos(turn + math.tau * i / count), cy + ry * math.sin(turn + math.tau * i / count)) for i in range(count)]


def walk(points, step, closed=False):
    """The same line in steps of about `step`, corners kept."""
    pts = list(points) + ([points[0]] if closed else [])
    out, carry = [pts[0]], 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        if not length:
            continue
        pos = step - carry
        while pos < length:
            out.append((x0 + (x1 - x0) * pos / length, y0 + (y1 - y0) * pos / length))
            pos += step
        carry = length - (pos - step)
    if closed:
        if math.hypot(out[-1][0] - out[0][0], out[-1][1] - out[0][1]) < step * 0.5:
            out.pop()
    else:
        out.append(pts[-1])
    return out


def turned(points, cx, cy, degrees):
    a = math.radians(degrees)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in points]


def moved(points, dx, dy):
    return [(x + dx, y + dy) for x, y in points]


class Pen:
    def __init__(self, seed):
        self.rng = random.Random(zlib.crc32(seed.encode()))
        self.parts = []

    # ---- the hand

    def _shake(self, points, amount):
        return [(x + self.rng.uniform(-amount, amount), y + self.rng.uniform(-amount, amount)) for x, y in points]

    def _weights(self, count, width):
        """Line weight along the way: a slow drift, never even."""
        out, drift = [], self.rng.uniform(-1, 1)
        for _ in range(count):
            drift = max(-1, min(1, drift + self.rng.uniform(-0.45, 0.45)))
            out.append(width * (1 + 0.2 * drift))
        return out

    @staticmethod
    def _normals(points, closed):
        n, out = len(points), []
        for i in range(n):
            a = points[(i - 1) % n] if closed else points[max(0, i - 1)]
            b = points[(i + 1) % n] if closed else points[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy) or 1
            out.append((-dy / length, dx / length))
        return out

    @staticmethod
    def _d(points, close=True):
        pts = [(round(x), round(y)) for x, y in points]
        d, (px, py) = f'M{pts[0][0]} {pts[0][1]}l', pts[0]
        steps = []
        for x, y in pts[1:]:
            if (x, y) != (px, py):
                steps.append(f'{x - px} {y - py}')
                px, py = x, y
        return d + ' '.join(steps).replace(' -', '-') + ('z' if close else '')

    # ---- marks

    def add(self, markup):
        self.parts.append(markup)

    def fill(self, points, colour, step=9, shake=0.8):
        """A flat patch of colour with a hand-cut edge."""
        self.add(f'<path d="{self._d(self._shake(walk(points, step, True), shake))}" fill="{colour}"/>')

    def ring(self, points, width=9, step=8, colour=INK):
        """The ink line round a closed shape."""
        pts = self._shake(walk(points, step, True), 0.7)
        normals, weights = self._normals(pts, True), self._weights(len(pts), width)
        outer = [(x + nx * w / 2, y + ny * w / 2) for (x, y), (nx, ny), w in zip(pts, normals, weights)]
        inner = [(x - nx * w / 2, y - ny * w / 2) for (x, y), (nx, ny), w in zip(pts, normals, weights)]
        self.add(f'<path d="{self._d(outer)}{self._d(inner[::-1])}" fill="{colour}" fill-rule="evenodd"/>')

    def shape(self, points, colour='#fff', width=9, step=8):
        self.fill(points, colour, step)
        self.ring(points, width, step)

    def stroke(self, points, width=7, step=7, taper=True, colour=INK):
        """One pull of the pen: thick in the middle, thin where it lifts."""
        pts = self._shake(walk(points, step), 0.6)
        normals, weights = self._normals(pts, False), self._weights(len(pts), width)
        last = len(pts) - 1
        if taper:
            weights = [w * (0.25 + 0.75 * max(0.0, math.sin(math.pi * i / last)) ** 0.6) for i, w in enumerate(weights)]
        left = [(x + nx * w / 2, y + ny * w / 2) for (x, y), (nx, ny), w in zip(pts, normals, weights)]
        right = [(x - nx * w / 2, y - ny * w / 2) for (x, y), (nx, ny), w in zip(pts, normals, weights)]
        self.add(f'<path d="{self._d(left + right[::-1])}" fill="{colour}"/>')

    def zig(self, points, width=5, colour=INK):
        """Hatching: a zigzag pulled through the points with a plain stroke."""
        self.add(f'<path d="{self._d(self._shake(points, 1.5), close=False)}" fill="none" stroke="{colour}" stroke-width="{width}"/>')

    def dot(self, x, y, r=3, colour=INK):
        self.fill(oval(x, y, r * self.rng.uniform(0.8, 1.2), r * self.rng.uniform(0.8, 1.2), 6, self.rng.uniform(0, 3)), colour, step=r, shake=0.4)

    def group(self, name, draw):
        """Everything `draw` puts down goes in one <g class="name">, so it can move."""
        start = len(self.parts)
        draw()
        inner = ''.join(self.parts[start:])
        del self.parts[start:]
        self.add(f'<g class="{name}">{inner}</g>')

    def body(self):
        return '<g transform="scale(.5)">' + '\n'.join(self.parts) + '</g>'

    def svg(self, style=''):
        style = f'<style>{style}</style>' if style else ''
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256" '
                f'stroke-linejoin="miter" stroke-linecap="butt">{style}\n{self.body()}\n</svg>\n')
