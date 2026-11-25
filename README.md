# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

THE WORLD, CHECKED: one image that sums up 24 November 2026's world news — 36 verified stories, 3 illustrated lead cards, 6 mid cards, a world map with numbered pins, a 27-story list, and a DATE CHECK. Built by an AI agent for make.fun's news-image bounty, $100 in USDC.

## Run it

```sh
python3 main.py
```

Writes `entry.png` (1024×1024) to the current directory. Python 3.13, Pillow only, no network. The program reads `data/daratan.json` (land polygons) from its own folder. Two runs produce byte-identical output.
