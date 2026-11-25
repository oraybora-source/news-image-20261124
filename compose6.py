#!/usr/bin/env python3
"""compose6.py — komposisi entry V2 skill Lapis 1 v5.3 (jalur ASET, dari nol) (news-image-20261124).

Ditulis BARU untuk uji ini (diadaptasi dari compose4.py uji keempat).
Geometri + teks disalin dari layout.md / teks.md folder ini (dokumen kerja
uji kelima, ditulis dari skill v5.3 + alat ukur skill sendiri).

Jalur gambar: ASET (Muse image), TANPA PIL. Komposisi pakai ffmpeg
(overlay + drawtext + drawbox). Peta dari map5.py (stdlib, DIPOTONG +
pin 19 px).

Perubahan vs uji keempat (v5.3):
- Strip: keterangan DI KANAN angka (Sans Bold 10, sebaris) — bukan Sans 9
  di bawah angka. Keterangan dipersingkat supaya muat sebaris.
- Tab wilayah jadi PILL: teks putih di dalam blok warna wilayah, baris
  dipusatkan (x230-793), teks dan kotak berbagi pusat vertikal y163.
- Lencana SATU CHIP "N · LABEL" (teks di tengah chip, latar warna wilayah,
  digambar drawbox+drawtext DI DALAM gambar). Lingkaran bernomor DIBUANG
  dari kartu — tidak ada lagi badge-N.png.
- Palet wilayah baru: Americas #4F46E5 (rona 243,4), APAC #0E8074 (rona
  173,7) — selisih rona semua >= 30 derajat (lihat arah.md).
- Semua aset 1920x1280 LANSEKAP (termasuk Shanghai — prompt v5 membuang
  kata "Vertical composition" yang membuat aset v4 kembali potret), jadi
  TIDAK ADA lagi crop band khusus untuk Shanghai.

Aturan keras (pelajaran uji 1): SEMUA drawtext memakai expansion=none
(teks "Nvidia falls 6%..." pernah hilang diam-diam karena %).
Semua teks dilewatkan textfile (tanpa newline akhir) supaya karakter
khusus (—, ·, %, $, –) tidak perlu di-escape di filter.

Pemakaian:
  python3 compose6.py wireframe-A   -> wireframe-A.png (Layout A)
  python3 compose6.py wireframe-B   -> wireframe-B.png (Layout B: konvensi uji 4)
  python3 compose6.py entry         -> entry.png (dan entry-run2.png bila --twice)
  python3 compose6.py entry --twice -> entry.png + entry-run2.png (cek determinisme)
"""

import hashlib
import os
import subprocess
import sys

BASE = "/home/hatch/workspace/makefun/news-image-20261124/V2/kerja-v2-skill-v5-3"
ASET = os.path.join(BASE, "aset")
TEKS_DIR = os.path.join(BASE, "teks")

SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

BG = "0xF5EFE0"
INK = "0x1C1A17"
GRAY = "0x6E675C"
RED = "0xC92A2A"
ORANGE = "0xD9480F"   # ME
INDIGO = "0x4F46E5"   # Americas (BARU; v4: #4263EB)
TEAL = "0x0E8074"     # APAC (BARU; v4: #0B7285)
STEEL = "0x1971C2"    # Europe
GREEN = "0x2B8A3E"    # Africa
WORLD = "0xA61E7A"    # World (magenta, rona ~319; abu-abu DIBUANG: rona 210 cuma 17,9 dr Europe)
BOXGRAY = "0xD8D2C4"  # kotak wireframe
STRIP_BG = "0xEDE6D6"  # latar pita strip angka
TAB_BG = "0xE7DECB"    # latar pita tab wilayah (sedikit lebih gelap)
SEPLINE = "0xC9BFA9"   # garis pemisah antar pita (lama, tidak dipakai lagi)
SILVER = "0x8A8378"    # garis pemisah antar pita (ala ni25 — lebih tegas)
MUTED = "0x5A534B"     # teks sekunder (caption strip, 00/24 — ala ni25)

MASTHEAD = "Tuesday 24 November 2026"
HEADLINE = ("Houthi strike hits Riyadh tower again \u00b7 US jury finds Huawei guilty "
            "\u00b7 China probes Shanghai party chief")
DATECHECK = ("Left out as other days' news: COP31 ends without a deal "
             "(Sun 22 Nov) \u00b7 Nvidia reinstates Huang (Mon 23 Nov) \u00b7 CrowdStrike buys "
             "Zscaler (Mon 23 Nov).")
LIST_HEAD = "ALSO ON TUESDAY 24 NOVEMBER \u2014 25 MORE STORIES"
MAP_TITLE = "WHERE IT HAPPENED \u2014 PINS 1\u201311"
MAP_LEGEND = "Circles = stories 1\u201311 \u00b7 colour = region"

# --- Layout A: sepertiga atas v5.3 ---
# Strip dari cerita DAFTAR (14, 15, 18, 21, 31, 33) — keterangan DI KANAN
# angka. (angka, lebar angka terukur SANS_B 20, keterangan CAPS, lebar
# keterangan terukur SANS_R 9, warna angka). Caption CAPS + abu-abu ala ni25.
# REVISI CEPAT: strip dijustifikasi rata (celah antar-unit sama 38,1 px) —
# kolom tetap 162 px bikin celah 6,6 px (kol 3-4) sampai 48,4 px (kol 2-3).
NUMBERS_A = [
    ("175", 34.3, "MIGRANTS MISSING", 85.7, INK),
    ("1.5M", 47.4, "EBOLA DOSES", 59.2, INK),
    ("$125BN", 75.5, "UKRAINE NEEDS", 69.1, INK),
    ("103.3", 51.5, "US CONFIDENCE", 70.0, INK),
    ("6,929", 51.5, "LANDMINE VICTIMS", 84.5, INK),
    ("5,258", 51.5, "HEAT DEATHS", 57.4, INK),
]
# Tab pill: (teks, warna, x pill, lebar pill). Baris dipusatkan x230-793.
TABS = [
    ("EUROPE 11", STEEL, 230, 79),
    ("ASIA-PACIFIC 10", TEAL, 319, 107),
    ("AFRICA 5", GREEN, 436, 69),
    ("AMERICAS 6", INDIGO, 515, 86),
    ("MIDDLE EAST 3", ORANGE, 611, 102),
    ("WORLD 1", WORLD, 723, 70),
]
# Garis waktu visual: (label, x_dot, x_label, di_atas?)
TIMELINE = [
    ("09:53 UK heat deaths", 426, 376, True),
    ("10:17 Progress MS-36", 442, 391, False),
    ("14:00 Chess opens", 593, 549, True),
    ("16:37 Magyar\u2013Zelenskyy", 700, 642, False),
    ("19:08 Falcon 9", 800, 766, True),
    ("22:00 PRESS TIME", 918, 876, False),
]

# --- Layout B: konvensi uji keempat (pembanding) ---
KICKER_B = "THE WORLD ON ONE PAGE \u00b7 TUESDAY 24 NOVEMBER 2026"
NUMBERS_B = [
    ("11", "hurt in Riyadh tower strike", RED),
    ("10 of 12", "counts: Huawei guilty", INK),
    ("4TH", "Politburo member probed", INK),
    ("500,000", "Russian war dead, leaked count", INK),
    ("$41bn", "Sanofi buys Insmed", INK),
    ("50,000", "Dow closes above, first time", INK),
]
UTC_B = ("09:53 UK heat deaths \u00b7 10:17 Progress MS-36 lifts off \u00b7 14:00 Chess title "
         "match opens \u00b7 16:37 Magyar meets Zelenskyy \u00b7 19:08 Falcon 9 launches "
         "\u00b7 22:00 PRESS TIME")

# Kartu: no, file, x, chip ("N · LABEL", lebar chip = lebar teks terukur + 16),
# warna chip, judul (baris), dek (baris), tag. Label B = label uji keempat
# (dipakai hanya untuk wireframe-B).
LEADS = [
    dict(no=1, f="media-generation-lead1-riyadh-0-207c6d3b-e984-4529-89c7-a0e502c91889.webp",
         x=24, chip="1 \u00b7 11 HURT", cw=77, lc=RED, label="11 HURT",
         title=["Houthi strike hits Riyadh", "tower again; 11 hurt"],
         dek=["Drone hits the PIF Tower a second time in a week;",
              "Saudi civil defence counts 11 hurt."],
         tag="MIDDLE EAST \u00b7 WAR \u2014 CONFIRMED \u2014 Reuters"),
    dict(no=2, f="media-generation-lead2-huawei-0-3b8b710c-3e06-4ca3-af2c-02d4562028d7.webp",
         x=352, chip="2 \u00b7 GUILTY 10 OF 12", cw=120, lc=INDIGO, label="GUILTY 10 OF 12",
         title=["US jury finds Huawei guilty on", "10 of 12 counts"],
         dek=["Brooklyn jury convicts on bank fraud, sanctions and",
              "trade-secret theft; Huawei will appeal."],
         tag="AMERICAS \u00b7 COURTS \u2014 CONFIRMED \u2014 Reuters"),
    dict(no=3, f="media-generation-lead3-shanghai-0-f0e6a45b-53dc-4dcd-adeb-fc7dfc0381fb.webp",
         x=680, chip="3 \u00b7 4TH PROBED", cw=100, lc=TEAL, label="4TH PROBED",
         title=["China investigates its Shanghai", "party boss"],
         dek=["Chen Jining is the fourth Politburo member probed",
              "since 2025."],
         tag="ASIA-PACIFIC \u00b7 POLITICS \u2014 CONFIRMED \u2014 Xinhua"),
]
MEDIUMS = [
    dict(no=4, f="media-generation-medium4-rosstat-0-bf710ae8-732d-4978-a930-0a2072984a1b.webp",
         x=24, row=0, chip="4 \u00b7 500,000", cw=72, lc=STEEL, label="500,000",
         title=["Leaked count puts Russia's war dead", "near 500,000"],
         dek=["Hackers leak Rosstat records; Kremlin silent"],
         tag="EUROPE \u00b7 WAR \u2014 CONFIRMED"),
    dict(no=5, f="media-generation-medium5-zaporizhzhia-0-e1eb268d-7220-4206-8afd-362fe6d3b431.webp",
         x=270, row=0, chip="5 \u00b7 2 DEAD \u00b7 41 HURT", cw=125, lc=RED, label="2 DEAD \u00b7 41 HURT",
         title=["Russian strike kills 2 in Zaporizhzhia;", "41 hurt"],
         dek=["Two killed, 41 wounded overnight."],
         tag="EUROPE \u00b7 WAR \u2014 CONFIRMED"),
    dict(no=6, f="media-generation-medium6-hormuz-0-fc2b1816-aa17-49dd-97c0-18919b3878e3.webp",
         x=516, row=0, chip="6 \u00b7 4TH TANKER", cw=98, lc=ORANGE, label="4TH TANKER",
         title=["Iran says a 4th tanker hit a mine in", "Hormuz"],
         dek=["Iran's claim; two tankers afire, unverified."],
         tag="MIDDLE EAST \u00b7 SHIPPING \u2014 CLAIM"),
    dict(no=7, f="media-generation-medium7-sanofi-0-5f1c3290-b0a6-49f7-84d3-d8b2ac059c56.webp",
         x=762, row=0, chip="7 \u00b7 $41BN DEAL", cw=97, lc=WORLD, label="$41BN DEAL",
         title=["Sanofi buys Insmed for $41 billion"],
         dek=["$175 a share in cash; closing early 2027."],
         tag="WORLD \u00b7 MARKETS \u2014 CONFIRMED"),
    dict(no=8, f="media-generation-medium8-senegal-0-51b27481-8c5e-4818-93a3-a2a57d143f8f.webp",
         x=24, row=1, chip="8 \u00b7 TITLE BACK", cw=93, lc=GREEN, label="TITLE BACK",
         title=["Senegal gets its Africa Cup title back"],
         dek=["CAS restores the title; Senegal celebrates."],
         tag="AFRICA \u00b7 SPORT \u2014 CONFIRMED"),
    dict(no=9, f="media-generation-medium9-hanoi-0-bd096865-809d-4dfd-ac9d-c8db70c87130.webp",
         x=270, row=1, chip="9 \u00b7 6 KILLED", cw=79, lc=RED, label="6 KILLED",
         title=["Hotpot blast kills six in Hanoi"],
         dek=["Blast at a hotpot restaurant; six dead."],
         tag="ASIA-PACIFIC \u00b7 DISASTER \u2014 CONFIRMED"),
    dict(no=10, f="media-generation-medium10-dow-0-69d7c877-1b3e-4cca-bb68-c2d6e556dfb7.webp",
         x=516, row=1, chip="10 \u00b7 DOW 50,000", cw=102, lc=INDIGO, label="DOW 50,000",
         title=["Dow closes above 50,000 for the first", "time"],
         dek=["First close above 50,000 in history."],
         tag="AMERICAS \u00b7 MARKETS \u2014 CONFIRMED"),
    dict(no=11, f="media-generation-medium11-libya-0-fe2da829-3e0e-4c56-aee8-221a607e01a4.webp",
         x=762, row=1, chip="11 \u00b7 SUNK BY DRONE", cw=127, lc=STEEL, label="SUNK BY DRONE",
         title=["Ukraine defends sinking off Libya"],
         dek=["Kyiv says a drone sank a vessel off Libya."],
         tag="EUROPE \u00b7 WAR \u2014 CONFIRMED"),
]
LIST_TITLES = {
    12: "Putin vows payback for strikes on oil plants",
    13: "Israel kills senior Hamas security chief",
    14: "About 175 migrants missing off Senegal",
    15: "Gavi secures 1.5m Ebola doses for Congo",
    16: "Madagascar seeks ex-president's arrest",
    17: "Britain warns firms of Russian sabotage",
    18: "Zelenskyy says Ukraine needs $125bn for 2027",
    19: "Nvidia falls 6% after its historic rally",
    20: "US prepares new tariffs on China, 15 others",
    21: "US consumer confidence jumps to 103.3",
    22: "Three rockets launch in one day",
    23: "Pakistan's first astronaut joins Shenzhou 24",
    24: "Bird flu kills one in Washington outbreak",
    25: "Real Madrid thrash PSV 5\u20131 in Europe",
    26: "Sooryavanshi, 15, smashes 204 off 53 balls",
    27: "Seoul scrambles jets over Russian planes",
    28: "Garment workers clash in Bangladesh",
    29: "Hasina asks to fly home on 16 December",
    30: "Malaysia to send home 6,803 Myanmar migrants",
    31: "Landmine victims hit a five-year high: 6,929",
    32: "PNG votes on Bougainville independence",
    33: "Record 5,258 heat deaths in England",
    34: "Youngest chess title match opens with a draw",
    35: "Magyar meets Zelenskyy in Uzhhorod",
    36: "Gaza declares a meningitis epidemic alert",
}

# Lebar teks chip "N · LABEL" terukur dengan font ASLI (NotoSans-Bold 11,
# PIL ImageFont.getlength) — dipakai untuk memusatkan teks di dalam chip.
# cw di tiap kartu = lebar ini + 16 (padding 8+8). REVISI CEPAT: teks chip
# sebelumnya digambar di +2 px dari atas chip (tidak di tengah vertikal).
CHIP_TEXT_W = {1: 61.0, 2: 103.5, 3: 83.7, 4: 56.1, 5: 109.0, 6: 82.0,
               7: 81.3, 8: 76.5, 9: 62.6, 10: 86.4, 11: 111.3}


def textfile(name, text):
    """Tulis teks ke teks/<name>.txt TANPA newline akhir; kembalikan path."""
    os.makedirs(TEKS_DIR, exist_ok=True)
    p = os.path.join(TEKS_DIR, name + ".txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def dt(font, size, color, x, y, tf):
    return (f"drawtext=fontfile={font}:fontsize={size}:fontcolor={color}:"
            f"x={x}:y={y}:textfile='{tf}':expansion=none")


def box(color, x, y, w, h):
    return f"drawbox=color={color}:x={x}:y={y}:w={w}:h={h}:thickness=fill"


def build(mode, out_path):
    """mode: 'wireframe-A', 'wireframe-B', 'entry'."""
    wire = mode.startswith("wireframe")
    layout_a = (mode != "wireframe-B")

    # ---- input: latar + 11 gambar + peta ----
    inputs = ["-f", "lavfi", "-i", f"color=c={BG}:s=1024x1024"]
    img_index = {}
    n = 1
    for card in LEADS + MEDIUMS:
        inputs += ["-i", os.path.join(ASET, card["f"])]
        img_index[card["no"]] = n
        n += 1
    inputs += ["-i", os.path.join(ASET, "peta.png")]
    map_idx = n

    fc = []
    # ---- skala + crop gambar ke slot (hanya mode entry; wireframe tidak
    # memakai gambar sama sekali). Semua aset 1920x1280 lansekap. ----
    if not wire:
        for card in LEADS:
            i = img_index[card["no"]]
            fc.append(f"[{i}:v]scale=320:213,crop=320:142:0:35[im{card['no']}]")
        for card in MEDIUMS:
            i = img_index[card["no"]]
            fc.append(f"[{i}:v]scale=238:159,crop=238:99:0:30[im{card['no']}]")
        fc.append(f"[{map_idx}:v]null[map]")

    # ---- overlay gambar / kotak wireframe ----
    cur = "0:v"
    step = 0
    lead_y = 214 if layout_a else 240
    lead_h = 138 if layout_a else 120
    for card in LEADS:
        if wire:
            fc.append(f"[{cur}]drawbox=color={BOXGRAY}:x={card['x']}:y={lead_y}:w=320:h={lead_h}:thickness=fill[v{step}]")
        else:
            fc.append(f"[{cur}][im{card['no']}]overlay={card['x']}:{lead_y}[v{step}]")
        cur = f"v{step}"
        step += 1
    med_y = {0: 468, 1: 635} if layout_a else {0: 490, 1: 657}
    med_h = 95 if layout_a else 80
    for card in MEDIUMS:
        y = med_y[card["row"]]
        if wire:
            fc.append(f"[{cur}]drawbox=color={BOXGRAY}:x={card['x']}:y={y}:w=238:h={med_h}:thickness=fill[v{step}]")
        else:
            fc.append(f"[{cur}][im{card['no']}]overlay={card['x']}:{y}[v{step}]")
        cur = f"v{step}"
        step += 1
    map_y = 815 if layout_a else 819
    map_h = 136 if layout_a else 136
    if wire:
        fc.append(f"[{cur}]drawbox=color={BOXGRAY}:x=680:y={map_y}:w=320:h={map_h}:thickness=fill[v{step}]")
    else:
        fc.append(f"[{cur}][map]overlay=680:{map_y}[v{step}]")
    cur = f"v{step}"
    step += 1

    def apply(filt):
        nonlocal cur, step
        fc.append(f"[{cur}]{filt}[v{step}]")
        cur = f"v{step}"
        step += 1

    if layout_a:
        # ---- kepala A ----
        apply(dt(SERIF_B, 64, INK, 24, 8, textfile("masthead", MASTHEAD)))
        apply(box(INK, 24, 80, 976, 2))          # garis bawah masthead
        apply(dt(SERIF_I, 16, INK, 24, 90, textfile("headline", HEADLINE)))
        # ---- pita strip angka (y113-151): keterangan CAPS DI KANAN angka,
        # dijustifikasi rata (celah antar-unit sama) — ala ni25 ----
        apply(box(SILVER, 24, 112, 976, 1))
        apply(box(STRIP_BG, 24, 112, 976, 40))
        strip_gap = (976 - sum(nw + 8 + cw for _, nw, _, cw, _ in NUMBERS_A)) / 5
        strip_x = 24.0
        for i, (num, nw, lab, cw, col) in enumerate(NUMBERS_A):
            x = int(round(strip_x))
            apply(dt(SANS_B, 20, col, x, 118, textfile(f"num{i+1}", num)))
            apply(dt(SANS_R, 9, MUTED, x + int(round(nw)) + 8, 124,
                     textfile(f"numlab{i+1}", lab)))
            strip_x += nw + 8 + cw + strip_gap
        # ---- pita tab wilayah (y153-173): PILL, baris dipusatkan ----
        apply(box(TAB_BG, 24, 152, 976, 22))
        apply(box(SILVER, 24, 152, 976, 1))
        for i, (tab, col, px, pw) in enumerate(TABS):
            apply(box(col, px, 153, pw, 20))
            apply(dt(SANS_B, 11, "0xFFFFFF", px + 10, 158, textfile(f"tab{i+1}", tab)))
        # ---- garis waktu visual (y175-205): tick MERAH 7x7, sumbu 2 px,
        # "00"/"24" DI BAWAH sumbu — ala ni25 ----
        apply(box(SILVER, 24, 174, 976, 1))
        apply(box(INK, 24, 192, 976, 2))         # sumbu 00-24
        apply(dt(SANS_B, 10, MUTED, 24, 195, textfile("tl00", "00")))
        apply(dt(SANS_B, 10, MUTED, 984, 195, textfile("tl24", "24")))
        for j, (lab, dx, lx, above) in enumerate(TIMELINE):
            apply(box(RED, dx - 3, 189, 7, 7))
            y = 178 if above else 197
            apply(dt(SANS_R, 10, INK, lx, y, textfile(f"tl{j}", lab)))
        # ---- chip lencana SATU BENTUK di dalam gambar: teks DIPUSATKAN
        # horizontal (dari lebar terukur) + vertikal (rumus ni25:
        # chip_y + (chip_h-11)//2) — sebelumnya teks di +2 px dari atas chip.
        for card in LEADS:
            x = card["x"]
            chip_x, chip_y, chip_w, chip_h = x + 6, lead_y + 6, card["cw"], 22
            tx = chip_x + int(round((chip_w - CHIP_TEXT_W[card["no"]]) / 2))
            ty = chip_y + max(2, (chip_h - 11) // 2)
            apply(box(card["lc"], chip_x, chip_y, chip_w, chip_h))
            apply(dt(SANS_B, 11, "0xFFFFFF", tx, ty,
                     textfile(f"badge{card['no']}", card["chip"])))
        for card in MEDIUMS:
            x = card["x"]
            y = med_y[card["row"]]
            chip_x, chip_y, chip_w, chip_h = x + 5, y + 5, card["cw"], 20
            tx = chip_x + int(round((chip_w - CHIP_TEXT_W[card["no"]]) / 2))
            ty = chip_y + max(2, (chip_h - 11) // 2)
            apply(box(card["lc"], chip_x, chip_y, chip_w, chip_h))
            apply(dt(SANS_B, 11, "0xFFFFFF", tx, ty,
                     textfile(f"badge{card['no']}", card["chip"])))
    else:
        # ---- kepala B (konvensi uji keempat) ----
        apply(dt(SANS_B, 11, INK, 24, 8, textfile("kicker", KICKER_B)))
        apply(dt(SERIF_B, 64, INK, 24, 24, textfile("masthead", MASTHEAD)))
        apply(box(INK, 24, 96, 976, 2))
        apply(dt(SERIF_I, 16, INK, 24, 104, textfile("headline", HEADLINE)))
        for i, (num, lab, col) in enumerate(NUMBERS_B):
            x = 24 + i * 162
            apply(dt(SANS_B, 20, col, x, 128, textfile(f"num{i+1}", num)))
            apply(dt(SANS_R, 9, GRAY, x, 152, textfile(f"numlab{i+1}", lab)))
        for i, (tab, col, px, pw) in enumerate(TABS):
            x = 24 + i * 162
            apply(box(col, x, 171, 10, 10))
            apply(dt(SANS_B, 11, INK, x + 14, 168, textfile(f"tab{i+1}", tab)))
        apply(dt(SANS_R, 10, GRAY, 24, 190, textfile("utc", UTC_B)))
        # ---- label DI ATAS gambar + kotak nomor merah (konvensi uji 4) ----
        for card in LEADS:
            x = card["x"]
            apply(dt(SANS_B, 11, card["lc"], x, 218, textfile(f"label{card['no']}", card["label"])))
            apply(box(RED, x, 240, 24, 24))
            apply(dt(SANS_B, 13, "0xFFFFFF", x + 8, 243, textfile(f"badge{card['no']}", str(card["no"]))))
        for card in MEDIUMS:
            x = card["x"]
            y0 = 472 if card["row"] == 0 else 639
            apply(dt(SANS_B, 11, card["lc"], x, y0, textfile(f"label{card['no']}", card["label"])))
            apply(box(RED, x, y0 + 18, 18, 18))
            apply(dt(SANS_B, 10, "0xFFFFFF", x + 6 if card["no"] < 10 else x + 2, y0 + 20,
                     textfile(f"badge{card['no']}", str(card["no"]))))

    # ---- lead: judul/dek/tag ----
    for card in LEADS:
        x = card["x"]
        if layout_a:
            ty, dy, gy = 358, 406, 436
        else:
            ty, dy, gy = 366, 418, 452
        for j, line in enumerate(card["title"]):
            apply(dt(SERIF_B, 19, INK, x, ty + j * 24, textfile(f"lt{card['no']}_{j}", line)))
        for j, line in enumerate(card["dek"]):
            apply(dt(SANS_R, 12, INK, x, dy + j * 15, textfile(f"ld{card['no']}_{j}", line)))
        apply(dt(SANS_B, 10, RED, x, gy, textfile(f"ltag{card['no']}", card["tag"])))

    # ---- medium: judul/dek/tag ----
    for card in MEDIUMS:
        x = card["x"]
        if layout_a:
            y0 = 468 if card["row"] == 0 else 635
            ty, dy, gy = y0 + 101, y0 + 134, y0 + 148
        else:
            y0 = 472 if card["row"] == 0 else 639
            ty, dy, gy = y0 + 104, y0 + 137, y0 + 151
        for j, line in enumerate(card["title"]):
            apply(dt(SANS_B, 12, INK, x, ty + j * 15, textfile(f"mt{card['no']}_{j}", line)))
        apply(dt(SANS_R, 11, INK, x, dy, textfile(f"md{card['no']}", card["dek"][0])))
        apply(dt(SANS_B, 8, RED, x, gy, textfile(f"mtag{card['no']}", card["tag"])))

    # ---- daftar ----
    lh = 802 if layout_a else 806
    ly = 815 if layout_a else 819
    apply(dt(SANS_B, 11, INK, 24, lh, textfile("listhead", LIST_HEAD)))
    for x0, nums in ((24, range(12, 25)), (352, range(25, 37))):
        for j, no in enumerate(nums):
            y = ly + j * 13
            apply(dt(SANS_B, 11, INK, x0, y, textfile(f"ln{no}", str(no))))
            apply(dt(SANS_R, 11, INK, x0 + 24, y, textfile(f"lt{no}", LIST_TITLES[no])))

    # ---- peta ----
    mh = 802 if layout_a else 806
    mly = 956 if layout_a else 960
    apply(dt(SANS_B, 11, INK, 680, mh, textfile("maptitle", MAP_TITLE)))
    apply(dt(SANS_R, 9, GRAY, 680, mly, textfile("maplegend", MAP_LEGEND)))

    # ---- DATE CHECK (kotak aksen + teks) ----
    if layout_a:
        apply(box(RED, 24, 988, 74, 14))
        apply(dt(SANS_B, 10, "0xFFFFFF", 31, 990, textfile("dcbox", "DATE CHECK")))
        apply(dt(SANS_R, 10, GRAY, 106, 990, textfile("datecheck", DATECHECK)))
    else:
        apply(box(INK, 24, 989, 976, 2))
        apply(dt(SANS_R, 10, GRAY, 24, 992, textfile("datecheck", DATECHECK)))

    filt = ";".join(fc)
    cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + [
        "-filter_complex", filt, "-map", f"[{cur}]", "-frames:v", "1", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg GAGAL:", r.stderr[-3000:], file=sys.stderr)
        sys.exit(1)
    print(f"{mode} -> {out_path}")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("entry",):
        print("pakai: compose6.py {wireframe-A|wireframe-B|entry} [--twice]", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]
    twice = "--twice" in sys.argv
    out = {"entry": "entry.png"}[mode]
    build(mode, os.path.join(BASE, out))
    if twice and mode == "entry":
        build(mode, os.path.join(BASE, "entry-run2.png"))
        s1, s2 = sha(os.path.join(BASE, "entry.png")), sha(os.path.join(BASE, "entry-run2.png"))
        print(f"entry.png sha256: {s1}")
        print(f"entry-run2.png sha256: {s2}")
        print("DETERMINISTIK:", "YA (byte-identik)" if s1 == s2 else "TIDAK — SELISIH!")


if __name__ == "__main__":
    main()
