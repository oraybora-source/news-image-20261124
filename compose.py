#!/usr/bin/env python3
"""Komposisi entry ni24 — UJI KEDUA skill Lapis 1. Stdlib saja, TANPA PIL.

Render: ffmpeg (color source + overlay + drawbox + drawtext).
Semua teks sudah diukur/di-wrap sebelumnya dengan ukur.py (fontTools, tanpa PIL);
skrip ini hanya menempatkan baris yang sudah jadi.

PERBAIKAN UJI KEDUA vs compose.py uji pertama:
1. expansion=none di SETIAP filter drawtext — bug uji pertama: "%" di
   "Nvidia falls 6% after its historic rally" ditelan expansion default
   (ffmpeg log "Stray %", build tetap sukses diam-diam, baris 19 kosong).
2. CEK KELENGKAPAN TEKS: sebelum render, periksa semua 29 judul daftar + semua
   judul/dek lead & medium ada di daftar teks (harus 29/29 daftar).
3. Medium: 1 baris x 4, gambar di atas + teks di bawah (arahan Kevin).
4. Daftar 29 cerita (8-36); pin peta 7 (1-7).

Pakai:
  python3 compose.py --layout A --out entry.png [--wireframe]
  python3 compose.py --layout A --out entry.png --run2 entry2.png  (uji determinisme)
"""
import argparse
import hashlib
import os
import subprocess
import sys

BASE = "/home/hatch/workspace/makefun/news-image-20261124/V1/kerja-uji-skill-lapis1-v2"
SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF_IT = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

INK = "0x1A2332"
RED = "0xB3271E"
CREAM = "F7F2E7"
GRAY = "0x6B6B6B"
LIGHT = "0xD8D2C4"
BLUE_EU = "0x2E5A88"
BROWN_ME = "0x8A5A2B"
GREEN_AF = "0x3E7A4E"
TEAL_AP = "0x2E7A7A"
PURPLE_AM = "0x6B4E8A"
GRAY_W = "0x5A5A5A"

ASSET = f"{BASE}/aset"
# Nama file aset diisi tahap 5 (media.generate_image); placeholder di bawah
# diganti dengan nama file sebenarnya sebelum render final.
LEAD1 = f"{ASSET}/lead1-riyadh.webp"
LEAD2 = f"{ASSET}/lead2-huawei.webp"
LEAD3 = f"{ASSET}/lead3-shanghai.webp"
MED4 = f"{ASSET}/medium4-rosstat.webp"
MED5 = f"{ASSET}/medium5-zaporizhzhia.webp"
MED6 = f"{ASSET}/medium6-hormuz.webp"
MED7 = f"{ASSET}/medium7-sanofi.webp"
MAP = f"{ASSET}/peta.png"


def esc(s):
    return (s.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
             .replace("%", "\\%").replace(",", "\\,"))


class Spec:
    def __init__(self):
        self.images = []   # (path, x, y, w, h)
        self.boxes = []    # (x, y, w, h, color)
        self.texts = []    # (text, font, size, color, x, y, boxcolor or None)

    def img(self, path, x, y, w, h):
        self.images.append((path, x, y, w, h))

    def box(self, x, y, w, h, color):
        self.boxes.append((x, y, w, h, color))

    def txt(self, text, font, size, color, x, y, boxcolor=None):
        self.texts.append((text, font, size, color, x, y, boxcolor))


def top_blocks(s):
    """Blok atas yang sama di A dan B: kicker, masthead, headline, angka, tab, UTC."""
    s.txt("THE WORLD ON ONE PAGE  ·  TUESDAY 24 NOVEMBER 2026", SANS_B, 11, INK, 24, 8)
    s.box(24, 30, 976, 1, INK)
    s.txt("Tuesday 24 November 2026", SERIF, 71, INK, 24, 32)
    s.txt("Houthi strike hits Riyadh tower again  ·  US jury finds Huawei guilty  ·  China probes Shanghai party chief",
          SERIF_IT, 16, INK, 24, 126)
    # strip angka: 6 sel
    nums = [("11", "hurt in Riyadh tower strike", RED),
            ("10 of 12", "counts: Huawei guilty", INK),
            ("4TH", "Politburo member probed", INK),
            ("500,000", "Russian war dead, leaked count", INK),
            ("$41bn", "Sanofi buys Insmed", INK),
            ("50,000", "Dow closes above, first time", INK)]
    for i, (n, lab, col) in enumerate(nums):
        x = 24 + i * 163
        if i:
            s.box(x - 1, 152, 1, 40, LIGHT)
        s.txt(n, SANS_B, 20, col, x, 152)
        s.txt(lab, SANS, 9, GRAY, x, 178)
    # tab wilayah
    tabs = [("EUROPE", "11", BLUE_EU), (("ASIA-PACIFIC", "10", TEAL_AP)),
            ("AFRICA", "5", GREEN_AF), ("AMERICAS", "6", PURPLE_AM),
            ("MIDDLE EAST", "3", BROWN_ME), ("WORLD", "1", GRAY_W)]
    for i, (name, cnt, col) in enumerate(tabs):
        x = 24 + i * 163
        s.box(x, 200, 8, 8, col)
        s.txt(f"{name} {cnt}", SANS_B, 11, INK, x + 14, 198)
    # strip UTC
    s.txt("09:53  UK heat deaths   ·   10:17  Progress MS-36 lifts off   ·   14:00  Chess title match opens   ·   16:37  Magyar meets Zelenskyy   ·   19:08  Falcon 9 launches   ·   22:00  PRESS TIME",
          SANS, 10, GRAY, 24, 224)


LEADS = [
    (LEAD1, "1", ["Houthi strike hits Riyadh", "tower again; 11 hurt"],
     ["Drone hits the PIF Tower a second time in a week; Saudi", "civil defence counts 11 hurt."],
     "MIDDLE EAST · WAR — CONFIRMED", RED),
    (LEAD2, "2", ["US jury finds Huawei guilty", "on 10 of 12 counts"],
     ["Brooklyn jury convicts on bank fraud, sanctions and", "trade-secret theft; Huawei will appeal."],
     "AMERICAS · COURTS — CONFIRMED", INK),
    (LEAD3, "3", ["China investigates its Shanghai", "party boss"],
     ["Chen Jining is the fourth Politburo member", "probed since 2025. — Reuters"],
     "ASIA-PACIFIC · POLITICS — CONFIRMED", INK),
]

MEDIUM = [
    (MED4, "4", ["Leaked count puts Russia's war dead", "near 500,000"],
     ["Hackers leak Rosstat death records; the", "Kremlin stays silent."],
     "EUROPE · WAR — CONFIRMED"),
    (MED5, "5", ["Russian strike kills 2 in", "Zaporizhzhia; 41 hurt"],
     ["Two killed and 41 wounded overnight in", "Zaporizhzhia."],
     "EUROPE · WAR — CONFIRMED"),
    (MED6, "6", ["Iran says a 4th tanker hit a mine in", "Hormuz"],
     ["Iran's claim; two tankers caught fire,", "unverified."],
     "MIDDLE EAST · SHIPPING — CLAIM"),
    (MED7, "7", ["Sanofi buys Insmed for $41 billion"],
     ["$175 a share in cash; set to close in early", "2027."],
     "WORLD · MARKETS — CONFIRMED"),
]

LIST_ITEMS = [
    (8, "Senegal gets its Africa Cup title back"),
    (9, "Hotpot blast kills six in Hanoi"),
    (10, "Ukraine defends sinking off Libya"),
    (11, "Putin vows payback for strikes on oil plants"),
    (12, "Israel kills senior Hamas security chief"),
    (13, "About 175 migrants missing off Senegal"),
    (14, "Gavi secures 1.5m Ebola doses for Congo"),
    (15, "Madagascar seeks ex-president's arrest"),
    (16, "Britain warns firms of Russian sabotage"),
    (17, "Zelenskyy says Ukraine needs $125bn for 2027"),
    (18, "Dow closes above 50,000 for the first time"),
    (19, "Nvidia falls 6% after its historic rally"),
    (20, "US prepares new tariffs on China, 15 others"),
    (21, "US consumer confidence jumps to 103.3"),
    (22, "Three rockets launch in one day"),
    (23, "Pakistan's first astronaut joins Shenzhou 24"),
    (24, "Bird flu kills one in Washington outbreak"),
    (25, "Real Madrid thrash PSV 5–1 in Europe"),
    (26, "Sooryavanshi, 15, smashes 204 off 53 balls"),
    (27, "Seoul scrambles jets over Russian planes"),
    (28, "Garment workers clash in Bangladesh"),
    (29, "Hasina asks to fly home on 16 December"),
    (30, "Malaysia to send home 6,803 Myanmar migrants"),
    (31, "Landmine victims hit a five-year high: 6,929"),
    (32, "PNG votes on Bougainville independence"),
    (33, "Record 5,258 heat deaths in England"),
    (34, "Youngest chess title match opens with a draw"),
    (35, "Magyar meets Zelenskyy in Uzhhorod"),
    (36, "Gaza declares a meningitis epidemic alert"),
]

# label pin peta: (nomor, dot_x, dot_y, label_x, label_y, side) — koordinat lokal peta 320x190
PIN_LABELS = [
    (1, 201, 69, 196, 47, "above"),
    (2, 94, 52, 89, 30, "above"),
    (3, 268, 62, 263, 40, "above"),
    (4, 193, 36, 188, 14, "above"),
    (5, 191, 44, 184, 60, "below"),
    (6, 210, 67, 203, 79, "below"),
    (7, 162, 43, 155, 21, "above"),
]


def leads_block(s, wireframe):
    # lead y240-494: gambar 320x150, judul y396/420, dek y448/463, tag y482
    for i, (img, num, title, dek, tag, tagcol) in enumerate(LEADS):
        x = 24 + i * 328
        if wireframe:
            s.box(x, 240, 320, 150, "0xC9C2B2")
            s.txt(f"[GAMBAR LEAD {num}]", SANS_B, 12, GRAY, x + 100, 308)
        else:
            s.img(img, x, 240, 320, 150)
        s.box(x, 240, 24, 24, RED)
        s.txt(num, SANS_B, 14, "0xFFFFFF", x + 8, 242)
        s.txt(title[0], SERIF, 19, INK, x, 396)
        s.txt(title[1], SERIF, 19, INK, x, 420)
        s.txt(dek[0], SANS, 12, INK, x, 448)
        s.txt(dek[1], SANS, 12, INK, x, 463)
        s.txt(tag, SANS_B, 9, tagcol, x, 482)


def list_and_map(s, wireframe):
    # daftar + peta y720-965; header y720, daftar y744 pitch 15, peta y744 320x190
    s.txt("ALSO ON TUESDAY 24 NOVEMBER — 29 MORE STORIES", SANS_B, 12, INK, 24, 720)
    s.txt("WHERE IT HAPPENED — PINS 1–7", SANS_B, 12, INK, 664, 720)
    for j, (num, title) in enumerate(LIST_ITEMS):
        col = 0 if j < 15 else 1
        row = j if j < 15 else j - 15
        x = 24 + col * 320
        y = 744 + row * 15
        s.txt(str(num), SANS_B, 11, RED, x, y)
        s.txt(title, SANS, 11, INK, x + 26, y)
    if wireframe:
        s.box(664, 744, 320, 190, "0xC9C2B2")
        s.txt("[PETA]", SANS_B, 12, GRAY, x=664 + 130, y=830)
    else:
        s.img(MAP, 664, 744, 320, 190)
    for num, dx, dy, lx, ly, side in PIN_LABELS:
        ax, ay = 664 + dx, 744 + dy
        bx, by = 664 + lx, 744 + ly
        if side == "above":
            s.box(ax, by + 10, 1, ay - (by + 10) - 4, INK)
        else:
            s.box(ax, ay + 5, 1, by - (ay + 5), INK)
        s.txt(str(num), SANS_B, 10, INK, bx + 2, by, boxcolor="0xFFFFFF")
    s.txt("Dots = stories 1–7 · colour = region", SANS, 9, GRAY, 664, 940)
    # date check
    s.box(24, 980, 976, 1, INK)
    s.txt("DATE CHECK — Left out as other days' news: COP31 ends without a deal (Sun 22 Nov) · Nvidia reinstates Huang (Mon 23 Nov) · CrowdStrike buys Zscaler (Mon 23 Nov).",
          SANS, 10, GRAY, 24, 988)


def layout_a(s, wireframe):
    top_blocks(s)
    leads_block(s, wireframe)
    # medium y502-708: 1 baris x 4, kartu 238 lebar, gambar 238x120 di atas
    for c, (img, num, title, dek, tag) in enumerate(MEDIUM):
        x = 24 + c * 246
        if wireframe:
            s.box(x, 502, 238, 120, "0xC9C2B2")
            s.txt(f"[GAMBAR {num}]", SANS_B, 11, GRAY, x + 80, 556)
        else:
            s.img(img, x, 502, 238, 120)
        s.box(x, 502, 20, 20, RED)
        s.txt(num, SANS_B, 11, "0xFFFFFF", x + 6, 503)
        for k, line in enumerate(title):
            s.txt(line, SANS_B, 12, INK, x, 628 + k * 15)
        for k, line in enumerate(dek):
            s.txt(line, SANS, 11, INK, x, 664 + k * 14)
        s.txt(tag, SANS_B, 8, GRAY, x, 696)
    list_and_map(s, wireframe)


def layout_b(s, wireframe):
    """Alternatif (ditolak): medium gambar kiri 110x110 + teks kanan 120 px."""
    top_blocks(s)
    leads_block(s, wireframe)
    for c, (img, num, title, dek, tag) in enumerate(MEDIUM):
        x = 24 + c * 246
        if wireframe:
            s.box(x, 502, 110, 110, "0xC9C2B2")
            s.txt(f"[{num}]", SANS_B, 11, GRAY, x + 44, 550)
        else:
            s.img(img, x, 502, 110, 110)
        tx = x + 118
        s.txt(" ".join(title), SANS_B, 12, INK, tx, 508)
        s.txt(dek[0], SANS, 11, INK, tx, 540)
        s.txt(dek[1], SANS, 11, INK, tx, 554)
        s.txt(tag, SANS_B, 8, GRAY, tx, 572)
    list_and_map(s, wireframe)


def check_text_completeness(s):
    """CEK KELENGKAPAN TEKS (perbaikan uji kedua): semua judul daftar (29) +
    semua judul/dek lead & medium harus ada di s.texts. Mengembalikan (ok, rincian)."""
    rendered = [t[0] for t in s.texts]
    # Pencocokan substring: layout B menggabung baris judul medium jadi satu
    # baris (" ".join), jadi baris individual hanya muncul sebagai substring.
    def present(line):
        return any(line in t for t in rendered)
    missing = []
    found_list = 0
    for num, title in LIST_ITEMS:
        if present(title):
            found_list += 1
        else:
            missing.append(f"daftar {num}: {title!r}")
    found_other = 0
    total_other = 0
    for _, _, title, dek, _, _ in LEADS:
        for line in title + dek:
            total_other += 1
            if present(line):
                found_other += 1
            else:
                missing.append(f"lead: {line!r}")
    for _, _, title, dek, _ in MEDIUM:
        for line in title + dek:
            total_other += 1
            if present(line):
                found_other += 1
            else:
                missing.append(f"medium: {line!r}")
    # khusus: baris yang mengandung '%' harus ter-render (bug uji pertama)
    pct = [t for _, t in LIST_ITEMS if "%" in t]
    pct_ok = all(present(t) for t in pct)
    print(f"CEK KELENGKAPAN TEKS: daftar {found_list}/29, lead+medium {found_other}/{total_other}, "
          f"baris-% ter-render: {pct_ok} ({pct})")
    if missing:
        print("HILANG:", *missing, sep="\n  - ")
    return found_list == 29 and found_other == total_other and pct_ok, missing


def build_filter(s, wireframe):
    parts = []
    inputs = []
    txtdir = f"{BASE}/texts"
    os.makedirs(txtdir, exist_ok=True)
    filt = [f"color=c={CREAM}:s=1024x1024:d=1[base]"]
    last = "base"
    # gambar
    for i, (path, x, y, w, h) in enumerate(s.images):
        inputs.append(["-i", path])
        filt.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[im{i}]")
        filt.append(f"[{last}][im{i}]overlay={x}:{y}[o{i}]")
        last = f"o{i}"
    # kotak
    for j, (x, y, w, h, color) in enumerate(s.boxes):
        filt.append(f"[{last}]drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t=fill[b{j}]")
        last = f"b{j}"
    # teks — expansion=none di SETIAP drawtext (perbaikan bug "%" uji pertama)
    for k, (text, font, size, color, x, y, boxcolor) in enumerate(s.texts):
        tf = f"{txtdir}/t{k:03d}.txt"
        open(tf, "w").write(text)
        dt = (f"drawtext=fontfile={font}:textfile='{tf}':fontsize={size}:"
              f"fontcolor={color}:x={x}:y={y}:expansion=none")
        if boxcolor:
            dt += f":box=1:boxcolor={boxcolor}:boxborderw=3"
        filt.append(f"[{last}]{dt}[t{k}]")
        last = f"t{k}"
    return inputs, ";".join(filt), last


def run(out_path, layout, wireframe):
    s = Spec()
    (layout_a if layout == "A" else layout_b)(s, wireframe)
    ok, missing = check_text_completeness(s)
    if not ok:
        raise SystemExit(f"CEK KELENGKAPAN TEKS GAGAL: {missing}")
    if not wireframe:
        for path, _, _, _, _ in s.images:
            if not os.path.exists(path):
                raise SystemExit(f"aset hilang: {path}")
    inputs, filt, last = build_filter(s, wireframe)
    cmd = ["ffmpeg", "-y", "-v", "error"] + sum(inputs, []) + [
        "-filter_complex", filt, "-map", f"[{last}]", "-frames:v", "1", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"ffmpeg gagal (rc={r.returncode})")
    return out_path


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", choices=["A", "B"], default="A")
    ap.add_argument("--out", required=True)
    ap.add_argument("--wireframe", action="store_true")
    ap.add_argument("--run2", default=None, help="jalankan kedua kalinya ke path ini lalu bandingkan sha")
    args = ap.parse_args()
    run(args.out, args.layout, args.wireframe)
    print("wrote", args.out, sha(args.out))
    if args.run2:
        run(args.run2, args.layout, args.wireframe)
        s1, s2 = sha(args.out), sha(args.run2)
        print("run2", args.run2, s2)
        print("DETERMINISTIK:", "YA" if s1 == s2 else "TIDAK — sha berbeda!")
