#!/usr/bin/env python3
"""news-image-20261124 — entrypoint: entry V2 skill Lapis 1 v5.3 (revisi).

Mereproduksi entry.png (1024x1024, sha256
ffa566c75f5240b24f579c565ad3d4f659db8b9ee3b30b09a5dae58bdb1b5073)
secara deterministik: dua run menghasilkan byte yang identik.

Cara kerja: entry ini dirakit ffmpeg (overlay + drawbox + drawtext) oleh
compose6.py, tanpa PIL. compose6.py aslinya menulis BASE absolut folder V2
tempat ia dibangun; main.py ini menjalankan ulang compose6.py dengan SATU
baris itu diarahkan ke folder repo ini (ROOT), selebihnya byte-identik —
supaya entrypoint bisa jalan dari checkout mana pun, bukan hanya dari
folder V2 aslinya. Tidak ada jaringan, jam, atau acak di build ini.

Pakai:
  python3 main.py                  # tulis entry.png di folder ini
  python3 main.py --out <path>     # tulis ke path lain

Dependensi: python3 stdlib + ffmpeg di PATH + font Noto (Serif/Sans) di
/usr/share/fonts/truetype/noto/. Aset gambar di aset/ (11 ilustrasi Muse
image + peta.png). Peta dibuat map6.py dari data/peta-ne110m.json
(Natural Earth 1:110m, domain publik) — peta.png yang dipakai sudah ada
di aset/, map6.py disertakan untuk keterlacakan.
"""
import hashlib
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EXPECTED_SHA = "ffa566c75f5240b24f579c565ad3d4f659db8b9ee3b30b09a5dae58bdb1b5073"
BASE_LINE = ('BASE = "/home/hatch/workspace/makefun/news-image-20261124/'
             'V2/kerja-v2-skill-v5-3"')


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main(argv):
    out = os.path.join(ROOT, "entry.png")
    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]
            i += 2
        else:
            i += 1
    compose_path = os.path.join(ROOT, "compose6.py")
    src = open(compose_path, encoding="utf-8").read()
    if BASE_LINE not in src:
        raise SystemExit("compose6.py berubah: baris BASE yang diharapkan "
                         "tidak ditemukan — entrypoint menolak jalan.")
    # Satu-satunya perubahan terhadap compose6.py: BASE menunjuk folder repo.
    src = src.replace(BASE_LINE, "BASE = " + repr(ROOT), 1)
    ns = {"__name__": "__main__", "__file__": compose_path}
    sys.argv = ["compose6.py", "entry"]
    exec(compile(src, compose_path, "exec"), ns)
    built = os.path.join(ROOT, "entry.png")
    if os.path.abspath(out) != os.path.abspath(built):
        shutil.copyfile(built, out)
    got = sha256(out)
    print("main.py: entry sha", got)
    if got != EXPECTED_SHA:
        raise SystemExit("SHA TIDAK COCOK dengan entry V2 revisi "
                         f"(diharapkan {EXPECTED_SHA})")
    print("main.py: SHA COCOK dengan entry V2 revisi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
