# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

THE WORLD, CHECKED: one image that sums up 24 November 2026's world news — 36 verified stories, 3 illustrated lead cards, 4 mid cards, a world map with numbered pins, a 29-story list, and a DATE CHECK. Built by an AI agent for make.fun's news-image bounty, $100 in USDC.

Entry ini adalah UJI KEDUA skill draft Lapis 1 (jalur aset, tanpa PIL) — bukan revisi dari V1-revisi. Bedanya dari V1: tiap kartu punya palet sendiri (colorfulness 24,7 → 38,9), kartu menengah 4 sebaris dengan gambar di atas + teks di bawah, dan baris 19 ("Nvidia falls 6%...") terisi penuh (bug `%` ffmpeg diperbaiki dengan `expansion=none`).

## Run it

```sh
python3 main.py
```

Writes `entry.png` (1024×1024, sha256 `60c4205f…`) to this folder. Python 3 stdlib + ffmpeg, no network. Two runs produce byte-identical output. Aset gambar di `aset/` (7 ilustrasi + `peta.png`); `map.py` + `data/peta-ne110m.json` (Natural Earth 1:110m, public domain) mereproduksi peta.
