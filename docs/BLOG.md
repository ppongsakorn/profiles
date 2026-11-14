# Blog (บันทึก / Blog)

Thai label **บันทึก**, English label **Blog**, URL `/blog/` (`/en/blog/`, mobile `/m/blog/`).

## Write a post
1. Make `blog/<slug>/` (kebab-case) and add `index.th.md` and/or `index.en.md`.
2. Front matter:
   ```yaml
   ---
   title: "Quote it if it has a colon"
   date: 2026-11-14          # a future date keeps it hidden until that day's build
   tags: [data, ai]          # focus slugs: management cloud data ai ux mobile web (+ software teaching)
   summary: One or two sentences for the list and RSS.
   status: published         # draft = never built (python build.py --drafts shows it)
   ---
   ```
3. Body is Markdown (code fences, tables). Put images next to the file and refer with `![alt](name.png)`.
4. `python scripts/validate_data.py` checks tags, dates, images; `python build.py` builds; push to `main` to deploy.
5. No PII, no customer or internal names, no invented facts.

## What the build writes
`blog/index.html`, `posts.json` (list + search data), `feed.xml`, `<slug>/index.html`, `<slug>/post.json` (plain text for AI agents), same under `en/` and `m/`.
A post missing in the other language is listed as "Thai only" in Thai and hidden in English.

## JavaScript (`static/blog.js`)
List: filter by topic, search, sort, load more, state in the URL (`?tag=ai&q=..&sort=old`). Post: related posts. GitHub feed: reads JSON from
`https://raw.githubusercontent.com/<repo>/<branch>/<path>` for each entry in `github.feeds` (data file), caches for one hour in localStorage,
and falls back to the static link if offline. Only public repos you list are read; text is inserted with `textContent`.

## Static blog frameworks (if you ever outgrow this builder)
Astro (Markdown + islands, best fit), Eleventy (simplest), Hugo (fastest, Go templates), Jekyll (native to GitHub Pages), Docusaurus/VitePress (docs-style).
This repo keeps its own tiny builder so one data file drives the site, resumes, `profile.json` and WebMCP.
