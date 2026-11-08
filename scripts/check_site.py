#!/usr/bin/env python3
"""Browser checks on the built site (run after `python build.py [--pdf]`).
overflow at 360/390px · phone redirect · timeline controls · Thai/English text · no TODO · One Page PDF is 1 page."""
import functools, http.server, os, re, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); h.log_message = lambda *a: None
LIVE = os.environ.get("SITE_URL")          # e.g. SITE_URL=https://user.github.io/profiles/  -> test the deployed site
if LIVE:
    B = LIVE if LIVE.endswith("/") else LIVE + "/"
else:
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    B = f"http://127.0.0.1:{srv.server_address[1]}/"
THAI = re.compile(r"[฀-๿]")
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

PAGES = ["", "en/", "m/", "m/work/", "m/resume/", "m/contact/", "en/m/work/", "profile/", "profile/full/", "en/profile/", "en/profile/full/"]
with sync_playwright() as p:
    exe = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    b = p.chromium.launch(executable_path=exe) if os.path.exists(exe) else p.chromium.launch()
    errs = []
    # 1) overflow + TODO + console errors, light and dark
    for w in (360, 390):
        for scheme in ("light", "dark"):
            ctx = b.new_context(viewport={"width": w, "height": 800}, color_scheme=scheme)
            ctx.add_init_script("localStorage.setItem('fullweb','1')")
            for u in PAGES:
                pg = ctx.new_page(); pg.on("pageerror", lambda e, u=u: errs.append(f"{u}: {e}"))
                pg.goto(B + u); pg.wait_for_timeout(150)
                over = pg.evaluate("document.documentElement.scrollWidth>innerWidth+1")
                if over: check(False, f"overflow {w}px {scheme} /{u}")
                if w == 390 and scheme == "light" and "TODO" in pg.inner_text("body"):
                    check(False, f"TODO text visible on /{u}")
                pg.close()
            ctx.close()
    check(True, f"no horizontal overflow on {len(PAGES)} pages x 2 widths x 2 themes") if not [f for f in fails if f.startswith("overflow")] else None
    check(not errs, "no JS errors" + (f": {errs[:2]}" if errs else ""))
    check(not [f for f in fails if f.startswith("TODO")], "no TODO placeholder text visible")
    # 2) phone redirect
    for u, dest in (("", "m/"), ("en/", "en/m/")):
        pg = b.new_page(viewport={"width": 390, "height": 800}); pg.goto(B + u); pg.wait_for_timeout(300)
        check(pg.url == B + dest, f"phone /{u} -> /{dest}")
        pg.close()
    # 3) timeline controls (desktop)
    pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.goto(B); pg.wait_for_timeout(300)
    n_items = pg.locator("ol.tl > li[data-kind]").count(); n_det = pg.locator("ol.tl details").count()
    check(n_items >= 9 and pg.locator("ol.eras li").count() == 5, f"timeline: {n_items} cards, 5 era chips")
    tiny = pg.evaluate("[...document.querySelectorAll('ol.tl > li.tl-item')].filter(li=>{const r=li.getBoundingClientRect();return r.width<200||r.height<30}).map(li=>li.id)")
    check(not tiny, f"every timeline card has a real size (collapsed: {tiny})")
    check(pg.locator("ol.tl details[open]").count() == 1, "only the current role is open by default")
    pg.click("[data-act=expand]"); check(pg.locator("ol.tl details[open]").count() == n_det, "expand all")
    pg.click("[data-act=collapse]"); check(pg.locator("ol.tl details[open]").count() == 0, "collapse all")
    first = pg.evaluate("document.querySelector('ol.tl > li:not([hidden])').id||''")
    pg.click("[data-act=order]"); pg.wait_for_timeout(100)
    top_after = pg.evaluate("""()=>{const l=[...document.querySelectorAll('ol.tl > li')].filter(x=>x.offsetParent);return l.sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top)[0].id||'(milestone)'}""")
    check(top_after != first, "order toggle reverses the timeline")
    pg.click("[data-act=order]")
    pg.click("[data-act=filter][data-tag=ai]"); pg.wait_for_timeout(100)
    vis = pg.evaluate("[...document.querySelectorAll('ol.tl > li')].filter(x=>!x.hidden).length")
    check(0 < vis < n_items, f"filter 'ai' shows {vis}/{n_items}")
    pg.click("[data-act=filter][data-tag='']")
    target = pg.get_attribute("ol.eras li:nth-child(2) a", "href")
    pg.click("ol.eras li:nth-child(2) a"); pg.wait_for_timeout(300)
    check(pg.evaluate("(id)=>{const d=document.getElementById(id).querySelector('details');return !d||d.open}", target[1:]), "era chip opens its card")
    pg.close()
    # 3b) hero: one paragraph, no current position; technology timeline matrix and direction switch
    pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.goto(B); pg.wait_for_timeout(300)
    htxt = pg.inner_text(".hero")
    check("Data & AI Lead" not in htxt and "Team Lead" not in htxt and "หัวหน้าทีม Data" not in htxt, "hero does not name the current position")
    check(pg.locator(".hero > div:first-child p:not(.role)").count() == 1, "hero tells the story in one paragraph")
    check(pg.locator(".wheel a").count() == 7, "wheel shows 7 interest areas")
    check("Creativity" in (pg.text_content(".wheel") or "") and "แกนกลาง" not in (pg.text_content(".wheel") or ""), "wheel centre reads Creativity with no sub-caption")
    check(pg.locator("#stack .sm-row").count() >= 7 and pg.locator("#stack .sm-t").count() >= 30, "technology timeline renders (rows and technologies)")
    first = lambda: pg.evaluate("[...document.querySelectorAll('#stack .sm-cell.h')].sort((a,b)=>a.getBoundingClientRect().left-b.getBoundingClientRect().left)[0].querySelector('b').textContent")
    before = first()
    pg.click("#stack [data-act=sm-dir][data-dir=fwd]"); pg.wait_for_timeout(100)
    after = first()
    check(before == "Data & AI" and after != before, f"direction switch reverses the technology timeline ('{before}' first, then '{after}')")
    pg.close()
    pm = b.new_page(viewport={"width": 390, "height": 844}); pm.add_init_script("localStorage.setItem('fullweb','1')"); pm.goto(B); pm.wait_for_timeout(300)
    check(pm.evaluate("getComputedStyle(document.querySelector('#stack .sm-chart')).display") == "none" and pm.evaluate("getComputedStyle(document.querySelector('#stack .sm-list')).display") != "none", "phone: technology timeline switches to the stage list")
    pm.close()
    # 4) language content
    th = b.new_page(); th.goto(B + "profile/full/"); en = b.new_page(); en.goto(B + "en/profile/full/")
    tb = th.inner_text("ol.tl .body li") ; eb = en.inner_text("ol.tl .body")
    check(bool(THAI.search(tb)), "Thai page: timeline bullets are Thai")
    check(not THAI.search(eb), "English page: timeline bullets have no Thai")
    check(th.evaluate("document.documentElement.lang") == "th" and en.evaluate("document.documentElement.lang") == "en", "html lang th / en")
    # 5) MOCK labelling: banner on every page type, a label on every mock block, machine-readable flag
    for u in ("", "en/", "m/", "m/work/", "profile/", "profile/full/", "en/profile/"):
        pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.goto(B + u)
        check(pg.locator(".mockbar").count() == 1, f"MOCK banner on /{u}")
        blocks = pg.evaluate("[...document.querySelectorAll('.mock-block')].filter(x=>!x.querySelector('.badge.mock')).length")
        check(blocks == 0, f"every mock block on /{u} carries a MOCK label")
        pg.close()
    import json, urllib.request
    doc = json.load(urllib.request.urlopen(B + "profile.json"))
    check(doc.get("contains_mock") is True and "NOT facts" in doc.get("mock_note", ""), "profile.json flags contains_mock")
    check("MOCK" in urllib.request.urlopen(B + "llms.txt").read().decode(), "llms.txt carries the MOCK notice")
    # 6) identity: wheel packets, reduced motion, favicon
    pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.goto(B)
    check(pg.locator(".wheel .orbit").count() == 7, "wheel has 7 orbiting packets")
    check(pg.evaluate("getComputedStyle(document.querySelector('.wheel .orbit')).animationName") != "none", "wheel animates by default")
    pg.close()
    rm = b.new_context(reduced_motion="reduce").new_page(); rm.goto(B)
    check(rm.evaluate("getComputedStyle(document.querySelector('.wheel .orbit')).animationName") == "none", "reduced motion: wheel is static")
    check(urllib.request.urlopen(B + "assets/favicon.svg").status == 200, "favicon.svg served")
    b.close()
# 5) One Page PDF (only if built with --pdf)
pdf = os.path.join(ROOT, "profile", "one-page.pdf")
if not LIVE and os.path.exists(pdf):
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", open(pdf, "rb").read()))
    check(pages == 1, f"One Page PDF is {pages} page(s)")
if LIVE:
    import urllib.request
    for path in ("profile/one-page.pdf", "profile/full.pdf", "en/profile/one-page.pdf", "default/resume.pdf", "profile.json", "llms.txt", "assets/favicon.svg"):
        r = urllib.request.urlopen(B + path); check(r.status == 200, f"live GET {path} -> {r.status}")
print("FAILED" if fails else "ALL PASSED"); sys.exit(1 if fails else 0)
