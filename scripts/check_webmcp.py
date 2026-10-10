#!/usr/bin/env python3
"""Serve dist/, inject a fake document.modelContext, and call every registered WebMCP tool.
   python scripts/check_webmcp.py   (after python build.py)"""
import functools, http.server, json, os, sys, threading
from playwright.sync_api import sync_playwright

EXPECTED = {"get_profile", "list_focus_areas", "get_experience", "list_projects", "get_skills", "list_resumes", "search_profile", "get_contact"}
FAKE = "window.__tools={};document.modelContext={registerTool:async(t)=>{window.__tools[t.name]=t}};"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); h.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}/"
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

with sync_playwright() as p:
    exe = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    b = p.chromium.launch(executable_path=exe) if os.path.exists(exe) else p.chromium.launch()
    for path, vp in [("", (1280, 900)), ("en/", (1280, 900)), ("m/work/", (390, 844))]:
        pg = b.new_page(viewport=dict(width=vp[0], height=vp[1])); pg.add_init_script(FAKE)
        if vp[0] < 641: pg.add_init_script("localStorage.setItem('fullweb','0')")
        pg.goto(base + path); pg.wait_for_timeout(400)
        names = set(pg.evaluate("Object.keys(window.__tools)"))
        check(names == EXPECTED, f"[{path or '/'}] registers {len(names)} tools")
        ro = pg.evaluate("Object.values(window.__tools).every(t=>t.annotations&&t.annotations.readOnlyHint===true)")
        check(ro, f"[{path or '/'}] all tools are readOnlyHint")
        if path == "":
            call = lambda n, a={}: pg.evaluate("([n,a])=>window.__tools[n].execute(a)", [n, a])
            prof = call("get_profile"); check(prof["name"] and len(prof["focus_areas"]) == 6, "get_profile name + 6 focus areas")
            check(len(call("list_focus_areas")) == 6, "list_focus_areas = 6")
            check(call("get_experience")["experience"][0]["company"] == "Buzzebees", "get_experience first = Buzzebees")
            r = call("list_projects", {"tech": "databricks"}); check(r["count"] >= 1, f"list_projects tech=databricks -> {r['count']}")
            check(len(call("get_skills")) >= 3, "get_skills groups")
            rs = call("list_resumes"); check(len(rs) == 3 and rs[0]["links"]["md"].startswith("http"), "list_resumes absolute links")
            s = call("search_profile", {"query": "databricks cost"}); check(s["count"] >= 1, f"search_profile 'databricks cost' -> {s['count']}")
            check("error" in call("search_profile", {"query": "  "}), "search_profile empty query -> error")
            check(call("get_contact")["links"][0]["label"] == "GitHub", "get_contact links")
            en = call("get_profile", {"lang": "en"}); check(en["role"] == "Data & AI Team Lead", "lang=en override")
            check(call("get_profile", {"lang": "<script>"})["name"], "invalid lang falls back safely")
        pg.close()
    nomc = b.new_page(); errs = []; nomc.on("pageerror", lambda e: errs.append(str(e)))
    nomc.goto(base); nomc.wait_for_timeout(300); check(not errs, "no JS error without WebMCP support")
    b.close()
print("FAILED" if fails else "ALL PASSED"); sys.exit(1 if fails else 0)
