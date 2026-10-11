#!/usr/bin/env python3
"""WCAG contrast of the design tokens in static/base.css (light + dark). Text >= 4.5:1, graphics >= 3:1.
Also checks text over the hero colour wash (HERO_WASH must match the % used in static/desktop.css)."""
import os, re, sys
HERO_WASH = 0.09
css = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "base.css"), encoding="utf-8").read()
norm = lambda h: "#" + ("".join(c * 2 for c in h.lstrip("#")) if len(h.lstrip("#")) == 3 else h.lstrip("#"))
toks = lambda blk: {k: norm(v) for k, v in re.findall(r"--([\w-]+):(#[0-9a-fA-F]{3,6})\b", blk)}
LIGHT = toks(re.search(r":root\{(.*?)color-scheme:light", css, re.S).group(1))
DARK = {**LIGHT, **toks(re.search(r"prefers-color-scheme:dark\)\{:root\{(.*?)color-scheme:dark", css, re.S).group(1))}
rgb = lambda h: [int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
def lum(h):
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = [f(x / 255) for x in rgb(h)]
    return .2126 * r + .7152 * g + .0722 * b
def ratio(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + .05) / (lb + .05)
def blend(fg, bg, a):
    return "#%02x%02x%02x" % tuple(round(f * a + g * (1 - a)) for f, g in zip(rgb(fg), rgb(bg)))
bad = []
for name, t in (("light", LIGHT), ("dark", DARK)):
    text = [("ink", "bg"), ("ink", "paper"), ("ink2", "bg"), ("ink2", "paper"), ("accent", "bg"), ("accent", "accent-bg"), ("bg", "ink")] + [("ink", f"b{i}") for i in range(1, 8)]
    graphics = [(f"c{i}", "paper") for i in range(1, 8)] + [(m, bgk) for m in ("bronze", "silver", "gold") for bgk in ("paper", "bg")]
    for fg, bg in text:
        r = ratio(t[fg], t[bg]); ok = r >= 4.5
        if not ok: bad.append(f"{name}: text {fg} on {bg} = {r:.2f}")
    for fg, bg in graphics:
        r = ratio(t[fg], t[bg]); ok = r >= 3
        if not ok: bad.append(f"{name}: graphic {fg} on {bg} = {r:.2f}")
    for i in range(1, 8):                       # hero wash: worst case = full alpha of one hue behind the text
        wash = blend(t[f"c{i}"], t["bg"], HERO_WASH)
        for fg in ("ink", "ink2"):
            r = ratio(t[fg], wash)
            if r < 4.5: bad.append(f"{name}: {fg} on hero wash c{i} = {r:.2f}")
    print(f"{name}: {len(text)} text pairs, {len(graphics)} graphic pairs, 12 hero-wash cases checked")
for m in bad: print("FAIL", m)
print("FAILED" if bad else "ALL PASSED"); sys.exit(1 if bad else 0)
