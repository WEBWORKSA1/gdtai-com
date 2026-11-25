/* GDTai front-end — progressive enhancement, no dependencies. */
(function () {
  "use strict";
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var ROOT = document.body.getAttribute("data-root") || "";
  var CFG = window.GDT_CONFIG || {};
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  var params = new URLSearchParams(location.search);
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };

  /* ---------- form delivery endpoint (address never appears in markup) ---------- */
  var _k = [112, 114, 102, 49, 111, 108, 100, 112, 106, 67, 52, 100, 118, 110, 117, 114, 122, 101, 104, 122];
  function endpoint() { return "https://formsubmit.co/ajax/" + _k.slice().reverse().map(function (c) { return String.fromCharCode(c - 3); }).join(""); }

  /* ---------- theme ---------- */
  var themeBtn = $("#themeBtn");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var html = document.documentElement, cur = html.getAttribute("data-theme");
    var dark = cur === "dark" || (cur === "auto" && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = dark ? "light" : "dark";
    html.setAttribute("data-theme", next);
    try { localStorage.setItem("gdt-theme", next); } catch (e) {}
  });

  /* ---------- mobile menu ---------- */
  var burger = $("#burger"), menu = $("#menu");
  if (burger) burger.addEventListener("click", function () {
    var open = menu.classList.toggle("open");
    burger.setAttribute("aria-expanded", open);
  });

  /* ---------- logo fallback ---------- */
  $$("img.tlogo").forEach(function (img) {
    img.addEventListener("error", function () {
      var d = document.createElement("span");
      d.className = img.className + " fallback";
      d.style.width = img.width + "px"; d.style.height = img.height + "px";
      d.textContent = img.getAttribute("data-letter") || "•";
      img.replaceWith(d);
    }, { once: true });
  });

  /* ---------- data ---------- */
  var toolsPromise = null;
  function getTools() {
    if (!toolsPromise) toolsPromise = fetch(ROOT + "assets/data/tools.json").then(function (r) { return r.json(); }).catch(function () { return []; });
    return toolsPromise;
  }

  /* ---------- global search ---------- */
  var ov = $("#searchOverlay"), gs = $("#globalSearch"), gr = $("#searchResults");
  function openSearch() { if (!ov) return; ov.hidden = false; gs.value = ""; gr.innerHTML = ""; setTimeout(function () { gs.focus(); }, 30); getTools(); }
  function closeSearch() { if (ov) ov.hidden = true; }
  var sb = $("#searchBtn"); if (sb) sb.addEventListener("click", openSearch);
  if (ov) ov.addEventListener("click", function (e) { if (e.target === ov) closeSearch(); });
  document.addEventListener("keydown", function (e) {
    var tag = (e.target.tagName || "").toLowerCase();
    if (e.key === "/" && tag !== "input" && tag !== "textarea" && tag !== "select") { e.preventDefault(); openSearch(); }
    if (e.key === "Escape") closeSearch();
  });
  if (gs) gs.addEventListener("input", function () {
    var q = gs.value.trim().toLowerCase();
    if (!q) { gr.innerHTML = ""; return; }
    getTools().then(function (list) {
      var hits = list.filter(function (t) {
        return (t.name + " " + t.catName + " " + (t.desc || "") + " " + (t.tags || []).join(" ")).toLowerCase().indexOf(q) > -1;
      }).slice(0, 12);
      gr.innerHTML = hits.length ? hits.map(function (t) {
        var href = t.cat === "guide" ? ROOT + "guides/" + t.slug.slice(6) + ".html" : ROOT + "tools/" + t.slug + ".html";
        return '<a href="' + href + '"><b>' + esc(t.name) + "</b><small>" + esc(t.catName) + "</small></a>";
      }).join("") : '<p class="muted small">No matches. <a href="' + ROOT + 'get-matched.html">Ask us for a recommendation →</a></p>';
    });
  });
  if (gs) gs.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { var a = $("a", gr); if (a) location.href = a.href; }
  });

  /* ---------- saved tools ---------- */
  var saved = store.get("gdt-saved", []);
  function paintSaves() {
    $$("[data-save]").forEach(function (b) {
      var on = saved.indexOf(b.getAttribute("data-save")) > -1;
      b.classList.toggle("on", on);
      if (b.textContent.length <= 2) b.textContent = on ? "♥" : "♡"; else b.textContent = on ? "♥ Saved" : "♡ Save";
    });
  }
  $$("[data-save]").forEach(function (b) {
    b.addEventListener("click", function () {
      var s = b.getAttribute("data-save"), i = saved.indexOf(s);
      if (i > -1) saved.splice(i, 1); else saved.push(s);
      store.set("gdt-saved", saved); paintSaves();
    });
  });
  paintSaves();

  /* ---------- compare selection ---------- */
  var cmp = store.get("gdt-compare", []);
  var bar = $("#compareBar");
  function paintCompare() {
    $$("[data-compare]").forEach(function (c) { c.checked = cmp.indexOf(c.getAttribute("data-compare")) > -1; });
    if (bar) {
      bar.hidden = cmp.length === 0;
      $("#cmpText").textContent = cmp.length + " of 3 selected";
      $("#cmpGo").href = ROOT + "compare.html?ids=" + cmp.join(",");
    }
  }
  $$("[data-compare]").forEach(function (c) {
    c.addEventListener("change", function () {
      var s = c.getAttribute("data-compare"), i = cmp.indexOf(s);
      if (c.checked && i < 0) { if (cmp.length >= 3) cmp.shift(); cmp.push(s); }
      if (!c.checked && i > -1) cmp.splice(i, 1);
      store.set("gdt-compare", cmp); paintCompare();
    });
  });
  if ($("#cmpClear")) $("#cmpClear").addEventListener("click", function () { cmp = []; store.set("gdt-compare", cmp); paintCompare(); });
  paintCompare();

  /* ---------- directory filters ---------- */
  var grid = $("#toolGrid");
  if (grid) {
    var fq = $("#fq"), fcat = $("#fcat"), fprice = "", onlySaved = false;
    if (params.get("q")) fq.value = params.get("q");
    if (params.get("cat")) fcat.value = params.get("cat");
    var apply = function () {
      var q = fq.value.trim().toLowerCase(), c = fcat.value, n = 0;
      $$(".tcard", grid).forEach(function (card) {
        var hay = (card.dataset.name + " " + card.dataset.tags + " " + card.textContent).toLowerCase();
        var ok = (!q || hay.indexOf(q) > -1) && (!c || card.dataset.cat === c) && (!fprice || card.dataset.price === fprice) &&
          (!onlySaved || saved.indexOf(card.dataset.slug) > -1);
        card.hidden = !ok; if (ok) n++;
      });
      $("#fcount").textContent = n; $("#noResults").hidden = n > 0;
    };
    fq.addEventListener("input", apply); fcat.addEventListener("change", apply);
    $$("#fprice button").forEach(function (b) {
      b.addEventListener("click", function () {
        $$("#fprice button").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on"); fprice = b.dataset.p; apply();
      });
    });
    $("#fsaved").addEventListener("click", function () { onlySaved = !onlySaved; this.classList.toggle("btn-grad", onlySaved); apply(); });
    apply();
  }

  /* ---------- compare page ---------- */
  var ct = $("#cmpTable");
  if (ct) {
    var sels = $$(".cmp-sel");
    var ids = (params.get("ids") || cmp.join(",")).split(",").filter(Boolean).slice(0, 3);
    sels.forEach(function (s, i) { if (ids[i]) s.value = ids[i]; s.addEventListener("change", render); });
    function render() {
      getTools().then(function (list) {
        var pick = sels.map(function (s) { return list.filter(function (t) { return t.slug === s.value; })[0]; }).filter(Boolean);
        if (!pick.length) { ct.innerHTML = '<p class="empty">Choose tools above to compare them.</p>'; return; }
        var row = function (label, fn) { return "<tr><th>" + label + "</th>" + pick.map(function (t) { return "<td>" + fn(t) + "</td>"; }).join("") + "</tr>"; };
        ct.innerHTML = "<table>" +
          row("Tool", function (t) { return '<b><a href="' + ROOT + "tools/" + t.slug + '.html">' + esc(t.name) + "</a></b>"; }) +
          row("Category", function (t) { return esc(t.catName); }) +
          row("Pricing model", function (t) { return esc(t.price); }) +
          row("Best for", function (t) { return esc(t.best); }) +
          row("What it does", function (t) { return esc(t.desc); }) +
          row("Tags", function (t) { return (t.tags || []).map(function (x) { return '<span class="tag">#' + esc(x) + "</span>"; }).join(" "); }) +
          row("Website", function (t) { return '<a href="' + esc(t.url) + '" target="_blank" rel="' + (t.ugc ? "nofollow ugc noopener" : "noopener nofollow") + '">' + esc(t.domain) + " ↗</a>"; }) +
          "</table>";
        history.replaceState(null, "", "?ids=" + pick.map(function (t) { return t.slug; }).join(","));
      });
    }
    render();
  }

  /* ---------- glossary & prompts ---------- */
  var gq = $("#gq");
  if (gq) gq.addEventListener("input", function () {
    var q = gq.value.toLowerCase();
    $$("#glossList .gloss").forEach(function (d) { d.hidden = q && d.textContent.toLowerCase().indexOf(q) < 0; });
  });
  $$("#pseg button").forEach(function (b) {
    b.addEventListener("click", function () {
      $$("#pseg button").forEach(function (x) { x.classList.remove("on"); }); b.classList.add("on");
      $$(".pcard").forEach(function (c) { c.hidden = b.dataset.pc && c.dataset.pc !== b.dataset.pc; });
    });
  });
  function copyText(t, btn) {
    var done = function () { var o = btn.textContent; btn.textContent = "Copied ✓"; setTimeout(function () { btn.textContent = o; }, 1500); };
    if (navigator.clipboard) navigator.clipboard.writeText(t).then(done, done); else { var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); } catch (e) {} ta.remove(); done(); }
  }
  $$("[data-copy]").forEach(function (b) { b.addEventListener("click", function () { copyText($("pre", b.parentNode).textContent, b); }); });
  $$("[data-share]").forEach(function (b) { b.addEventListener("click", function () { if (navigator.share) navigator.share({ title: document.title, url: location.href }).catch(function () {}); else copyText(location.href, b); }); });

  /* ---------- token calculator ---------- */
  if ($("#tcText")) {
    var tc = function () {
      var t = $("#tcText").value, ch = t.length, w = (t.trim().match(/\S+/g) || []).length;
      var tok = Math.round(Math.max(ch / 4, w / 0.75) || 0);
      $("#tcTok").textContent = tok.toLocaleString(); $("#tcWords").textContent = w.toLocaleString(); $("#tcChars").textContent = ch.toLocaleString();
      var pin = +$("#tcIn").value || 0, pout = +$("#tcOut").value || 0, otok = +$("#tcOutTok").value || 0, req = +$("#tcReq").value || 0, cur = $("#tcCur").value || "$";
      var per = tok / 1e6 * pin + otok / 1e6 * pout;
      $("#tcPer").textContent = cur + per.toFixed(per < 0.01 ? 5 : 4);
      $("#tcMonth").textContent = cur + (per * req * 30).toFixed(2);
    };
    $$("#tcText,#tcIn,#tcOut,#tcOutTok,#tcReq,#tcCur").forEach(function (x) { x.addEventListener("input", tc); }); tc();
  }

  /* ---------- prompt builder ---------- */
  if ($("#pb")) {
    var pb = function () {
      var v = function (k) { var el = $('[data-pb="' + k + '"]'); return el.type === "checkbox" ? el.checked : el.value.trim(); };
      var out = [];
      if (v("role")) out.push("Role: You are a " + v("role") + ".");
      if (v("goal")) out.push("Goal: " + v("goal") + ".");
      if (v("aud")) out.push("Audience: " + v("aud") + ".");
      if (v("ctx")) out.push('Context:\n"""\n' + v("ctx") + '\n"""');
      if (v("con")) out.push("Constraints: " + v("con") + ".");
      out.push("Output format: " + v("fmt") + ".");
      if (v("steps")) out.push("Work through the problem step by step, then double-check your answer before giving it.");
      if (v("ask")) out.push("Before you answer, ask me up to 3 clarifying questions if anything important is missing.");
      $("#pbOut").value = out.join("\n\n");
    };
    $$("#pb [data-pb]").forEach(function (x) { x.addEventListener("input", pb); x.addEventListener("change", pb); }); pb();
    $("#pbCopy").addEventListener("click", function () { copyText($("#pbOut").value, this); });
  }

  /* ---------- ROI calculator ---------- */
  if ($("#roiH")) {
    var roi = function () {
      var h = +$("#roiH").value || 0, r = +$("#roiR").value || 0, n = +$("#roiN").value || 0, c = +$("#roiC").value || 0, s = +$("#roiS").value || 0, cur = $("#roiCur").value || "$";
      var val = h * 4.33 * r * n, cost = c * n, net = val - cost, x = cost ? val / cost : 0;
      var payDays = net > 0 ? (s * r * n + cost) / (val / 30) : Infinity;
      var f = function (v) { return cur + Math.round(v).toLocaleString(); };
      $("#roiVal").textContent = f(val); $("#roiNet").textContent = f(net);
      $("#roiX").textContent = cost ? x.toFixed(1) + "×" : "∞";
      $("#roiPay").textContent = isFinite(payDays) ? Math.max(1, Math.ceil(payDays)) + " days" : "Never";
      var vd = $("#roiVerdict");
      vd.className = "verdict " + (net > 0 ? "good" : "bad");
      vd.textContent = net > 0 ? "✓ Worth it: this tool creates about " + f(net * 12) + " of net value per year." : "✗ Not worth it at this usage. Save more hours, pick a cheaper plan, or stay on the free tier.";
    };
    $$("#roiH,#roiR,#roiN,#roiC,#roiS,#roiCur").forEach(function (x) { x.addEventListener("input", roi); }); roi();
  }

  /* ---------- forms ---------- */
  function collect(form) {
    var data = {}, fd = new FormData(form);
    fd.forEach(function (v, k) { if (k === "_honey") return; data[k] = data[k] ? data[k] + ", " + v : v; });
    return data;
  }
  function submitForm(form, onOk) {
    var st = $(".form-status", form), btn = $('button[type="submit"]', form);
    var hp = $('[name="_honey"]', form);
    if (hp && hp.value) return; // bot
    if (!form.checkValidity()) { form.reportValidity(); return; }
    var data = collect(form);
    data._subject = form.getAttribute("data-subject") || "New message — GDTai";
    data._template = "table"; data._captcha = "false";
    data.form = form.getAttribute("data-form"); data.page = location.href; data.submitted_at = new Date().toISOString();
    if (btn) { btn.disabled = true; btn.dataset.t = btn.textContent; btn.textContent = "Sending…"; }
    if (st) { st.className = "form-status"; st.textContent = ""; }
    fetch(endpoint(), { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(data) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || j.success === "false" || j.success === false) throw new Error(j.message || "Error"); return j; }); })
      .then(function () {
        if (st) { st.className = "form-status ok"; st.textContent = "✓ Thank you! Your message was sent. We'll be in touch soon."; }
        var rev = form.getAttribute("data-reveal"); if (rev && $("#" + rev)) $("#" + rev).hidden = false;
        if (onOk) onOk(data); else form.reset();
        try { (window.dataLayer = window.dataLayer || []).push({ event: "lead", form: data.form }); } catch (e) {}
      })
      .catch(function () {
        if (st) { st.className = "form-status err"; st.textContent = "Sorry, something went wrong. Please try again in a minute."; }
      })
      .then(function () { if (btn) { btn.disabled = false; btn.textContent = btn.dataset.t; } });
  }
  $$("form.gform").forEach(function (f) {
    if (f.id === "wizard") return;
    f.addEventListener("submit", function (e) { e.preventDefault(); submitForm(f); });
  });

  /* plan / role / donate shortcuts */
  $$("[data-plan]").forEach(function (a) { a.addEventListener("click", function () { var s = $("#planSel"); if (s) s.value = a.dataset.plan; }); });
  $$("[data-role]").forEach(function (a) { a.addEventListener("click", function () { var s = $("#roleSel"); if (s) s.value = a.dataset.role; }); });
  var dl = $("#donateLinks");
  if (dl && CFG.donate) {
    var labels = { paypal: "PayPal", kofi: "Ko-fi", buymeacoffee: "Buy Me a Coffee", upi: "UPI", github: "GitHub Sponsors" };
    dl.innerHTML = Object.keys(labels).filter(function (k) { return CFG.donate[k]; }).map(function (k) {
      return '<a class="btn btn-ghost" target="_blank" rel="noopener" href="' + esc(CFG.donate[k]) + '">Donate via ' + labels[k] + "</a>";
    }).join("");
  }
  $$("[data-donate]").forEach(function (b) {
    b.addEventListener("click", function () {
      var amt = b.dataset.donate, pp = CFG.donate && CFG.donate.paypal;
      if (pp && amt !== "custom") { window.open(pp + (pp.indexOf("?") > -1 ? "&" : "?") + "amount=" + amt, "_blank", "noopener"); return; }
      var a = $("#donAmt"); if (a) { a.value = amt === "custom" ? "" : amt; }
      location.hash = "pledge"; setTimeout(function () { (a || {}).focus && a.focus(); }, 300);
    });
  });

  /* ---------- wizard ---------- */
  var wz = $("#wizard");
  if (wz) {
    var steps = $$(".wz-step", wz), i = 0, back = $("#wzBack"), next = $("#wzNext"), sub = $("#wzSubmit");
    if (params.get("tool") && $("#refTool")) $("#refTool").value = params.get("tool");
    var show = function () {
      steps.forEach(function (s, k) { s.classList.toggle("on", k === i); });
      $("#wzBar").style.width = ((i + 1) / steps.length * 100) + "%"; $("#wzNum").textContent = i + 1;
      back.disabled = i === 0; next.hidden = i === steps.length - 1; sub.hidden = i !== steps.length - 1;
    };
    var valid = function () {
      var ok = true;
      $$("input[required],select[required],textarea[required]", steps[i]).forEach(function (el) {
        if (el.type === "radio") { if (!$('input[name="' + el.name + '"]:checked', steps[i])) ok = false; }
        else if (!el.checkValidity()) ok = false;
      });
      if (!ok) { var st = $(".form-status", wz); st.className = "form-status err"; st.textContent = "Please complete this step to continue."; setTimeout(function () { st.textContent = ""; }, 2500); }
      return ok;
    };
    next.addEventListener("click", function () { if (valid()) { i++; show(); wz.scrollIntoView({ behavior: "smooth", block: "start" }); } });
    back.addEventListener("click", function () { if (i > 0) { i--; show(); } });
    $$(".opt input[type=radio]", wz).forEach(function (r) { r.addEventListener("change", function () { setTimeout(function () { if (i < steps.length - 1 && valid()) { i++; show(); } }, 220); }); });
    wz.addEventListener("submit", function (e) {
      e.preventDefault();
      submitForm(wz, function (data) {
        var map = { "AI Chatbots & Assistants": "chatbots", "Writing & Copy": "writing", "Image Generation & Editing": "image", "Video Creation & Editing": "video", "Voice, Music & Audio": "audio", "Coding & App Builders": "coding", "Productivity & Meetings": "productivity", "Research & Knowledge": "research", "Marketing & SEO": "marketing", "Design & Websites": "design", "Automation & AI Agents": "automation", "Data & Analytics": "data" };
        var want = String(data.interests || "").split(", ").map(function (x) { return map[x]; }).filter(Boolean);
        if (!want.length) want = ["chatbots", "productivity", "automation"];
        var freeOnly = /Free tools only/.test(data.budget || "");
        var picks = [];
        want.forEach(function (c) {
          var pool = (window.GDT_TOOLS || []).filter(function (t) { return t.c === c && (!freeOnly || t.p === "Free" || t.p === "Freemium"); });
          picks = picks.concat(pool.slice(0, 2));
        });
        $("#wzTools").innerHTML = picks.slice(0, 8).map(function (t) { return '<a class="chip" href="' + ROOT + "tools/" + t.s + '.html">' + esc(t.n) + "</a>"; }).join("");
        $("#wzPreview").hidden = false;
        steps.forEach(function (s) { s.classList.remove("on"); });
        $(".wz-nav", wz).hidden = true; $(".wz-progress", wz).hidden = true; $(".wz-step-label", wz).hidden = true;
      });
    });
    show();
  }

  /* ---------- YouTube lite embeds ---------- */
  $$("[data-yt]").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(b.dataset.yt) + "?autoplay=1&rel=0";
      f.title = "YouTube video"; f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"; f.allowFullscreen = true;
      b.innerHTML = ""; b.appendChild(f);
    }, { once: true });
  });

  /* ---------- manual ad units (optional; Auto ads work without this) ---------- */
  var slots = CFG.adSlots || {};
  $$(".ad-slot[data-ad]").forEach(function (el) {
    var side = el.parentNode.classList.contains("ad-side");
    var id = side ? (slots.side || slots.inline) : slots.inline;
    if (!id) return;
    el.innerHTML = '<ins class="adsbygoogle" style="display:block" data-ad-client="' + CFG.adClient + '" data-ad-slot="' + id + '" data-ad-format="auto" data-full-width-responsive="true"></ins>';
    el.parentNode.classList.add("filled");
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) {}
  });

  /* ---------- cookie consent ---------- */
  var ck = $("#cookie");
  if (ck && !store.get("gdt-consent-set", false)) ck.hidden = false;
  $$("[data-consent]").forEach(function (b) {
    b.addEventListener("click", function () {
      try { localStorage.setItem("gdt-consent", b.dataset.consent); } catch (e) {}
      store.set("gdt-consent-set", true); ck.hidden = true;
      if (b.dataset.consent === "essential") (window.adsbygoogle = window.adsbygoogle || []).requestNonPersonalizedAds = 1;
    });
  });
  $$("[data-cookie-settings]").forEach(function (a) { a.addEventListener("click", function (e) { e.preventDefault(); if (ck) ck.hidden = false; }); });

  /* ---------- reveal, counters, back-to-top ---------- */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } }); }, { threshold: .12 });
    $$(".reveal").forEach(function (el) { io.observe(el); });
    var co = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (!en.isIntersecting) return; co.unobserve(en.target);
        var el = en.target, end = +el.dataset.count, t0 = performance.now();
        var tick = function (t) { var p = Math.min(1, (t - t0) / 900); el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(tick); };
        requestAnimationFrame(tick);
      });
    });
    $$("[data-count]").forEach(function (el) { co.observe(el); });
  } else { $$(".reveal").forEach(function (el) { el.classList.add("in"); }); }
  var tt = $("#toTop");
  if (tt) {
    window.addEventListener("scroll", function () { tt.classList.toggle("show", scrollY > 700); }, { passive: true });
    tt.addEventListener("click", function () { scrollTo({ top: 0, behavior: "smooth" }); });
  }
})();
