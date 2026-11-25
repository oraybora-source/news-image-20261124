#!/usr/bin/env python3
"""news-image-20261124 — V1 entry renderer, REVISI ILUSTRASI (pack v26.1).

Revision of the V1 renderer (sha 91c51422): lead cards 1-3 use detailed
informative maps / a rich scene; medium cards 4-9 use a narrow tall
illustration beside a larger report text (Kevin 25 Nov 13:49 WIB).
Everything else (36 stories, layout, strips, map, list, DATE CHECK,
all verified text and numbers) is unchanged from V1.

Draws one 1024x1024 PNG summing up world news of Tuesday 24 November
2026: 36 verified stories (3 leads + 6 medium + 27 listed), a numbers
band, a region bar, a UTC strip, a world map with 13 numbered pins, a
caption, a DATE CHECK box and a sources footer.

Deterministic: no network, no clock, no randomness. The program writes
entry.png (default /output/entry.png) and manifest-verifikasi-V1.json
(default: same folder as this file's working directory). Running it twice
produces byte-identical output.

Data: all 36 stories verified against primary sources dated 24 Nov 2026
(see STORIES.md in the notes folder). Map coastlines come from
data/daratan.json (a copy of the pack's reference/daratan.json).
"""
import hashlib
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN_X = 16
CONTENT_W = 992

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 233)      # warm cream page
CARD = (255, 253, 247)       # card background
CARD_LINE = (216, 207, 192)  # card border
NAVY = (27, 58, 92)          # numbers band, date check, pins, date
NAVY_LIGHT = (46, 84, 124)   # band cell dividers
INK = (26, 26, 26)           # main text
MUTED = (107, 101, 90)       # secondary text
SEA = (217, 230, 240)        # map sea
LAND = (239, 230, 210)       # map land
LAND_LINE = (201, 184, 138)  # map coastline
WHITE = (255, 255, 255)
STATUS = {
    "CONFIRMED": (46, 125, 50),
    "REPORTED": (183, 121, 31),
    "CLAIM": (179, 38, 30),
    "PENDING": (95, 99, 104),
}

# ---------------------------------------------------------------- fonts
_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_font(name, size):
    """Try bundled fonts, then system DejaVu, then PIL default."""
    candidates = [
        os.path.join(_HERE, "data", "fonts", name),
        os.path.join("/usr/share/fonts/truetype/dejavu", name),
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def F(name, size):
    return _load_font(name, size)


SERIF_B = "DejaVuSerif-Bold.ttf"
SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"

# ---------------------------------------------------------------- data
# Stories: (number, region, field, source, status, title, dek, scene)
LEADS = [
    dict(n=1, region="EUROPE", field="WAR", source="Le Monde",
         status="CONFIRMED",
         title="Leaked count puts Russia's war dead near 500,000",
         dek="Hackers leak Rosstat death records; the Kremlin stays silent.",
         scene="rosstat"),
    dict(n=2, region="ASIA-PACIFIC", field="POLITICS", source="Reuters",
         status="CONFIRMED",
         title="China investigates its Shanghai party boss",
         dek="Chen Jining is the fourth Politburo member probed since 2025.",
         scene="shanghai"),
    dict(n=3, region="EUROPE", field="WAR", source="Reuters",
         status="REPORTED",
         title="Russian strike tears apart a Zaporizhzhia block",
         dek="Two killed and 41 wounded overnight; rescuers dig through rubble.",
         scene="zaporizhzhia"),
]
MEDIUM = [
    dict(n=4, region="MIDDLE EAST", field="ENERGY", source="Reuters",
         status="CLAIM",
         title="Four tankers hit mines in the Strait of Hormuz, Iran says",
         dek="Iran's navy blames mines; CENTCOM silent so far.",
         scene="hormuz"),
    dict(n=5, region="WORLD", field="MARKETS", source="Reuters",
         status="CONFIRMED",
         title="Sanofi buys Insmed for $41 billion",
         dek="The biggest biotech deal in three years.",
         scene="sanofi"),
    dict(n=6, region="ASIA-PACIFIC", field="MARKETS", source="Focus Taiwan",
         status="CONFIRMED",
         title="Taiwan stocks jump 8.99% in a record day",
         dek="TAIEX posts its largest points gain ever.",
         scene="taiex"),
    dict(n=7, region="EUROPE", field="WAR", source="Reuters",
         status="CONFIRMED",
         title="Russian drone strays into Poland; jets scrambled",
         dek="Second incursion in four days; NATO on alert.",
         scene="poland"),
    dict(n=8, region="MIDDLE EAST", field="HEALTH", source="Irish Times",
         status="CONFIRMED",
         title="Gaza declares a meningitis epidemic alert",
         dek="533 cases and rising; hospitals overwhelmed.",
         scene="gaza"),
    dict(n=9, region="AFRICA", field="SPORT", source="TSN",
         status="CONFIRMED",
         title="Senegal gets its Africa Cup title back",
         dek="CAS overturns Morocco's final win, 1-0.",
         scene="afcon"),
]
# List items: (number, status, title). Full titles in STORIES.md.
LISTED = [
    (10, "CONFIRMED", "Ukraine defends sinking Russian ship"),
    (11, "REPORTED", "Putin vows payback for oil-plant strikes"),
    (12, "CONFIRMED", "Israel kills senior Hamas security chief"),
    (13, "REPORTED", "About 175 migrants missing off Senegal"),
    (14, "CONFIRMED", "Gavi secures Ebola vaccines for Congo"),
    (15, "PENDING", "Madagascar seeks ex-president's arrest"),
    (16, "CONFIRMED", "Britain warns firms of Russian sabotage"),
    (17, "REPORTED", "Ukraine needs $125bn for 2027"),
    (18, "CONFIRMED", "Nvidia falls 6% after its historic rally"),
    (19, "REPORTED", "US prepares tariffs on China, 15 others"),
    (20, "CONFIRMED", "US consumer confidence jumps to 103.3"),
    (21, "CLAIM", "OpenAI says GPT-6 can design proteins"),
    (22, "CONFIRMED", "Three rockets launch in one day"),
    (23, "CONFIRMED", "Pakistan astronaut joins Shenzhou 24 crew"),
    (24, "CONFIRMED", "Bird flu kills one in Washington outbreak"),
    (25, "CONFIRMED", "Real Madrid thrash PSV 5-1 in Europe"),
    (26, "CONFIRMED", "Sooryavanshi, 15, hits 204 off 53 balls"),
    (27, "CONFIRMED", "Seoul scrambles jets for Russian planes"),
    (28, "CONFIRMED", "Hotpot blast kills six in Hanoi"),
    (29, "CONFIRMED", "Garment workers clash with police"),
    (30, "CLAIM", "Hasina asks to fly home on 16 December"),
    (31, "CONFIRMED", "Malaysia deports 6,500 migrants"),
    (32, "CONFIRMED", "Landmine victims at five-year high: 6,929"),
    (33, "PENDING", "PNG votes on Bougainville independence"),
    (34, "CONFIRMED", "Record 5,258 heat deaths in England"),
    (35, "CONFIRMED", "Chess title match opens with a draw"),
    (36, "CONFIRMED", "Hungary's Magyar meets Zelenskyy"),
]
NUMBERS = [
    ("500,000", "RUSSIAN DEAD, LEAKED"),
    ("4", "TANKERS HIT IN HORMUZ"),
    ("$41bn", "SANOFI BUYS INSMED"),
    ("+8.99%", "TAIEX RECORD JUMP"),
    ("5,258", "UK HEAT DEATHS"),
    ("6,929", "LANDMINE VICTIMS"),
]
REGIONS = ("EUROPE 11", "ASIA-PACIFIC 10", "AFRICA 4", "AMERICAS 5",
           "MIDDLE EAST 3", "WORLD 2", "OCEANIA 1")
UTC_STRIP = ("09:53 UK heat deaths", "10:17 Progress MS-36 lifts off",
             "14:00 Chess opens in Geneva", "16:37 Magyar meets Zelenskyy",
             "19:08 Falcon 9 launches", "22:00 PRESS TIME")
DATECHECK_TITLE = "DATE CHECK - What we left out, and why it is not 24 November:"
DATECHECK_ITEMS = ("COP31 22 Nov", "CrowdStrike 23 Nov", "Nvidia 23 Nov",
                   "Cikande fire 21 Nov", "Khartoum 22 Nov",
                   "Brentford 23 Nov", "Solomon pact 25 Nov",
                   "DeepMind 23 Nov")
FOOTER = ("Sources: Reuters - Le Monde - AP - BBC - AFP - Xinhua - UKHSA "
          "- WHO - UEFA - every story dated 24 November 2026.")
CAPTION_LINES = [
    "Pins show each story's number; shared pins also cover:",
    "1: 3, 7, 11, 17, 22, 36  -  5: 9, 16, 25, 34, 35  -  8: 10, 12",
    "4: 26  -  2: 6, 23, 27  -  18: 19, 20  -  28: 29, 30, 32  -  21: 24",
]
# Map pins: (id, lon, lat, centre-x, centre-y, label, cluster or None,
#             story numbers). Centres are map-relative (map box 330x200).
# lon/lat are the story's place; coastal places use the nearest land
# point inside the coarse coastline polygons (Dakar, Kuala Lumpur and
# the Strait of Hormuz coast), documented in STORIES.md / build-log.
PINS = [
    ("pin-A", 30.52, 50.45, 211, 45, "1", "klaster-A",
     [1, 3, 7, 11, 17, 22, 36]),
    ("pin-B", 2.35, 48.86, 181, 50, "5", "klaster-B",
     [5, 9, 16, 25, 34, 35]),
    ("pin-C", 34.47, 31.50, 209, 74, "8", "klaster-C", [8, 10, 12]),
    ("pin-D", 56.30, 26.90, 236, 80, "4", "klaster-D", [4, 26]),
    ("pin-E", 121.47, 31.23, 294, 74, "2", "klaster-E", [2, 6, 23, 27]),
    ("pin-F", -74.01, 40.71, 113, 61, "18", "klaster-F", [18, 19, 20]),
    ("pin-G", 96.08, 21.92, 267, 85, "28", "klaster-G", [28, 29, 30, 32]),
    ("pin-H", -122.42, 37.77, 69, 65, "21", "klaster-H", [21, 24]),
    ("pin-13", -16.95, 14.86, 166, 97, "13", None, [13]),
    ("pin-14", 38.75, 9.01, 217, 105, "14", None, [14]),
    ("pin-15", 47.51, -18.88, 225, 143, "15", None, [15]),
    ("pin-31", 102.04, 3.29, 277, 113, "31", None, [31]),
    ("pin-33", 147.15, -9.44, 316, 130, "33", None, [33]),
]
PIN_D = 14  # pin diameter px; minimum centre distance = diameter + 12

# ---------------------------------------------------------------- layout
# Vertical flow (y). Gaps between zones are 12 px everywhere.
Y_MASTHEAD = 12
H_MASTHEAD = 102
Y_NUMBERS = 126
H_NUMBERS = 35
Y_REGIONS = 173
H_REGIONS = 14
Y_UTC = 199
H_UTC = 20
Y_LEADS = 231
H_LEAD = 202
Y_MED1 = 445
Y_MED2 = 571
H_MED = 114
Y_BOTTOM = 697
H_BOTTOM = 247
Y_DATECHECK = 956
H_DATECHECK = 28
Y_FOOTER = 996
H_FOOTER = 10
CARD_W = 322
CARD_GAP = 13
COL_X = [MARGIN_X, MARGIN_X + CARD_W + CARD_GAP,
         MARGIN_X + 2 * (CARD_W + CARD_GAP)]
MAP_BOX = (MARGIN_X, Y_BOTTOM, 330, 200)   # x, y, w, h
MAP_LON = (-180.0, 180.0)
MAP_LAT = (-60.0, 85.0)
LIST_X = (358, 689)
LIST_W = 319
LIST_Y = 725
LIST_H = 210
ROW_H = 15
CAPTION_BOX = (MARGIN_X, 909, 330, 37)
LEGEND_BOX = (358, Y_BOTTOM, 650, 16)


def project(lon, lat):
    """Linear projection lon/lat -> absolute canvas px (same as verifier)."""
    x0, y0, w, h = MAP_BOX
    x = x0 + (lon - MAP_LON[0]) / (MAP_LON[1] - MAP_LON[0]) * w
    y = y0 + (MAP_LAT[1] - lat) / (MAP_LAT[1] - MAP_LAT[0]) * h
    return x, y


# ---------------------------------------------------------------- helpers
def measure(font, text):
    return font.getlength(text)


def wrap_text(font, text, max_w, max_lines):
    """Greedy word wrap; shorten the last line with an ellipsis at a word
    boundary when the text does not fit in max_lines lines."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if measure(font, trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    # If words remain unwrapped, shorten the last line at a word boundary.
    joined = " ".join(lines)
    if len(joined) < len(text):
        last = lines[-1]
        while last and measure(font, last + " ...") > max_w:
            last = last.rsplit(" ", 1)[0] if " " in last else ""
        lines[-1] = (last + " ...") if last else "..."
    return lines


def shorten(font, text, max_w):
    """Shorten one line at a word boundary with a trailing ellipsis."""
    if measure(font, text) <= max_w:
        return text
    words = text.split(" ")
    out = ""
    for word in words:
        trial = word if not out else out + " " + word
        if measure(font, trial + " ...") <= max_w:
            out = trial
        else:
            break
    return (out + " ...") if out else "..."


def text_top(draw, xy, text, font, fill):
    """Draw text with its top at xy (anchor left-top)."""
    draw.text(xy, text, font=font, fill=fill, anchor="lt")


def text_centre(draw, cx, y, text, font, fill):
    draw.text((cx, y), text, font=font, fill=fill, anchor="mt")

# ---------------------------------------------------------------- scenes
# Each scene draws flat geometric shapes (no humans) inside the
# illustration box (bx, by, bw, bh) and returns adegan entries whose
# bboxes sit at least 2 px inside that box. The status badge sits on the
# top-right corner of the illustration, so scenes keep the rectangle
# x > bx + bw - 70, y < by + 24 clear.


def _adegan(box, dx, dy, w, h, aid):
    bx, by, bw, bh = box
    x, y = bx + dx, by + dy
    assert x >= bx + 2 and y >= by + 2, aid
    assert x + w <= bx + bw - 2 and y + h <= by + bh - 2, aid
    return {"id": aid, "bbox": [int(x), int(y), int(w), int(h)]}


def _geo(box, lon0, lon1, lat0, lat1):
    """Project lon/lat to box px for a stylized map."""
    bx, by, bw, bh = box

    def P(lon, lat):
        return (bx + (lon - lon0) / (lon1 - lon0) * bw,
                by + (lat1 - lat) / (lat1 - lat0) * bh)
    return P


def _dashed(d, pts, color, width=3, dash=6, gap=4):
    """Draw a dashed polyline through pts (list of (x, y))."""
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / (dash + gap)))
        for s in range(n):
            t0 = s / n
            t1 = min(1.0, (s * (dash + gap) + dash) / seg)
            xa = x0 + (x1 - x0) * t0
            ya = y0 + (y1 - y0) * t0
            xb = x0 + (x1 - x0) * t1
            yb = y0 + (y1 - y0) * t1
            d.line([xa, ya, xb, yb], fill=color, width=width)



def scene_rosstat(d, box):
    """Lead 1: Ukraine war-theater map (rank 1 style).

    Black Sea along the bottom, Crimean peninsula jutting down, Dnipro
    river, dashed red front line, dotted drone path toward Kyiv, city
    markers, compass rose, and the leaked toll on a chip.
    """
    bx, by, bw, bh = box
    SEA_M = (168, 200, 222)
    LAND_M = (238, 228, 205)
    LAND_L = (186, 168, 120)
    d.rectangle([bx, by, bx + bw, by + bh], fill=SEA_M)
    P = _geo(box, 24, 44, 43, 54)
    # North coast of the Black Sea, west -> east; Crimea exaggerated.
    coast = [(24, 45.9), (26, 46.3), (28, 46.4), (30, 46.6), (31, 46.7),
             (32, 46.5), (32.3, 45.9), (32.8, 44.4), (33.4, 44.1),
             (34.0, 44.6), (34.6, 45.6), (35.5, 46.4), (36.5, 46.9),
             (37.5, 47.1), (38.5, 47.3), (39.5, 47.4), (40.5, 47.2),
             (42, 47.0), (44, 46.9)]
    poly = [P(lon, lat) for lon, lat in coast] + [P(44, 54), P(24, 54)]
    d.polygon(poly, fill=LAND_M, outline=LAND_L)
    # Sea of Azov inlet.
    azov = [(38.5, 47.3), (39.5, 47.4), (39.8, 46.9), (39.0, 46.8)]
    d.polygon([P(lon, lat) for lon, lat in azov], fill=SEA_M)
    # Dnipro river, Kyiv -> Black Sea.
    river = [(30.5, 50.4), (31.0, 49.2), (31.8, 47.9), (32.3, 47.0),
             (32.6, 46.7)]
    d.line([P(lon, lat) for lon, lat in river], fill=(120, 175, 210),
           width=3)
    # Front line (dashed red).
    front = [(34.0, 50.2), (35.2, 49.2), (36.4, 48.3), (37.6, 47.6),
             (38.8, 47.3)]
    _dashed(d, [P(lon, lat) for lon, lat in front], (192, 57, 43),
            width=3)
    # Drone path: dotted arc from the east toward Kyiv.
    dx0, dy0 = P(39, 50.6)
    dx1, dy1 = P(30.5, 50.4)
    for t in [i / 14 for i in range(15)]:
        x = dx0 + (dx1 - dx0) * t
        y = dy0 + (dy1 - dy0) * t - 10 * math.sin(math.pi * t)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(26, 26, 26))
    # City markers + labels.
    f = F(SANS_B, 11)
    fs = F(SANS_B, 10)
    for lon, lat, lab in [(30.5, 50.4, "KYIV"),
                          (35.2, 47.8, "ZAPORIZHZHIA")]:
        x, y = P(lon, lat)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(192, 57, 43),
                  outline=(255, 255, 255), width=1)
        d.text((x + 10, y - 6), lab, font=f, fill=NAVY)
    # Compass rose, top-left (clear of the badge).
    cx, cy = bx + 18, by + 14
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=NAVY, width=1)
    d.polygon([(cx, cy - 7), (cx + 2, cy), (cx, cy + 7), (cx - 2, cy)],
              fill=NAVY)
    d.text((cx + 11, cy - 5), "N", font=fs, fill=NAVY)
    # Sea label, bottom-right (clear of the chip).
    d.text((bx + 208, by + 80), "BLACK SEA", font=fs, fill=(255, 255, 255))
    # The leaked toll on a chip, bottom-left on the sea.
    d.rectangle([bx + 8, by + 66, bx + 108, by + 86], fill=(255, 255, 255),
                outline=NAVY)
    fb = F(SANS_B, 15)
    d.text((bx + 58, by + 76), "500,000", font=fb, fill=(192, 57, 43),
           anchor="mm")
    return [
        _adegan(box, 2, 2, 302, 80, "theater-map"),
        _adegan(box, 150, 28, 80, 32, "front-line"),
        _adegan(box, 8, 66, 100, 20, "chip-500000"),
    ]


def scene_shanghai(d, box):
    """Lead 2: China coast map (rank 1 style).

    East China Sea on the right, China on the left, Yangtze river
    running into the sea at Shanghai, Hangzhou Bay, city markers,
    compass rose, and the count on a chip.
    """
    bx, by, bw, bh = box
    SEA_M = (168, 200, 222)
    LAND_M = (238, 228, 205)
    LAND_L = (186, 168, 120)
    d.rectangle([bx, by, bx + bw, by + bh], fill=SEA_M)
    P = _geo(box, 118, 124, 28, 34)
    # China coast, north -> south (Jiangsu -> Yangtze mouth -> Zhejiang).
    # Land is WEST of this line; sea is EAST.
    coast = [(120.6, 34.0), (120.9, 33.0), (121.1, 32.2), (121.6, 31.6),
             (121.9, 31.2), (121.8, 30.8), (121.6, 30.3), (121.4, 29.5),
             (121.1, 28.8), (120.9, 28.0)]
    poly = [P(lon, lat) for lon, lat in coast] + [P(118, 28), P(118, 34)]
    d.polygon(poly, fill=LAND_M, outline=LAND_L)
    # Yangtze river, west -> mouth at Shanghai.
    river = [(118.0, 31.6), (119.0, 31.5), (120.0, 31.4), (121.0, 31.3),
             (121.9, 31.2)]
    d.line([P(lon, lat) for lon, lat in river], fill=(120, 175, 210),
           width=4)
    # Hangzhou Bay: wide bay south of Shanghai (sea inlet).
    bay = [(121.7, 30.6), (121.9, 30.4), (121.8, 30.1), (121.5, 30.2),
           (121.4, 30.5)]
    d.polygon([P(lon, lat) for lon, lat in bay], fill=SEA_M)
    # City markers + labels.
    f = F(SANS_B, 11)
    fs = F(SANS_B, 10)
    x, y = P(121.5, 31.2)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(192, 57, 43),
              outline=(255, 255, 255), width=1)
    d.text((x + 8, y - 6), "SHANGHAI", font=f, fill=NAVY)
    x2, y2 = P(120.2, 30.3)
    d.ellipse([x2 - 4, y2 - 4, x2 + 4, y2 + 4], fill=NAVY,
              outline=(255, 255, 255), width=1)
    d.text((x2 - 70, y2 - 6), "HANGZHOU", font=fs, fill=NAVY)
    # Compass rose, top-left (clear of the badge).
    cx, cy = bx + 18, by + 14
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=NAVY, width=1)
    d.polygon([(cx, cy - 7), (cx + 2, cy), (cx, cy + 7), (cx - 2, cy)],
              fill=NAVY)
    d.text((cx + 11, cy - 5), "N", font=fs, fill=NAVY)
    # Sea label.
    d.text((bx + 200, by + 52), "EAST CHINA SEA", font=fs,
           fill=(255, 255, 255))
    # The count on a chip, bottom-right on the sea.
    d.rectangle([bx + 228, by + 64, bx + 298, by + 86],
                fill=(255, 255, 255), outline=NAVY)
    fb = F(SANS_B, 15)
    d.text((bx + 263, by + 75), "4TH", font=fb, fill=(192, 57, 43),
           anchor="mm")
    return [
        _adegan(box, 2, 2, 302, 88, "coast-map"),
        _adegan(box, 2, 35, 197, 10, "yangtze"),
        _adegan(box, 228, 64, 70, 22, "chip-4th"),
    ]


def scene_zaporizhzhia(d, box):
    """Lead 3: Zaporizhzhia city block under attack (rich scene).

    Detailed skyline with lit windows and damaged tops, smoke columns,
    a large explosion with the wounded count, rubble at the base, and
    rescue lights. No humans; the scene is buildings, smoke, fire.
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(27, 42, 58))
    # Night sky: a few stars.
    for sx, sy in [(24, 10), (70, 7), (120, 12), (268, 9), (292, 14)]:
        d.ellipse([bx + sx - 1, by + sy - 1, bx + sx + 1, by + sy + 1],
                  fill=(220, 228, 240))
    # Skyline: 9 buildings, varying heights, some with jagged (damaged)
    # tops; lit windows in warm yellow.
    specs = [(10, 46, 30), (44, 34, 26), (74, 52, 30), (108, 40, 26),
             (138, 30, 28), (170, 48, 26), (200, 36, 28), (232, 44, 26),
             (262, 32, 30)]
    for i, (ox, top, wdt) in enumerate(specs):
        base = by + 88
        d.rectangle([bx + ox, by + top, bx + ox + wdt, base],
                    fill=(18, 30, 40))
        if i in (2, 5):
            # Jagged damaged top.
            d.polygon([(bx + ox, by + top), (bx + ox + 8, by + top - 6),
                       (bx + ox + 16, by + top + 2),
                       (bx + ox + 24, by + top - 5),
                       (bx + ox + wdt, by + top)], fill=(18, 30, 40))
        for wy in range(by + top + 6, by + 82, 11):
            for wx in range(bx + ox + 5, bx + ox + wdt - 4, 11):
                if (wx + wy) % 23:
                    d.rectangle([wx, wy, wx + 4, wy + 4],
                                fill=(232, 184, 75))
    # Smoke columns rising from two damaged buildings.
    for cx, cy, r in [(88, 26, 9), (100, 16, 11), (112, 22, 8),
                      (214, 22, 10), (226, 14, 12), (238, 20, 8)]:
        d.ellipse([bx + cx - r, by + cy - r, bx + cx + r, by + cy + r],
                  fill=(127, 140, 141))
    # Explosion starburst with the wounded count inside.
    cx, cy, r1, r2 = bx + 200, by + 55, 30, 15
    pts = []
    for i in range(16):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / 8.0
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=(230, 126, 34))
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(241, 196, 15))
    f = F(SANS_B, 20)
    d.text((cx, cy - 11), "41", font=f, fill=(26, 26, 26), anchor="mt")
    # Rubble at the base: broken slabs and dust.
    for ox, oy, wdt, hgt in [(16, 86, 26, 6), (60, 88, 34, 4),
                             (120, 87, 30, 5), (248, 88, 40, 4)]:
        d.polygon([(bx + ox, by + oy), (bx + ox + wdt // 2, by + oy - hgt),
                   (bx + ox + wdt, by + oy)], fill=(120, 113, 96))
    # Rescue lights: small red/white beacons near the rubble.
    for lx, col in [(40, (192, 57, 43)), (150, (255, 255, 255)),
                    (280, (192, 57, 43))]:
        d.ellipse([bx + lx - 3, by + 82, bx + lx + 3, by + 88], fill=col)
    return [
        _adegan(box, 8, 28, 290, 60, "city"),
        _adegan(box, 170, 25, 60, 60, "burst-41"),
        _adegan(box, 8, 80, 290, 10, "rubble"),
    ]


def scene_hormuz(d, box):
    """Medium 4: Strait of Hormuz, two tankers stacked in a tall box.

    Sea fills the box; two tankers (upper with fire, lower with a
    pennant), a spiked mine at the bottom-right, wave lines at the base.
    Content stays below the badge zone (top-right).
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(127, 179, 213))
    d.rectangle([bx, by, bx + bw, by + 10], fill=(220, 233, 242))
    # Tanker 1 (upper): hull, containers, bridge, funnel, fire.
    d.rectangle([bx + 8, by + 34, bx + 72, by + 46], fill=(44, 62, 80))
    for cx in (14, 26, 38):
        d.rectangle([bx + cx, by + 30, bx + cx + 9, by + 34],
                    fill=(192, 57, 43) if cx == 26 else (232, 184, 75))
    d.rectangle([bx + 52, by + 26, bx + 64, by + 34], fill=(240, 240, 240))
    d.rectangle([bx + 66, by + 28, bx + 70, by + 34], fill=(26, 26, 26))
    # Fire licking from tanker 1's deck.
    d.polygon([(bx + 54, by + 26), (bx + 59, by + 16), (bx + 64, by + 26)],
              fill=(230, 126, 34))
    d.polygon([(bx + 57, by + 26), (bx + 59, by + 20), (bx + 61, by + 26)],
              fill=(241, 196, 15))
    # Tanker 2 (lower): hull, bridge on the left, pennant.
    d.rectangle([bx + 8, by + 60, bx + 72, by + 72], fill=(44, 62, 80))
    d.rectangle([bx + 14, by + 52, bx + 26, by + 60], fill=(240, 240, 240))
    d.rectangle([bx + 30, by + 56, bx + 58, by + 60], fill=(232, 184, 75))
    d.polygon([(bx + 20, by + 52), (bx + 20, by + 44), (bx + 28, by + 48)],
              fill=(192, 57, 43))
    # Waterlines under each hull.
    d.line([bx + 6, by + 47, bx + 74, by + 47], fill=(255, 255, 255),
           width=1)
    d.line([bx + 6, by + 73, bx + 74, by + 73], fill=(255, 255, 255),
           width=1)
    # Spiked mine, bottom-right.
    cx, cy = bx + 62, by + 88
    for a in range(0, 360, 45):
        r = math.radians(a)
        d.line([cx + 6 * math.cos(r), cy + 6 * math.sin(r),
                cx + 9 * math.cos(r), cy + 9 * math.sin(r)],
               fill=(26, 26, 26), width=2)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(26, 26, 26))
    # Wave lines at the base.
    for wy in (94, 98):
        d.arc([bx + 8, by + wy - 3, bx + 30, by + wy + 3], start=200,
              end=340, fill=(255, 255, 255), width=1)
        d.arc([bx + 46, by + wy - 3, bx + 68, by + wy + 3], start=200,
              end=340, fill=(255, 255, 255), width=1)
    return [
        _adegan(box, 6, 24, 68, 50, "tankers"),
        _adegan(box, 52, 16, 14, 12, "fire"),
        _adegan(box, 52, 80, 20, 18, "mine"),
    ]


def scene_sanofi(d, box):
    """Medium 5: Sanofi buys Insmed, $41bn biotech deal.

    Two merging blocks (top-left), a large capsule (center), a flask
    with liquid (bottom-left), and a rising green arrow (right).
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(234, 242, 248))
    # Two blocks merging, with a plus between them (top-left).
    d.rectangle([bx + 8, by + 26, bx + 30, by + 40], fill=NAVY)
    d.rectangle([bx + 36, by + 26, bx + 58, by + 40], fill=(20, 143, 119))
    d.rectangle([bx + 31, by + 31, bx + 35, by + 35], fill=INK)
    d.rectangle([bx + 32, by + 29, bx + 34, by + 37], fill=INK)
    # Large capsule, center.
    d.ellipse([bx + 10, by + 48, bx + 30, by + 64], fill=(192, 57, 43))
    d.rectangle([bx + 20, by + 48, bx + 50, by + 64], fill=(192, 57, 43))
    d.ellipse([bx + 40, by + 48, bx + 60, by + 64], fill=WHITE,
              outline=(192, 57, 43))
    d.rectangle([bx + 40, by + 48, bx + 50, by + 64], fill=WHITE)
    d.rectangle([bx + 20, by + 54, bx + 50, by + 58], fill=(255, 255, 255))
    # Flask with green liquid, bottom-left.
    d.polygon([(bx + 12, by + 72), (bx + 24, by + 72), (bx + 30, by + 94),
               (bx + 6, by + 94)], outline=NAVY, width=2)
    d.polygon([(bx + 9, by + 84), (bx + 27, by + 84), (bx + 30, by + 94),
               (bx + 6, by + 94)], fill=(20, 143, 119))
    d.rectangle([bx + 15, by + 68, bx + 21, by + 72], fill=NAVY)
    # Rising arrow, right side.
    d.polygon([(bx + 62, by + 92), (bx + 70, by + 92), (bx + 70, by + 78),
               (bx + 76, by + 78), (bx + 66, by + 66), (bx + 56, by + 78),
               (bx + 62, by + 78)], fill=(46, 125, 50))
    return [
        _adegan(box, 6, 24, 54, 18, "merging-blocks"),
        _adegan(box, 8, 46, 54, 20, "capsule"),
        _adegan(box, 6, 66, 30, 30, "flask"),
    ]


def scene_taiex(d, box):
    """Medium 6: Taiwan stocks jump 8.99%.

    Faint gridlines, a steep rising chart with data points, a chip
    (bottom-left), and the jump in green at the base.
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(234, 247, 238))
    # Faint gridlines.
    for gy in (40, 56, 72):
        d.line([bx + 6, by + gy, bx + 74, by + gy], fill=(210, 230, 214),
               width=1)
    # Chart line shooting up (stays below the badge zone).
    pts = [(bx + 8, by + 84), (bx + 24, by + 76), (bx + 38, by + 66),
           (bx + 52, by + 50), (bx + 66, by + 34)]
    d.line(pts, fill=(46, 125, 50), width=3, joint="curve")
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(46, 125, 50))
    d.polygon([(bx + 66, by + 34), (bx + 58, by + 32), (bx + 62, by + 42)],
              fill=(46, 125, 50))
    # Chip, bottom-left.
    d.rectangle([bx + 10, by + 70, bx + 30, by + 86], fill=(44, 62, 80))
    for px in (14, 20, 26):
        d.line([bx + px, by + 66, bx + px, by + 70], fill=(232, 184, 75),
               width=2)
        d.line([bx + px, by + 86, bx + px, by + 90], fill=(232, 184, 75),
               width=2)
    d.rectangle([bx + 15, by + 75, bx + 25, by + 81], fill=(232, 184, 75))
    # The jump, in green at the base.
    f = F(SANS_B, 12)
    d.text((bx + 38, by + 88), "+8.99%", font=f, fill=(46, 125, 50),
           anchor="lt")
    return [
        _adegan(box, 6, 30, 68, 58, "chart-up"),
        _adegan(box, 8, 66, 24, 24, "chip"),
        _adegan(box, 36, 86, 42, 14, "jump-899"),
    ]


def scene_poland(d, box):
    """Medium 7: Russian drone strays into Poland.

    A small jet (top-left), a detailed quadcopter drone (center),
    radar arcs (bottom-right), and the Polish flag band at the base.
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(220, 233, 242))
    # Small jet silhouette, top-left.
    d.polygon([(bx + 8, by + 30), (bx + 26, by + 28), (bx + 30, by + 30),
               (bx + 26, by + 32), (bx + 8, by + 32)], fill=(44, 62, 80))
    d.polygon([(bx + 16, by + 28), (bx + 20, by + 24), (bx + 22, by + 28)],
              fill=(44, 62, 80))
    # Quadcopter drone, center.
    cx, cy = bx + 40, by + 48
    d.rectangle([cx - 13, cy - 6, cx + 13, cy + 6], fill=(44, 62, 80))
    d.ellipse([cx - 6, cy - 3, cx + 6, cy + 3], fill=(120, 130, 140))
    for sx in (-1, 1):
        for sy in (-1, 1):
            d.line([cx, cy, cx + sx * 24, cy + sy * 10], fill=(44, 62, 80),
                   width=3)
            d.ellipse([cx + sx * 24 - 12, cy + sy * 10 - 2,
                       cx + sx * 24 + 12, cy + sy * 10 + 2],
                      fill=(120, 130, 140))
    # Radar arcs, bottom-right.
    rcx, rcy = bx + 62, by + 84
    for r in (8, 14, 20):
        d.arc([rcx - r, rcy - r, rcx + r, rcy + r], start=180, end=270,
              fill=(20, 143, 119), width=2)
    d.ellipse([rcx - 3, rcy - 3, rcx + 3, rcy + 3], fill=(20, 143, 119))
    # Polish flag band at the base.
    d.rectangle([bx + 6, by + 92, bx + 74, by + 96], fill=WHITE)
    d.rectangle([bx + 6, by + 96, bx + 74, by + 100], fill=(192, 57, 43))
    return [
        _adegan(box, 6, 24, 26, 10, "jet"),
        _adegan(box, 14, 32, 54, 32, "drone"),
        _adegan(box, 40, 62, 34, 26, "radar"),
    ]


def scene_gaza(d, box):
    """Medium 8: Gaza meningitis epidemic alert.

    A large hospital cross on a teal disc (center), a shield with a
    check (bottom-left), a warning triangle (bottom-right), and a small
    microbe (top-left).
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(253, 240, 230))
    # Small microbe, top-left (clear of the badge).
    mx, my = bx + 14, by + 30
    d.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=(192, 57, 43))
    for a in range(0, 360, 60):
        r = math.radians(a)
        d.line([mx + 6 * math.cos(r), my + 6 * math.sin(r),
                mx + 10 * math.cos(r), my + 10 * math.sin(r)],
               fill=(192, 57, 43), width=2)
    # Hospital cross on a teal disc, center.
    cx, cy = bx + 40, by + 46
    d.ellipse([cx - 17, cy - 17, cx + 17, cy + 17], fill=(20, 143, 119))
    d.rectangle([cx - 4, cy - 12, cx + 4, cy + 12], fill=WHITE)
    d.rectangle([cx - 12, cy - 4, cx + 12, cy + 4], fill=WHITE)
    # Shield with a check, bottom-left.
    d.polygon([(bx + 10, by + 66), (bx + 32, by + 66), (bx + 32, by + 80),
               (bx + 21, by + 92), (bx + 10, by + 80)], outline=NAVY,
              width=3)
    d.line([bx + 15, by + 79, bx + 20, by + 84, bx + 28, by + 73],
           fill=NAVY, width=3, joint="curve")
    # Warning triangle, bottom-right.
    d.polygon([(bx + 50, by + 92), (bx + 62, by + 68), (bx + 74, by + 92)],
              fill=(232, 184, 75))
    f = F(SANS_B, 14)
    d.text((bx + 62, by + 78), "!", font=f, fill=(26, 26, 26), anchor="mt")
    return [
        _adegan(box, 6, 22, 18, 18, "microbe"),
        _adegan(box, 22, 28, 38, 38, "hospital-cross"),
        _adegan(box, 8, 64, 68, 30, "shield-warning"),
    ]


def scene_afcon(d, box):
    """Medium 9: Senegal gets its Africa Cup title back.

    A gold trophy (top), a football (center), Senegal stripes at the
    base, and a small star above the trophy.
    """
    bx, by, bw, bh = box
    d.rectangle([bx, by, bx + bw, by + bh], fill=(232, 245, 233))
    # Small star above the trophy.
    sx, sy = bx + 40, by + 30
    spts = []
    for i in range(10):
        r = 7 if i % 2 == 0 else 3
        a = math.pi * i / 5.0 - math.pi / 2
        spts.append((sx + r * math.cos(a), sy + r * math.sin(a)))
    d.polygon(spts, fill=(232, 184, 75))
    # Trophy: bowl, stem, base.
    d.polygon([(bx + 22, by + 40), (bx + 58, by + 40), (bx + 52, by + 54),
               (bx + 28, by + 54)], fill=(232, 184, 75))
    d.rectangle([bx + 37, by + 54, bx + 43, by + 60], fill=(232, 184, 75))
    d.rectangle([bx + 30, by + 60, bx + 50, by + 66], fill=(232, 184, 75))
    d.arc([bx + 14, by + 42, bx + 26, by + 54], start=90, end=270,
          fill=(232, 184, 75), width=3)
    d.arc([bx + 54, by + 42, bx + 66, by + 54], start=270, end=90,
          fill=(232, 184, 75), width=3)
    # Football, center.
    cx, cy = bx + 40, by + 80
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=WHITE,
              outline=(26, 26, 26))
    d.polygon([(cx - 4, cy - 7), (cx + 4, cy - 7), (cx + 6, cy),
               (cx, cy + 6), (cx - 6, cy)], fill=(26, 26, 26))
    # Senegal stripes at the base.
    for i, col in enumerate([(0, 122, 61), (252, 209, 22), (206, 17, 38)]):
        d.rectangle([bx + 8 + i * 22, by + 96, bx + 8 + (i + 1) * 22,
                     by + 100], fill=col)
    return [
        _adegan(box, 30, 22, 20, 16, "star"),
        _adegan(box, 12, 38, 56, 28, "trophy"),
        _adegan(box, 26, 66, 28, 28, "football"),
    ]


SCENES = {
    "rosstat": scene_rosstat,
    "shanghai": scene_shanghai,
    "zaporizhzhia": scene_zaporizhzhia,
    "hormuz": scene_hormuz,
    "sanofi": scene_sanofi,
    "taiex": scene_taiex,
    "poland": scene_poland,
    "gaza": scene_gaza,
    "afcon": scene_afcon,
}

# ---------------------------------------------------------------- page
def draw_masthead(d, elements):
    f_kick = F(SANS_B, 10)
    f_date = F(SERIF_B, 52)
    f_sub = F(SANS, 12)
    f_cnt = F(SANS, 10)
    date = "Tuesday 24 November 2026"
    sub = ("Half a million dead in a leaked count \u00b7 Shanghai's party "
           "boss falls \u00b7 tankers burn in Hormuz")
    cnt = ("36 stories \u00b7 7 regions \u00b7 26 confirmed \u00b7 5 reported "
           "\u00b7 3 claims \u00b7 2 pending")
    text_top(d, (MARGIN_X, Y_MASTHEAD), "THE WORLD, CHECKED", f_kick, NAVY)
    text_top(d, (MARGIN_X, Y_MASTHEAD + 14), date, f_date, NAVY)
    text_top(d, (MARGIN_X, Y_MASTHEAD + 78), sub, f_sub, INK)
    text_top(d, (MARGIN_X, Y_MASTHEAD + 92), cnt, f_cnt, MUTED)
    elements.append({
        "id": "masthead", "jenis": "masthead",
        "bbox": [MARGIN_X, Y_MASTHEAD, CONTENT_W, H_MASTHEAD],
        "teks": "THE WORLD, CHECKED / " + date + " / " + sub + " / " + cnt,
        "ukuran_font": 52, "lebar_terukur": round(measure(f_date, date), 1),
    })


def draw_numbers(d, elements):
    d.rectangle([MARGIN_X, Y_NUMBERS, MARGIN_X + CONTENT_W,
                 Y_NUMBERS + H_NUMBERS], fill=NAVY)
    widths = [166, 165, 165, 165, 165, 166]
    f_num = F(SANS_B, 18)
    f_lab = F(SANS_B, 9)
    x = MARGIN_X
    leftmost, rightmost = None, None
    for (num, lab), wcell in zip(NUMBERS, widths):
        cx = x + wcell / 2.0
        wn, wl = measure(f_num, num), measure(f_lab, lab)
        text_centre(d, cx, Y_NUMBERS + 2, num, f_num, WHITE)
        text_centre(d, cx, Y_NUMBERS + 23, lab, f_lab, (200, 210, 225))
        leftmost = cx - max(wn, wl) / 2.0 if leftmost is None else min(
            leftmost, cx - max(wn, wl) / 2.0)
        rightmost = cx + max(wn, wl) / 2.0 if rightmost is None else max(
            rightmost, cx + max(wn, wl) / 2.0)
        if x + wcell < MARGIN_X + CONTENT_W:
            d.line([x + wcell, Y_NUMBERS + 6, x + wcell,
                    Y_NUMBERS + H_NUMBERS - 6], fill=NAVY_LIGHT, width=1)
        x += wcell
    teks = " | ".join(n + " " + l for n, l in NUMBERS)
    elements.append({
        "id": "pita-angka", "jenis": "strip",
        "bbox": [MARGIN_X, Y_NUMBERS, CONTENT_W, H_NUMBERS],
        "teks": teks, "ukuran_font": 18,
        "lebar_terukur": round(rightmost - leftmost, 1),
    })


def draw_regions(d, elements):
    f = F(SANS_B, 10)
    teks = " \u00b7 ".join(REGIONS)
    w = measure(f, teks)
    assert w <= CONTENT_W, "region bar too wide"
    text_centre(d, MARGIN_X + CONTENT_W / 2.0, Y_REGIONS + 1, teks, f, MUTED)
    elements.append({
        "id": "bar-wilayah", "jenis": "strip",
        "bbox": [MARGIN_X, Y_REGIONS, CONTENT_W, H_REGIONS],
        "teks": teks, "ukuran_font": 10, "lebar_terukur": round(w, 1),
    })


def draw_utc(d, elements):
    d.rectangle([MARGIN_X, Y_UTC, MARGIN_X + CONTENT_W, Y_UTC + H_UTC],
                fill=(240, 235, 225))
    f = F(SANS, 10)
    f_b = F(SANS_B, 10)
    sep = " \u00b7 "
    total = sum(measure(f_b if lab.endswith("PRESS TIME") else f, lab)
                for lab in UTC_STRIP)
    total += measure(f, sep) * (len(UTC_STRIP) - 1)
    assert total <= CONTENT_W, "UTC strip too wide"
    x = MARGIN_X + (CONTENT_W - total) / 2.0
    for i, lab in enumerate(UTC_STRIP):
        font = f_b if lab.endswith("PRESS TIME") else f
        col = STATUS["CLAIM"] if lab.endswith("PRESS TIME") else NAVY
        text_top(d, (x, Y_UTC + 4), lab, font, col)
        x += measure(font, lab)
        if i < len(UTC_STRIP) - 1:
            text_top(d, (x, Y_UTC + 4), sep, f, MUTED)
            x += measure(f, sep)
    elements.append({
        "id": "strip-utc", "jenis": "strip",
        "bbox": [MARGIN_X, Y_UTC, CONTENT_W, H_UTC],
        "teks": sep.join(UTC_STRIP), "ukuran_font": 10,
        "lebar_terukur": round(total, 1),
    })


def draw_card(d, x, y, kind, story, elements):
    n = story["n"]
    if kind == "lead":
        h, ill = 202, (x + 8, y + 8, 306, 92)
        tbox = (x + 8, y + 106, 306, 90)
        badge_f, badge_h, badge_dy = 9, 15, 6
        meta_f, title_f, dek_f = 11, 17, 11
        title_lh, dek_lh = 21, 13
    else:
        # Side-by-side (revisi ilustrasi): narrow tall illustration on
        # the left, report text on the right. Kevin: non-hero art too
        # wide; give the report (title + dek) more room.
        h, ill = 114, (x + 6, y + 6, 80, 102)
        tbox = (x + 94, y + 6, 222, 104)
        badge_f, badge_h, badge_dy = 8, 13, 5
        meta_f, title_f, dek_f = 10, 15, 11
        title_lh, dek_lh = 18, 13
    card_id = "kartu-%d" % n
    d.rectangle([x, y, x + CARD_W, y + h], fill=CARD, outline=CARD_LINE)
    adegan = SCENES[story["scene"]](d, ill)
    # Status badge on the illustration's top-right corner.
    bf = F(SANS_B, badge_f)
    status = story["status"]
    bw = int(math.ceil(measure(bf, status))) + 12
    bxx = ill[0] + ill[2] - 6 - bw
    byy = ill[1] + badge_dy
    d.rectangle([bxx, byy, bxx + bw, byy + badge_h],
                fill=STATUS[status])
    d.text((bxx + bw / 2.0, byy + badge_h / 2.0), status, font=bf,
           fill=WHITE, anchor="mm")
    # Text block.
    mf = F(SANS_B, meta_f)
    tf = F(SANS_B, title_f)
    tx, ty, tw, th = tbox
    if kind == "lead":
        meta = "%d \u00b7 %s \u00b7 %s \u2014 %s" % (
            n, story["region"], story["field"], story["source"])
        assert measure(mf, meta) <= tw, "meta too wide: " + meta
        text_top(d, (tx, ty), meta, mf, NAVY)
        title_lines = wrap_text(tf, story["title"], tw, 2)
        ycur = ty + meta_f + 4
        for line in title_lines:
            text_top(d, (tx, ycur), line, tf, INK)
            ycur += title_lh
        lines = [meta] + title_lines
        widths = [measure(mf, meta)] + [measure(tf, ln)
                                         for ln in title_lines]
        df = F(SANS, dek_f)
        dek_lines = wrap_text(df, story["dek"], tw, 2)
        ycur += 4
        for line in dek_lines:
            text_top(d, (tx, ycur), line, df, MUTED)
            ycur += dek_lh
        lines += dek_lines
        widths += [measure(df, ln) for ln in dek_lines]
        assert ycur - dek_lh <= ty + th, "lead text overflow"
        teks = (meta + " / " + " ".join(title_lines) + " / "
                + " ".join(dek_lines))
    else:
        # Medium: one-line meta (number/region/field), title up to
        # 3 lines, dek + source up to 2 lines. The source rides on the
        # dek so the title can use 3 lines when it needs them (#4).
        meta1 = "%d \u00b7 %s \u00b7 %s" % (
            n, story["region"], story["field"])
        assert measure(mf, meta1) <= tw, "meta1 too wide: " + meta1
        text_top(d, (tx, ty), meta1, mf, NAVY)
        ycur = ty + meta_f + 3
        title_lines = wrap_text(tf, story["title"], tw, 3)
        for line in title_lines:
            text_top(d, (tx, ycur), line, tf, INK)
            ycur += title_lh
        lines = [meta1] + title_lines
        widths = [measure(mf, meta1)] + [
            measure(tf, ln) for ln in title_lines]
        df = F(SANS, dek_f)
        dek_text = story["dek"] + " \u2014 " + story["source"]
        dek_lines = wrap_text(df, dek_text, tw, 2)
        ycur += 4
        for line in dek_lines:
            text_top(d, (tx, ycur), line, df, MUTED)
            ycur += dek_lh
        lines += dek_lines
        widths += [measure(df, ln) for ln in dek_lines]
        assert ycur - dek_lh <= ty + th, "medium text overflow"
        teks = (meta1 + " / " + " ".join(title_lines)
                + " / " + " ".join(dek_lines))
    elements.append({
        "id": card_id, "jenis": "kartu",
        "jenis_kartu": "lead" if kind == "lead" else "grid",
        "bbox": [x, y, CARD_W, h], "ilustrasi_bbox": list(ill),
        "elemen_adegan": adegan,
    })
    elements.append({
        "id": "teks-%d" % n, "jenis": "teks", "induk": card_id,
        "bbox": list(tbox), "teks": teks,
        "ukuran_font": title_f, "lebar_terukur": round(max(widths), 1),
    })
    elements.append({
        "id": "badge-%d" % n, "jenis": "badge", "induk": card_id,
        "kartu": card_id, "bbox": [bxx, byy, bw, badge_h],
        "teks": status, "ukuran_font": badge_f,
        "lebar_terukur": round(measure(bf, status), 1),
    })


def load_daratan():
    cands = [os.path.join(_HERE, "data", "daratan.json"),
             os.environ.get("DARATAN_PATH", ""),
             os.path.join(os.path.expanduser("~"), "workspace",
                          "makefun-prompt-v12", "reference", "daratan.json")]
    for path in cands:
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)["benua"]
    sys.exit("daratan.json not found (tried data/daratan.json, "
             "DARATAN_PATH, pack reference)")


def draw_map(img, d, elements):
    x0, y0, w, h = MAP_BOX
    # Draw the map on its own layer and paste it: coastline polygons
    # (Antarctica reaches lat -90) would otherwise spill below the map
    # box onto the caption. The layer clips them exactly at the box.
    layer = Image.new("RGB", (w, h), SEA)
    dl = ImageDraw.Draw(layer)
    for benua in load_daratan():
        pts = []
        for lon, lat in benua["poligon"]:
            px, py = project(lon, lat)
            pts.append((px - x0, py - y0))
        if len(pts) >= 3:
            dl.polygon(pts, fill=LAND, outline=LAND_LINE)
    dl.rectangle([0, 0, w, h], outline=LAND_LINE)
    img.paste(layer, (x0, y0))
    # Title chip inside the map.
    chip = (x0 + 8, y0 + 8, 176, 18)
    d.rectangle([chip[0], chip[1], chip[0] + chip[2], chip[1] + chip[3]],
                fill=NAVY)
    f_chip = F(SANS_B, 11)
    d.text((chip[0] + chip[2] / 2.0, chip[1] + chip[3] / 2.0),
           "WHERE IT HAPPENED", font=f_chip, fill=WHITE, anchor="mm")
    # Pins.
    f_pin = F(SANS_B, 8)
    pins = []
    centres = []
    for pid, lon, lat, rx, ry, label, kelompok, cerita in PINS:
        # rx is absolute canvas x (map spans x 16..346); ry is relative
        # to the map box top.
        cx, cy = rx, y0 + ry
        centres.append((cx, cy))
        px, py = project(lon, lat)
        disp = math.hypot(cx - px, cy - py)
        assert disp <= 4.0, "pin %s displaced %.2f px" % (pid, disp)
        if kelompok:
            d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=WHITE,
                      width=2)
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=NAVY,
                  outline=WHITE, width=1)
        d.text((cx, cy), label, font=f_pin, fill=WHITE, anchor="mm")
        entry = {"id": pid, "bbox": [cx - 7, cy - 7, PIN_D, PIN_D],
                 "diameter": PIN_D, "lon": lon, "lat": lat,
                 "titik_proyeksi_px": [round(px, 2), round(py, 2)],
                 "digeser_px": round(disp, 2), "cerita": cerita}
        if kelompok:
            entry["kelompok"] = kelompok
        pins.append(entry)
    for i in range(len(centres)):
        for j in range(i + 1, len(centres)):
            dist = math.hypot(centres[i][0] - centres[j][0],
                              centres[i][1] - centres[j][1])
            assert dist >= PIN_D + 12, "pins too close: %.1f px" % dist
    elements.append({
        "id": "peta", "jenis": "peta", "bbox": list(MAP_BOX),
        "teks": "WHERE IT HAPPENED", "ukuran_font": 11,
        "lebar_terukur": round(measure(f_chip, "WHERE IT HAPPENED"), 1),
    })
    return pins


def draw_legend(d, elements):
    f = F(SANS_B, 10)
    items = [("CONFIRMED", STATUS["CONFIRMED"]),
             ("REPORTED", STATUS["REPORTED"]),
             ("CLAIM", STATUS["CLAIM"]),
             ("PENDING", STATUS["PENDING"])]
    total = 0
    for word, _ in items:
        total += 10 + measure(f, word) + 26
    total -= 26
    x = LEGEND_BOX[0] + (LEGEND_BOX[2] - total) / 2.0
    y = LEGEND_BOX[1] + 3
    for word, col in items:
        d.ellipse([x, y + 2, x + 6, y + 8], fill=col)
        text_top(d, (x + 10, y), word, f, INK)
        x += 10 + measure(f, word) + 26
    elements.append({
        "id": "legenda-daftar", "jenis": "label",
        "bbox": list(LEGEND_BOX),
        "teks": "CONFIRMED  REPORTED  CLAIM  PENDING",
        "ukuran_font": 10, "lebar_terukur": round(total, 1),
    })


def draw_lists(d, elements):
    # List floor (rubrik.md): 13 px on canvas.
    f_num = F(SANS_B, 13)
    f_txt = F(SANS, 13)
    cols = [LISTED[:14], LISTED[14:]]
    for ci, items in enumerate(cols):
        x = LIST_X[ci]
        max_w = 0
        texts = []
        for ri, (n, status, title) in enumerate(items):
            ry = LIST_Y + ri * ROW_H
            col = STATUS[status]
            d.ellipse([x + 2, ry + 6, x + 8, ry + 12], fill=col)
            num = "%d. " % n
            title = shorten(f_txt, title, LIST_W - 12 - measure(f_num, num))
            text_top(d, (x + 12, ry + 1), num, f_num, INK)
            text_top(d, (x + 12 + measure(f_num, num), ry + 1), title,
                     f_txt, INK)
            w = 12 + measure(f_num, num) + measure(f_txt, title)
            max_w = max(max_w, w)
            texts.append(num + title)
        elements.append({
            "id": "daftar-kiri" if ci == 0 else "daftar-kanan",
            "jenis": "daftar",
            "bbox": [x, LIST_Y, LIST_W, LIST_H],
            "teks": " / ".join(texts), "ukuran_font": 13,
            "lebar_terukur": round(max_w, 1),
        })


def draw_caption(d, elements):
    f = F(SANS, 10)
    widths = [measure(f, ln) for ln in CAPTION_LINES]
    assert max(widths) <= CAPTION_BOX[2], "caption line too wide"
    for i, line in enumerate(CAPTION_LINES):
        text_top(d, (CAPTION_BOX[0], CAPTION_BOX[1] + i * 12), line, f,
                 MUTED)
    elements.append({
        "id": "caption-peta", "jenis": "caption",
        "bbox": list(CAPTION_BOX), "teks": " / ".join(CAPTION_LINES),
        "ukuran_font": 10, "lebar_terukur": round(max(widths), 1),
    })


def draw_datecheck(d, elements):
    d.rectangle([MARGIN_X, Y_DATECHECK, MARGIN_X + CONTENT_W,
                 Y_DATECHECK + H_DATECHECK], fill=NAVY)
    f_t = F(SANS_B, 11)
    f_i = F(SANS, 11)
    items = " \u00b7 ".join(DATECHECK_ITEMS)
    text_top(d, (MARGIN_X + 12, Y_DATECHECK + 2), DATECHECK_TITLE, f_t,
             WHITE)
    text_top(d, (MARGIN_X + 12, Y_DATECHECK + 15), items, f_i,
             (220, 228, 240))
    w = max(measure(f_t, DATECHECK_TITLE), measure(f_i, items))
    assert w <= CONTENT_W - 24, "datecheck line too wide"
    elements.append({
        "id": "kotak-datecheck", "jenis": "datecheck",
        "bbox": [MARGIN_X, Y_DATECHECK, CONTENT_W, H_DATECHECK],
        "teks": DATECHECK_TITLE + " / " + items, "ukuran_font": 11,
        "lebar_terukur": round(w, 1),
    })


def draw_footer(d, elements):
    f = F(SANS, 8)
    w = measure(f, FOOTER)
    assert w <= CONTENT_W, "footer too wide"
    text_centre(d, MARGIN_X + CONTENT_W / 2.0, Y_FOOTER, FOOTER, f, MUTED)
    elements.append({
        "id": "footer", "jenis": "teks",
        "bbox": [MARGIN_X, Y_FOOTER, CONTENT_W, H_FOOTER],
        "teks": FOOTER, "ukuran_font": 8, "lebar_terukur": round(w, 1),
    })


def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    elements = []
    draw_masthead(d, elements)
    draw_numbers(d, elements)
    draw_regions(d, elements)
    draw_utc(d, elements)
    for i, story in enumerate(LEADS):
        draw_card(d, COL_X[i], Y_LEADS, "lead", story, elements)
    for i, story in enumerate(MEDIUM):
        row = i // 3
        col = i % 3
        draw_card(d, COL_X[col], Y_MED1 if row == 0 else Y_MED2,
                  "medium", story, elements)
    pins = draw_map(img, d, elements)
    draw_legend(d, elements)
    draw_lists(d, elements)
    draw_caption(d, elements)
    draw_datecheck(d, elements)
    draw_footer(d, elements)
    assert Y_FOOTER + H_FOOTER <= H, "layout overflows canvas"
    manifest = {
        "gambar": {"file": "entry.png", "lebar": W, "tinggi": H},
        "jenis_artefak": "news-image",
        "elemen": elements,
        "pin": pins,
        "peta": {"proyeksi": "linier", "map_box": list(MAP_BOX),
                 "lon_min": MAP_LON[0], "lon_max": MAP_LON[1],
                 "lat_min": MAP_LAT[0], "lat_max": MAP_LAT[1]},
        "irisan_diizinkan": [],
        "area": {"atas": [0, 0, 1024, 341], "tengah": [0, 341, 1024, 341],
                 "bawah": [0, 682, 1024, 342],
                 "peta": list(MAP_BOX),
                 "daftar": [358, Y_BOTTOM, 650, H_BOTTOM]},
    }
    return img, manifest


def main():
    out = os.environ.get("OUTPUT_PATH", "/output/entry.png")
    man_path = os.environ.get("MANIFEST_PATH", "manifest-verifikasi-V1.json")
    img, manifest = render()
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out, format="PNG")
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    with open(out, "rb") as fh:
        data = fh.read()
    print("wrote %s (%d bytes, sha256 %s)"
          % (out, len(data), hashlib.sha256(data).hexdigest()))
    print("manifest: %s (%d elemen, %d pin)"
          % (man_path, len(manifest["elemen"]), len(manifest["pin"])))


if __name__ == "__main__":
    main()
