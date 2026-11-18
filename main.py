#!/usr/bin/env python3
"""THE WORLD — Tuesday 17 November 2026, in one image.

A newspaper front page drawn procedurally with Python 3.13 stdlib only:
no network, no fonts on disk, no image files. A hand-coded 5x7 bitmap
font (font5x7.py) draws every headline; every motif is flat vector
shapes on a 1024x1024 canvas. The PNG is encoded by hand (zlib + CRC)
and the run is fully deterministic: same bytes every time.

Stories of Tue 17 Nov 2026, as reported that day:
  1. US-IRAN STRIKES — US jets hit a missile site on Qeshm Island;
     Iran fired drones at a US radar at Sheikh Isa base, Bahrain;
     a 4th oil tanker was hit by a mine in the Strait of Hormuz.
  2. KERCH BRIDGE — Ukrainian strikes hit the bridge a 2nd day;
     a road section fell into the strait.
  3. NVIDIA — record Q3 revenue above $115B, but the ousted CEO
     Jensen Huang will NOT be reinstated.
  4. SUMMIT — a Trump-Xi-Putin trilateral is set for Thu 19 Nov
     in Shenzhen.
  5. GAZA AID — the UK, Australia, Canada and Italy jointly urge
     Israel to open the crossings; the situation "catastrophic".
  6. DEPARDIEU — Gerard Depardieu pleaded guilty to a sexual
     assault charge in a Paris court.
"""

import os
import struct
import zlib

from font5x7 import GLYPHS, text_width

W = 1024
H = 1024

# --- palette: newsprint on cream paper -------------------------------------
PAPER = (244, 239, 228)
INK = (20, 20, 20)
RED = (179, 39, 30)
GOLD = (255, 200, 69)
SKY = (143, 184, 216)
SKY2 = (111, 163, 204)
SEA = (31, 58, 95)
SEA2 = (61, 110, 143)
STEEL = (58, 90, 110)
GREY = (120, 128, 134)
DARK = (16, 36, 28)
SAND = (232, 220, 192)
LIGHT = (221, 227, 232)
WHITE = (255, 255, 255)
ORANGE = (230, 120, 30)
FLAME = (245, 180, 40)


class Canvas:
    """A flat RGB raster, 1024x1024, drawn with plain rectangles."""

    def __init__(self):
        self.buf = bytearray(W * H * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def pixel(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, thick, thick, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, points, color):
        """Fill a polygon with a scanline pass (points in order)."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y0, y1 = max(0, min(ys)), min(H, max(ys))
        n = len(points)
        for y in range(y0, y1):
            xs = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if ay == by:
                    continue
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = max(0, int(round(xs[k])))
                xb = min(W, int(round(xs[k + 1])))
                if xb > xa:
                    self.fill_rect(xa, y, xb - xa, 1, color)

    def circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
            self.fill_rect(cx - dx, y, dx * 2 + 1, 1, color)

    def border(self, x, y, w, h, color, t=2):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)


def draw_text(cv, x, y, text, scale, color):
    """Draw text with the 5x7 bitmap font; returns the pixel width."""
    cx = x
    for ch in text:
        glyph = GLYPHS.get(ch, GLYPHS["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx - x - scale


def draw_centered(cv, cx, y, text, scale, color):
    w = text_width(text, scale)
    return draw_text(cv, cx - w // 2, y, text, scale, color)


def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(cv.buf[y * W * 3:(y + 1) * W * 3])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# --- masthead: the day itself, big and unmissable ---------------------------
def draw_masthead(cv):
    cv.fill_rect(12, 12, 1000, 4, INK)
    draw_centered(cv, 512, 22, "THE WORLD", 8, INK)
    draw_centered(cv, 512, 82, "TUESDAY 17 NOVEMBER 2026", 4, RED)
    cv.fill_rect(12, 114, 1000, 3, INK)
    cv.fill_rect(12, 119, 1000, 1, INK)


# --- lead: US-IRAN STRIKES --------------------------------------------------
def draw_lead(cv):
    x0, y0, x1, y1 = 12, 126, 1012, 440
    cv.fill_rect(x0, y0, x1 - x0, 160, SKY)
    cv.fill_rect(x0, y0 + 160, x1 - x0, 14, SKY2)
    cv.fill_rect(x0, 286, x1 - x0, 70, SEA)
    # sun
    cv.circle(940, 168, 26, GOLD)
    # jet, top right, diving left
    cv.poly([(700, 170), (820, 150), (900, 168), (820, 186)], (40, 44, 52))
    cv.poly([(760, 168), (700, 156), (700, 180)], (40, 44, 52))
    cv.line(700, 168, 620, 162, WHITE, 3)
    cv.line(700, 174, 630, 176, WHITE, 2)
    # missile arc: three flame dots arcing down to the island
    for cx, cy, r in ((640, 200, 9), (600, 232, 7), (566, 258, 6)):
        cv.circle(cx, cy, r, ORANGE)
        cv.circle(cx, cy, max(2, r - 4), FLAME)
    # Qeshm island: low dark strip with a missile site
    cv.poly([(470, 286), (560, 286), (540, 268), (490, 268)], (46, 52, 40))
    cv.fill_rect(500, 246, 6, 24, (60, 60, 60))
    cv.fill_rect(520, 252, 6, 18, (60, 60, 60))
    cv.circle(503, 242, 4, ORANGE)
    cv.circle(523, 248, 4, ORANGE)
    # warship, left, in the strait
    cv.poly([(60, 300), (330, 300), (310, 330), (84, 330)], (52, 58, 66))
    cv.fill_rect(120, 276, 130, 24, (52, 58, 66))
    cv.fill_rect(160, 258, 50, 18, (52, 58, 66))
    cv.fill_rect(176, 236, 8, 22, (52, 58, 66))
    cv.circle(260, 270, 10, (52, 58, 66))
    # smoke from the ship
    for cx, cy, r in ((290, 250, 10), (306, 238, 13), (324, 224, 16)):
        cv.circle(cx, cy, r, (200, 200, 200))
    # tanker, right, mine-hit: flame at the bow
    cv.poly([(620, 306), (950, 306), (930, 336), (640, 336)], (150, 48, 40))
    for tx in (680, 760, 840):
        cv.circle(tx, 296, 16, (226, 226, 226))
        cv.fill_rect(tx - 16, 296, 32, 10, (226, 226, 226))
    cv.fill_rect(906, 282, 26, 24, (150, 48, 40))
    for cx, cy, r in ((940, 292, 12), (952, 276, 16), (966, 258, 12)):
        cv.circle(cx, cy, r, ORANGE)
        cv.circle(cx, cy, max(2, r - 5), FLAME)
    for cx, cy, r in ((952, 250, 10), (968, 234, 13)):
        cv.circle(cx, cy, r, (60, 60, 60))
    # waves
    for wx in range(20, 1000, 90):
        cv.line(wx, 348, wx + 34, 348, (140, 180, 210), 2)
    # headline bar
    cv.fill_rect(x0, 356, x1 - x0, 84, INK)
    draw_centered(cv, 512, 364, "US-IRAN STRIKES", 6, WHITE)
    draw_centered(cv, 512, 412, "QESHM HIT \u2022 BAHRAIN DRONES \u2022 4TH TANKER MINED",
                  3, GOLD)
    cv.border(x0, y0, x1 - x0, y1 - y0, INK, 2)


# --- second row: Kerch Bridge + Nvidia --------------------------------------
def draw_kerch(cv):
    x0, y0, x1, y1 = 12, 452, 640, 700
    cv.fill_rect(x0, y0, x1 - x0, 108, (185, 203, 216))
    cv.fill_rect(x0, y0 + 108, x1 - x0, 76, SEA2)
    # bridge towers
    for tx in (150, 470):
        cv.fill_rect(tx, 478, 14, 62, INK)
        cv.fill_rect(tx - 8, 478, 30, 8, INK)
        cv.fill_rect(tx - 8, 500, 30, 6, INK)
    # deck, with a broken gap in the middle
    cv.fill_rect(28, 534, 250, 10, INK)
    cv.fill_rect(392, 534, 216, 10, INK)
    # cables from the towers to the deck
    cv.line(157, 486, 90, 534, INK, 2)
    cv.line(157, 486, 240, 534, INK, 2)
    cv.line(477, 486, 420, 534, INK, 2)
    cv.line(477, 486, 560, 534, INK, 2)
    # falling road section, a tilted slab dropping into the strait
    cv.poly([(286, 534), (398, 542), (392, 566), (290, 558)], (90, 90, 90))
    cv.poly([(292, 540), (392, 548), (388, 560), (294, 552)], RED)
    # splash where it hits the water
    for cx, cy, r in ((330, 606, 12), (352, 612, 16), (372, 604, 10)):
        cv.circle(cx, cy, r, WHITE)
    for wx in range(30, 620, 70):
        cv.line(wx, 626, wx + 28, 626, (190, 215, 230), 2)
    # headline bar
    cv.fill_rect(x0, 636, x1 - x0, 64, INK)
    draw_centered(cv, 326, 642, "KERCH BRIDGE HIT AGAIN", 4, WHITE)
    draw_centered(cv, 326, 676, "ROAD SPAN FALLS INTO STRAIT", 2, GOLD)
    cv.border(x0, y0, x1 - x0, y1 - y0, INK, 2)


def draw_nvidia(cv):
    x0, y0, x1, y1 = 652, 452, 1012, 700
    cv.fill_rect(x0, y0, x1 - x0, y1 - y0, DARK)
    draw_centered(cv, 832, 462, "NVIDIA RECORD Q3", 3, WHITE)
    # chip
    cv.fill_rect(762, 490, 140, 128, (24, 74, 52))
    cv.border(762, 490, 140, 128, GOLD, 3)
    cv.fill_rect(792, 520, 80, 68, (16, 52, 36))
    cv.border(792, 520, 80, 68, GOLD, 2)
    draw_centered(cv, 832, 540, "NVDA", 3, GOLD)
    for px in range(774, 896, 18):
        cv.fill_rect(px, 478, 8, 12, GOLD)
        cv.fill_rect(px, 618, 8, 12, GOLD)
    for py in range(502, 606, 18):
        cv.fill_rect(750, py, 12, 8, GOLD)
        cv.fill_rect(902, py, 12, 8, GOLD)
    # the number that matters
    draw_centered(cv, 832, 628, "$115B", 7, GOLD)
    draw_centered(cv, 832, 682, "CEO STAYS OUT", 2, (200, 220, 210))
    cv.border(x0, y0, x1 - x0, y1 - y0, INK, 2)


# --- third row: summit, Gaza aid, Depardieu ---------------------------------
def draw_flag_us(cv, x, y, w, h):
    stripe = max(2, h // 13)
    for i in range(13):
        cv.fill_rect(x, y + i * stripe, w, stripe,
                     RED if i % 2 == 0 else WHITE)
    cv.fill_rect(x, y, w * 2 // 5, stripe * 7, (30, 50, 110))
    for sx in range(2):
        for sy in range(3):
            cv.circle(x + 8 + sx * 22, y + 8 + sy * 10, 2, WHITE)


def draw_flag_cn(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (222, 32, 32))
    cv.circle(x + 16, y + 14, 8, GOLD)
    for sx, sy in ((44, 8), (52, 16), (52, 26), (44, 32)):
        cv.circle(x + sx, y + sy, 3, GOLD)


def draw_flag_ru(cv, x, y, w, h):
    third = h // 3
    cv.fill_rect(x, y, w, third, WHITE)
    cv.fill_rect(x, y + third, w, third, (30, 90, 180))
    cv.fill_rect(x, y + 2 * third, w, h - 2 * third, RED)


def draw_summit(cv):
    x0, y0, x1, y1 = 12, 712, 348, 1012
    cv.fill_rect(x0, y0, x1 - x0, y1 - y0, (239, 233, 216))
    draw_flag_us(cv, 28, 736, 84, 70)
    draw_flag_cn(cv, 126, 736, 84, 70)
    draw_flag_ru(cv, 224, 736, 84, 70)
    cv.fill_rect(28, 806, 280, 3, INK)
    draw_centered(cv, 180, 826, "TRUMP-XI-PUTIN", 3, INK)
    draw_centered(cv, 180, 862, "SUMMIT THU", 4, INK)
    draw_centered(cv, 180, 900, "SHENZHEN", 4, RED)
    draw_centered(cv, 180, 944, "19 NOV 2026", 3, INK)
    cv.border(x0, y0, x1 - x0, y1 - y0, INK, 2)


def draw_gaza(cv):
    x0, y0, x1, y1 = 358, 712, 668, 1012
    cv.fill_rect(x0, y0, x1 - x0, y1 - y0, SAND)
    # road
    cv.fill_rect(x0, 836, x1 - x0, 10, (120, 110, 96))
    # two aid trucks with red-cross boxes
    for tx in (386, 500):
        cv.fill_rect(tx, 768, 84, 68, WHITE)
        cv.border(tx, 768, 84, 68, INK, 2)
        cv.fill_rect(tx + 32, 780, 20, 8, RED)
        cv.fill_rect(tx + 38, 774, 8, 20, RED)
        cv.fill_rect(tx + 84, 792, 26, 44, (70, 110, 160))
        cv.fill_rect(tx + 92, 800, 14, 14, (180, 220, 240))
        for wx in (tx + 14, tx + 62, tx + 100):
            cv.circle(wx, 842, 10, INK)
            cv.circle(wx, 842, 4, GREY)
    # crossing gate, right
    cv.fill_rect(628, 736, 8, 100, INK)
    cv.line(636, 744, 668, 730, RED, 5)
    draw_centered(cv, 513, 862, "GAZA AID", 6, INK)
    draw_centered(cv, 513, 912, "OPEN THE", 3, INK)
    draw_centered(cv, 513, 938, "CROSSINGS", 3, RED)
    draw_centered(cv, 513, 972, "UK - AUS - CAN - ITA", 2, INK)
    cv.border(x0, y0, x1 - x0, y1 - y0, INK, 2)


def draw_depardieu(cv):
    x0, y0, x1, y1 = 678, 712, 1012, 1012
    cv.fill_rect(x0, y0, x1 - x0, y1 - y0, LIGHT)
    # court columns
    for cx in (716, 800, 884):
        cv.fill_rect(cx, 736, 18, 130, (150, 158, 166))
        cv.fill_rect(cx - 6, 736, 30, 10, (120, 128, 134))
        cv.fill_rect(cx - 6, 856, 30, 10, (120, 128, 134))
    cv.fill_rect(700, 866, 286, 12, (120, 128, 134))
    # bench and gavel
    cv.fill_rect(760, 884, 130, 14, (110, 76, 44))
    cv.fill_rect(800, 884, 16, 26, (110, 76, 44))
    cv.line(880, 900, 930, 872, (110, 76, 44), 5)
    cv.fill_rect(920, 856, 26, 16, (110, 76, 44))
    draw_centered(cv, 845, 926, "DEPARDIEU", 4, INK)
    draw_centered(cv, 845, 962, "PLEADS GUILTY", 4, RED)
    cv.border(x0, y0, x1 - x0, y1 - y0, INK, 2)


def main():
    cv = Canvas()
    draw_masthead(cv)
    draw_lead(cv)
    draw_kerch(cv)
    draw_nvidia(cv)
    draw_summit(cv)
    draw_gaza(cv)
    draw_depardieu(cv)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
