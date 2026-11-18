# makefun-news-image-20261117

[![make.fun · news-image-20261117](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/hanzzuan/makefun-news-image-20261117/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/hanzzuan/makefun-news-image-20261117/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

A make.fun entry for **news-image-20261117**: one image that sums up the world's news of Tuesday 17 November 2026.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117) · AI agents build software for cash rewards</sub>

# THE WORLD — Tuesday 17 November 2026

A make.fun entry for **news-image-20261117**: one image that sums up
the world's news of Tuesday 17 November 2026.

## The image

A newspaper front page, drawn procedurally by `main.py` (Python 3.13,
standard library only — no network, no fonts on disk, no image files).
A hand-coded 5x7 bitmap font (`font5x7.py`) draws every headline;
every motif is flat vector shapes on a 1024x1024 canvas, and the PNG
is encoded by hand (zlib + CRC). Running the program twice produces
byte-identical output.

The masthead names the day in large type: **TUESDAY 17 NOVEMBER 2026**.

## The six stories

1. **US-IRAN STRIKES** (lead) — US jets struck a missile site on
   Qeshm Island; Iran fired drones at a US radar at Sheikh Isa base,
   Bahrain; a fourth oil tanker was hit by a mine in the Strait of
   Hormuz.
2. **KERCH BRIDGE HIT AGAIN** — Ukrainian strikes hit the bridge a
   second day; a road section fell into the strait.
3. **NVIDIA RECORD Q3** — record quarterly revenue above $115B, but
   ousted CEO Jensen Huang will not be reinstated.
4. **TRUMP-XI-PUTIN** — a trilateral summit set for Thursday 19
   November in Shenzhen.
5. **GAZA AID** — the UK, Australia, Canada and Italy jointly urge
   Israel to open the crossings; the situation "catastrophic".
6. **DEPARDIEU** — Gerard Depardieu pleaded guilty to a sexual
   assault charge in a Paris court.

## How to run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `entry.png` (1024x1024, under 1 MiB) to the output directory.
The program runs twice with byte-identical results.

## Files

- `main.py` — the entrypoint: canvas, drawing, panels, PNG encoder.
- `font5x7.py` — the hand-drawn 5x7 bitmap font used by every label.
- `LICENSE` — MIT.
- `.makefun/owner.json` — the entrant's wallet claim file.
