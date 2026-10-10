#!/usr/bin/env python3
"""Turn a LinkedIn "Get a copy of your data" export into a DRAFT profile fragment for review.

  python scripts/import_linkedin.py <export_dir> [-o private/linkedin.draft.yaml]

* Keep the raw export OUTSIDE git (put it in ./private/, which is gitignored) and delete it when done.
* Reads only an allow-list of files: Profile (headline, summary, city only), Positions, Projects, Skills, Education,
  Certifications, Honors, Publications (authors are NOT copied), Patents, Languages.
  It never opens Connections, Invitations, Messages, Email Addresses, Phone Numbers, Registration, Receipts,
  Ad Targeting, Company Follows, Rich Media or anything else: those hold PII or third-party data.
* Everything is written with `status: draft` and empty tags. Nothing reaches the site until a person
  reviews it, classifies the tags, removes confidential wording and merges it into data/profile.yaml.
"""
import argparse, csv, html, os, re, sys
import yaml

FILES = {"profile": "Profile.csv", "positions": "Positions.csv", "projects": "Projects.csv",
         "skills": "Skills.csv", "education": "Education.csv", "certs": "Certifications.csv",
         "honors": "Honors.csv", "pubs": "Publications.csv", "patents": "Patents.csv", "langs": "Languages.csv"}
MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def rows(d, key):
    path = os.path.join(d, FILES[key])
    if not os.path.exists(path):
        print(f"skip  {FILES[key]} (not found)", file=sys.stderr)
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def g(r, *names):
    for n in names:
        if r.get(n.lower()):
            return r[n.lower()]
    return ""


def ym(v):
    """'Mar 2021' | '2021-03' | '03/2021' | '2021' -> 'YYYY-MM' (month unknown -> 'TODO-YYYY')."""
    v = v.strip()
    if not v:
        return ""
    m = re.match(r"^([A-Za-z]{3})[a-z]*\.?\s+(\d{4})$", v)
    if m and m.group(1).title() in MONTHS:
        return f"{m.group(2)}-{MONTHS[m.group(1).title()]:02d}"
    m = re.match(r"^(\d{4})-(\d{1,2})", v) or None
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{1,2})/(\d{4})$", v)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{4})$", v)
    return f"TODO-{m.group(1)}" if m else f"TODO {v}"


def fd(v):
    """Flexible date: 'Sep 11, 2008' -> 2008-09-11, 'Mar 2013' -> 2013-03, '2005' -> 2005."""
    v = v.strip()
    m = re.match(r"^([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),\s*(\d{4})$", v)
    if m and m.group(1).title() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1).title()]:02d}-{int(m.group(2)):02d}"
    return v if re.match(r"^\d{4}$", v) else ym(v)


def yr(v):
    """Education dates: keep a bare year as 'YYYY'; anything else goes through ym()."""
    v = v.strip()
    return v if re.match(r"^\d{4}$", v) else ym(v)


def bullets(desc):
    # LinkedIn exports often join sentences with a double space instead of a newline
    parts = [re.sub(r"^[\-•*●–]\s*", "", ln).strip() for ln in re.split(r"[\r\n]+|\s{2,}", html.unescape(desc)) if ln.strip()]
    return [{"text": p, "tags": [], "status": "draft"} for p in parts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("-o", "--out", default="private/linkedin.draft.yaml")
    a = ap.parse_args()
    out = {}
    prof = rows(a.export_dir, "profile")
    if prof:
        p = prof[0]
        out["basics_draft"] = {"headline": g(p, "headline"), "location": g(p, "geo location", "location"), "status": "draft"}
        if g(p, "summary"):
            out["summary_draft"] = {"text": html.unescape(g(p, "summary")), "status": "draft"}
    out["experience"] = [{"company": g(r, "company name", "company"), "role": g(r, "title"), "location": g(r, "location"),
                          "start": ym(g(r, "started on", "start date")), "end": ym(g(r, "finished on", "end date")) or "Present",
                          "tags": [], "status": "draft", "bullets": bullets(g(r, "description"))} for r in rows(a.export_dir, "positions")]
    out["projects"] = []
    for r in rows(a.export_dir, "projects"):
        t = g(r, "title", "name")
        slug = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "todo-project"
        out["projects"].append({"slug": slug, "name": t, "period": " – ".join(x for x in (ym(g(r, "started on")), ym(g(r, "finished on"))) if x),
                                "role": "TODO", "tags": [], "summary": g(r, "description"), "problem": "TODO", "actions": ["TODO"], "result": "TODO",
                                "metrics": [], "stack": [], "links": ([{"label": "Link", "url": g(r, "url")}] if g(r, "url") else []),
                                "sanitized": False, "status": "draft"})
    out["skills_draft"] = [g(r, "name") for r in rows(a.export_dir, "skills") if g(r, "name")]
    out["education"] = [{"school": g(r, "school name", "school") or "TODO", "degree": g(r, "degree name", "degree"), "field": g(r, "notes"),
                         "start": yr(g(r, "start date")), "end": yr(g(r, "end date")), "status": "draft"} for r in rows(a.export_dir, "education")]
    out["certifications"] = [{"name": g(r, "name"), "issuer": g(r, "authority"), "date": ym(g(r, "started on")), "url": g(r, "url"), "status": "draft"}
                             for r in rows(a.export_dir, "certs")]
    out["honors"] = [{"title": g(r, "title"), "description": g(r, "description"), "date": fd(g(r, "issued on")), "result": "TODO", "status": "draft"}
                     for r in rows(a.export_dir, "honors")]
    # publications: co-author names (third parties) are intentionally NOT copied
    out["publications"] = [{"title": g(r, "name"), "venue": g(r, "description"), "date": fd(g(r, "published on")), "role": "TODO", "status": "draft"}
                           for r in rows(a.export_dir, "pubs")]
    out["patents"] = [{"title": g(r, "title"), "description": g(r, "description"), "issuer": g(r, "issuer"), "number": g(r, "patent number") or "TODO",
                       "url": g(r, "url"), "status": "draft"} for r in rows(a.export_dir, "patents")]
    out["languages"] = [{"name": g(r, "name"), "level": g(r, "proficiency"), "status": "draft"} for r in rows(a.export_dir, "langs")]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("# DRAFT from LinkedIn export. Review, classify tags, remove confidential wording, then merge into data/profile.yaml.\n")
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False, width=100)
    print(f"wrote {a.out}: " + ", ".join(f"{len(out[k])} {k}" for k in ("experience", "projects", "skills_draft", "education", "certifications", "honors", "publications", "patents", "languages")))


if __name__ == "__main__":
    main()
