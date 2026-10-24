#!/usr/bin/env python3
"""Draw the last year of GitHub contributions as an isometric city in the README's red theme.

Reads the public contribution graph (no token needed) and writes one SVG.

    python3 scripts/isocal.py <github user> <output.svg> [saved contributions.html]
"""
import re
import sys
import urllib.request
from datetime import date, timedelta
from html import escape

INK, DARK, CREAM, MUTE, RED = "#1A0B0E", "#2A1518", "#FFF1EA", "#8E6F72", "#FA374E"
LEVELS = ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"]
GREEN = "#39D353"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace"


def fetch(user, saved=None):
    if saved:
        html = open(saved, encoding="utf-8").read()
    else:
        req = urllib.request.Request(f"https://github.com/users/{user}/contributions", headers={"User-Agent": "isocal"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    counts = {}
    for m in re.finditer(r'<tool-tip[^>]*for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)<', html):
        n = re.match(r"\s*(\d+) contribution", m.group(2))
        counts[m.group(1)] = int(n.group(1)) if n else 0
    days = []
    for m in re.finditer(r"<td[^>]*data-date=\"([\d-]+)\"[^>]*>", html):
        tag = m.group(0)
        cid = re.search(r'id="([^"]+)"', tag).group(1)
        level = int(re.search(r'data-level="(\d)"', tag).group(1))
        days.append((date.fromisoformat(m.group(1)), level, counts.get(cid, 0)))
    return sorted(days)


def shade(hex_colour, f):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % (int(r * f), int(g * f), int(b * f))


def streaks(days):
    best = cur = 0
    for _, _, n in days:
        cur = cur + 1 if n else 0
        best = max(best, cur)
    current = 0
    for _, _, n in reversed(days):
        if n:
            current += 1
        elif current or _ == days[-1][0]:
            if current:
                break
    return current, best


def render(user, days):
    W, H, a = 960, 420, 8.5
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    cells = [((d - start).days // 7, (d - start).days % 7, lv, n) for d, lv, n in days]
    nonzero = sorted(n for *_, n in cells if n)
    cap = max(1, nonzero[int(len(nonzero) * .95)] if nonzero else 1)
    ox, oy = 404, 118
    cubes = []
    for w, dd, lv, n in sorted(cells, key=lambda c: (c[0] + c[1], c[0])):
        X, Y = ox + (w - dd) * a, oy + (w + dd) * a / 2
        h = 2 + (min(n, cap) / cap) ** .5 * 64
        top = LEVELS[lv]
        k = .92  # small gap between columns
        A, B = a * k, a / 2 * k
        cubes.append(
            f'<path d="M{X - A:.1f} {Y - h:.1f}L{X:.1f} {Y + B - h:.1f}V{Y + B:.1f}L{X - A:.1f} {Y:.1f}Z" fill="{shade(top, .62)}"/>'
            f'<path d="M{X:.1f} {Y + B - h:.1f}L{X + A:.1f} {Y - h:.1f}V{Y:.1f}L{X:.1f} {Y + B:.1f}Z" fill="{shade(top, .45)}"/>'
            f'<path d="M{X:.1f} {Y - B - h:.1f}L{X + A:.1f} {Y - h:.1f}L{X:.1f} {Y + B - h:.1f}L{X - A:.1f} {Y - h:.1f}Z" fill="{top}"/>')
    total = sum(n for *_, n in cells)
    best_day = max(days, key=lambda x: x[2])
    current, longest = streaks(days)
    stats = [(f"{total:,}", "contributions, last year"), (str(best_day[2]), f"best day · {best_day[0]:%b %d}"),
             (f"{current}d", "current streak"), (f"{longest}d", "longest streak")]
    s = []
    s.append(f'<text x="32" y="58" fill="{CREAM}" font-family="{SANS}" font-size="30" font-weight="800" letter-spacing="-1">Commit log</text>')
    s.append(f'<text x="34" y="82" fill="{MUTE}" font-family="{MONO}" font-size="11">@{escape(user)} · {days[0][0]:%b %Y} → {days[-1][0]:%b %Y}</text>')
    for i, (big, small) in enumerate(stats):
        y = 140 + i * 62
        s.append(f'<path d="M32 {y - 34}H200" stroke="{CREAM}" stroke-opacity=".2"/>')
        s.append(f'<text x="32" y="{y}" fill="{CREAM if i else GREEN}" font-family="{SANS}" font-size="28" font-weight="800">{big}</text>')
        s.append(f'<text x="32" y="{y + 17}" fill="{MUTE}" font-family="{SANS}" font-size="10.5" font-weight="700" letter-spacing="1.5">{escape(small.upper())}</text>')
    s.append(f'<text x="{W - 210}" y="{H - 26}" fill="{MUTE}" font-family="{MONO}" font-size="10.5">less</text>')
    for i, c in enumerate(LEVELS):
        s.append(f'<rect x="{W - 176 + i * 22}" y="{H - 36}" width="16" height="12" fill="{c}"/>')
    s.append(f'<text x="{W - 32}" y="{H - 26}" fill="{MUTE}" font-family="{MONO}" font-size="10.5" text-anchor="end">more</text>')
    for i in range(4):
        s.append(f'<path d="M{32 + i * 20} {H - 24}l7 -14h10l-7 14z" fill="{GREEN}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="Isometric contribution calendar for {escape(user)}: {total} contributions in the last year">'
            f'<rect width="{W}" height="{H}" rx="8" fill="{INK}"/>{"".join(cubes)}{"".join(s)}</svg>\n')


if __name__ == "__main__":
    user, out = sys.argv[1], sys.argv[2]
    days = fetch(user, sys.argv[3] if len(sys.argv) > 3 else None)
    if not days:
        sys.exit("no contribution data found")
    with open(out, "w") as f:
        f.write(render(user, days))
    print(f"wrote {out}: {len(days)} days")
