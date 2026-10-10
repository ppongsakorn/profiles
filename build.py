#!/usr/bin/env python3
"""Generate the GitHub Pages site and every resume variant from data/profile.yaml.

  python build.py            # html + md  -> dist/
  python build.py --pdf      # also PDF (needs: pip install playwright; Chromium)
  python build.py --only ai-lead-th
"""
import argparse, glob, os, re, shutil, sys
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
               home="หน้าแรก", work="ผลงาน", wheel_t1="Data & AI", wheel_t2="แตะเพื่อดูรายละเอียด", agents="สำหรับ AI Agent:",
               story="เส้นทางของผม", story_sub="เล่าตั้งแต่เรียนจนถึงวันนี้ กดการ์ดเพื่อดูรายละเอียด", expand_all="ขยายทั้งหมด", collapse_all="ย่อทั้งหมด",
               order_old="เรียง: เก่า → ใหม่", order_new="เรียง: ใหม่ → เก่า", filter_all="ทั้งหมด", built="สิ่งที่ได้สร้างและส่งมอบ", impact="ผลลัพธ์",
               learned="ความรู้และประสบการณ์ที่ได้รับ", tech="เทคโนโลยี", highlight="ไฮไลต์", side_job="ควบคู่", snapshot="ภาพรวมสำหรับผู้ว่าจ้าง",
               f_now="ตอนนี้", f_years="ประสบการณ์", years="ปี", since="ตั้งแต่", f_stack="เทคโนโลยีหลัก", f_open="เปิดรับ", f_scope="ขอบเขต",
               f_edu="การศึกษา", f_cert="ใบรับรอง", f_lang="ภาษา", f_loc="ที่ตั้ง", one_page="One Page", full_profile="ฉบับเต็ม", pdf="PDF",
               docs_title="โปรไฟล์ให้โหลดและพิมพ์", paper="งานวิจัย", cred="ใบรับรองและสิทธิบัตร", patent="สิทธิบัตร", now_word="ปัจจุบัน",
               hobbies="นอกเวลางาน", tag_leadership="Leadership", tag_software="Software", tag_teaching="Teaching", read_full="อ่านฉบับเต็ม", glance="เส้นทางโดยสรุป",
               skills_short="ทักษะหลัก", contact_short="ติดต่อ"),
    "en": dict(focus="What I can help with", experience="Experience", projects="Projects", resume="Resume", contact="Contact",
               interests="Interests", cta_resume="View resume", cta_contact="Get in touch", full="Full site",
               mobile_ver="Mobile version", tab_home="Home", tab_work="Work", tab_resume="Resume", tab_contact="Contact",
               home="Home", work="Work", wheel_t1="Data & AI", wheel_t2="Tap a segment", agents="For AI agents:",
               story="My story", story_sub="From study to today. Tap a card for details.", expand_all="Expand all", collapse_all="Collapse all",
               order_old="Order: oldest first", order_new="Order: newest first", filter_all="All", built="What I built and delivered", impact="Impact",
               learned="What I learned", tech="Technologies", highlight="Highlight", side_job="Alongside", snapshot="At a glance for hiring teams",
               f_now="Now", f_years="Experience", years="years", since="since", f_stack="Core stack", f_open="Open to", f_scope="Scope",
               f_edu="Education", f_cert="Certifications", f_lang="Languages", f_loc="Based in", one_page="One Page", full_profile="Full profile", pdf="PDF",
               docs_title="Profiles to download and print", paper="Paper", cred="Certifications and patents", patent="Patent", now_word="Present",
               hobbies="Outside work", tag_leadership="Leadership", tag_software="Software", tag_teaching="Teaching", read_full="Read the full profile", glance="Career at a glance",
               skills_short="Key skills", contact_short="Contact"),
}
SITE_LANGS = ["th", "en"]  # th lives at the site root, others under /<lang>/
MOBILE_SCREENS = {"home": "", "work": "work/", "resume": "resume/", "contact": "contact/"}


def wheel_svg(focus, ui):
    """Donut of the focus areas; each segment links to its card (#f-<slug>)."""
    import math
    cx = cy = 160; ro, ri = 150, 82; n = len(focus); out = []
    pt = lambda r, a: (cx + r * math.cos(a), cy + r * math.sin(a))
    for i, f in enumerate(focus):
        a0 = -math.pi / 2 + 2 * math.pi * i / n; a1 = -math.pi / 2 + 2 * math.pi * (i + 1) / n
        x0, y0 = pt(ro, a0); x1, y1 = pt(ro, a1); x2, y2 = pt(ri, a1); x3, y3 = pt(ri, a0)
        tx, ty = pt((ro + ri) / 2, (a0 + a1) / 2)
        ax0, ay0 = pt(ro - 2.5, a0); ax1, ay1 = pt(ro - 2.5, a1)
        out.append(f'<a href="#f-{f["slug"]}" aria-label="{f["title"]}"><path fill="var(--b{i+1})" stroke="var(--bg)" stroke-width="2" '
                   f'd="M{x0:.1f} {y0:.1f}A{ro} {ro} 0 0 1 {x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}A{ri} {ri} 0 0 0 {x3:.1f} {y3:.1f}Z"/>'
                   f'<path fill="none" stroke="var(--c{i+1})" stroke-width="5" d="M{ax0:.1f} {ay0:.1f}A{ro-2.5} {ro-2.5} 0 0 1 {ax1:.1f} {ay1:.1f}"/>'
                   f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle">{f["short"]}</text></a>')
    return (f'<svg class="wheel" viewBox="0 0 320 320" role="img" aria-label="{ui["focus"]}">' + "".join(out) +
            f'<circle class="core" cx="{cx}" cy="{cy}" r="{ri-6}"/><text class="t1" x="{cx}" y="{cy-4}" text-anchor="middle">{ui["wheel_t1"]}</text>'
            f'<text class="t2" x="{cx}" y="{cy+16}" text-anchor="middle">{ui["wheel_t2"]}</text></svg>')


def build_site(env, data, resumes, pdf_built=False):
    pdfs = []
    for lang in SITE_LANGS:
        ctx = select(data, dict(lang=lang, summary="default", max_bullets=99, max_projects=9))
        ui = UI[lang]; prefix = "" if lang == "th" else f"{lang}/"
        alt_lang = next(l for l in SITE_LANGS if l != lang); alt_prefix = "" if alt_lang == "th" else f"{alt_lang}/"
        pages = ([("desktop.html.j2", "", "home")] + [("mobile.html.j2", "m/" + sub, scr) for scr, sub in MOBILE_SCREENS.items()]
                 + [("profile_doc.html.j2", "profile/", "one"), ("profile_doc.html.j2", "profile/full/", "full")])
        for tpl, sub, screen in pages:
            path = prefix + sub
            up = "../" * path.count("/")
            link = lambda t, up=up: (up + t) or "./"
            sctx = ctx if screen != "full" else {**ctx, "story": {**ctx["story"], "open_all": True, "static": True}}
            html = env.get_template(tpl).render(**sctx, ui=ui, prefix=prefix, screen=screen, link=link, alt_lang=alt_lang, pdf_built=pdf_built, mode=screen,
                                                doc_title=ui["one_page"] if screen == "one" else ui["full_profile"],
                                                alt_path=alt_prefix + sub, wheel=wheel_svg(ctx["focus"], ui), resumes=resumes, jsonld=jsonld(ctx))
            os.makedirs(os.path.join(DIST, path), exist_ok=True)
            open(os.path.join(DIST, path, "index.html"), "w", encoding="utf-8").write(html)
            if pdf_built and screen == "one":
                pdfs.append((os.path.join(DIST, path, "index.html"), os.path.join(DIST, path, "one-page.pdf")))
            elif pdf_built and screen == "full":
                pdfs.append((os.path.join(DIST, path, "index.html"), os.path.join(DIST, prefix + "profile", "full.pdf")))
    return pdfs


def real(x):
    """Drop unfilled TODO placeholders from machine-readable output."""
    return x if isinstance(x, str) and x and not x.startswith("TODO") else None


def agent_view(ctx):
    return dict(basics=ctx["b"], summary=ctx["summary"], focus=[{k: f[k] for k in ("slug", "title", "desc")} for f in ctx["focus"]],
                skills=[{"group": g["group"], "items": g["list"]} for g in ctx["skills"]],
                experience=ctx["experience"], projects=ctx["projects"], interests=ctx["interests"], hobbies=ctx["hobbies"])


def jsonld(ctx):
    import json
    b = ctx["b"]
    d = {"@context": "https://schema.org", "@type": "Person", "name": b["name"], "jobTitle": b["label"],
         "description": real(ctx["summary"]), "email": real(b.get("email")), "address": real(b.get("location")),
         "worksFor": {"@type": "Organization", "name": next((e["company"] for e in ctx["experience"] if real(e["company"])), None)},
         "sameAs": [l["url"] for l in b.get("links", []) if real(l["url"])],
         "knowsAbout": [i for g in ctx["skills"] for i in g["list"]]}
    d = {k: v for k, v in d.items() if v}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def build_agent_files(data, resumes):
    import json
    langs = {l: agent_view(select(data, dict(lang=l, summary="default", max_bullets=99, max_projects=99))) for l in SITE_LANGS}
    doc = {"schema": "profile/1", "site": {"languages": SITE_LANGS, "default": SITE_LANGS[0], "mobile_path": "m/"},
           "resumes": resumes, "langs": langs}
    open(os.path.join(DIST, "profile.json"), "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1))
    lines = []
    for l in SITE_LANGS:
        v = langs[l]; pre = "" if l == "th" else f"{l}/"
        lines += [f"# {v['basics']['name']} ({l})", f"> {v['basics']['label']}. {real(v['summary']) or ''}".rstrip(), "",
                  f"- Site: ./{pre}", f"- Mobile: ./{pre}m/", ""]
    lines += ["## Machine-readable", "- ./profile.json: full profile in every language (JSON)",
              "- Resumes: " + ", ".join(f"./{r['slug']}/resume.md" for r in resumes),
              "- WebMCP: read-only tools on document.modelContext (get_profile, list_focus_areas, get_experience, list_projects, get_skills, list_resumes, search_profile, get_contact)", ""]
    open(os.path.join(DIST, "llms.txt"), "w", encoding="utf-8").write("\n".join(lines))


MONTHS = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
          "th": "ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.".split()}


def fmt_date(v, lang):
    """'2024-02' -> 'Feb 2024' (th: 'ก.พ. 2024', CE year); 'Present' -> 'ปัจจุบัน' in Thai; anything else unchanged."""
    m = re.match(r"^(\d{4})-(\d{2})$", str(v))
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{MONTHS.get(lang, MONTHS['en'])[int(m.group(2)) - 1]} {m.group(1)}"
    return "ปัจจุบัน" if v == "Present" and lang == "th" else v


def sortkey(v):
    """'YYYY' | 'YYYY-MM' | 'YYYY-MM-DD' -> sortable 'YYYY-MM' (year-only sits mid-year)."""
    m = re.match(r"^(\d{4})(?:-(\d{2}))?", str(v))
    return f"{m.group(1)}-{m.group(2) or '07'}" if m else "9999-99"


def build_story(data, exp, lang):
    """Narrative timeline (study + work + milestones), era strip, recruiter snapshot and credentials."""
    import datetime
    ui = UI[lang]
    real = lambda x: isinstance(x, str) and bool(x) and not x.startswith("TODO")
    clean = lambda xs: [x for x in tr(xs or [], lang) if real(x)]
    items = []
    for i, e in enumerate(data.get("education", [])):
        field, degree, school = tr(e.get("field", ""), lang), tr(e.get("degree", ""), lang), tr(e.get("school", ""), lang)
        learned = clean(e.get("learned"))
        items.append(dict(kind="study", id=f"t-study-{i + 1}", era=e.get("era", "study"), key=sortkey(e.get("start")), title=field or degree,
                          org=" · ".join(x for x in ((degree if field else ""), school if real(school) else "") if x),
                          when=f'{e.get("start", "")} – {e.get("end", "")}', headline=tr(e.get("headline", ""), lang), bullets=[], impact=[],
                          learned=learned, stack=[], tags=e.get("tags", []), side=False, highlight=False, current=False,
                          start_raw=str(e.get("start", "")), end_raw=str(e.get("end", "")), body=bool(learned)))
    seen_current = False
    for n, e in enumerate(exp):
        cur = e["end_raw"] == "Present" and not seen_current
        seen_current = seen_current or cur
        imp, lrn, stk = clean(e.get("impact")), clean(e.get("learned")), tr(e.get("stack", []), lang)
        items.append(dict(kind="work", id=f"t-work-{n + 1}", era=e.get("era", ""), key=sortkey(e["start_raw"]), title=e["role"], org=e["company"],
                          when=f'{e["start"]} – {e["end"]}', headline=e.get("headline", ""), bullets=e["bullets"], impact=imp, learned=lrn, stack=stk,
                          tags=e.get("tags", []), side=bool(e.get("side")), highlight=bool(e.get("highlight")), current=cur,
                          start_raw=e["start_raw"], end_raw=e["end_raw"], body=bool(e["bullets"] or imp or lrn or stk)))
    for h in data.get("honors", []):
        items.append(dict(kind="milestone", key=sortkey(h.get("date")), year=str(h.get("date", ""))[:4], title=tr(h["title"], lang), sub=tr(h.get("description", ""), lang)))
    for p in data.get("publications", []):
        items.append(dict(kind="milestone", key=sortkey(p.get("date")), year=str(p.get("date", ""))[:4], title=tr(p["title"], lang),
                          sub=f'{ui["paper"]}: {tr(p.get("venue", ""), lang).split(",")[0]}'))
    items.sort(key=lambda x: (x["key"], 1 if x["kind"] == "milestone" else 0))
    eras = []
    for era in data.get("eras", []):
        mem = sorted([x for x in items if x.get("era") == era["id"]], key=lambda x: x["key"])
        if not mem:
            continue
        y0 = min(int(m["start_raw"][:4]) for m in mem)
        ends = [m["end_raw"] for m in mem]
        y1 = ui["now_word"] if "Present" in ends else max(int(x[:4]) for x in ends if x[:4].isdigit())
        eras.append(dict(id=era["id"], label=tr(era["label"], lang), headline=tr(era["headline"], lang), years=f"{y0}–{y1}", first_id=mem[0]["id"]))
    works = [x for x in items if x["kind"] == "work"]
    starts = [int(x["start_raw"][:4]) for x in works if x["start_raw"][:4].isdigit()]
    years = datetime.date.today().year - min(starts) if starts else None
    cur = next((x for x in works if x["current"]), None)
    snap = data.get("snapshot", {})
    edu = data.get("education", [{}])[0] if data.get("education") else {}
    certs = [c["name"] for c in data.get("certifications", [])]
    snapshot = dict(
        now=dict(title=cur["title"], org=cur["org"], since=fmt_date(cur["start_raw"], lang)) if cur else None,
        years=years, stack=tr(snap.get("stack", []), lang),
        highlights=[tr(h, lang).replace("{years}", str(years)) for h in snap.get("highlights", [])],
        open_to=tr(snap.get("open_to", ""), lang) if real(snap.get("open_to", "")) else "",
        scope=tr(snap.get("scope", ""), lang) if real(snap.get("scope", "")) else "",
        edu=" · ".join(x for x in (tr(edu.get("field", ""), lang), tr(edu.get("degree", ""), lang)) if x) if edu else "",
        certs=certs, languages=[f'{tr(l["name"], lang)} — {tr(l["level"], lang)}' for l in data.get("languages", [])],
        location=tr(data["basics"].get("location", ""), lang) if real(tr(data["basics"].get("location", ""), lang)) else "")
    titles = {f["slug"]: tr(f["title"], lang) for f in data.get("focus", [])}
    extra = {"leadership": ui["tag_leadership"], "software": ui["tag_software"], "teaching": ui["tag_teaching"]}
    used = {t for x in items if x["kind"] != "milestone" for t in x["tags"]}
    order = ["leadership"] + [f["slug"] for f in data.get("focus", [])] + ["software", "teaching"]
    filters = [(t, titles.get(t) or extra.get(t, t)) for t in order if t in used]
    cred = dict(certs=[dict(name=c["name"], issuer=c.get("issuer", "")) for c in data.get("certifications", [])],
                patents=[dict(title=tr(p["title"], lang), issuer=tr(p.get("issuer", ""), lang), url=p.get("url", "")) for p in data.get("patents", [])])
    return dict(entries=items, eras=eras, filters=filters, cred=cred, snapshot=snapshot, open_all=False, static=False)


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


def published(data):
    """Drop items marked `status: draft` (unreviewed imports never reach the site, resumes or profile.json)."""
    ok = lambda x: not (isinstance(x, dict) and x.get("status") == "draft")
    out = dict(data)
    for k in ("skills", "experience", "projects", "notes", "education", "certifications", "honors", "publications", "patents", "languages", "hobbies"):
        out[k] = [x for x in data.get(k, []) if ok(x)]
    out["experience"] = [{**e, "bullets": [b for b in e.get("bullets", []) if ok(b)]} for e in out["experience"]]
    return out


def select(data, v):
    lang, want = v.get("lang", "en"), v.get("tags", [])
    rank = lambda xs: sorted(xs, key=lambda i: -score(i.get("tags"), want))  # stable: keeps file order on ties
    b = {k: tr(val, lang) for k, val in data["basics"].items()}
    b["links"] = data["basics"].get("links", [])
    for k in ("email", "location"):   # unfilled placeholders never reach the page
        if isinstance(b.get(k), str) and b[k].startswith("TODO"):
            b[k] = ""
    sums = data.get("summaries", {})
    summary = tr(sums.get(v.get("summary", "default")) or sums.get("default", ""), lang)
    skills = [{**g, "group": tr(g["group"], lang), "list": tr(g["items"], lang)} for g in rank(data.get("skills", [])) if match(g.get("tags"), want)]
    exp = []
    for e in data.get("experience", []):
        if not match(e.get("tags"), want):
            continue
        bl = [x for x in rank([x if isinstance(x, dict) else {"text": x} for x in e.get("bullets", [])]) if match(x.get("tags"), want)]
        item = {k: tr(val, lang) for k, val in e.items() if k != "bullets"}
        item["start_raw"], item["end_raw"] = str(item.get("start", "")), str(item.get("end", ""))
        item["start"], item["end"] = fmt_date(item.get("start", ""), lang), fmt_date(item.get("end", ""), lang)
        exp.append({**item, "bullets": [tr(x["text"], lang) for x in bl[: v.get("max_bullets", 99)]]})
    prj = [{**p, **{k: tr(p.get(k, ""), lang) for k in ("name", "summary", "problem", "result", "role", "period")},
            "actions": tr(p.get("actions", []), lang)}
           for p in rank(data.get("projects", [])) if match(p.get("tags"), want)][: v.get("max_projects", 99)]
    focus = [{**f, **{k: tr(f.get(k, ""), lang) for k in ("short", "title", "desc")}} for f in data.get("focus", [])]
    story = build_story(data, exp, lang)
    hobbies = [tr(h["name"], lang) for h in data.get("hobbies", []) if h.get("public", True)]
    return dict(hobbies=hobbies, story=story, focus=focus, b=b, summary=summary, skills=skills, experience=exp, projects=prj,
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
    ap.add_argument("--drafts", action="store_true", help="include items marked status: draft (local preview only)")
    a = ap.parse_args()
    data = yaml.safe_load(open(os.path.join(ROOT, "data/profile.yaml"), encoding="utf-8"))
    if not a.drafts:
        data = published(data)
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
        resumes.append(dict(slug=slug, title=v["title"], lang=v.get("lang", "en"), formats=[x for x in ["html", "pdf", "md"] if x in fmts]))
    if not a.only:
        pdfs += build_site(env, data, resumes, pdf_built=a.pdf)
        build_agent_files(data, resumes)
        shutil.copytree(os.path.join(ROOT, "static"), os.path.join(DIST, "assets"))
        open(os.path.join(DIST, ".nojekyll"), "w").close()
    if pdfs:
        html_to_pdf(pdfs)
    print(f"built {len(resumes)} variant(s) -> {DIST}" + (f"  [warn: {todo} TODO placeholder(s)]" if todo else ""))


if __name__ == "__main__":
    sys.exit(main())
