# profiles — notes for Claude sessions

Personal portfolio of Pongsakorn P. (Data & AI Team Lead). Public repo, deployed to GitHub Pages.
Audience: employers, colleagues, people looking for collaborators. See `ROADMAP.md` for what is planned.

## How the owner wants to work
- Reply in Thai; English technical terms are fine.
- The repo is public: never commit credentials, customer data, internal hostnames or confidential company figures.
- Do not invent facts about the owner (dates, numbers, employers, results). Unknown = leave `TODO` and ask.
- Delivery: branch from `main`, clear commit message, push, open a PR only when asked, then verify the live site.
- Report limits honestly (what was not verified).

## Architecture
- `data/profile.yaml` is the single source of truth. Text fields accept `"text"` or `{en: ..., th: ...}`; items carry `tags`.
- `variants/*.yaml` = one resume each (tags filter, `max_bullets`, `max_projects`, `sections`, `lang`, `formats`).
- `build.py` → `dist/` (gitignored): resumes at `dist/<variant>/resume.{html,md,pdf}`, site at `/` (th) and `/en/`.
- Site has two versions: desktop (`templates/desktop.html.j2`, default) and a mobile web app under `m/`
  (`templates/mobile.html.j2`: Home / Work / Resume / Contact + "เว็บเต็ม"). Desktop redirects small screens to `m/`
  before paint unless `localStorage.fullweb === '1'`.
- CSS is plain, in `static/` (`base.css` tokens + dark mode, `desktop.css`, `mobile.css`). No CSS framework.
- Colour policy: content first. Text is always `--ink`/`--ink2`; the six area colours `--c1..c6` are markers only (dot, wheel rim, mobile side bar), big fills use the tints `--b1..b6`. Never use `--cN` as text colour. Check contrast of any new pair (text >= 4.5:1, graphics >= 3:1).
- AI-readable surface (WebMCP + fallbacks): `static/webmcp.js` registers 8 read-only tools on `document.modelContext`
  (get_profile, list_focus_areas, get_experience, list_projects, get_skills, list_resumes, search_profile, get_contact),
  fetching `profile.json` lazily. `build.py` also emits `profile.json`, `llms.txt` and a schema.org `Person` JSON-LD block.
  All of it is public page content only: never add private or non-displayed data there. When adding/removing a tool,
  update `EXPECTED` in `scripts/check_webmcp.py` and the list above.
- Keep README.md / about.md / skills.md etc. consistent with `data/profile.yaml` (they are the GitHub-facing copy).

## Commands
- `pip install -r requirements.txt`
- `python build.py` (html + md) · `python build.py --pdf` (needs Chromium; set `CHROMIUM_PATH` if not on the default path)
- Preview: `python -m http.server -d dist`
- `python scripts/check_webmcp.py` (after build; also runs in CI) calls every WebMCP tool with a fake `document.modelContext`.
- Playwright checks that matter: no horizontal overflow at 360–390px, phone viewport redirects `/` → `/m/`, light and dark.

## Gotchas
- Do not name a YAML/dict key `items` (clashes with `dict.items` in Jinja); skills use `list` after selection.
- `build.py` warns with the number of `TODO` placeholders; the count must reach 0 before announcing the site.
