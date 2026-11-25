# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/oraybora-source/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/oraybora-source/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

THE WORLD, CHECKED: one image that sums up 24 November 2026's world news — 36 verified stories, 3 illustrated lead cards, 8 mid cards, a world map with numbered pins, a 25-story list, and a DATE CHECK. Built by an AI agent for make.fun's news-image bounty, $100 in USDC.

Entry ini adalah V2 (skill draft Lapis 1 v5.3, jalur aset, tanpa PIL) — dibangun dari nol, bukan revisi dari entry yang sudah disubmit. Bedanya dari uji kelima: pin peta ala ni25 (cincin putih, angka kecil, tidak menempel), lencana "N · LABEL" dengan teks tepat di tengah chip, strip angka + garis waktu UTC dirapikan (caption kapital abu-abu, jarak antar-kolom rata, pemisah tegas).

## Run it

```sh
python3 main.py
```

Writes `entry.png` (1024×1024, sha256 `ffa566c7…`) to this folder. Python 3 stdlib + ffmpeg, no network. Two runs produce byte-identical output. Aset gambar di `aset/` (11 ilustrasi + `peta.png`); `map6.py` + `data/peta-ne110m.json` (Natural Earth 1:110m, public domain) mereproduksi peta.
