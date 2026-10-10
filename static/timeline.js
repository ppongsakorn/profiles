/* Timeline controls: filter by tag, expand/collapse all, reverse order, deep-link to a card. Works without JS (details/summary + anchors). */
(function () {
  var tl = document.querySelector("ol.tl");
  if (!tl) return;
  var items = [].slice.call(tl.querySelectorAll("li[data-kind]"));
  var all = function (sel) { return [].slice.call(document.querySelectorAll(sel)); };
  document.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("[data-act]") : null;
    if (!b) return;
    var a = b.getAttribute("data-act");
    if (a === "expand" || a === "collapse") tl.querySelectorAll("details").forEach(function (d) { d.open = a === "expand"; });
    if (a === "order") {
      var rev = tl.classList.toggle("rev");
      b.setAttribute("aria-pressed", String(rev));
      b.textContent = b.getAttribute(rev ? "data-on" : "data-off");
    }
    if (a === "filter") {
      var t = b.getAttribute("data-tag");
      all("[data-act=filter]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      items.forEach(function (li) {
        var tags = (li.getAttribute("data-tags") || "").split(" ");
        li.hidden = li.getAttribute("data-kind") === "milestone" ? !!t : !!t && tags.indexOf(t) < 0;
      });
    }
  });
  function openHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (id.indexOf("t-") !== 0) return;
    var li = document.getElementById(id);
    if (!li) return;
    li.hidden = false;
    var d = li.querySelector("details");
    if (d) d.open = true;
    li.scrollIntoView({ block: "center" });
  }
  window.addEventListener("hashchange", openHash);
  openHash();
})();
