#!/usr/bin/env python3
"""Peta dunia dari data Natural Earth 1:110m (peta-ne110m.json, domain publik).

Stdlib saja — tanpa PIL. Garis pantai berasal dari data, bukan digambar tangan
(peta.md aturan 2). Keluaran PNG deterministik (tanpa timestamp).
"""
import json
import math
import struct
import sys
import zlib

W, H = 320, 190
OCEAN = (201, 214, 221)   # biru pucat
LAND = (232, 220, 192)    # pasir
BORDER = (120, 110, 85)   # garis pantai tipis (nanti via outline sederhana)

# pin: (nomor, lon, lat, warna RGB) — warna = warna wilayah di arah.md
PINS = [
    (1, 46.68, 24.71, (138, 90, 43)),    # Riyadh — Middle East
    (2, -74.01, 40.71, (107, 78, 138)),  # New York — Americas
    (3, 121.47, 31.23, (46, 122, 122)),  # Shanghai — Asia-Pacific
    (4, 37.62, 55.76, (46, 90, 136)),    # Moscow — Europe
    (5, 35.14, 47.85, (46, 90, 136)),    # Zaporizhzhia — Europe
    (6, 56.25, 26.57, (138, 90, 43)),    # Selat Hormuz (titik laut, disengaja) — Middle East
    (7, 2.35, 48.86, (90, 90, 90)),      # Paris — World
]
# UJI KEDUA: pin 8 (Dakar/Senegal) dan 9 (Hanoi) DIHAPUS — kedua cerita pindah ke
# daftar (bukan medium lagi); peta hanya memuat 7 cerita berilustrasi (1–7).


def proj(lon, lat):
    x = (lon + 180.0) / 360.0 * W
    y = (90.0 - lat) / 180.0 * H
    return x, y


def fill_polygon(px, poly):
    """Scanline fill untuk satu poligon (daftar titik piksel)."""
    pts = [proj(lon, lat) for lon, lat in poly]
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0, y1 = max(0, int(math.floor(min(ys)))), min(H - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, y1p = pts[i]
            x2, y2p = pts[(i + 1) % n]
            if (y1p <= yc < y2p) or (y2p <= yc < y1p):
                t = (yc - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa, xb = int(math.ceil(xs[i])), int(math.floor(xs[i + 1]))
            for x in range(max(0, xa), min(W - 1, xb) + 1):
                px[y][x] = LAND


def circle(px, cx, cy, r, color):
    for y in range(max(0, cy - r), min(H - 1, cy + r) + 1):
        for x in range(max(0, cx - r), min(W - 1, cx + r) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px[y][x] = color


def write_png(path, px):
    raw = b"".join(b"\x00" + b"".join(bytes(px[y][x]) for x in range(W)) for y in range(H))
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


def main():
    src = sys.argv[1]
    out = sys.argv[2]
    data = json.load(open(src))
    px = [[OCEAN for _ in range(W)] for _ in range(H)]
    for b in data["benua"]:
        fill_polygon(px, b["poligon"])
    pin_xy = {}
    for num, lon, lat, color in PINS:
        x, y = proj(lon, lat)
        cx, cy = int(round(x)), int(round(y))
        circle(px, cx, cy, 5, (255, 255, 255))  # cincin putih
        circle(px, cx, cy, 4, color)
        pin_xy[num] = (cx, cy)
    write_png(out, px)
    print("pin_xy:", pin_xy)


if __name__ == "__main__":
    main()
