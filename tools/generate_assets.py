#!/usr/bin/env python3
"""Generate the 8-bit profile assets: assets/screen.svg + link buttons.

Pixel font and sprites live in tools/pixeldata.json (5x5 glyph bitmaps).
Star counts are fetched from the GitHub API with --fetch, otherwise the
hardcoded values below are used.

Usage:  python3 tools/generate_assets.py [--fetch]
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "tools", "pixeldata.json")))
FONT = {ch: [tuple(cell) for cell in cells] for ch, cells in DATA["FONT"].items()}

# palette
BG = "#0a0c10"
BORDER = "#1c2733"
GREEN = "#00ff41"
CYAN = "#00e5ff"
PINK = "#ff2079"
GOLD = "#ffd23f"
WHITE = "#ffffff"
GRAY = "#8b949e"

# (menu label, skill tag, stars) — refresh stars with --fetch
REPOS = [
    ("TONKATSU BOX", "FLUTTER", 359, "tonkatsu_box"),
    ("CO-OP RETRO GAMES", "NES·SNES·RA", 10, "co-op-retro-games"),
    ("TONKATSU COLLECTIONS", "PYTHON", 5, "tonkatsu-collections"),
    ("ODIN COMPATIBILITY", "ODIN 2", 0, "odin-compatibility"),
]

W, H = 830, 512
CX = W // 2
TICKER = "RETRO GAMER + MAKER · I BUILD STUFF FOR THE HOBBY · "


def fetch_stars():
    req = urllib.request.Request(
        "https://api.github.com/users/hacan359/repos?per_page=100",
        headers={"User-Agent": "hacan359-profile-gen"},
    )
    repos = json.load(urllib.request.urlopen(req))
    stars = {r["name"]: r["stargazers_count"] for r in repos}
    global REPOS
    REPOS = [(label, skill, stars.get(name, n), name) for label, skill, n, name in REPOS]
    return sum(stars.values())


def text_rects(s, x, y, px, fill, pitch=None):
    pitch = pitch or px * 6
    out = []
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        gx = x + i * pitch
        cells = "".join(
            f'<rect x="{gx + c * px}" y="{y + r * px}" width="{px}" height="{px}" fill="{fill}"/>'
            for r, c in FONT[ch]
        )
        out.append(f"<g>{cells}</g>")
    return "\n".join(out)


def text_width(s, px, pitch=None):
    pitch = pitch or px * 6
    return (len(s) - 1) * pitch + 5 * px


def centered_text(s, cx, y, px, fill, pitch=None):
    return text_rects(s, cx - text_width(s, px, pitch) // 2, y, px, fill, pitch)


def sprite_rects(cells, x, y, px, fill):
    body = "".join(
        f'<rect x="{c * px}" y="{r * px}" width="{px}" height="{px}" fill="{fill}"/>'
        for c, r in cells
    )
    return body, x, y


STAR = [(2, 0), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
        (1, 3), (2, 3), (3, 3), (1, 4), (3, 4)]  # (col,row)
HEART = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2),
         (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 0), (4, 1),
         (4, 2), (4, 3), (4, 4), (5, 0), (5, 1), (5, 2), (5, 3), (6, 1), (6, 2)]
ARROW = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 2), (1, 3),
         (2, 1), (2, 2), (2, 3), (3, 2), (4, 2)]  # (col,row)
INFINITY = [(1, 0), (2, 0), (5, 0), (6, 0), (0, 1), (3, 1), (4, 1), (7, 1),
            (0, 2), (3, 2), (4, 2), (7, 2), (1, 3), (2, 3), (5, 3), (6, 3)]  # (col,row), 8 cols wide


def flat_sprite(cells, x, y, px, fill):
    return "".join(
        f'<rect x="{x + c * px}" y="{y + r * px}" width="{px}" height="{px}" fill="{fill}"/>'
        for c, r in cells
    )


def build_screen(total_stars):
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    p.append(f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>')
    p.append(f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="10" fill="none" stroke="{BORDER}" stroke-width="2"/>')

    # top bar: hearts (lives) | HI-SCORE ★total | 2UP
    for i in range(3):
        p.append(f"<g>{flat_sprite(HEART, 40 + i * 27, 21, 3, PINK)}</g>")
    p.append(text_rects("2UP", W - 40 - text_width("2UP", 3), 22, 3, WHITE))
    p.append(centered_text("HI-SCORE", CX, 22, 3, WHITE))
    score = f"{total_stars:04d}"
    score_w = 15 + 7 + text_width(score, 3)  # star + gap + digits
    sx = CX - score_w // 2
    p.append(f"<g>{flat_sprite(STAR, sx, 44, 3, GOLD)}</g>")
    p.append(text_rects(score, sx + 22, 44, 3, GOLD))

    # invader row: centered, bobbing
    inv_specs = [
        (DATA["INVADER_A"], GREEN, "2.0s"),
        (DATA["INVADER_B"], CYAN, "2.3s"),
        (DATA["INVADER_A"], PINK, "2.6s"),
        (DATA["INVADER_B"], CYAN, "2.9s"),
        (DATA["INVADER_A"], GREEN, "3.2s"),
    ]
    for i, (cells, fill, dur) in enumerate(inv_specs):
        cells = [tuple(c) for c in cells]
        w = (max(c for c, r in cells) + 1) * 4
        x = CX - 200 + i * 100 - w // 2
        body = "".join(
            f'<rect x="{c * 4}" y="{r * 4}" width="4" height="4" fill="{fill}"/>'
            for c, r in cells
        )
        anim = (f'<animateTransform attributeName="transform" type="translate" '
                f'values="{x},80;{x},74;{x},80" dur="{dur}" repeatCount="indefinite"/>')
        p.append(f'<g transform="translate({x},80)">{body}{anim}</g>')

    # logo HACAN359 with glow (same font at 10px)
    logo_x = CX - text_width("HACAN359", 10, 60) // 2
    logo = text_rects("HACAN359", logo_x, 140, 10, GREEN, 60)
    p.append('<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter></defs>')
    p.append(f'<g filter="url(#glow)" opacity="0.7"><g>{logo}</g></g>')
    p.append(f"<g>{logo}</g>")

    # marquee ticker between logo and heading
    tw = len(TICKER) * 12  # full char-grid width so the loop joins seamlessly
    copy1 = text_rects(TICKER, 0, 0, 2, GREEN, 12)
    copy2 = f'<g transform="translate({tw},0)">{text_rects(TICKER, 0, 0, 2, GREEN, 12)}</g>'
    dur = round(tw / 30, 1)
    p.append(
        '<defs><clipPath id="tickerclip"><rect x="40" y="210" width="750" height="14"/></clipPath></defs>'
        f'<g clip-path="url(#tickerclip)"><g transform="translate(40,212)">{copy1}{copy2}'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="40,212;{40 - tw},212" dur="{dur}s" repeatCount="indefinite"/></g></g>'
    )

    # heading
    p.append(centered_text("SELECT LEVEL", CX, 266, 4, CYAN))

    # menu rows: name | skill | ★stars — block centered as a whole
    rows_y = [308, 340, 372, 404]
    count_w = max(text_width(str(n), 3) for _, _, n, _ in REPOS)
    block_w = 588 + count_w  # arrow..count-column right edge
    mx = CX - block_w // 2
    for (label, skill, stars, _), y in zip(REPOS, rows_y):
        p.append(text_rects(label, mx + 40, y, 3, WHITE))
        p.append(text_rects(skill, mx + 424, y + 2, 2, GRAY))
        p.append(f"<g>{flat_sprite(STAR, mx + 566, y, 3, GOLD)}</g>")
        p.append(text_rects(str(stars), mx + 588, y, 3, GOLD))

    # cursor arrow cycling through rows
    arrow_body = "".join(
        f'<rect x="{c * 3}" y="{r * 3}" width="3" height="3" fill="{GREEN}"/>'
        for c, r in ARROW
    )
    stops = ";".join(f"{mx},{y}" for y in rows_y)
    p.append(
        f'<g transform="translate({mx},{rows_y[0]})">{arrow_body}'
        f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
        f'values="{stops}" keyTimes="0;0.25;0.5;0.75" dur="4.8s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0.25;1" dur="0.6s" repeatCount="indefinite"/></g>'
    )

    # PRESS START (blinking)
    ps = centered_text("PRESS START", CX, 446, 4, GOLD)
    p.append(
        f"<g><g>{ps}</g>"
        '<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.55;0.6;0.95;1" '
        'dur="1.4s" repeatCount="indefinite"/></g>'
    )

    # CREDIT ∞ (right-aligned where CREDIT 99 used to end)
    p.append(text_rects("CREDIT", 643, 478, 3, WHITE))
    p.append(f"<g>{flat_sprite(INFINITY, 766, 480, 3, WHITE)}</g>")

    # scanlines
    p.append('<defs><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000000" opacity="0.18"/></pattern></defs>')
    p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#scan)"/>')
    p.append("</svg>")
    return "\n".join(p)


def build_button(label, color, blink=False, boxed=True):
    px, pitch, h, pad = 2, 12, 36, 16
    tw = text_width(label, px, pitch)
    w = tw + pad * 2
    body = text_rects(label, pad, (h - 10) // 2, px, color, pitch)
    if blink:
        body = (f"<g>{body}"
                '<animate attributeName="opacity" values="1;1;0.15;1" keyTimes="0;0.7;0.85;1" '
                'dur="1.6s" repeatCount="indefinite"/></g>')
    box = ""
    if boxed:
        box = (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="8" '
               f'fill="{BG}" stroke="{BORDER}" stroke-width="2"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f"{box}{body}</svg>")


def main():
    total = fetch_stars() if "--fetch" in sys.argv else sum(n for _, _, n, _ in REPOS)
    assets = os.path.join(ROOT, "assets")
    open(os.path.join(assets, "screen.svg"), "w").write(build_screen(total))

    buttons = {
        "btn-tonkatsu.svg": ("TONKATSU BOX", GREEN, False, True),
        "btn-coop.svg": ("CO-OP RETRO GAMES", GREEN, False, True),
        "btn-collections.svg": ("COLLECTIONS", GREEN, False, True),
        "btn-odin.svg": ("ODIN COMPAT", GREEN, False, True),
        "lbl-insert-coin.svg": ("INSERT COIN", GOLD, True, False),
        "btn-x.svg": ("X", WHITE, False, True),
        "btn-discord.svg": ("DISCORD", CYAN, False, True),
    }
    for fname, (label, color, blink, boxed) in buttons.items():
        open(os.path.join(assets, fname), "w").write(build_button(label, color, blink, boxed))
    print(f"generated screen.svg (HI-SCORE {total:04d}) + {len(buttons)} buttons")


if __name__ == "__main__":
    main()
