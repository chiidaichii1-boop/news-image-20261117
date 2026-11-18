#!/usr/bin/env python3
"""News in one image: Tuesday 17 November 2026.

A program that draws one newspaper-style summary image of the world's news
of 17 November 2026 and writes it to /output/entry.png (or the directory in
MAKEFUN_OUTPUT_DIR). Pure Python 3 standard library: no network, no clock,
no randomness, so two runs write byte-identical output.

The picture is drawn with code: a masthead naming the day, one lead story
with a drawn scene, five more stories with drawn icons, and a ticker of
three further stories. All news text is baked into this file, researched
from real reporting of the day.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# --------------------------------------------------------------------------
# 5x7 bitmap font, authored here. Each glyph is 7 rows of 5 bits, written
# as five-character strings ("1" = ink). Only capitals, digits and the
# punctuation the copy needs: the whole image is set in capitals, like a
# newspaper front page.
# --------------------------------------------------------------------------

FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "10110", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00100", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("01110", "10001", "00001", "00110", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    ";": ("00000", "00100", "00000", "00000", "00100", "00100", "01000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "`": ("00100", "00100", "00010", "00000", "00000", "00000", "00000"),
    "{": ("00110", "01000", "01000", "01110", "01000", "01000", "00110"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "}": ("01100", "00010", "00010", "01110", "00010", "00010", "01100"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "\u2022": ("00000", "00100", "01110", "01110", "01110", "00100", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "\u2013": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "\u00d7": ("00000", "10001", "01010", "00100", "01010", "10001", "00000"),
    "\u2019": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "\u201c": ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "\u201d": ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
}

# Normalise curly quotes and dashes to the glyphs above.
NORMALISE = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-",
}


def glyph(ch):
    return FONT.get(NORMALISE.get(ch, ch), FONT[" "])


def text_width(s, scale):
    return sum(6 * scale for _ in s) - (scale if s else 0)


def wrap_text(s, scale, max_w):
    """Split s into lines that fit max_w pixels at the given scale."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w) if cur else w
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------

PAPER = (247, 243, 234)
INK = (26, 26, 26)
NAVY = (15, 42, 74)
NAVY_DARK = (10, 30, 54)
GOLD = (201, 162, 39)
GOLD_LIGHT = (232, 196, 90)
RED = (179, 38, 30)
BLUE = (31, 78, 121)
TEAL = (14, 124, 107)
ORANGE = (224, 123, 57)
SKY = (135, 178, 214)
SEA = (12, 46, 74)
WHITE = (255, 255, 255)
GREY = (120, 120, 115)
LIGHT_GREY = (226, 222, 212)
GREEN_DARK = (18, 92, 52)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.pix = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.pix[i] = color[0]
            self.pix[i + 1] = color[1]
            self.pix[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.pix[i:i + len(row)] = row

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self._set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        # Filled circle, midpoint scanlines.
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - half, cy + dy, half * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            inner = int(max(0, (r - thick) * (r - thick) - dy * dy) ** 0.5) if abs(dy) < r - thick else 0
            self.rect(cx - half, cy + dy, half - inner + 1, 1, color)
            self.rect(cx + inner, cy + dy, half - inner + 1, 1, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Filled triangle by scanlines.
        ys = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = ys
        if ay == cy:
            return
        def edge_x(p, q, y):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
        for y in range(ay, cy + 1):
            if y < by:
                xa = edge_x((ax, ay), (bx, by), y)
                xb = edge_x((ax, ay), (cx, cy), y)
            else:
                xa = edge_x((bx, by), (cx, cy), y)
                xb = edge_x((ax, ay), (cx, cy), y)
            x0l, x1l = int(min(xa, xb)), int(max(xa, xb))
            self.rect(x0l, y, x1l - x0l + 1, 1, color)

    def text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            rows = glyph(ch)
            for r in range(7):
                bits = rows[r]
                for c in range(5):
                    if bits[c] == "1":
                        self.rect(cx + c * scale, y + r * scale, scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centred(self, s, cx, y, scale, color):
        w = text_width(s, scale)
        self.text(s, cx - w // 2, y, scale, color)

    def text_wrapped(self, s, x, y, scale, max_w, color, line_h=None):
        if line_h is None:
            line_h = 7 * scale + 3
        yy = y
        for line in wrap_text(s, scale, max_w):
            self.text(line, x, yy, scale, color)
            yy += line_h
        return yy


# --------------------------------------------------------------------------
# PNG writer (deterministic: fixed compression level, no timestamps).
# --------------------------------------------------------------------------

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, canvas):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw.extend(canvas.pix[y * canvas.w * 3:(y + 1) * canvas.w * 3])
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# --------------------------------------------------------------------------
# The day's news (researched from real reporting of 17 November 2026).
# --------------------------------------------------------------------------

LEAD = {
    "kicker": "MIDDLE EAST",
    "headline": "U.S. STRIKES IRAN",
    "sub": "WARPLANES HIT A MISSILE SITE ON QESHM ISLAND. A TANKER BURNS OFF "
           "OMAN; 24 CREW SAVED. TRUMP WEIGHS A REPORT OF AN IRANIAN DIRTY-BOMB PLOT.",
    "tag": "STRAIT OF HORMUZ",
}

STORIES = [
    {
        "kicker": "UKRAINE",
        "headline": "CRIMEAN BRIDGE STRUCK",
        "sub": "UKRAINE HITS THE SPAN; RUSSIA STRIKES KYIV BRIDGES, CUTTING HEAT AND WATER.",
        "color": BLUE,
        "icon": "bridge",
    },
    {
        "kicker": "ASIA",
        "headline": "XI, TRUMP AND PUTIN TO MEET",
        "sub": "FIRST TRILATERAL SUMMIT SET FOR THURSDAY AT APEC IN SHENZHEN, CHINA.",
        "color": RED,
        "icon": "summit",
    },
    {
        "kicker": "TECH",
        "headline": "NVIDIA CHIEF QUITS IN SPY SCANDAL",
        "sub": "HUANG RESIGNS OVER AFFAIR WITH SUSPECTED CHINESE AGENT; U.S. TIGHTENS AI CHIP CURBS.",
        "color": GREEN_DARK,
        "icon": "chip",
    },
    {
        "kicker": "BRITAIN",
        "headline": "UK SANCTIONS ISRAELI SETTLERS",
        "sub": "LONDON BLACKLISTS 8 FIRMS OVER WEST BANK BUILDING; WEST URGES GAZA AID CROSSINGS OPEN.",
        "color": NAVY,
        "icon": "jack",
    },
    {
        "kicker": "HEALTH",
        "headline": "U.S. LOSES MEASLES-FREE STATUS",
        "sub": "FIRST LOSS SINCE 2000 AS VACCINATION RATES FALL, HEALTH OFFICIALS WARN.",
        "color": RED,
        "icon": "virus",
    },
]

TICKER = ("ALSO: WALL STREET FALLS  \u2022  JAPAN SCRAMBLES JETS  \u2022  "
          "DUBAI TRAFFIC DOWN 28%")


# --------------------------------------------------------------------------
# Drawn illustrations (simple flat scenes, all geometry).
# --------------------------------------------------------------------------

def draw_lead_scene(c, x, y, w, h):
    # Dusk sky over the strait.
    c.rect(x, y, w, 150, (27, 42, 74))
    c.rect(x, y + 100, w, 50, (90, 70, 90))
    c.rect(x, y + 130, w, 20, (224, 123, 57))
    # Low sun.
    c.circle(x + 300, y + 138, 26, (245, 166, 35))
    c.circle(x + 300, y + 138, 18, (255, 205, 90))
    # Sea.
    c.rect(x, y + 150, w, h - 150, SEA)
    for wy in (y + 168, y + 196, y + 236, y + 262):
        for wx in range(x + 12, x + w - 40, 64):
            c.hline(wx, wy, 34, (70, 130, 170))
    # Missile arc from the top right.
    pts = []
    for t in range(0, 21):
        fx = t / 20.0
        px = int(x + w - 20 - fx * 260)
        py = int(y + 8 + fx * fx * 120)
        pts.append((px, py))
    for (px0, py0), (px1, py1) in zip(pts, pts[1:]):
        c.line(px0, py0, px1, py1, (255, 220, 130))
    c.circle(pts[-1][0], pts[-1][1], 4, WHITE)
    # Tanker.
    c.rect(x + 40, y + 208, 320, 26, (12, 12, 12))
    c.rect(x + 40, y + 204, 320, 4, (40, 40, 40))
    c.rect(x + 300, y + 180, 42, 24, (240, 240, 235))
    c.rect(x + 306, y + 186, 8, 8, (20, 60, 110))
    c.rect(x + 320, y + 186, 8, 8, (20, 60, 110))
    c.rect(x + 316, y + 166, 12, 14, (179, 38, 30))
    # Blast above the tanker.
    c.circle(x + 118, y + 168, 30, (224, 123, 57))
    c.circle(x + 118, y + 168, 20, (245, 166, 35))
    c.circle(x + 118, y + 168, 10, (255, 220, 130))
    for dx, dy in ((-34, -18), (30, -26), (-28, 22), (34, 14)):
        c.line(x + 118, y + 168, x + 118 + dx, y + 168 + dy, (245, 166, 35))
    # Smoke.
    c.circle(x + 96, y + 128, 14, (120, 120, 115))
    c.circle(x + 122, y + 112, 18, (140, 140, 135))
    c.circle(x + 150, y + 124, 12, (120, 120, 115))


def draw_icon(c, kind, x, y, s):
    """Draw a small square icon (s x s) for a story thumbnail."""
    if kind == "bridge":
        c.rect(x, y, s, s, (214, 230, 240))
        c.rect(x, y + s - 34, s, 34, (70, 110, 150))
        c.rect(x, y + 40, s, 8, (90, 90, 90))
        c.rect(x + 16, y + 12, 8, 36, (90, 90, 90))
        c.rect(x + s - 24, y + 12, 8, 36, (90, 90, 90))
        c.line(x + 20, y + 14, x + s // 2, y + 40, (120, 120, 120))
        c.line(x + s - 20, y + 14, x + s // 2, y + 40, (120, 120, 120))
        c.circle(x + s // 2, y + 34, 12, ORANGE)
        c.circle(x + s // 2, y + 34, 6, (255, 220, 130))
    elif kind == "summit":
        c.rect(x, y, s, s, WHITE)
        bw = s // 3
        c.rect(x, y + 14, bw - 4, s - 28, (200, 40, 40))
        c.rect(x + bw, y + 14, bw - 4, s - 28, (30, 60, 140))
        c.rect(x + 2 * bw, y + 14, bw - 4, s - 28, (180, 30, 30))
        for cx in (x + bw // 2 - 2, x + bw + bw // 2 - 2, x + 2 * bw + bw // 2 - 2):
            c.circle(cx, y + s // 2, 7, GOLD_LIGHT)
    elif kind == "chip":
        c.rect(x, y, s, s, (230, 238, 228))
        c.rect(x + 20, y + 20, s - 40, s - 40, GREEN_DARK)
        c.rect(x + 34, y + 34, s - 68, s - 68, (18, 92, 52))
        for px in (x + 8, x + s - 12):
            for py in range(y + 26, y + s - 20, 14):
                c.rect(px, py, 4, 8, GOLD)
        for py in (y + 8, y + s - 12):
            for px in range(x + 26, x + s - 20, 14):
                c.rect(px, py, 8, 4, GOLD)
        # Falling arrow.
        c.line(x + 18, y + 22, x + s - 22, y + s - 26, RED)
        c.line(x + 18, y + 22, x + s - 22, y + s - 26, RED)
        c.triangle(x + s - 24, y + s - 30, x + s - 14, y + s - 30,
                   x + s - 18, y + s - 16, RED)
    elif kind == "jack":
        c.rect(x, y, s, s, (20, 60, 140))
        c.line(x, y, x + s, y + s, WHITE)
        c.line(x + s, y, x, y + s, WHITE)
        c.rect(x, y + s // 2 - 10, s, 20, WHITE)
        c.rect(x + s // 2 - 10, y, 20, s, WHITE)
        c.rect(x, y + s // 2 - 6, s, 12, RED)
        c.rect(x + s // 2 - 6, y, 12, s, RED)
    elif kind == "virus":
        c.rect(x, y, s, s, (250, 238, 232))
        cx, cy, r = x + s // 2, y + s // 2, 22
        for k in range(8):
            ang = k * 3.14159265 / 4.0
            x0 = int(cx + math.cos(ang) * (r - 2))
            y0 = int(cy + math.sin(ang) * (r - 2))
            x1 = int(cx + math.cos(ang) * (r + 12))
            y1 = int(cy + math.sin(ang) * (r + 12))
            c.line(x0, y0, x1, y1, RED)
            c.circle(x1, y1, 4, RED)
        c.circle(cx, cy, r, RED)
        c.circle(cx - 7, cy - 6, 4, (255, 180, 170))
        c.circle(cx + 8, cy + 5, 3, (255, 180, 170))
        c.circle(cx + 2, cy - 10, 2, (255, 180, 170))


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def draw():
    c = Canvas(W, H, PAPER)

    # Masthead.
    c.rect(0, 0, W, 116, NAVY)
    c.text_centred("THE WORLD", W // 2, 12, 9, WHITE)
    c.text_centred("TUESDAY, 17 NOVEMBER 2026", W // 2, 86, 4, GOLD_LIGHT)
    c.rect(0, 116, W, 4, GOLD)

    # Lead story.
    lx, ly, lw, lh = 28, 132, 400, 288
    draw_lead_scene(c, lx, ly, lw, lh)
    c.rect(lx, ly + lh - 26, lw, 26, NAVY)
    c.text_centred(LEAD["tag"], lx + lw // 2, ly + lh - 21, 2, GOLD_LIGHT)
    tx = lx + lw + 24
    tw = W - 28 - tx
    c.text(LEAD["kicker"], tx, 150, 3, RED)
    c.rect(tx, 178, 64, 4, RED)
    c.text(LEAD["headline"], tx, 192, 5, INK)
    c.text_wrapped(LEAD["sub"], tx, 242, 3, tw, (60, 60, 58), line_h=26)

    # Divider.
    c.rect(28, 432, W - 56, 2, LIGHT_GREY)

    # Story rows.
    y = 444
    for st in STORIES:
        draw_icon(c, st["icon"], 28, y, 96)
        # Thin frame around the icon.
        c.rect(28, y, 96, 2, INK)
        c.rect(28, y + 94, 96, 2, INK)
        c.rect(28, y, 2, 96, INK)
        c.rect(122, y, 2, 96, INK)
        tx2 = 140
        c.text(st["kicker"], tx2, y + 4, 2, st["color"])
        c.text(st["headline"], tx2, y + 24, 4, INK)
        c.text_wrapped(st["sub"], tx2, y + 58, 3, W - 28 - tx2, (60, 60, 58),
                       line_h=24)
        y += 108

    # Ticker.
    c.rect(0, 986, W, 28, NAVY_DARK)
    c.text(TICKER, 28, 993, 2, GOLD_LIGHT)

    return c


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    size = write_png(path, draw())
    print(f"wrote {path} ({size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
