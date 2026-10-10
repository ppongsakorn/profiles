#!/usr/bin/env python3
"""Browser checks on the built site (run after `python build.py [--pdf]`).
overflow at 360/390px · phone redirect · timeline controls · Thai/English text · no TODO · One Page PDF is 1 page."""
import functools, http.server, os, re, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); h.log_message = lambda *a: None
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
    # 4) language content
    th = b.new_page(); th.goto(B + "profile/full/"); en = b.new_page(); en.goto(B + "en/profile/full/")
    tb = th.inner_text("ol.tl .body li") ; eb = en.inner_text("ol.tl .body")
    check(bool(THAI.search(tb)), "Thai page: timeline bullets are Thai")
    check(not THAI.search(eb), "English page: timeline bullets have no Thai")
    check(th.evaluate("document.documentElement.lang") == "th" and en.evaluate("document.documentElement.lang") == "en", "html lang th / en")
    b.close()
# 5) One Page PDF (only if built with --pdf)
pdf = os.path.join(ROOT, "profile", "one-page.pdf")
if os.path.exists(pdf):
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", open(pdf, "rb").read()))
    check(pages == 1, f"One Page PDF is {pages} page(s)")
print("FAILED" if fails else "ALL PASSED"); sys.exit(1 if fails else 0)
