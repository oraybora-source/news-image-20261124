#!/usr/bin/env python3
"""news-image-20261124 — entrypoint: entry uji kedua skill Lapis 1.

Mereproduksi entry.png (1024x1024, sha256
60c4205f8dde2e237094b0962f32b8ca8b789d46be9dd47ab3d7c9d6b670dc56)
secara deterministik: dua run menghasilkan byte yang identik.

Cara kerja: entry ini dirakit ffmpeg (overlay + drawbox + drawtext) oleh
compose.py, tanpa PIL. compose.py aslinya menulis BASE absolut folder uji
tempat ia dibangun; main.py ini menjalankan ulang compose.py dengan SATU
baris itu diarahkan ke folder repo ini (ROOT), selebihnya byte-identik —
supaya entrypoint bisa jalan dari checkout mana pun, bukan hanya dari
folder uji aslinya. Tidak ada jaringan, jam, atau acak di build ini.

Pakai:
  python3 main.py                  # tulis entry.png di folder ini
  python3 main.py --out <path>     # tulis ke path lain
  python3 main.py --run2 <path>    # jalankan 2x, bandingkan sha (uji determinisme)

Dependensi: python3 stdlib + ffmpeg di PATH + font Noto (Serif/Sans) di
/usr/share/fonts/truetype/noto/. Aset gambar di aset/ (7 ilustrasi Muse
image + peta.png). Peta dibuat map.py dari data/peta-ne110m.json
(Natural Earth 1:110m, domain publik) — peta.png yang dipakai sudah ada
di aset/, map.py disertakan untuk keterlacakan.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EXPECTED_SHA = "60c4205f8dde2e237094b0962f32b8ca8b789d46be9dd47ab3d7c9d6b670dc56"
BASE_LINE = ('BASE = "/home/hatch/workspace/makefun/news-image-20261124/'
             'V1/kerja-uji-skill-lapis1-v2"')


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main(argv):
    out = os.path.join(ROOT, "entry.png")
    rest = []
    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    compose_path = os.path.join(ROOT, "compose.py")
    src = open(compose_path, encoding="utf-8").read()
    if BASE_LINE not in src:
        raise SystemExit("compose.py berubah: baris BASE yang diharapkan "
                         "tidak ditemukan — entrypoint menolak jalan.")
    # Satu-satunya perubahan terhadap compose.py: BASE menunjuk folder repo.
    src = src.replace(BASE_LINE, "BASE = " + repr(ROOT), 1)
    ns = {"__name__": "__main__", "__file__": compose_path}
    sys.argv = ["compose.py", "--layout", "A", "--out", out] + rest
    exec(compile(src, compose_path, "exec"), ns)
    got = sha256(out)
    print("main.py: entry sha", got)
    if got != EXPECTED_SHA:
        raise SystemExit("SHA TIDAK COCOK dengan entry uji kedua "
                         f"(diharapkan {EXPECTED_SHA})")
    print("main.py: SHA COCOK dengan entry uji kedua.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
