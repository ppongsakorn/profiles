# profiles — notes for Claude sessions

Personal portfolio of Pongsakorn P. (Data & AI Team Lead). Public repo, deployed to GitHub Pages.
Audience: employers, colleagues, people looking for collaborators. See `ROADMAP.md` for what is planned.

## How the owner wants to work
- Reply in Thai; English technical terms are fine.
- The repo is public: never commit credentials, customer data, internal hostnames or confidential company figures.
- Do not invent facts about the owner (dates, numbers, employers, results). Unknown = leave `TODO` and ask.
  **Exception (owner's explicit permission): MOCK content.** Guessed placeholder content is allowed only in `impact_mock`, `learned_mock`, `snapshot.open_to_mock`, `snapshot.scope_mock` and `projects[].mock`, and must always render with a visible `MOCK` label, the page-top banner and the `contains_mock` flag (profile.json, llms.txt, WebMCP `notice`). Never mock contact details, institutions, certifications, awards/ranks, employers or anything in resumes/JSON-LD. Remove a mock block as soon as the real data arrives. Fields not mocked show "ข้อมูลกำลังเตรียมอยู่" (status `coming` for projects).
- Delivery: branch from `main`, clear commit message, push, open a PR only when asked, then verify the live site.
- Report limits honestly (what was not verified).

## Architecture
- `data/profile.yaml` is the single source of truth (schema in `docs/DATA.md`). Text fields accept `"text"` or `{en: ..., th: ...}`; items carry `tags`.
  Tag vocabulary = the six `focus` slugs + `extra_tags`; `scripts/validate_data.py` enforces it (runs in CI).
  Items with `status: draft` are excluded from site, resumes, profile.json and WebMCP (`python build.py --drafts` shows them locally).
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

## Design intent
- **Never name the intended audience on the site** (no "for employers / recruiters / headhunters / hiring" in page text, data, JSON-LD, llms.txt or WebMCP). The audience and goals are the design brief, not copy. Write in plain, human, first-person Thai (short sentences, jargon only where needed), not report language.
- The owner's defining strength is creativity. **Never state this as a claim anywhere on the site, in data, JSON-LD, llms.txt or WebMCP output.** Let the design and interactions show it (show, don't tell).
- Creativity must not cost clarity: recruiters scan in seconds, so the summary layer (snapshot, era strip) stays plain and fast. Expressive touches belong to one signature motif plus purposeful micro-interactions; respect `prefers-reduced-motion`, keep it keyboard accessible and light (no framework).

## Languages
- The site is bilingual: Thai at `/` (default), English at `/en/`; every page has an `alt_path` switch. Narrative text in `data/profile.yaml` must exist in both (`{en, th}`); proper nouns, role titles, company names and technical terms stay English.
- `scripts/validate_data.py` warns on narrative fields missing a language. Thai text drafted by Claude is marked in the data and needs the owner's review.

## Career story (profile views)
- Entries carry story fields: `era`, `headline`, `highlight`, `side`, `stack`, `impact[]`, `learned[]` (+ `bullets` = what was built). `eras` (5) and `snapshot` (recruiter summary: highlights, stack, open_to, scope) are in the data; years of experience is computed at build time.
- Views: home page timeline (collapsed cards, filter by tag, expand/collapse, reorder) · `/profile/` One Page (must stay 1 A4 page; PDF `profile/one-page.pdf`) · `/profile/full/` Full (all open; PDF `profile/full.pdf`) · mobile `/m/work/`.
- `impact` and `learned` stay empty until the owner supplies them; never invent achievements, numbers or lessons.
- Hobbies live in `hobbies` (`public: false` hides one). Keep the wording as the owner gave it.

## PII policy (public repo)
- Never commit personal data: personal e-mail, phone, address, birth date, IP, IDs, receipts, other people's names/contacts, signed LinkedIn media URLs. The only intentional exception is `basics.email` in `data/profile.yaml`, and only after the owner chooses an address.
- `scripts/check_pii.py` enforces this (pre-commit hook via `sh scripts/install_hooks.sh`, and CI). Do not weaken or bypass it; if it blocks a commit, remove the data.
- Do not open export files that are PII or third-party data (Connections, Invitations, Messages, Email Addresses, PhoneNumbers, Receipts, Registration, Ad_Targeting). Say so and skip them. When summarising, never repeat private values back in chat.
- Omit third-party names (co-authors, customers, contacts) from published data; use roles.

## LinkedIn / personal data intake
- Raw LinkedIn exports live only in `private/` (gitignored) and are deleted after use; never commit them or paste contact lists/emails into the repo.
- `python scripts/import_linkedin.py private/<dir>` writes a draft fragment (`status: draft`, empty tags). Review each item with the owner,
  classify tags, strip confidential names/figures, write problem/actions/result, then merge and set `status: published`.
- Ask before publishing anything that looks like a customer name, internal metric or non-public figure; set `sanitized: true` only after the owner confirms.

## Commands
- `pip install -r requirements.txt`
- `python build.py` (html + md) · `python build.py --pdf` (needs Chromium; set `CHROMIUM_PATH` if not on the default path)
- Preview: `python -m http.server -d dist`
- `python scripts/check_pii.py` (also `--staged`, `--history`; runs in CI and as pre-commit hook) blocks PII from entering git.
- `python scripts/validate_data.py` checks tags, slugs, dates, statuses and variants (errors fail CI; warnings list TODOs and unsanitised projects).
- `python scripts/check_contrast.py` checks WCAG contrast of every token pair (text 4.5:1, graphics 3:1, hero wash).
- `python scripts/check_site.py` (after `python build.py --pdf`; runs in CI) checks overflow at 360/390px in light/dark, phone redirect, timeline controls, Thai vs English text, no visible TODO, One Page PDF = 1 page.
- `python scripts/check_webmcp.py` (after build; also runs in CI) calls every WebMCP tool with a fake `document.modelContext`.
- Live site: `SITE_URL=https://ppongsakorn.github.io/profiles/ python scripts/check_site.py` (also `check_webmcp.py`) runs the same checks against the deployed pages. Deploy = merge to `main` (Pages workflow); the repo's Pages source is already GitHub Actions.
- Playwright checks that matter: no horizontal overflow at 360–390px, phone viewport redirects `/` → `/m/`, light and dark.

## Gotchas
- Do not name a YAML/dict key `items` (it bit twice: `story.items` → `story.entries`) (clashes with `dict.items` in Jinja); skills use `list` after selection.
- `build.py` warns with the number of `TODO` placeholders; the count must reach 0 before announcing the site.
