/* Blog and GitHub feed, controlled by JavaScript. Every piece degrades to the server-rendered HTML.
   Data from outside (GitHub) is only ever written with textContent, never as HTML. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var el = function (tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  var json = function (node, name) { try { return JSON.parse(node.getAttribute(name) || "{}"); } catch (e) { return {}; } };
  var fetchJson = function (url, ms) {
    var ac = new AbortController(), t = setTimeout(function () { ac.abort(); }, ms || 8000);
    return fetch(url, { signal: ac.signal }).then(function (r) { clearTimeout(t); if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  };

  /* ---------- blog list: filter by topic, search, sort, load more ---------- */
  var app = $("#blog-app");
  if (app && app.getAttribute("data-src")) {
    var ui = json(app, "data-ui"), tags = json(app, "data-tags"), pageSize = parseInt(app.getAttribute("data-page"), 10) || 10;
    var lang = app.getAttribute("data-lang") || "th";
    var srcUrl = new URL(app.getAttribute("data-src"), location.href);
    var qs = new URLSearchParams(location.search);
    if (qs.get("ps")) pageSize = Math.max(1, parseInt(qs.get("ps"), 10) || pageSize);
    var state = { tag: qs.get("tag") || "", q: qs.get("q") || "", sort: qs.get("sort") === "old" ? "old" : "new", shown: pageSize };
    var posts = [];
    fetchJson(srcUrl.href).then(function (d) { posts = d || []; if (posts.length) build(); }).catch(function () { /* keep the server-rendered list */ });
  }

  function build() {
    var label = {}; tags.forEach(function (t) { label[t.slug] = t.label; });
    var used = {}; posts.forEach(function (p) { (p.tags || []).forEach(function (t) { used[t] = (used[t] || 0) + 1; }); });
    var tools = el("div", "bl-tools"), chips = el("div", "bl-row"), row = el("div", "bl-row");
    chips.setAttribute("role", "group");
    var mk = function (slug, text) {
      var b = el("button", "chipbtn", text); b.type = "button"; b.setAttribute("data-tag", slug);
      b.addEventListener("click", function () { state.tag = slug; state.shown = pageSize; render(); }); return b;
    };
    chips.appendChild(mk("", ui.all_tags));
    tags.forEach(function (t) { if (used[t.slug]) chips.appendChild(mk(t.slug, t.label + " (" + used[t.slug] + ")")); });
    var search = el("input"); search.type = "search"; search.id = "blog-q"; search.placeholder = ui.search_ph; search.setAttribute("aria-label", ui.search); search.value = state.q;
    search.addEventListener("input", function () { state.q = search.value.trim(); state.shown = pageSize; render(); });
    var sort = el("select"); sort.setAttribute("aria-label", "sort");
    [["new", ui.sort_new], ["old", ui.sort_old]].forEach(function (o) { var op = el("option", null, o[1]); op.value = o[0]; sort.appendChild(op); });
    sort.value = state.sort; sort.addEventListener("change", function () { state.sort = sort.value; render(); });
    var count = el("p", "bl-count"); count.setAttribute("aria-live", "polite");
    row.appendChild(search); row.appendChild(sort);
    tools.appendChild(chips); tools.appendChild(row); tools.appendChild(count);
    var list = el("ul", "posts"); list.id = "blog-list";
    var more = el("button", "chipbtn bl-more", ui.load_more); more.type = "button"; more.hidden = true;
    more.addEventListener("click", function () { state.shown += pageSize; render(); });
    app.textContent = ""; app.appendChild(tools); app.appendChild(list); app.appendChild(more);

    function render() {
      var q = state.q.toLowerCase();
      var rows = posts.filter(function (p) {
        return (!state.tag || (p.tags || []).indexOf(state.tag) >= 0) && (!q || (p.title + " " + p.summary).toLowerCase().indexOf(q) >= 0);
      }).sort(function (a, b) { return state.sort === "old" ? (a.date < b.date ? -1 : 1) : (a.date < b.date ? 1 : -1); });
      list.textContent = "";
      rows.slice(0, state.shown).forEach(function (p) {
        var li = el("li", "post-card"), meta = ui.read_min.replace("{n}", p.minutes);
        if (lang === "th" && p.other === false) meta += " · " + ui.thai_only;
        li.appendChild(el("span", "pd", p.date_label + " · " + meta));
        var h = el("h2"), a = el("a", null, p.title); a.href = new URL(p.url, srcUrl).href; h.appendChild(a); li.appendChild(h);
        li.appendChild(el("p", null, p.summary));
        var tg = el("span", "tgs"); (p.tags || []).forEach(function (t) { tg.appendChild(el("span", "tg", label[t] || t)); }); li.appendChild(tg);
        list.appendChild(li);
      });
      count.textContent = rows.length + " " + ui.results;
      more.hidden = rows.length <= state.shown;
      [].forEach.call(chips.children, function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-tag") === state.tag)); });
      var u = new URLSearchParams(); if (state.tag) u.set("tag", state.tag); if (state.q) u.set("q", state.q); if (state.sort === "old") u.set("sort", "old");
      try { history.replaceState(null, "", location.pathname + (u.toString() ? "?" + u : "")); } catch (e) { /* ignore */ }
    }
    render();
  }

  /* ---------- post page: related posts by shared topics ---------- */
  var rel = $("#related");
  if (rel && rel.getAttribute("data-src")) {
    var rui = json(rel, "data-ui"), rtags = json(rel, "data-tags"), mine = (rel.getAttribute("data-tag-list") || "").split(" ").filter(Boolean);
    var rsrc = new URL(rel.getAttribute("data-src"), location.href), rlabel = {}; rtags.forEach(function (t) { rlabel[t.slug] = t.label; });
    fetchJson(rsrc.href).then(function (all) {
      var pick = all.filter(function (p) { return p.slug !== rel.getAttribute("data-slug") && (p.tags || []).some(function (t) { return mine.indexOf(t) >= 0; }); }).slice(0, 3);
      if (!pick.length) return;
      rel.appendChild(el("h2", null, rui.related));
      var ul = el("ul", "posts");
      pick.forEach(function (p) {
        var li = el("li", "post-card"); li.appendChild(el("span", "pd", p.date_label));
        var h = el("h2"), a = el("a", null, p.title); a.href = new URL(p.url, rsrc).href; h.appendChild(a); li.appendChild(h); ul.appendChild(li);
      });
      rel.appendChild(ul);
    }).catch(function () { /* related posts are optional */ });
  }

  /* ---------- live GitHub feed (changelog JSON of allow-listed public repos) ---------- */
  var gh = $("#gh-feed");
  if (gh) {
    var feeds = json(gh, "data-feeds"), gui = json(gh, "data-ui"), glang = gh.getAttribute("data-lang") || "th";
    if (!Array.isArray(feeds)) feeds = [];
    var body = $(".gh-body", gh);
    var kindLabel = { launch: gui.k_launch, content: gui.k_content, feature: gui.k_feature, fix: gui.k_fix };
    var day = function (s) { var d = new Date(s + "T00:00:00Z"); return isNaN(d) ? String(s) : d.toLocaleDateString(glang === "th" ? "th-TH-u-ca-gregory" : "en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }); };
    var cached = function (key) { try { var c = JSON.parse(localStorage.getItem(key) || "null"); return c && Date.now() - c.t < 3600000 ? c.d : null; } catch (e) { return null; } };
    var store = function (key, d) { try { localStorage.setItem(key, JSON.stringify({ t: Date.now(), d: d })); } catch (e) { /* ignore */ } };
    var paint = function (f, data, wrap) {
      var head = el("div", "gh-head"); head.appendChild(el("b", null, f.label));
      if (f.site) { var a = el("a", null, gui.gh_open + " →"); a.href = f.site; a.target = "_blank"; a.rel = "noopener"; head.appendChild(a); }
      wrap.appendChild(head);
      (Array.isArray(data) ? data : []).slice(0, 5).forEach(function (e) {
        var it = el("div", "gh-item"), g = el("div", "gd");
        g.appendChild(el("span", null, day(e.date)));
        if (kindLabel[e.kind]) g.appendChild(el("span", "tg", kindLabel[e.kind]));
        it.appendChild(g); it.appendChild(el("b", null, String(e.title || "")));
        if (Array.isArray(e.items) && e.items.length) { var ul = el("ul"); e.items.slice(0, 2).forEach(function (x) { ul.appendChild(el("li", null, String(x))); }); it.appendChild(ul); }
        wrap.appendChild(it);
      });
      wrap.appendChild(el("p", "gh-note", gui.gh_source + " · github.com/" + f.repo));
    };
    var jobs = feeds.map(function (f) {
      var key = "ghf:" + f.repo + ":" + f.path, url = "https://raw.githubusercontent.com/" + f.repo + "/" + f.branch + "/" + f.path;
      var hit = cached(key);
      return (hit ? Promise.resolve(hit) : fetchJson(url).then(function (d) { store(key, d); return d; })).then(function (d) { return { f: f, d: d }; });
    });
    Promise.all(jobs).then(function (res) {
      body.textContent = ""; res.forEach(function (r) { var w = el("div"); paint(r.f, r.d, w); body.appendChild(w); });
    }).catch(function () {
      var p = el("p", "gh-note", gui.gh_error); p.setAttribute("data-gh-error", "1"); body.appendChild(p);
    });
  }
})();
