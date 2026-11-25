#!/usr/bin/env python3
"""map6.py — peta DIPOTONG + pin bernomor 19 px untuk V2 skill Lapis 1 v5.3.

Diadaptasi dari map4.py uji keempat (stdlib saja, TANPA PIL).
Perubahan REVISI CEPAT (06:0x WIB, komentar Kevin atas entry V2):
- Peta DIPOTONG ALA NI25: bujur -132..170, lintang -12..68, skala 1,0596
  px/derajat; peta 320x136 dengan daratan ~85 px dipusatkan vertikal
  (offset y +25,6). Pin ALA NI25: cincin putih r=10 + isi warna r=9 +
  nomor skala 1 (angka 7 px di dalam pin 18 px — tidak lagi memenuhi pin).
- Geseran + garis penuntun (jarak pusat minimum > 22 px): 5 (-14,+8),
  6 (+16,+10), 9 (-8,+8), 10 (+22,-18), 11 (-10,+20).
- Lencana kartu TIDAK lagi dirender di sini: lencana v5.3 adalah SATU CHIP
  ("N · LABEL") yang digambar compose5.py (drawbox+drawtext). GESEKAN:
  peta.md butir 7 ("bentuk pin sama dengan lencana") tidak bisa dipenuhi
  bersamaan dengan lencana satu chip — chip 77-127 px tidak bisa jadi pin
  19 px. Keputusan uji ini: pin tetap lingkaran bernomor; lencana chip.
  Butir 7 butuh revisi draf.

Data: skill v5.3 alat/peta-ne110m.json (Natural Earth 1:110m, domain publik).
Proyeksi equirectangular. Kanvas 320x136.

Jalankan: python3 map6.py -> aset/peta.png + laporan cek pin (darat/laut,
jarak antar-pusat pin sesudah geser).
"""

import itertools
import json
import math
import os
import struct
import sys
import zlib

BASE = "/home/hatch/workspace/makefun/news-image-20261124/V2/kerja-v2-skill-v5-3"
DATA = "/home/hatch/workspace/tmp/skill-lapis1-draf-v5-3/makefun-skills/alat/peta-ne110m.json"
OUT = os.path.join(BASE, "aset", "peta.png")

W, H = 320, 136
LON_MIN, LON_MAX = -132.0, 170.0
LAT_TOP, LAT_BOT = 68.0, -12.0
SCALE = W / (LON_MAX - LON_MIN)  # 1,0596 px/derajat (ala ni25)
MAP_H = (LAT_TOP - LAT_BOT) * SCALE  # ~84,8 px
Y_OFF = (H - MAP_H) / 2.0  # ~25,6 px — daratan dipusatkan vertikal

OCEAN = (0xB9, 0xCF, 0xE3)
LAND = (0xFB, 0xF8, 0xF0)
LAND_EDGE = (0x8C, 0x84, 0x74)
INK = (0x1C, 0x1A, 0x17)
WHITE = (0xFF, 0xFF, 0xFF)
RED = (0xC9, 0x2A, 0x2A)

REGION_COLORS = {
    "ME": (0xD9, 0x48, 0x0F),
    "Americas": (0x4F, 0x46, 0xE5),   # BARU (v4: #4263EB) — rona 243,4
    "APAC": (0x0E, 0x80, 0x74),      # BARU (v4: #0B7285) — rona 173,7
    "Europe": (0x19, 0x71, 0xC2),
    "Africa": (0x2B, 0x8A, 0x3E),
    "World": (0xA6, 0x1E, 0x7A),  # magenta, ganti abu-abu
}

# no, lon, lat, wilayah, nama, geser(dx, dy) dari titik sebenarnya
PINS = [
    (1, 46.67, 24.76, "ME", "Riyadh", 0, 0),
    (2, -74.01, 40.71, "Americas", "New York (Huawei)", 0, 0),
    (3, 121.47, 31.23, "APAC", "Shanghai", 0, 0),
    (4, 37.62, 55.75, "Europe", "Moscow", 0, 0),
    (5, 35.12, 47.85, "Europe", "Zaporizhzhia", -14, 8),
    (6, 56.25, 26.50, "ME", "Hormuz", 16, 10),
    (7, 2.35, 48.86, "Europe", "Paris", 0, 0),
    (8, -17.45, 14.69, "Africa", "Dakar", 0, 0),
    (9, 105.85, 21.03, "APAC", "Hanoi", -8, 8),
    (10, -74.01, 40.71, "Americas", "New York (Dow)", 22, -18),
    (11, 13.50, 33.50, "Europe", "lepas Libya", -10, 20),
]

GLYPHS = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}


def project(lon, lat):
    return (lon - LON_MIN) * SCALE, Y_OFF + (LAT_TOP - lat) * SCALE


def point_on_land(lon, lat, land_polys):
    inside = False
    for poly in land_polys:
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if (yi > lat) != (yj > lat):
                xinters = (xj - xi) * (lat - yi) / (yj - yi) + xi
                if lon < xinters:
                    inside = not inside
            j = i
    return inside


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * w * h)

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def hline(self, x0, x1, y, c):
        y = int(round(y))
        if not (0 <= y < self.h):
            return
        x0, x1 = sorted((int(round(x0)), int(round(x1))))
        for x in range(max(0, x0), min(self.w, x1 + 1)):
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def line(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def fill_poly(self, pts, c):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = max(0, int(math.floor(min(ys)))), min(self.h - 1, int(math.ceil(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > y + 0.5) != (yj > y + 0.5):
                    xs.append((xj - xi) * (y + 0.5 - yi) / (yj - yi) + xi)
                j = i
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(xs[k], xs[k + 1], y, c)

    def disc(self, cx, cy, r, c):
        r = float(r)
        for dy in range(-int(r), int(r) + 1):  # int, BUKAN ceil: ceil membuat 19x21 kapsul vertikal
            dx = int(math.sqrt(max(0.0, r * r - dy * dy)))
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def glyph_centered(self, text, cx, cy, c, scale=1):
        # Ala ni25: lebar tiap digit 6*scale (dua digit = 11 px pada skala 1).
        w = len(text) * 6 * scale - scale
        h = 7 * scale
        x = cx - w // 2
        y = cy - h // 2
        for ch in text:
            g = GLYPHS[ch]
            for row in range(7):
                for col in range(5):
                    if g[row][col] == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                self.set(x + col * scale + sx, y + row * scale + sy, c)
            x += 6 * scale


def write_png(path, canv):
    raw = b""
    for y in range(canv.h):
        raw += b"\x00" + bytes(canv.px[y * canv.w * 3:(y + 1) * canv.w * 3])

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canv.w, canv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    land_polys = [p["poligon"] for p in data["benua"]]

    cv = Canvas(W, H, OCEAN)
    for poly in land_polys:
        pts = [project(lon, lat) for lon, lat in poly]
        cv.fill_poly(pts, LAND)
    for poly in land_polys:
        pts = [project(lon, lat) for lon, lat in poly]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            cv.line(a[0], a[1], b[0], b[1], LAND_EDGE)

    print(f"peta potong ALA NI25: bujur {LON_MIN}..{LON_MAX}, lintang {LAT_BOT}..{LAT_TOP}, "
          f"skala {SCALE:.4f} px/derajat (dunia penuh 0,889) -> {SCALE/0.889:.2f}x")
    print("cek pin (nomor DI DALAM lingkaran r=9 + cincin putih r=10, angka skala 1):")
    centers = {}
    for no, lon, lat, wil, nama, gdx, gdy in PINS:
        on_land = point_on_land(lon, lat, land_polys)
        status = "DARAT" if on_land else "LAUT"
        expect = "laut (dimaksud)" if no in (6, 11) else "darat"
        flag = "" if (on_land == (no not in (6, 11))) else "  <-- PERIKSA"
        print(f"  pin {no:2d} {nama:22s} lon {lon:7.2f} lat {lat:6.2f} -> {status} (harap {expect}){flag}")
        x, y = project(lon, lat)
        dx, dy = x + gdx, y + gdy
        centers[no] = (dx, dy)
        if (gdx, gdy) != (0, 0):
            cv.line(x, y, dx, dy, INK)
        cv.disc(dx, dy, 10, WHITE)
        cv.disc(dx, dy, 9, REGION_COLORS[wil])
        cv.glyph_centered(str(no), dx, dy, WHITE, scale=1)

    print("cek jarak antar-pusat pin sesudah geser (harus > 20 px):")
    worst = None
    for a, b in itertools.combinations(sorted(centers), 2):
        (x1, y1), (x2, y2) = centers[a], centers[b]
        d = math.hypot(x2 - x1, y2 - y1)
        if worst is None or d < worst[0]:
            worst = (d, a, b)
        if d <= 20:
            print(f"  pin {a}-{b}: {d:.1f} px  <-- TUMPUK")
    print(f"  jarak terkecil: pin {worst[1]}-{worst[2]} = {worst[0]:.1f} px "
          f"({'LOLOS' if worst[0] > 20 else 'GAGAL'})")

    write_png(OUT, cv)
    print(f"peta ditulis: {OUT} ({W}x{H})")


if __name__ == "__main__":
    sys.exit(main())
