#!/usr/bin/env python3
"""Generate the GitHub Pages site and every resume variant from data/profile.yaml.

  python build.py            # html + md  -> dist/
  python build.py --pdf      # also PDF (needs: pip install playwright; Chromium)
  python build.py --only ai-lead-th
"""
import argparse, glob, os, shutil, sys
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
LABELS = {
    "en": dict(summary="Summary", skills="Skills", experience="Experience", projects="Projects", interests="Interests"),
    "th": dict(summary="สรุป", skills="ทักษะ", experience="ประสบการณ์", projects="ผลงาน", interests="สิ่งที่สนใจ"),
}


UI = {
    "th": dict(focus="สิ่งที่ผมช่วยได้", experience="ประสบการณ์", projects="ผลงาน", resume="Resume", contact="ติดต่อ",
               interests="สิ่งที่กำลังสนใจ", cta_resume="ดู Resume", cta_contact="ติดต่อผม", full="เว็บเต็ม",
               mobile_ver="เวอร์ชันมือถือ", tab_home="หน้าแรก", tab_work="ผลงาน", tab_resume="Resume", tab_contact="ติดต่อ",
               home="หน้าแรก", work="ผลงาน", wheel_t1="Data & AI", wheel_t2="แตะเพื่อดูรายละเอียด"),
    "en": dict(focus="What I can help with", experience="Experience", projects="Projects", resume="Resume", contact="Contact",
               interests="Interests", cta_resume="View resume", cta_contact="Get in touch", full="Full site",
               mobile_ver="Mobile version", tab_home="Home", tab_work="Work", tab_resume="Resume", tab_contact="Contact",
               home="Home", work="Work", wheel_t1="Data & AI", wheel_t2="Tap a segment"),
}
SITE_LANGS = ["th", "en"]  # th lives at the site root, others under /<lang>/
MOBILE_SCREENS = {"home": "", "work": "work/", "resume": "resume/", "contact": "contact/"}


def wheel_svg(focus, ui):
    """Donut of the focus areas; each segment links to its card (#f-<slug>)."""
    import math
    cx = cy = 160; ro, ri = 150, 92; n = len(focus); out = []
    pt = lambda r, a: (cx + r * math.cos(a), cy + r * math.sin(a))
    for i, f in enumerate(focus):
        a0 = -math.pi / 2 + 2 * math.pi * i / n; a1 = -math.pi / 2 + 2 * math.pi * (i + 1) / n
        x0, y0 = pt(ro, a0); x1, y1 = pt(ro, a1); x2, y2 = pt(ri, a1); x3, y3 = pt(ri, a0)
        tx, ty = pt((ro + ri) / 2, (a0 + a1) / 2)
        out.append(f'<a href="#f-{f["slug"]}" aria-label="{f["title"]}"><path fill="var(--c{i+1})" stroke="var(--bg)" stroke-width="2" '
                   f'd="M{x0:.1f} {y0:.1f}A{ro} {ro} 0 0 1 {x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}A{ri} {ri} 0 0 0 {x3:.1f} {y3:.1f}Z"/>'
                   f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle">{f["short"]}</text></a>')
    return (f'<svg class="wheel" viewBox="0 0 320 320" role="img" aria-label="{ui["focus"]}">' + "".join(out) +
            f'<circle class="core" cx="{cx}" cy="{cy}" r="{ri-6}"/><text class="t1" x="{cx}" y="{cy-4}" text-anchor="middle">{ui["wheel_t1"]}</text>'
            f'<text class="t2" x="{cx}" y="{cy+16}" text-anchor="middle">{ui["wheel_t2"]}</text></svg>')


def build_site(env, data, resumes):
    for lang in SITE_LANGS:
        ctx = select(data, dict(lang=lang, summary="default", max_bullets=5, max_projects=9))
        ui = UI[lang]; prefix = "" if lang == "th" else f"{lang}/"
        alt_lang = next(l for l in SITE_LANGS if l != lang); alt_prefix = "" if alt_lang == "th" else f"{alt_lang}/"
        pages = [("desktop.html.j2", "", "home")] + [("mobile.html.j2", "m/" + sub, scr) for scr, sub in MOBILE_SCREENS.items()]
        for tpl, sub, screen in pages:
            path = prefix + sub
            up = "../" * path.count("/")
            link = lambda t, up=up: (up + t) or "./"
            html = env.get_template(tpl).render(**ctx, ui=ui, prefix=prefix, screen=screen, link=link, alt_lang=alt_lang,
                                                alt_path=alt_prefix + sub, wheel=wheel_svg(ctx["focus"], ui), resumes=resumes)
            os.makedirs(os.path.join(DIST, path), exist_ok=True)
            open(os.path.join(DIST, path, "index.html"), "w", encoding="utf-8").write(html)


def tr(x, lang):
    """Resolve {en:..., th:...} to a string, falling back to en then any value."""
    if isinstance(x, dict) and x and set(x) <= {"en", "th"}:
        return x.get(lang) or x.get("en") or next(iter(x.values()), "")
    if isinstance(x, list):
        return [tr(i, lang) for i in x]
    return x


def match(item_tags, want):
    return not want or not item_tags or bool(set(item_tags) & set(want))


def score(item_tags, want):
    return len(set(item_tags or []) & set(want))


def select(data, v):
    lang, want = v.get("lang", "en"), v.get("tags", [])
    rank = lambda xs: sorted(xs, key=lambda i: -score(i.get("tags"), want))  # stable: keeps file order on ties
    b = {k: tr(val, lang) for k, val in data["basics"].items()}
    b["links"] = data["basics"].get("links", [])
    sums = data.get("summaries", {})
    summary = tr(sums.get(v.get("summary", "default")) or sums.get("default", ""), lang)
    skills = [{**g, "list": tr(g["items"], lang)} for g in rank(data.get("skills", [])) if match(g.get("tags"), want)]
    exp = []
    for e in data.get("experience", []):
        if not match(e.get("tags"), want):
            continue
        bl = [x for x in rank([x if isinstance(x, dict) else {"text": x} for x in e.get("bullets", [])]) if match(x.get("tags"), want)]
        exp.append({**{k: tr(val, lang) for k, val in e.items() if k != "bullets"},
                    "bullets": [tr(x["text"], lang) for x in bl[: v.get("max_bullets", 99)]]})
    prj = [{**p, "name": tr(p["name"], lang), "summary": tr(p.get("summary", ""), lang)}
           for p in rank(data.get("projects", [])) if match(p.get("tags"), want)][: v.get("max_projects", 99)]
    focus = [{**f, **{k: tr(f.get(k, ""), lang) for k in ("short", "title", "desc")}} for f in data.get("focus", [])]
    return dict(focus=focus, b=b, summary=summary, skills=skills, experience=exp, projects=prj,
                interests=tr(data.get("interests", []), lang), v=v, lang=lang, L=LABELS.get(lang, LABELS["en"]))


def html_to_pdf(pairs):
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_PATH")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for src, dst in pairs:
            pg = br.new_page()
            pg.goto("file://" + src)
            pg.pdf(path=dst, format="A4", print_background=True, margin=dict(top="14mm", bottom="14mm", left="14mm", right="14mm"))
            pg.close()
        br.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    data = yaml.safe_load(open(os.path.join(ROOT, "data/profile.yaml"), encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")), autoescape=False, trim_blocks=True, lstrip_blocks=True)
    env.filters["select"] = lambda xs: [x for x in xs if x]
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST)
    resumes, pdfs, todo = [], [], 0
    for f in sorted(glob.glob(os.path.join(ROOT, "variants/*.yaml"))):
        slug = os.path.splitext(os.path.basename(f))[0]
        if a.only and slug != a.only:
            continue
        v = yaml.safe_load(open(f, encoding="utf-8"))
        ctx = select(data, v)
        out = os.path.join(DIST, slug)
        os.makedirs(out)
        fmts = [x for x in v.get("formats", ["html"]) if x != "pdf" or a.pdf]
        for fmt in {"html", "md"} & set(fmts) | ({"html"} if "pdf" in fmts else set()):
            txt = env.get_template(f"resume.{fmt}.j2").render(**ctx)
            todo += txt.count("TODO")
            open(os.path.join(out, f"resume.{fmt}"), "w", encoding="utf-8").write(txt)
        if "pdf" in fmts:
            pdfs.append((os.path.join(out, "resume.html"), os.path.join(out, "resume.pdf")))
        resumes.append(dict(slug=slug, title=v["title"], formats=[x for x in ["html", "pdf", "md"] if x in fmts]))
    if not a.only:
        build_site(env, data, resumes)
        shutil.copytree(os.path.join(ROOT, "static"), os.path.join(DIST, "assets"))
        open(os.path.join(DIST, ".nojekyll"), "w").close()
    if pdfs:
        html_to_pdf(pdfs)
    print(f"built {len(resumes)} variant(s) -> {DIST}" + (f"  [warn: {todo} TODO placeholder(s)]" if todo else ""))


if __name__ == "__main__":
    sys.exit(main())
