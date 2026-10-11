/* WebMCP (W3C WebML CG draft): exposes this profile as read-only tools on document.modelContext
   so an in-browser AI agent can query it. No-op on browsers without the API.
   Data comes from profile.json (same content as the pages), fetched on the first tool call. */
(function () {
  var ctx = document.modelContext || navigator.modelContext;
  if (!ctx || typeof ctx.registerTool !== "function") return;
  var tag = document.querySelector("script[data-profile]");
  if (!tag) return;
  var src = new URL(tag.getAttribute("data-profile"), location.href).href;
  var pageLang = document.documentElement.lang === "en" ? "en" : "th";
  var cache;
  function load() {
    cache = cache || fetch(src).then(function (r) {
      if (!r.ok) throw new Error("profile.json HTTP " + r.status);
      return r.json();
    });
    return cache;
  }
  var abs = function (p) { return new URL(p, src).href; };
  var str = function (v) { return typeof v === "string" ? v.trim().slice(0, 200) : ""; };
  var pick = function (d, input) {
    var l = input && (input.lang === "en" || input.lang === "th") ? input.lang : pageLang;
    return { l: l, p: d.langs[l] };
  };
  var langProp = { lang: { type: "string", enum: ["th", "en"], description: "Content language; defaults to the page language." } };
  var RO = { readOnlyHint: true };
  // Sample (MOCK) data is flagged so an agent never reports it as fact.
  function withNotice(d, o) { if (d.contains_mock) o.notice = d.mock_note; return o; }

  function pages(d, l, screen) {
    var pre = l === "th" ? "" : l + "/";
    var m = { home: "", work: "work/", resume: "resume/", contact: "contact/" };
    return {
      desktop: abs(pre) + (screen === "home" ? "" : "#" + screen),
      mobile: abs(pre + d.site.mobile_path + (m[screen] || ""))
    };
  }
  function hay(o) { return JSON.stringify(o).toLowerCase(); }

  var tools = [
    {
      name: "get_profile", title: "Get profile",
      description: "Who the owner is: name, role, summary, location, public links and what they can help with.",
      inputSchema: { type: "object", properties: langProp }, annotations: RO,
      execute: function (i) { return load().then(function (d) { var x = pick(d, i);
        return withNotice(d, { name: x.p.basics.name, role: x.p.basics.label, summary: x.p.summary, location: x.p.basics.location,
          links: x.p.basics.links, focus_areas: x.p.focus.map(function (f) { return f.title; }), url: pages(d, x.l, "home") }); }); }
    },
    {
      name: "list_focus_areas", title: "List focus areas",
      description: "The areas the owner cares about and has worked in (UX/UI, data, AI, cloud, management, mobile).",
      inputSchema: { type: "object", properties: langProp }, annotations: RO,
      execute: function (i) { return load().then(function (d) { return pick(d, i).p.focus; }); }
    },
    {
      name: "get_experience", title: "Get work experience",
      description: "Work history, newest first, with achievements.",
      inputSchema: { type: "object", properties: langProp }, annotations: RO,
      execute: function (i) { return load().then(function (d) { var x = pick(d, i);
        return withNotice(d, { experience: x.p.experience, url: pages(d, x.l, "experience") }); }); }
    },
    {
      name: "list_projects", title: "List projects",
      description: "Past projects with summary and technology stack. Optionally filter by a technology or topic keyword (e.g. Databricks, fraud).",
      inputSchema: { type: "object", properties: Object.assign({ tech: { type: "string", description: "Keyword to match in name, summary, stack or tags." } }, langProp) },
      annotations: RO,
      execute: function (i) { return load().then(function (d) { var x = pick(d, i), q = str(i && i.tech).toLowerCase();
        var r = x.p.projects.filter(function (p) { return !q || hay(p).indexOf(q) >= 0; });
        return withNotice(d, { count: r.length, projects: r, url: pages(d, x.l, "projects") }); }); }
    },
    {
      name: "get_tech_timeline", title: "Get technology timeline",
      description: "Technologies used across the career, grouped by kind (data & AI, cloud, databases, backend, front end & mobile, tools), each with the period it was used. Entries with mock:true are sample data, not facts.",
      inputSchema: { type: "object", properties: langProp }, annotations: RO,
      execute: function (i) { return load().then(function (d) { var x = pick(d, i); return withNotice(d, { lanes: x.p.tech_timeline }); }); }
    },
    {
      name: "get_skills", title: "Get skills",
      description: "Skills and technologies grouped by area.",
      inputSchema: { type: "object", properties: langProp }, annotations: RO,
      execute: function (i) { return load().then(function (d) { return pick(d, i).p.skills; }); }
    },
    {
      name: "list_resumes", title: "List resumes",
      description: "Resume variants (each tailored to a role) with absolute download links in html, md and pdf.",
      inputSchema: { type: "object", properties: {} }, annotations: RO,
      execute: function () { return load().then(function (d) {
        return d.resumes.map(function (r) { var o = { slug: r.slug, title: r.title, language: r.lang, links: {} };
          r.formats.forEach(function (f) { o.links[f] = abs(r.slug + "/resume." + f); }); return o; }); }); }
    },
    {
      name: "search_profile", title: "Search profile",
      description: "Keyword search across experience, projects, skills and focus areas. Every word must match. Returns the matching items with their section.",
      inputSchema: { type: "object", required: ["query"], properties: Object.assign({ query: { type: "string", description: "Words to look for, e.g. 'databricks cost'." } }, langProp) },
      annotations: RO,
      execute: function (i) { return load().then(function (d) { var x = pick(d, i), words = str(i && i.query).toLowerCase().split(/\s+/).filter(Boolean);
        if (!words.length) return { error: "query is required" };
        var out = [];
        [["focus", x.p.focus], ["experience", x.p.experience], ["projects", x.p.projects], ["skills", x.p.skills]].forEach(function (s) {
          s[1].forEach(function (it) { var h = hay(it); if (words.every(function (w) { return h.indexOf(w) >= 0; })) out.push({ section: s[0], item: it }); });
        });
        return { count: out.length, results: out.slice(0, 20) }; }); }
    },
    {
      name: "get_contact", title: "Get contact details",
      description: "Public contact details and links. Nothing here is private; it is the same as the Contact section of the site.",
      inputSchema: { type: "object", properties: langProp }, annotations: RO,
      execute: function (i) { return load().then(function (d) { var x = pick(d, i);
        return { email: x.p.basics.email, location: x.p.basics.location, links: x.p.basics.links, url: pages(d, x.l, "contact") }; }); }
    }
  ];

  var ac = new AbortController();
  tools.forEach(function (t) {
    try {
      var r = ctx.registerTool(t, { signal: ac.signal });
      if (r && r.catch) r.catch(function (e) { console.warn("WebMCP register failed", t.name, e); });
    } catch (e) { console.warn("WebMCP register failed", t.name, e); }
  });
  window.addEventListener("pagehide", function () { ac.abort(); });
})();
