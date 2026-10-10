#!/usr/bin/env python3
"""Validate data/profile.yaml and variants/*.yaml.   python scripts/validate_data.py
Errors (exit 1): unknown tags, duplicate/invalid slugs, bad status/dates, variants pointing at nothing.
Warnings: TODO placeholders, missing en/th text, focus areas with no project, published items still unsanitised."""
import glob, os, re, sys
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
data = yaml.safe_load(open(os.path.join(ROOT, "data/profile.yaml"), encoding="utf-8"))
errors, warns = [], []
E = lambda m: errors.append(m)
W = lambda m: warns.append(m)

focus = [f["slug"] for f in data.get("focus", [])]
vocab = set(focus) | set(data.get("extra_tags", []))
if len(focus) != len(set(focus)):
    E("focus: duplicate slug")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

def tags(where, item):
    for t in item.get("tags", []) or []:
        if t not in vocab:
            E(f"{where}: unknown tag '{t}' (allowed: {', '.join(sorted(vocab))})")

def status(where, item):
    if item.get("status", "published") not in ("draft", "published"):
        E(f"{where}: status must be draft|published, got {item.get('status')!r}")

def date(where, v, allow_present=False):
    if v in (None, "") or (isinstance(v, str) and v.startswith("TODO")):
        return
    if allow_present and v == "Present":
        return
    if not (isinstance(v, str) and DATE.match(v)):
        E(f"{where}: date must be YYYY-MM{' or Present' if allow_present else ''}, got {v!r}")

def edu_date(where, v):
    if isinstance(v, int) or (isinstance(v, str) and re.match(r"^\d{4}$", v)):
        return
    date(where, v)

def flex_date(where, v):
    if v in (None, "") or (isinstance(v, str) and v.startswith("TODO")):
        return
    if not re.match(r"^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$", str(v)):
        E(f"{where}: date must be YYYY, YYYY-MM or YYYY-MM-DD, got {v!r}")

def bilingual(where, v):
    if isinstance(v, dict) and set(v) <= {"en", "th"} and v and len(v) < 2:
        W(f"{where}: only {next(iter(v))} given (the other language falls back)")

for i, e in enumerate(data.get("experience", [])):
    w = f"experience[{i}] {e.get('company')}"
    tags(w, e); status(w, e); date(w + ".start", e.get("start")); date(w + ".end", e.get("end"), True)
    for j, b in enumerate(e.get("bullets", [])):
        if isinstance(b, dict):
            tags(f"{w}.bullets[{j}]", b); status(f"{w}.bullets[{j}]", b)

slugs = set()
for i, p in enumerate(data.get("projects", [])):
    w = f"projects[{i}]"
    s = p.get("slug")
    if not s or not KEBAB.match(str(s)):
        E(f"{w}: slug must be kebab-case, got {s!r}")
    elif s in slugs:
        E(f"{w}: duplicate slug '{s}'")
    slugs.add(s)
    tags(w, p); status(w, p); bilingual(w + ".summary", p.get("summary"))
    if not p.get("tags"):
        W(f"{w} {s}: no tags, so no focus area will link to it")
    if p.get("status", "published") == "published" and not p.get("sanitized"):
        W(f"{w} {s}: published but sanitized=false (confirm no confidential figures/names before going live)")

for i, n in enumerate(data.get("notes", [])):
    w = f"notes[{i}]"
    if not n.get("slug") or not KEBAB.match(str(n["slug"])):
        E(f"{w}: slug must be kebab-case")
    tags(w, n); status(w, n)
for i, g in enumerate(data.get("skills", [])):
    tags(f"skills[{i}]", g)
for k in ("education", "certifications"):
    for i, x in enumerate(data.get(k, [])):
        status(f"{k}[{i}]", x)
        for f in ("start", "end", "date"):
            (edu_date if k == "education" else date)(f"{k}[{i}].{f}", x.get(f))
for i, n in enumerate(data.get("notes", [])):
    date(f"notes[{i}].date", n.get("date"))
for k in ("honors", "publications"):
    for i, x in enumerate(data.get(k, [])):
        status(f"{k}[{i}]", x); flex_date(f"{k}[{i}].date", x.get("date"))
        if not x.get("title"):
            E(f"{k}[{i}]: title is required")
for i, x in enumerate(data.get("patents", [])):
    status(f"patents[{i}]", x)
    if not x.get("title"):
        E(f"patents[{i}]: title is required")
for i, x in enumerate(data.get("hobbies", [])):
    if not x.get("slug") or not KEBAB.match(str(x["slug"])):
        E(f"hobbies[{i}]: slug must be kebab-case")
    if not x.get("name"):
        E(f"hobbies[{i}]: name is required")
for i, x in enumerate(data.get("languages", [])):
    if not x.get("name"):
        E(f"languages[{i}]: name is required")

used = {t for k in ("projects", "experience", "notes") for x in data.get(k, []) if x.get("status", "published") == "published" for t in x.get("tags", [])}
for f in focus:
    if f not in {t for p in data.get("projects", []) if p.get("status", "published") == "published" for t in p.get("tags", [])}:
        W(f"focus '{f}': no published project is tagged with it yet")

for f in sorted(glob.glob(os.path.join(ROOT, "variants/*.yaml"))):
    v = yaml.safe_load(open(f, encoding="utf-8")); w = "variants/" + os.path.basename(f)
    for t in v.get("tags", []):
        if t not in vocab:
            E(f"{w}: unknown tag '{t}'")
    if v.get("summary", "default") not in data.get("summaries", {}):
        E(f"{w}: summary key '{v.get('summary')}' not in summaries")
    if v.get("lang", "en") not in ("en", "th"):
        E(f"{w}: lang must be en|th")
    for s in v.get("sections", []):
        if s not in ("summary", "skills", "experience", "projects", "interests"):
            E(f"{w}: unknown section '{s}'")

# ---- bilingual coverage: narrative text on published items must exist in BOTH languages ----
THAI = re.compile(r"[\u0E00-\u0E7F]")
gaps = {"th": [], "en": []}

def lang_gap(path, val):
    if isinstance(val, list):
        for i, x in enumerate(val):
            lang_gap(f"{path}[{i}]", x)
    elif isinstance(val, dict) and val and set(val) <= {"en", "th"}:
        for l in ("en", "th"):
            if not val.get(l):
                gaps[l].append(path)
    elif isinstance(val, str) and len(val) > 12 and not val.startswith("TODO"):
        gaps["en" if THAI.search(val) else "th"].append(path)   # plain string reads as one language only

pub = lambda x: x.get("status", "published") == "published"
for i, e in enumerate(data.get("experience", [])):
    if not pub(e):
        continue
    for k in ("headline", "learned", "impact"):
        lang_gap(f"experience[{i}].{k}", e.get(k))
    for j, b in enumerate(e.get("bullets", [])):
        if isinstance(b, dict) and pub(b):
            lang_gap(f"experience[{i}].bullets[{j}]", b.get("text"))
for i, p in enumerate(data.get("projects", [])):
    if pub(p):
        for k in ("summary", "problem", "actions", "result", "role"):
            lang_gap(f"projects[{i}].{k}", p.get(k))
for k, fields in (("honors", ("description",)), ("publications", ("role",)), ("patents", ("description", "issuer"))):
    for i, x in enumerate(data.get(k, [])):
        if pub(x):
            for f in fields:
                lang_gap(f"{k}[{i}].{f}", x.get(f))
lang_gap("interests", data.get("interests", []))
for i, e in enumerate(data.get("eras", [])):
    lang_gap(f"eras[{i}].headline", e.get("headline"))
lang_gap("snapshot.highlights", data.get("snapshot", {}).get("highlights", []))
lang_gap("summaries.default", data.get("summaries", {}).get("default"))
for l, name in (("th", "Thai"), ("en", "English")):
    if gaps[l]:
        W(f"i18n: {len(gaps[l])} text field(s) missing {name}: " + ", ".join(gaps[l][:6]) + (" ..." if len(gaps[l]) > 6 else ""))

todo = open(os.path.join(ROOT, "data/profile.yaml"), encoding="utf-8").read().count("TODO")
if todo:
    W(f"{todo} TODO placeholder(s) left in data/profile.yaml")
for m in warns: print("warn  " + m)
for m in errors: print("ERROR " + m)
print(f"{len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
