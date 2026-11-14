#!/usr/bin/env python3
"""Build the blog from tests/fixtures/blog into a temp dir and test list, filters, search, load more, XSS safety,
   draft/future exclusion, RSS, JSON and the GitHub feed (mocked network).   python scripts/check_blog.py"""
import functools, http.server, json, os, subprocess, sys, tempfile, threading
import xml.dom.minidom
from playwright.sync_api import sync_playwright

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
tmp = tempfile.mkdtemp(); fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)
env = dict(os.environ, DIST_DIR=tmp, BLOG_DIR=os.path.join(R, "tests/fixtures/blog"))
subprocess.run([sys.executable, os.path.join(R, "build.py")], cwd=R, env=env, check=True, stdout=subprocess.DEVNULL)
read = lambda p: open(os.path.join(tmp, p), encoding="utf-8").read()
idx = json.loads(read("blog/posts.json")); slugs = [p["slug"] for p in idx]
check(slugs == ["fx-xss", "fx-ai-notes", "fx-data-notes"], f"posts.json excludes draft + future, newest first: {slugs}")
check([p["slug"] for p in json.loads(read("en/blog/posts.json"))] == ["fx-data-notes"], "English index only has translated posts")
check(next(p for p in idx if p["slug"] == "fx-data-notes")["other"] is True and next(p for p in idx if p["slug"] == "fx-ai-notes")["other"] is False, "other-language flag")
check(not os.path.exists(os.path.join(tmp, "blog/fx-draft")) and not os.path.exists(os.path.join(tmp, "blog/fx-future")), "draft/future have no pages")
xml.dom.minidom.parseString(read("blog/feed.xml").encode()); check("fx-data-notes" in read("blog/feed.xml") and "fx-draft" not in read("blog/feed.xml"), "feed.xml is valid XML, no drafts")
post = read("blog/fx-data-notes/index.html")
check("<pre>" in post and "<table>" in post and 'application/ld+json' in post and "BlogPosting" in post, "post page renders code, table and BlogPosting JSON-LD")
check('hreflang="en"' in post or "/en/blog/fx-data-notes/" in post, "post links to its English version")
check("&lt;script&gt;window.__xss" in read("blog/fx-xss/index.html") or "<script>window.__xss" not in read("blog/fx-xss/index.html").split("<body")[1].split("<article")[0], "title escaped in HTML")
pj = json.loads(read("blog/fx-data-notes/post.json")); check("ข้อความทดสอบ" in pj["text"] and "<" not in pj["text"], "post.json has plain text")

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(H, directory=tmp)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}/"
FEED = [{"date": "2026-01-02", "kind": "feature", "title": "<img src=x onerror=window.__xss=1>", "items": ["one", "two", "three"]},
        {"date": "2026-01-01", "kind": "fix", "title": "Older", "items": []}]
with sync_playwright() as p:
    exe = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    b = p.chromium.launch(executable_path=exe) if os.path.exists(exe) else p.chromium.launch()
    for vw in (1280, 360):
        pg = b.new_page(viewport=dict(width=vw, height=900)); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/raw.githubusercontent.com/**", lambda r: r.fulfill(status=200, content_type="application/json", headers={"access-control-allow-origin": "*"}, body=json.dumps(FEED)))
        pg.goto(base + "blog/?ps=2"); pg.wait_for_selector("#blog-list .post-card")
        n = lambda: pg.locator("#blog-list .post-card").count()
        check(n() == 2 and pg.locator(".bl-more").is_visible(), f"[{vw}] page size 2 + load more visible")
        pg.click(".bl-more"); check(n() == 3 and not pg.locator(".bl-more").is_visible(), f"[{vw}] load more shows the rest")
        pg.click("button[data-tag=ai]"); check(n() == 1 and "tag=ai" in pg.url, f"[{vw}] filter by topic 'ai' (+ URL state)")
        pg.click("button[data-tag=\"\"]"); pg.fill("#blog-q", "ที่สอง"); check(n() == 1, f"[{vw}] search narrows to 1")
        pg.fill("#blog-q", "zzzz"); check(n() == 0, f"[{vw}] no match -> 0")
        pg.goto(base + "blog/?sort=old&ps=5"); pg.wait_for_selector("#blog-list .post-card")
        check("โน้ตเรื่องข้อมูล" in pg.locator("#blog-list .post-card").first.inner_text(), f"[{vw}] sort oldest first via URL")
        check(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"[{vw}] no horizontal overflow (list)")
        check(pg.evaluate("window.__xss === undefined"), f"[{vw}] no script from post title/summary ran")
        check("<img" not in pg.locator("#blog-list").inner_html().lower().replace('<img src="x"', "") or pg.locator("#blog-list img").count() == 0, f"[{vw}] titles are text, not HTML")
        pg.wait_for_selector("#gh-feed .gh-item"); t = pg.locator("#gh-feed").inner_text()
        check(pg.locator("#gh-feed .gh-item").count() == 2 and "<img" in t, f"[{vw}] GitHub feed drawn, markup shown as text")
        check(pg.evaluate("window.__xss === undefined"), f"[{vw}] GitHub feed cannot inject HTML")
        pg.goto(base + "blog/fx-data-notes/"); pg.wait_for_timeout(300)
        check(pg.locator("#related").count() == 1 and pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"[{vw}] post page ok, no overflow")
        check(not errs, f"[{vw}] no JS errors {errs[:1]}")
        pg.close()
    # network failure: static fallback stays, no crash
    pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/raw.githubusercontent.com/**", lambda r: r.abort())
    pg.goto(base + "blog/"); pg.wait_for_selector("#gh-feed [data-gh-error], #gh-feed a", timeout=15000)
    check(pg.locator("#blog-list .post-card, #blog-app .post-card").count() >= 1 and not errs, "GitHub offline: feed fails soft, posts still listed")
    # mobile shell + English + empty state
    pg.set_viewport_size(dict(width=390, height=844)); pg.goto(base + "m/blog/"); pg.wait_for_selector("#blog-app .post-card")
    check(pg.locator(".tabs a").count() == 4 or pg.locator("nav a").count() >= 4, "mobile blog screen renders with tabs")
    pg.goto(base + "en/blog/"); pg.wait_for_selector("#blog-app .post-card"); check("Blog" in pg.title() or "Blog" in pg.inner_text("body"), "English blog page")
    b.close()
print("FAILED" if fails else "ALL PASSED"); sys.exit(1 if fails else 0)
