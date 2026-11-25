#!/usr/bin/env python3
"""GDTai static site generator.

Renders every page of the site from Python data + content/ + data/*.json into
the repository root, so GitHub Pages (branch: main, folder: /) can serve it.

Run:  python3 builder/build.py
"""
import datetime as dt
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "builder"))

from tools_data import CATEGORIES, T, SUBMITTED  # noqa: E402
from content_data import GLOSSARY, PROMPTS  # noqa: E402

SITE_NAME = "GDTai"
TAGLINE = "Guide · Discover · Test AI"
ADSENSE_CLIENT = "ca-pub-6620975821265271"
ADSENSE_TAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
               '?client=ca-pub-6620975821265271" crossorigin="anonymous"></script>')
INTEREST_URL = "https://web.works/contact"
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.strftime("%Y-%m-%d")
YEAR = NOW.year


def site_url():
    cname = os.path.join(ROOT, "CNAME")
    if os.path.exists(cname):
        dom = open(cname).read().strip()
        if dom:
            return "https://" + dom
    return os.environ.get("SITE_URL", "https://webworksa1.github.io/gdtai-com").rstrip("/")


SITE = site_url()
e = html.escape
PAGES = []  # for sitemap


def slugify(s):
    s = s.lower().replace("&", "and").replace(".", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def domain(url):
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


def load_json(name, default):
    p = os.path.join(ROOT, "data", name)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


# ---------------------------------------------------------------- data model
CAT = {c[0]: {"slug": c[0], "name": c[1], "desc": c[2], "icon": c[3]} for c in CATEGORIES}
TOOLS = []
for (name, url, cat, price, desc, best, tags) in T:
    TOOLS.append({"name": name, "slug": slugify(name), "url": url, "cat": cat, "price": price,
                  "desc": desc, "best": best, "tags": tags, "domain": domain(url)})
for (name, url, cat, price, desc, best, tags, review) in SUBMITTED:
    if not url.startswith("https://") or cat not in CAT or any(t["slug"] == slugify(name) for t in TOOLS) \
            or not all(review.get(k) for k in ("reviewed", "fit", "summary")):
        raise SystemExit(f"Rejected submitted tool {name!r}: needs an https:// URL, a known category, a unique slug and a completed review")
    TOOLS.append({"name": name, "slug": slugify(name), "url": url, "cat": cat, "price": price,
                  "desc": desc, "best": best, "tags": tags, "domain": domain(url), "ugc": True, "review": review})
BY_CAT = {}
for t in TOOLS:
    BY_CAT.setdefault(t["cat"], []).append(t)
PICKS = ["chatgpt", "claude", "perplexity", "cursor", "elevenlabs", "runway", "canva", "zapier",
         "notebooklm", "midjourney", "gamma", "n8n"]

GUIDES = []
gdir = os.path.join(ROOT, "content", "guides")
for fn in sorted(os.listdir(gdir)):
    if not fn.endswith(".html"):
        continue
    raw = open(os.path.join(gdir, fn), encoding="utf-8").read()
    m = re.match(r"<!--(.*?)-->(.*)", raw, re.S)
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    words = len(re.sub(r"<[^>]+>", " ", m.group(2)).split())
    GUIDES.append({"slug": fn[:-5], "body": m.group(2).strip(), "words": words, **meta})

NEWS = load_json("news.json", {"updated": None, "items": [], "papers": []})
VIDEOS = load_json("videos.json", {"updated": None, "items": []})
REPOS = load_json("repos.json", {"updated": None, "items": []})

CHANNELS = [
    ("Two Minute Papers", "@TwoMinutePapers", "Research papers explained in minutes"),
    ("Matt Wolfe", "@mreflow", "Weekly AI news and tool walkthroughs"),
    ("AI Explained", "@aiexplained-official", "Deep dives on model releases"),
    ("Fireship", "@Fireship", "Fast-paced developer and AI explainers"),
    ("Andrej Karpathy", "@AndrejKarpathy", "Neural networks from scratch"),
    ("3Blue1Brown", "@3blue1brown", "Visual intuition for deep learning"),
    ("Google DeepMind", "@googledeepmind", "Research and product updates"),
    ("Yannic Kilcher", "@YannicKilcher", "ML paper reviews"),
]

# ---------------------------------------------------------------- layout
NAV = [("tools/index.html", "AI Tools"), ("news.html", "News"), ("videos.html", "Videos"),
       ("guides/index.html", "Guides"), ("free-tools/index.html", "Free Tools"), ("prompts.html", "Prompts")]

LOGO = ('<svg class="logo-mark" viewBox="0 0 40 40" aria-hidden="true"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#7c3aed"/><stop offset="1" stop-color="#06b6d4"/></linearGradient></defs>'
        '<rect width="40" height="40" rx="11" fill="url(#lg)"/><path d="M12 21.5a8 8 0 1 0 8-8.5" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/>'
        '<path d="M20 21h8" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/><circle cx="28.5" cy="12" r="2.6" fill="#fff"/></svg>')


def head(path, title, desc, root, schema=None, noindex=False, og_type="website"):
    url = SITE + "/" + (path[:-10] if path.endswith("index.html") else path)
    full = title if title.startswith(SITE_NAME) else f"{title} | {SITE_NAME}"
    ld = ""
    for s in (schema or []):
        ld += '<script type="application/ld+json">' + json.dumps(s, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
{robots}
<link rel="canonical" href="{e(url)}">
<meta name="google-adsense-account" content="{ADSENSE_CLIENT}">
<meta name="theme-color" content="#7c3aed">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(full)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{SITE}/assets/img/og.svg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/img/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="{root}manifest.webmanifest">
<link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin>
<link rel="stylesheet" href="{root}assets/css/style.css?v={TODAY}">
<script>(function(){{try{{var t=localStorage.getItem('gdt-theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}}})();</script>
{ADSENSE_TAG}
{ld}
</head>
<body data-root="{root}">
<a class="skip" href="#main">Skip to content</a>
<div class="interest-bar" role="note"><div class="wrap">
<span class="ib-dot" aria-hidden="true"></span>
<a href="{INTEREST_URL}" target="_blank" rel="noopener nofollow">Contact, if you are interested in this website/domain name/Sponsorship/Advertisement/Partnership</a>
</div></div>
"""


def header(root, active=""):
    links = "".join(
        f'<a href="{root}{p}"{" aria-current=page" if active == p else ""}>{e(n)}</a>' for p, n in NAV)
    return f"""<header class="site-header"><div class="wrap nav">
<a class="brand" href="{root}index.html" aria-label="{SITE_NAME} home">{LOGO}<span><b>GDT</b>ai</span></a>
<nav class="menu" id="menu" aria-label="Main">{links}
<a class="menu-cta-m" href="{root}get-matched.html">Get matched free</a></nav>
<div class="nav-actions">
<button class="icon-btn" id="searchBtn" aria-label="Search tools (press /)"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg></button>
<button class="icon-btn" id="themeBtn" aria-label="Toggle dark mode"><svg viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
<a class="btn btn-sm btn-grad hide-m" href="{root}get-matched.html">Get matched</a>
<button class="icon-btn burger" id="burger" aria-label="Open menu" aria-controls="menu" aria-expanded="false"><svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
</div></div></header>
<div class="search-overlay" id="searchOverlay" hidden><div class="search-box">
<input id="globalSearch" type="search" placeholder="Search {len(TOOLS)}+ AI tools, categories, guides…" autocomplete="off" aria-label="Search">
<div id="searchResults" class="search-results"></div><p class="muted small">Press <kbd>Esc</kbd> to close · <kbd>/</kbd> to open</p></div></div>
"""


def ad(label="Advertisement", cls=""):
    return f'<div class="ad-wrap {cls}"><span class="ad-label">{label}</span><div class="ad-slot" data-ad></div></div>'


def newsletter_band(root):
    return f"""<section class="newsletter-band"><div class="wrap nl-grid">
<div><h2>Get the 5-minute AI briefing</h2><p>New tools, honest picks and practical how-tos. Twice a week. Free. Unsubscribe anytime.</p>
<ul class="ticks"><li>Hand-picked tools, no fluff</li><li>Free prompt packs &amp; checklists</li><li>Early access to contests</li></ul></div>
<form class="gform nl-form" data-form="newsletter" data-subject="New newsletter subscriber — GDTai" novalidate>
<label class="sr" for="nl-email">Email</label>
<input id="nl-email" name="email" type="email" required placeholder="you@company.com" autocomplete="email">
<input type="hidden" name="source" value="newsletter-band">
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad" type="submit">Subscribe free</button>
<p class="form-status" aria-live="polite"></p>
<p class="tiny muted">By subscribing you agree to our <a href="{root}privacy.html">Privacy Policy</a>.</p>
</form></div></section>"""


def footer(root):
    cats = "".join(f'<li><a href="{root}category/{c[0]}.html">{e(c[1])}</a></li>' for c in CATEGORIES[:8])
    return f"""{newsletter_band(root)}
<footer class="site-footer"><div class="wrap">
<div class="foot-grid">
<div class="foot-brand"><a class="brand" href="{root}index.html">{LOGO}<span><b>GDT</b>ai</span></a>
<p>{TAGLINE}. An independent, self-updating hub to find, compare and learn AI tools — with free utilities, daily news and practical guides.</p>
<div class="foot-cta"><a class="btn btn-sm btn-grad" href="{root}get-matched.html">Get your AI stack</a> <a class="btn btn-sm btn-ghost" href="{root}support.html">♥ Support us</a></div></div>
<div><h4>Categories</h4><ul>{cats}</ul></div>
<div><h4>Resources</h4><ul>
<li><a href="{root}tools/index.html">AI Tools Directory</a></li><li><a href="{root}compare.html">Compare Tools</a></li>
<li><a href="{root}news.html">AI News</a></li><li><a href="{root}videos.html">AI Videos</a></li>
<li><a href="{root}guides/index.html">Guides</a></li><li><a href="{root}glossary.html">AI Glossary</a></li>
<li><a href="{root}prompts.html">Prompt Library</a></li><li><a href="{root}free-tools/index.html">Free AI Utilities</a></li></ul></div>
<div><h4>Grow with us</h4><ul>
<li><a href="{root}get-matched.html">Free AI Stack Match</a></li><li><a href="{root}submit-tool.html">Submit / Feature a Tool</a></li>
<li><a href="{root}advertise.html">Advertise &amp; Sponsor</a></li><li><a href="{root}contests.html">Contests &amp; Prizes</a></li>
<li><a href="{root}careers.html">Careers / Contribute</a></li><li><a href="{root}support.html">Donate / Support</a></li></ul></div>
<div><h4>Company</h4><ul>
<li><a href="{root}about.html">About</a></li><li><a href="{root}contact.html">Contact</a></li>
<li><a href="{root}privacy.html">Privacy Policy</a></li><li><a href="{root}terms.html">Terms of Use</a></li>
<li><a href="{root}disclaimer.html">Disclaimer &amp; Trademarks</a></li><li><a href="#" data-cookie-settings>Cookie settings</a></li></ul></div>
</div>
<div class="foot-legal">
<p><strong>Trademark &amp; copyright notice:</strong> "GDTai" is used solely as the descriptive name of this independent website and is not affiliated with, endorsed by or connected to any company, product or registered mark using "GDT", "GDTai" or similar names. All third-party product names, logos and trademarks shown belong to their respective owners and are used for identification only. <a href="{root}disclaimer.html">Full disclosure</a>.</p>
<p>© {YEAR} GDTai. Original content licensed for personal reading; do not republish without permission. Last automatic update: <time datetime="{NOW.isoformat()}">{NOW.strftime("%d %b %Y, %H:%M UTC")}</time>.</p>
</div></div></footer>
<div class="cookie" id="cookie" hidden><p>We use cookies for essential features, analytics and to show ads (including personalised ads from Google). See our <a href="{root}privacy.html">Privacy Policy</a>.</p>
<div><button class="btn btn-sm btn-ghost" data-consent="essential">Essential only</button> <button class="btn btn-sm btn-grad" data-consent="all">Accept all</button></div></div>
<button class="to-top" id="toTop" aria-label="Back to top">↑</button>
<script src="{root}assets/js/config.js?v={TODAY}"></script>
<script src="{root}assets/js/app.js?v={TODAY}" defer></script>
</body></html>"""


def write(path, title, desc, body, schema=None, active="", noindex=False, priority="0.6", og_type="website", changefreq="weekly"):
    depth = path.count("/")
    root = "../" * depth
    html_doc = head(path, title, desc, root, schema, noindex, og_type) + header(root, active) + \
        f'<main id="main">{body(root) if callable(body) else body}</main>' + footer(root)
    out = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    if not noindex:
        PAGES.append((path, priority, changefreq))


def crumbs(root, items):
    parts = [f'<a href="{root}index.html">Home</a>']
    for href, label in items:
        parts.append(f'<a href="{root}{href}">{e(label)}</a>' if href else f'<span>{e(label)}</span>')
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": lbl, "item": SITE + "/" + (h or "")}
        for i, (h, lbl) in enumerate([("", "Home")] + items)]}
    return '<nav class="crumbs" aria-label="Breadcrumb">' + " / ".join(parts) + "</nav>", ld


def logo_img(t, size=40):
    return (f'<img class="tlogo" src="https://www.google.com/s2/favicons?domain={t["domain"]}&sz=64" alt="" width="{size}" height="{size}" '
            f'loading="lazy" data-letter="{e(t["name"][0])}">')


def out_rel(t):
    return "nofollow ugc noopener" if t.get("ugc") else "noopener nofollow"


def review_line(t):
    rv = t.get("review")
    if rv:
        return f"In our assessment it is a good fit for <strong>{e(rv['fit'])}</strong>."
    return f"We list it as best for <strong>{e(t['best'].lower())}</strong>."


def review_block(t, r):
    rv = t.get("review")
    if not rv:
        return ""
    return (f'<h2>How we reviewed {e(t["name"])}</h2><p>{e(rv["summary"])}</p>'
            f'<p class="small muted">Listing submitted by the maker and reviewed by GDTai on {e(fmt_date(rv["reviewed"]))} '
            f'against our <a href="{r}about.html#editorial">editorial policy</a>.</p>')


def price_cls(p):
    return {"Free": "p-free", "Freemium": "p-freemium", "Paid": "p-paid", "Free trial": "p-trial"}.get(p, "")


def tool_card(t, root):
    c = CAT[t["cat"]]
    return f"""<article class="tcard" data-name="{e(t['name'].lower())}" data-cat="{t['cat']}" data-price="{e(t['price'])}" data-tags="{e(' '.join(t['tags']))}" data-slug="{t['slug']}">
<div class="tc-top">{logo_img(t)}<div><h3><a href="{root}tools/{t['slug']}.html">{e(t['name'])}</a></h3>
<a class="tc-cat" href="{root}category/{c['slug']}.html">{c['icon']} {e(c['name'])}</a></div>
<button class="save" data-save="{t['slug']}" aria-label="Save {e(t['name'])}" title="Save">♡</button></div>
<p>{e(t['desc'])}</p>
<div class="tc-foot"><span class="badge {price_cls(t['price'])}">{e(t['price'])}</span>
<label class="cmp"><input type="checkbox" data-compare="{t['slug']}"> Compare</label>
<a class="tc-go" href="{root}tools/{t['slug']}.html" aria-label="View {e(t['name'])} details">Details →</a></div></article>"""


def fmt_date(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return s or ""


def news_list(items, limit):
    if not items:
        return '<p class="empty">Fresh headlines load automatically every few hours. Check back shortly.</p>'
    out = []
    for it in items[:limit]:
        out.append(f'<li><a href="{e(it["url"])}" target="_blank" rel="noopener nofollow">{e(it["title"])}</a>'
                   f'<span class="meta">{e(it.get("source", ""))} · {fmt_date(it.get("date", ""))}</span></li>')
    return '<ul class="news-list">' + "".join(out) + "</ul>"


def video_grid(items, limit):
    if not items:
        return '<p class="empty">Latest AI videos from top creators are fetched automatically. Browse the channels below in the meantime.</p>'
    out = []
    for v in items[:limit]:
        vid = e(v["id"])
        out.append(f'<article class="vcard"><button class="yt" data-yt="{vid}" aria-label="Play: {e(v["title"])}">'
                   f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><span class="play">▶</span></button>'
                   f'<h3>{e(v["title"])}</h3><p class="meta">{e(v.get("channel", ""))} · {fmt_date(v.get("date", ""))}</p></article>')
    return '<div class="vgrid">' + "".join(out) + "</div>"


def repo_list(items, limit):
    if not items:
        return '<p class="empty">Trending open-source AI repositories refresh automatically.</p>'
    out = []
    for r in items[:limit]:
        out.append(f'<li><a href="{e(r["url"])}" target="_blank" rel="noopener nofollow">{e(r["name"])}</a>'
                   f'<span class="meta">★ {r.get("stars", 0):,} · {e(r.get("lang") or "—")}</span>'
                   f'<p>{e((r.get("desc") or "")[:140])}</p></li>')
    return '<ul class="repo-list">' + "".join(out) + "</ul>"


def faq_block(qas):
    html_ = '<div class="faq">' + "".join(
        f'<details><summary>{e(q)}</summary><p>{a}</p></details>' for q, a in qas) + "</div>"
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in qas]}
    return html_, ld


# ---------------------------------------------------------------- pages
def build_home():
    picks = [t for s in PICKS for t in TOOLS if t["slug"] == s]
    home_faq = [
        ("What is GDTai?", "GDTai (Guide · Discover · Test AI) is an independent, self-updating hub where you can find and compare AI tools, read practical guides, use free AI utilities and follow the latest AI news and videos."),
        ("Is GDTai free to use?", "Yes. Browsing the directory, guides, prompt library and free utilities is completely free. The site is supported by advertising, sponsorships and reader donations."),
        ("How do you choose which AI tools to list?", "We list tools that are live, clearly useful and transparent about pricing. Tools submitted by their makers are reviewed against the same criteria before they are listed, and their pages say when and how we reviewed them. Editorial picks are never sold; sponsored placements are always labelled. Read our <a href='about.html#editorial'>editorial policy</a>."),
        ("Can you recommend the right AI tools for my business?", "Yes — use the free <a href='get-matched.html'>AI Stack Match</a>. Answer five quick questions and we will send a tailored shortlist and rollout plan."),
        ("How often is the content updated?", "News, research papers, trending repositories and videos are refreshed automatically several times a day. The tool directory and guides are edited by hand: submitted tools are reviewed before they are listed, and reported errors are corrected."),
    ]
    faq_html, faq_ld = faq_block(home_faq)
    cats = "".join(f'<a class="cat-tile" href="{{r}}category/{c[0]}.html"><span class="ct-ico">{c[3]}</span><b>{e(c[1])}</b><small>{len(BY_CAT.get(c[0], []))} tools</small></a>' for c in CATEGORIES)
    chips = "".join(f'<a class="chip" href="{{r}}category/{c}.html">{l}</a>' for c, l in [("chatbots", "Chatbots"), ("image", "Image"), ("video", "Video"), ("coding", "Coding"), ("writing", "Writing"), ("automation", "Agents"), ("audio", "Voice &amp; music"), ("marketing", "SEO")])
    guides = "".join(f'<a class="gcard" href="{{r}}guides/{g["slug"]}.html"><span class="pill">{e(g["category"])}</span><h3>{e(g["title"])}</h3><p>{e(g["description"])}</p><span class="meta">{g["read"]} min read →</span></a>' for g in GUIDES[:3])
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE + "/",
           "description": "Find, compare and learn AI tools.",
           "potentialAction": {"@type": "SearchAction", "target": SITE + "/tools/?q={search_term_string}", "query-input": "required name=search_term_string"}},
          {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": SITE + "/", "logo": SITE + "/assets/img/favicon.svg"}, faq_ld]

    def body(r):
        return f"""
<section class="hero"><div class="hero-bg" aria-hidden="true"><span></span><span></span><span></span></div>
<div class="wrap hero-grid">
<div class="hero-copy reveal">
<span class="eyebrow">✦ {TAGLINE}</span>
<h1>Find the <span class="grad">right AI tool</span> for any job — in seconds.</h1>
<p class="sub">Search a hand-curated directory of {len(TOOLS)}+ AI tools across {len(CATEGORIES)} categories, compare them side by side, and get a free personalised AI stack for your business.</p>
<form class="hero-search" action="{r}tools/index.html" method="get" role="search">
<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
<input name="q" type="search" placeholder="Try “video editing”, “free”, “write emails”…" aria-label="Search AI tools">
<button class="btn btn-grad" type="submit">Search</button></form>
<div class="chips">{chips.replace("{r}", r)}</div>
<div class="stats"><div><b data-count="{len(TOOLS)}">{len(TOOLS)}</b><span>AI tools</span></div><div><b data-count="{len(CATEGORIES)}">{len(CATEGORIES)}</b><span>categories</span></div><div><b data-count="{len(GUIDES)}">{len(GUIDES)}</b><span>in-depth guides</span></div><div><b>24/7</b><span>auto-updated</span></div></div>
</div>
<aside class="hero-card reveal" aria-label="Free AI stack match">
<span class="pill pill-hot">Free · 60 seconds</span>
<h2>Get your personalised AI stack</h2>
<p>Tell us your goal. We reply with a shortlist of tools, a rollout plan and cost estimate — no obligation.</p>
<form class="gform mini-lead" data-form="quick-lead" data-subject="Quick AI stack request — GDTai" novalidate>
<label>Your main goal<select name="goal" required><option value="">Choose one…</option><option>Create content faster</option><option>Automate repetitive work</option><option>Get more leads &amp; sales</option><option>Customer support with AI</option><option>Build an AI product / app</option><option>Learn AI for my career</option></select></label>
<label>Work email<input name="email" type="email" required placeholder="you@company.com" autocomplete="email"></label>
<input type="hidden" name="source" value="home-hero">
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad btn-block" type="submit">Send my free AI stack →</button>
<p class="form-status" aria-live="polite"></p>
<p class="tiny muted">🔒 No spam. We reply within 48 hours. <a href="{r}get-matched.html">Want a detailed match?</a></p>
</form></aside></div></section>

<div class="wrap">{ad()}</div>

<section class="section"><div class="wrap">
<div class="sec-head"><div><h2>Browse by category</h2><p>Start with the job you need done.</p></div><a class="link-more" href="{r}tools/index.html">All tools →</a></div>
<div class="cat-grid">{cats.replace("{r}", r)}</div></div></section>

<section class="section alt"><div class="wrap">
<div class="sec-head"><div><h2>Editor's picks</h2><p>The tools we would install first — chosen on quality, value and reliability, never paid placement.</p></div><a class="link-more" href="{r}compare.html">Compare tools →</a></div>
<div class="tgrid">{"".join(tool_card(t, r) for t in picks)}</div></div></section>

<section class="section"><div class="wrap lead-band reveal">
<div><span class="eyebrow">For businesses</span><h2>Stop guessing. Get an AI stack built for your workflow.</h2>
<p>Our free AI Stack Match analyses your goals, team and budget and recommends the exact tools and first automations to deploy — plus where you could save on subscriptions.</p>
<ul class="ticks"><li>Personal shortlist of 3–7 tools</li><li>30-day rollout plan</li><li>Expert partners for implementation (optional)</li></ul></div>
<div class="lb-cta"><a class="btn btn-lg btn-grad" href="{r}get-matched.html">Start my free match</a><a class="btn btn-lg btn-ghost" href="{r}free-tools/roi-calculator.html">Calculate my AI ROI</a></div></div></section>

<section class="section alt"><div class="wrap two-col">
<div><div class="sec-head"><div><h2>Latest AI news</h2><p>Auto-curated from leading sources every few hours.</p></div><a class="link-more" href="{r}news.html">More →</a></div>
{news_list(NEWS.get("items", []), 8)}</div>
<div><div class="sec-head"><div><h2>Trending on GitHub</h2><p>Open-source AI projects gaining stars.</p></div></div>
{repo_list(REPOS.get("items", []), 5)}</div></div></section>

<section class="section"><div class="wrap">
<div class="sec-head"><div><h2>Watch &amp; learn</h2><p>Fresh tutorials and explainers from top AI creators.</p></div><a class="link-more" href="{r}videos.html">All videos →</a></div>
{video_grid(VIDEOS.get("items", []), 4)}</div></section>

<div class="wrap">{ad()}</div>

<section class="section alt"><div class="wrap">
<div class="sec-head"><div><h2>Free AI utilities</h2><p>No sign-up. Runs in your browser.</p></div><a class="link-more" href="{r}free-tools/index.html">All utilities →</a></div>
<div class="util-grid">
<a class="util" href="{r}free-tools/token-calculator.html"><b>🧮 Token &amp; cost calculator</b><span>Estimate tokens and API costs for any text.</span></a>
<a class="util" href="{r}free-tools/prompt-builder.html"><b>🛠️ Prompt builder</b><span>Turn a rough idea into a structured prompt.</span></a>
<a class="util" href="{r}free-tools/roi-calculator.html"><b>📈 AI ROI calculator</b><span>See if an AI subscription pays for itself.</span></a>
<a class="util" href="{r}get-matched.html"><b>🎯 AI stack match</b><span>Five questions → your personalised toolkit.</span></a>
</div></div></section>

<section class="section"><div class="wrap">
<div class="sec-head"><div><h2>Guides that actually help</h2><p>Practical, original, no-hype explainers.</p></div><a class="link-more" href="{r}guides/index.html">All guides →</a></div>
<div class="ggrid">{guides.replace("{r}", r)}</div></div></section>

<section class="section alt"><div class="wrap three-cta">
<a class="cta-card" href="{r}submit-tool.html"><span>🚀</span><h3>Built an AI tool?</h3><p>Submit it free or get featured in front of thousands of AI buyers.</p><b>Submit your tool →</b></a>
<a class="cta-card" href="{r}advertise.html"><span>📣</span><h3>Advertise &amp; sponsor</h3><p>Category sponsorships, newsletter slots and sponsored guides.</p><b>See packages →</b></a>
<a class="cta-card" href="{r}contests.html"><span>🏆</span><h3>Monthly AI Build Challenge</h3><p>Build something with AI, win prizes and get featured.</p><b>Enter the contest →</b></a>
</div></section>

<section class="section"><div class="wrap narrow"><h2>Frequently asked questions</h2>{faq_html}
<p class="center"><a class="btn btn-ghost" href="{r}support.html">♥ Support independent AI curation</a></p></div></section>
"""
    write("index.html", "GDTai — Find, Compare & Learn the Best AI Tools",
          f"Discover {len(TOOLS)}+ curated AI tools across {len(CATEGORIES)} categories, compare them side by side, read practical guides, use free AI utilities and get a free personalised AI stack.",
          body, ld, priority="1.0", changefreq="daily")


def build_tools_index():
    cats_opts = "".join(f'<option value="{c[0]}">{e(c[1])}</option>' for c in CATEGORIES)
    items = ld_itemlist("AI Tools Directory", [(t["name"], f"tools/{t['slug']}.html") for t in TOOLS])
    cr, crld = crumbs("../", [("tools/index.html", "AI Tools")])

    def body(r):
        return f"""<section class="page-hero"><div class="wrap">{cr}
<h1>AI Tools Directory</h1><p class="sub">{len(TOOLS)} hand-picked AI tools across {len(CATEGORIES)} categories. Filter, save favourites (♡) and compare up to 3 side by side.</p></div></section>
<section class="section tight"><div class="wrap">
<div class="filters" role="search">
<input id="fq" type="search" placeholder="Search by name, use case or tag…" aria-label="Search tools">
<select id="fcat" aria-label="Category"><option value="">All categories</option>{cats_opts}</select>
<div class="seg" id="fprice" role="group" aria-label="Pricing">
<button data-p="" class="on">All</button><button data-p="Free">Free</button><button data-p="Freemium">Freemium</button><button data-p="Free trial">Trial</button><button data-p="Paid">Paid</button></div>
<button class="btn btn-sm btn-ghost" id="fsaved">♡ Saved</button></div>
<p class="muted small"><span id="fcount">{len(TOOLS)}</span> tools shown</p>
{ad()}
<div class="tgrid" id="toolGrid">{"".join(tool_card(t, r) for t in TOOLS)}</div>
<p class="empty" id="noResults" hidden>No tools match. Try another search — or <a href="{r}get-matched.html">ask us for a recommendation</a>.</p>
</div></section>
<div class="compare-bar" id="compareBar" hidden><span id="cmpText">0 selected</span><a class="btn btn-sm btn-grad" id="cmpGo" href="{r}compare.html">Compare now</a><button class="btn btn-sm btn-ghost" id="cmpClear">Clear</button></div>"""
    write("tools/index.html", "AI Tools Directory — Search & Filter the Best AI Tools",
          f"Search and filter {len(TOOLS)} curated AI tools by category and pricing. Save favourites and compare tools side by side.",
          body, [items, crld], active="tools/index.html", priority="0.9", changefreq="daily")


def ld_itemlist(name, pairs):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name,
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "url": SITE + "/" + u} for i, (n, u) in enumerate(pairs)]}


USE_CASES = {
    "chatbots": ["Drafting emails, posts and documents", "Summarising long PDFs and reports", "Brainstorming ideas and outlines", "Explaining concepts and answering questions"],
    "writing": ["Blog posts and newsletters", "Ad copy and product descriptions", "Proofreading and tone adjustment", "Rewriting for clarity and length"],
    "image": ["Social media graphics", "Product and lifestyle photos", "Concept art and mood boards", "Upscaling and retouching"],
    "video": ["Short-form social clips", "Explainers and training videos", "Captions and translations", "Repurposing long recordings"],
    "audio": ["Voiceovers and narration", "Podcast clean-up", "Background music", "Meeting transcription"],
    "coding": ["Writing and refactoring code", "Generating tests", "Building prototypes from prompts", "Explaining unfamiliar codebases"],
    "productivity": ["Meeting notes and action items", "Slide decks and documents", "Calendar and task planning", "Team knowledge Q&A"],
    "research": ["Literature reviews", "Evidence-backed answers", "Summarising papers", "Studying your own sources"],
    "marketing": ["SEO briefs and optimisation", "Ad creatives", "Social scheduling", "Campaign ideation"],
    "design": ["Wireframes and UI", "Websites and landing pages", "Logos and brand kits", "Templates and graphics"],
    "automation": ["Connecting apps", "Email and lead routing", "AI agents for repetitive tasks", "Chatbots for websites"],
    "data": ["Spreadsheet analysis", "Charts and dashboards", "Forecasting", "Natural-language SQL"],
    "education": ["Personal tutoring", "Language practice", "Flashcards and quizzes", "Lesson planning"],
    "business": ["Prospecting and enrichment", "Customer support automation", "Sales call insights", "Outbound email"],
    "models": ["Building AI features", "Running open models", "Prototyping prompts", "Comparing model providers"],
}


def build_tool_pages():
    for t in TOOLS:
        c = CAT[t["cat"]]
        alts = [x for x in BY_CAT[t["cat"]] if x["slug"] != t["slug"]][:6]
        cr, crld = crumbs("../", [("tools/index.html", "AI Tools"), (f"category/{c['slug']}.html", c["name"]), (None, t["name"])])
        qas = [
            (f"What is {t['name']} used for?", f"{e(t['desc'])} It is best suited for: {e(t['best'].lower())}."),
            (f"Is {t['name']} free?", {"Free": f"{e(t['name'])} is free to use.",
                                        "Freemium": f"{e(t['name'])} offers a free tier with limits; paid plans unlock more usage and features.",
                                        "Paid": f"{e(t['name'])} is a paid product. Check the official site for current plans and any trial.",
                                        "Free trial": f"{e(t['name'])} offers a free trial, after which a paid plan is required."}[t["price"]] + " Prices change often, so confirm on the official website."),
            (f"What are the best alternatives to {t['name']}?", "Popular alternatives in the same category include " + ", ".join(e(a["name"]) for a in alts[:4]) + "."),
        ]
        faq_html, faq_ld = faq_block(qas)
        ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": t["name"], "url": t["url"],
              "applicationCategory": c["name"], "operatingSystem": t.get("review", {}).get("os", "Web"), "description": t["desc"]}

        def body(r, t=t, c=c, alts=alts, cr=cr, faq_html=faq_html):
            uses = "".join(f"<li>{e(u)}</li>" for u in (t.get("review", {}).get("uses") or USE_CASES.get(t["cat"], [])))
            tags = "".join(f'<span class="tag">#{e(x)}</span>' for x in t["tags"])
            return f"""<section class="page-hero"><div class="wrap">{cr}
<div class="tool-head">{logo_img(t, 64)}<div><h1>{e(t['name'])}</h1>
<p class="sub">{e(t['desc'])}</p>
<div class="tool-meta"><span class="badge {price_cls(t['price'])}">{e(t['price'])}</span><a class="tc-cat" href="{r}category/{c['slug']}.html">{c['icon']} {e(c['name'])}</a><span class="muted">{e(t['domain'])}</span></div></div>
<div class="tool-actions"><a class="btn btn-grad" href="{e(t['url'])}" target="_blank" rel="{out_rel(t)}" data-out="{t['slug']}">Visit {e(t['name'])} ↗</a>
<button class="btn btn-ghost save" data-save="{t['slug']}">♡ Save</button></div></div></div></section>
<section class="section tight"><div class="wrap content-grid"><article class="prose">
<h2>Overview</h2><p>{e(t['name'])} is listed in our <a href="{r}category/{c['slug']}.html">{e(c['name'])}</a> category. {e(t['desc'])} {review_line(t)}</p>
{review_block(t, r)}<h2>Common use cases</h2><ul>{uses}</ul>
<h2>Quick facts</h2><table class="facts"><tr><th>Pricing model</th><td>{e(t['price'])}</td></tr><tr><th>Category</th><td>{e(c['name'])}</td></tr><tr><th>Best for</th><td>{e(t['best'])}</td></tr><tr><th>Website</th><td><a href="{e(t['url'])}" target="_blank" rel="{out_rel(t)}">{e(t['domain'])}</a></td></tr><tr><th>Tags</th><td>{tags}</td></tr></table>
{ad()}
<h2>How to evaluate {e(t['name'])}</h2>
<p>Run one real task from your own work through {e(t['name'])} and two alternatives below. Score each on output quality, speed, control and consistency, then weigh the result against the plan price and the time you spend editing. Our <a href="{r}guides/how-to-choose-ai-tools.html">7-step evaluation framework</a> walks through this in detail, and the <a href="{r}free-tools/roi-calculator.html">ROI calculator</a> shows whether a paid plan pays for itself.</p>
<h2>FAQ</h2>{faq_html}
<p class="tiny muted">Information is provided for discovery and may change; always confirm features, pricing and terms on the official website. GDTai is not affiliated with {e(t['name'])}. Trademarks belong to their owners.</p>
</article>
<aside class="side">
<div class="side-card lead-side"><h3>Not sure it's the right fit?</h3><p>Get a free, personalised shortlist for your use case.</p><a class="btn btn-grad btn-block" href="{r}get-matched.html?tool={t['slug']}">Get matched free</a></div>
<div class="side-card"><h3>Is this your tool?</h3><p>Claim the listing, update details or get featured.</p><a class="btn btn-ghost btn-block" href="{r}submit-tool.html#featured">Feature {e(t['name'])}</a></div>
{ad("Sponsored", "ad-side")}
</aside></div></section>
<section class="section alt"><div class="wrap"><div class="sec-head"><div><h2>Alternatives to {e(t['name'])}</h2></div><a class="link-more" href="{r}compare.html?ids={t['slug']},{','.join(a['slug'] for a in alts[:2])}">Compare side by side →</a></div>
<div class="tgrid">{"".join(tool_card(a, r) for a in alts)}</div></div></section>"""
        write(f"tools/{t['slug']}.html", f"{t['name']} — Features, Pricing Model & Alternatives",
              f"{t['name']}: {t['desc']} See use cases, pricing model, FAQs and the best alternatives.",
              body, [ld, faq_ld, crld], priority="0.7")


def build_categories():
    for c in CATEGORIES:
        slug, name, desc, icon = c
        tools = BY_CAT.get(slug, [])
        cr, crld = crumbs("../", [("tools/index.html", "AI Tools"), (None, name)])
        others = "".join(f'<a class="chip" href="{x[0]}.html">{x[3]} {e(x[1])}</a>' for x in CATEGORIES if x[0] != slug)
        qas = [(f"What are the best {name.lower()} tools?", "Top options we list include " + ", ".join(e(t["name"]) for t in tools[:5]) + ". The best choice depends on your specific task, budget and the tools you already use."),
               (f"Are there free {name.lower()} tools?", ("Yes: " + ", ".join(e(t["name"]) for t in tools if t["price"] in ("Free", "Freemium")) + " offer free or freemium plans.") if any(t["price"] in ("Free", "Freemium") for t in tools) else "Most tools in this category are paid, though many offer trials."),
               ("How do I choose between them?", "Test the same real task in two or three tools and compare quality, speed and cost. Our <a href='../guides/how-to-choose-ai-tools.html'>evaluation framework</a> explains how.")]
        faq_html, faq_ld = faq_block(qas)

        def body(r, tools=tools, name=name, desc=desc, icon=icon, cr=cr, others=others, faq_html=faq_html):
            return f"""<section class="page-hero"><div class="wrap">{cr}<h1>{icon} {e(name)}</h1><p class="sub">{e(desc)} {len(tools)} curated tools with their pricing model; confirm current prices on each official site.</p></div></section>
<section class="section tight"><div class="wrap">{ad()}<div class="tgrid">{"".join(tool_card(t, r) for t in tools)}</div>
<div class="lead-inline"><div><h3>Want the best {e(name.lower())} tool for <em>your</em> workflow?</h3><p>Answer five questions and get a free personalised recommendation.</p></div><a class="btn btn-grad" href="{r}get-matched.html">Get matched free</a></div>
<div class="narrow"><h2>FAQ</h2>{faq_html}</div>
<h2 class="mt">Explore other categories</h2><div class="chips">{others}</div></div></section>"""
        write(f"category/{slug}.html", f"Best {name} Tools", f"The best {name.lower()} tools: {desc} Compare {len(tools)} curated options with pricing models and alternatives.",
              body, [ld_itemlist(name, [(t["name"], f"tools/{t['slug']}.html") for t in tools]), faq_ld, crld], priority="0.8")


def build_guides():
    cr, crld = crumbs("../", [("guides/index.html", "Guides")])
    cards = "".join(f'<a class="gcard" href="{g["slug"]}.html"><span class="pill">{e(g["category"])}</span><h3>{e(g["title"])}</h3><p>{e(g["description"])}</p><span class="meta">{g["read"]} min read →</span></a>' for g in GUIDES)
    write("guides/index.html", "AI Guides — Practical, No-Hype Explainers",
          "Original, practical guides on choosing AI tools, prompt engineering, RAG, AI agents, AI for small business, video workflows and responsible AI.",
          lambda r: f'<section class="page-hero"><div class="wrap">{cr}<h1>AI Guides</h1><p class="sub">Practical, original explainers to help you choose and use AI well.</p></div></section><section class="section tight"><div class="wrap">{ad()}<div class="ggrid">{cards}</div></div></section>',
          [crld], active="guides/index.html", priority="0.8")
    for i, g in enumerate(GUIDES):
        others = [x for x in GUIDES if x["slug"] != g["slug"]][:3]
        cr2, crld2 = crumbs("../", [("guides/index.html", "Guides"), (None, g["title"])])
        art = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["description"],
               "datePublished": "2026-11-18", "dateModified": TODAY, "author": {"@type": "Organization", "name": "GDTai Editorial"},
               "publisher": {"@type": "Organization", "name": SITE_NAME, "logo": {"@type": "ImageObject", "url": SITE + "/assets/img/favicon.svg"}},
               "mainEntityOfPage": SITE + f"/guides/{g['slug']}.html", "wordCount": g["words"]}
        body_html = g["body"]
        # insert an in-article ad before the second section heading
        idx = body_html.find("<h2>", body_html.find("<h2>") + 1)
        if idx > 0:
            body_html = body_html[:idx] + ad() + body_html[idx:]
        rel = "".join(f'<li><a href="{o["slug"]}.html">{e(o["title"])}</a></li>' for o in others)

        def body(r, g=g, body_html=body_html, rel=rel, cr2=cr2):
            return f"""<section class="page-hero article-hero"><div class="wrap narrow">{cr2}<span class="pill">{e(g['category'])}</span><h1>{e(g['title'])}</h1>
<p class="meta">By GDTai Editorial · Updated {NOW.strftime('%d %b %Y')} · {g['read']} min read</p></div></section>
<section class="section tight"><div class="wrap content-grid"><article class="prose">{body_html}
<div class="share"><span>Share:</span><button class="btn btn-sm btn-ghost" data-share>Copy link</button></div></article>
<aside class="side"><div class="side-card lead-side"><h3>Free AI Stack Match</h3><p>Get tools picked for your goals, budget and team.</p><a class="btn btn-grad btn-block" href="{r}get-matched.html">Get matched</a></div>
<div class="side-card"><h3>Related guides</h3><ul class="plain">{rel}</ul></div>{ad("Sponsored", "ad-side")}</aside></div></section>"""
        write(f"guides/{g['slug']}.html", g["title"], g["description"], body, [art, crld2], og_type="article", priority="0.8")


def build_news():
    cr, crld = crumbs("", [(None, "AI News")])
    upd = NEWS.get("updated")

    def body(r):
        return f"""<section class="page-hero"><div class="wrap">{cr}<h1>Latest AI News &amp; Research</h1>
<p class="sub">Headlines from leading AI labs and publications, new research papers and trending open-source projects — refreshed automatically every few hours.{(' Last refreshed ' + fmt_date(upd) + '.') if upd else ''}</p></div></section>
<section class="section tight"><div class="wrap content-grid"><div>
<h2>Top headlines</h2>{news_list(NEWS.get("items", []), 40)}
{ad()}
<h2 class="mt">New research papers</h2>{news_list(NEWS.get("papers", []), 20)}
<p class="tiny muted">Headlines link to the original publishers. GDTai shows titles only and is not responsible for third-party content.</p></div>
<aside class="side"><div class="side-card"><h3>Trending AI repos</h3>{repo_list(REPOS.get("items", []), 8)}</div>
<div class="side-card lead-side"><h3>Get the briefing</h3><p>The week's most important AI news in 5 minutes.</p><a class="btn btn-grad btn-block" href="#nl-email">Subscribe free</a></div>{ad("Sponsored", "ad-side")}</aside></div></section>"""
    write("news.html", "AI News Today — Headlines, Research & Trending Repos",
          "Auto-updated AI news headlines from top labs and publications, the latest arXiv research papers and trending open-source AI projects.",
          body, [crld], active="news.html", priority="0.9", changefreq="hourly")


def build_videos():
    cr, crld = crumbs("", [(None, "AI Videos")])
    ch = "".join(f'<a class="cta-card" href="https://www.youtube.com/{h}" target="_blank" rel="noopener nofollow"><span>▶</span><h3>{e(n)}</h3><p>{e(d)}</p><b>Visit channel ↗</b></a>' for n, h, d in CHANNELS)

    def body(r):
        return f"""<section class="page-hero"><div class="wrap">{cr}<h1>AI Videos &amp; Tutorials</h1><p class="sub">The newest explainers, tool walkthroughs and research breakdowns from respected AI creators — updated automatically. Videos load in privacy-enhanced mode only when you click play.</p></div></section>
<section class="section tight"><div class="wrap">{video_grid(VIDEOS.get("items", []), 24)}{ad()}
<h2 class="mt">Channels we follow</h2><div class="three-cta four">{ch}</div>
<p class="tiny muted">Videos are embedded from YouTube and remain the property of their creators. Creator? <a href="{r}contact.html">Suggest your channel</a>.</p></div></section>"""
    write("videos.html", "AI Videos — Latest Tutorials & Explainers", "Watch the latest AI tutorials, tool walkthroughs and research explainers from top AI YouTube creators, updated automatically.",
          body, [crld], active="videos.html", priority="0.8", changefreq="daily")


def build_glossary():
    cr, crld = crumbs("", [(None, "AI Glossary")])
    letters = sorted({t[0][0].upper() for t in GLOSSARY})
    nav = "".join(f'<a href="#l-{l}">{l}</a>' for l in letters)
    rows, cur = [], ""
    for term, d in sorted(GLOSSARY, key=lambda x: x[0].lower()):
        L = term[0].upper()
        if L != cur:
            rows.append(f'<h2 id="l-{L}">{L}</h2>')
            cur = L
        rows.append(f'<dl class="gloss" id="{slugify(term)}"><dt>{e(term)}</dt><dd>{e(d)}</dd></dl>')
    ld = {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "GDTai AI Glossary",
          "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t, "description": d} for t, d in GLOSSARY]}
    write("glossary.html", "AI Glossary — 50+ AI Terms Explained Simply", "Plain-English definitions of 50+ essential AI terms: LLM, RAG, tokens, agents, embeddings, fine-tuning, MCP and more.",
          lambda r: f'<section class="page-hero"><div class="wrap">{cr}<h1>AI Glossary</h1><p class="sub">{len(GLOSSARY)} essential AI terms explained in plain English.</p><input id="gq" class="inline-search" type="search" placeholder="Filter terms…" aria-label="Filter glossary"><div class="alpha">{nav}</div></div></section><section class="section tight"><div class="wrap narrow" id="glossList">{ad()}{"".join(rows)}</div></section>',
          [ld, crld], priority="0.7")


def build_prompts():
    cr, crld = crumbs("", [(None, "Prompt Library")])
    cats = sorted({p[0] for p in PROMPTS})
    seg = '<button class="on" data-pc="">All</button>' + "".join(f'<button data-pc="{e(c)}">{e(c)}</button>' for c in cats)
    cards = "".join(f'<article class="pcard" data-pc="{e(c)}"><span class="pill">{e(c)}</span><h3>{e(t)}</h3><pre>{e(p)}</pre><button class="btn btn-sm btn-ghost" data-copy>Copy prompt</button></article>' for c, t, p in PROMPTS)
    write("prompts.html", "AI Prompt Library — 30 Tested Prompts for Work", "Copy-ready, tested AI prompts for business, marketing, writing, coding, research, video and careers. Works with ChatGPT, Claude, Gemini and more.",
          lambda r: f'<section class="page-hero"><div class="wrap">{cr}<h1>Prompt Library</h1><p class="sub">{len(PROMPTS)} copy-ready prompts. Replace the [brackets] with your details. Want a custom one? Try the <a href="{r}free-tools/prompt-builder.html">prompt builder</a>.</p><div class="seg wrap-seg" id="pseg">{seg}</div></div></section><section class="section tight"><div class="wrap">{ad()}<div class="pgrid">{cards}</div></div></section>',
          [crld], active="prompts.html", priority="0.7")


def build_compare():
    cr, crld = crumbs("", [(None, "Compare AI Tools")])
    opts = "".join(f'<option value="{t["slug"]}">{e(t["name"])}</option>' for t in sorted(TOOLS, key=lambda x: x["name"].lower()))
    sel = "".join(f'<select class="cmp-sel" aria-label="Tool {i + 1}"><option value="">Choose tool {i + 1}…</option>{opts}</select>' for i in range(3))
    write("compare.html", "Compare AI Tools Side by Side", "Pick up to three AI tools and compare category, pricing model, best use case and tags side by side.",
          lambda r: f'<section class="page-hero"><div class="wrap">{cr}<h1>Compare AI tools</h1><p class="sub">Choose up to three tools to see them side by side.</p><div class="cmp-pick">{sel}</div></div></section><section class="section tight"><div class="wrap"><div id="cmpTable" class="cmp-table"></div>{ad()}<div class="lead-inline"><div><h3>Still undecided?</h3><p>We will recommend the best option for your exact workflow — free.</p></div><a class="btn btn-grad" href="{r}get-matched.html">Get matched</a></div></div></section>',
          [crld], priority="0.6")


def build_free_tools():
    cr, crld = crumbs("../", [("free-tools/index.html", "Free AI Utilities")])
    write("free-tools/index.html", "Free AI Utilities — Calculators & Builders", "Free in-browser AI utilities: token and API cost calculator, prompt builder, AI ROI calculator and AI stack match.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<h1>Free AI utilities</h1><p class="sub">Handy tools that run entirely in your browser. Nothing you type is uploaded.</p></div></section>
<section class="section tight"><div class="wrap"><div class="util-grid">
<a class="util" href="token-calculator.html"><b>🧮 Token &amp; cost calculator</b><span>Estimate tokens, words and API costs for any text.</span></a>
<a class="util" href="prompt-builder.html"><b>🛠️ Prompt builder</b><span>Structure role, goal, context, constraints and format.</span></a>
<a class="util" href="roi-calculator.html"><b>📈 AI ROI calculator</b><span>Monthly value, payback time and yearly savings.</span></a>
<a class="util" href="{r}get-matched.html"><b>🎯 AI stack match</b><span>Personalised tool recommendations in 60 seconds.</span></a>
</div>{ad()}</div></section>""", [crld], active="free-tools/index.html", priority="0.7")

    cr1, l1 = crumbs("../", [("free-tools/index.html", "Free AI Utilities"), (None, "Token & Cost Calculator")])
    write("free-tools/token-calculator.html", "AI Token & API Cost Calculator", "Paste text to estimate tokens, words and characters, and calculate AI API costs per request and per month with your own prices.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr1}<h1>Token &amp; API cost calculator</h1><p class="sub">Estimate how many tokens your text uses and what it costs at your provider's prices.</p></div></section>
<section class="section tight"><div class="wrap content-grid"><div class="toolbox">
<label>Paste your prompt or document<textarea id="tcText" rows="9" placeholder="Paste text here…"></textarea></label>
<div class="kpis"><div><b id="tcTok">0</b><span>est. tokens</span></div><div><b id="tcWords">0</b><span>words</span></div><div><b id="tcChars">0</b><span>characters</span></div></div>
<div class="grid3">
<label>Input price (per 1M tokens)<input id="tcIn" type="number" step="0.01" value="3"></label>
<label>Output price (per 1M tokens)<input id="tcOut" type="number" step="0.01" value="15"></label>
<label>Expected output tokens<input id="tcOutTok" type="number" value="800"></label>
<label>Requests per day<input id="tcReq" type="number" value="100"></label>
<label>Currency symbol<input id="tcCur" type="text" value="$" maxlength="3"></label></div>
<div class="kpis"><div><b id="tcPer">—</b><span>cost per request</span></div><div><b id="tcMonth">—</b><span>cost per month (30 days)</span></div></div>
<p class="tiny muted">Token counts are estimates (≈4 characters or ≈0.75 words per token for English). Enter your model's current prices from the provider's pricing page.</p></div>
<aside class="side"><div class="side-card lead-side"><h3>Spending too much on AI?</h3><p>We'll suggest cheaper models and tools for your workload.</p><a class="btn btn-grad btn-block" href="{r}get-matched.html">Get a free review</a></div>{ad("Sponsored", "ad-side")}</aside></div>
<div class="wrap narrow prose"><h2>How token pricing works</h2><p>AI APIs bill separately for the tokens you send (input) and the tokens the model writes (output), usually quoted per million tokens. Output tokens are typically several times more expensive than input tokens, so long answers cost more than long prompts. Reduce costs by trimming unnecessary context, caching repeated instructions where your provider supports it, choosing smaller models for simple tasks, and setting a maximum output length.</p></div></section>""",
          [l1], priority="0.7")

    cr2, l2 = crumbs("../", [("free-tools/index.html", "Free AI Utilities"), (None, "Prompt Builder")])
    write("free-tools/prompt-builder.html", "Free AI Prompt Builder", "Build clear, structured prompts for ChatGPT, Claude, Gemini and other AI assistants with role, goal, context, constraints and format.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr2}<h1>Prompt builder</h1><p class="sub">Fill in the blocks — get a well-structured prompt you can paste into any AI assistant.</p></div></section>
<section class="section tight"><div class="wrap content-grid"><div class="toolbox" id="pb">
<div class="grid2"><label>Role (who should the AI be?)<input data-pb="role" placeholder="e.g. senior B2B copywriter"></label>
<label>Audience<input data-pb="aud" placeholder="e.g. busy operations managers"></label></div>
<label>Goal<input data-pb="goal" placeholder="e.g. write a landing page hero that gets demo sign-ups"></label>
<label>Context / source material<textarea data-pb="ctx" rows="4" placeholder="Product facts, previous attempts, pasted notes…"></textarea></label>
<div class="grid2"><label>Constraints<input data-pb="con" placeholder="e.g. under 120 words, plain English, no hype"></label>
<label>Output format<select data-pb="fmt"><option>Bullet list</option><option>Table</option><option>Step-by-step plan</option><option>Email</option><option>JSON</option><option>Short paragraphs</option></select></label></div>
<label class="row"><input type="checkbox" data-pb="ask" checked> Ask me clarifying questions first</label>
<label class="row"><input type="checkbox" data-pb="steps"> Think step by step and check the answer</label>
<label>Your prompt<textarea id="pbOut" rows="10" readonly></textarea></label>
<button class="btn btn-grad" id="pbCopy">Copy prompt</button></div>
<aside class="side"><div class="side-card"><h3>Need inspiration?</h3><p>Browse 30 ready-made prompts.</p><a class="btn btn-ghost btn-block" href="{r}prompts.html">Prompt library</a></div>{ad("Sponsored", "ad-side")}</aside></div></section>""",
          [l2], priority="0.7")

    cr3, l3 = crumbs("../", [("free-tools/index.html", "Free AI Utilities"), (None, "AI ROI Calculator")])
    write("free-tools/roi-calculator.html", "AI ROI Calculator — Is Your AI Subscription Worth It?", "Calculate the monthly value, net return and payback of AI tools from hours saved, hourly rate, team size and subscription cost.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr3}<h1>AI ROI calculator</h1><p class="sub">Find out whether an AI tool pays for itself — and by how much.</p></div></section>
<section class="section tight"><div class="wrap content-grid"><div class="toolbox">
<div class="grid3">
<label>Hours saved per person / week<input id="roiH" type="number" step="0.5" value="3"></label>
<label>Hourly cost of time<input id="roiR" type="number" value="25"></label>
<label>Team members using it<input id="roiN" type="number" value="1"></label>
<label>Subscription per seat / month<input id="roiC" type="number" value="20"></label>
<label>Setup / learning hours (one-off)<input id="roiS" type="number" value="4"></label>
<label>Currency symbol<input id="roiCur" type="text" value="$" maxlength="3"></label></div>
<div class="kpis"><div><b id="roiVal">—</b><span>value created / month</span></div><div><b id="roiNet">—</b><span>net gain / month</span></div><div><b id="roiX">—</b><span>return multiple</span></div><div><b id="roiPay">—</b><span>payback time</span></div></div>
<div id="roiVerdict" class="verdict"></div>
<div class="lead-inline"><div><h3>Want this ROI across your whole business?</h3><p>Get a free AI stack with estimated savings for each workflow.</p></div><a class="btn btn-grad" href="{r}get-matched.html">Get my free AI plan</a></div></div>
<aside class="side">{ad("Sponsored", "ad-side")}</aside></div></section>""",
          [l3], priority="0.7")


def build_get_matched():
    cats = "".join(f'<label class="opt"><input type="checkbox" name="interests" value="{e(c[1])}"><span>{c[3]} {e(c[1])}</span></label>' for c in CATEGORIES[:12])
    tools_js = json.dumps([{"s": t["slug"], "n": t["name"], "c": t["cat"], "p": t["price"]} for t in TOOLS])
    qas = [("Is the AI Stack Match really free?", "Yes. There is no cost and no obligation. We may offer optional paid implementation help from vetted partners if you ask for it."),
           ("What happens after I submit?", "We review your answers and email a personalised shortlist, rollout plan and cost estimate, usually within 48 hours."),
           ("Will you share my details?", "We only share your details with an implementation partner if you explicitly tick the box asking for partner quotes. See our <a href='privacy.html'>Privacy Policy</a>."),
           ("Who is this for?", "Founders, freelancers, marketers, agencies, educators and teams of any size who want to use AI productively without wasting money on the wrong tools.")]
    faq_html, faq_ld = faq_block(qas)
    cr, crld = crumbs("", [(None, "Free AI Stack Match")])

    def body(r):
        return f"""<section class="page-hero lead-hero"><div class="wrap">{cr}
<div class="lh-grid"><div><span class="eyebrow">Free · No obligation · 60 seconds</span>
<h1>Get your <span class="grad">personalised AI stack</span></h1>
<p class="sub">Answer five quick questions. We'll send the exact tools, first automations and a 30-day rollout plan for your goals and budget.</p>
<ul class="ticks big"><li>Shortlist of 3–7 tools matched to your workflow</li><li>Cost estimate &amp; subscriptions you can cut</li><li>Optional quotes from vetted implementation partners</li></ul>
<div class="trust"><span>🔒 Private &amp; secure</span><span>⏱ Reply in 48h</span><span>🤝 Vendor-neutral</span></div></div>

<form class="wizard gform" id="wizard" data-form="ai-stack-match" data-subject="🎯 New AI Stack Match lead — GDTai" novalidate>
<div class="wz-progress"><span id="wzBar"></span></div><p class="wz-step-label">Step <b id="wzNum">1</b> of 5</p>
<fieldset class="wz-step on" data-step="1"><legend>What best describes you?</legend>
<div class="opts">{''.join(f'<label class="opt"><input type="radio" name="profile" value="{v}" required><span>{v}</span></label>' for v in ["Solo founder / freelancer", "Small business (2–50)", "Mid-size company (50–500)", "Enterprise (500+)", "Agency / consultant", "Student / educator", "Creator / YouTuber", "Developer / startup"])}</div></fieldset>
<fieldset class="wz-step" data-step="2"><legend>What do you want AI to help with? <small>(pick any)</small></legend><div class="opts">{cats}</div></fieldset>
<fieldset class="wz-step" data-step="3"><legend>Monthly budget for AI tools</legend>
<div class="opts">{''.join(f'<label class="opt"><input type="radio" name="budget" value="{v}" required><span>{v}</span></label>' for v in ["Free tools only", "Under $50", "$50–$200", "$200–$1,000", "$1,000–$5,000", "$5,000+"])}</div>
<label>Tools you already use<input name="current_tools" placeholder="e.g. Google Workspace, Notion, HubSpot, ChatGPT"></label></fieldset>
<fieldset class="wz-step" data-step="4"><legend>Timeline &amp; help needed</legend>
<div class="opts">{''.join(f'<label class="opt"><input type="radio" name="timeline" value="{v}" required><span>{v}</span></label>' for v in ["This week", "This month", "Next 3 months", "Just exploring"])}</div>
<label>Describe your biggest time-waster or goal<textarea name="challenge" rows="3" placeholder="e.g. We spend 10 hours a week writing proposals…"></textarea></label>
<label class="row"><input type="checkbox" name="partner_quotes" value="yes"> I'd like quotes from vetted AI implementation partners</label></fieldset>
<fieldset class="wz-step" data-step="5"><legend>Where should we send your AI stack?</legend>
<div class="grid2"><label>Full name<input name="name" required autocomplete="name"></label><label>Work email<input name="email" type="email" required autocomplete="email"></label>
<label>Company / brand<input name="company" autocomplete="organization"></label><label>Website<input name="website" type="url" placeholder="https://"></label>
<label>Country<input name="country" autocomplete="country-name"></label><label>Phone / WhatsApp (optional)<input name="phone" type="tel" autocomplete="tel"></label></div>
<label class="row"><input type="checkbox" name="consent" value="yes" required> I agree to be contacted about my request and accept the <a href="{r}privacy.html">Privacy Policy</a>.</label>
<label class="row"><input type="checkbox" name="newsletter" value="yes" checked> Also send me the free twice-weekly AI briefing</label></fieldset>
<input type="hidden" name="source" value="get-matched"><input type="hidden" name="ref_tool" id="refTool">
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<div class="wz-nav"><button type="button" class="btn btn-ghost" id="wzBack" disabled>← Back</button><button type="button" class="btn btn-grad" id="wzNext">Next →</button><button type="submit" class="btn btn-grad" id="wzSubmit" hidden>Send my AI stack 🚀</button></div>
<p class="form-status" aria-live="polite"></p>
<div class="wz-preview" id="wzPreview" hidden><h3>Your instant starter stack</h3><p class="small muted">Based on your answers — your full personalised plan is on its way.</p><div id="wzTools" class="chips"></div></div>
</form></div></div></section>

<section class="section"><div class="wrap three-cta">
<div class="cta-card static"><span>1</span><h3>Tell us your goals</h3><p>Five questions about your work, budget and tools.</p></div>
<div class="cta-card static"><span>2</span><h3>We analyse your stack</h3><p>Matched against {len(TOOLS)}+ tools we track, vendor-neutral.</p></div>
<div class="cta-card static"><span>3</span><h3>Get your plan</h3><p>Tools, first automations, costs and a 30-day rollout.</p></div></div></section>

<section class="section alt" id="checklist"><div class="wrap lead-band">
<div><span class="eyebrow">Free download</span><h2>The AI Adoption Checklist</h2><p>A one-page, 25-point checklist to roll out AI safely and profitably in any team: tool selection, data rules, prompts, measurement and policy.</p></div>
<form class="gform magnet" data-form="lead-magnet" data-subject="Checklist download — GDTai" data-reveal="checklistLink" novalidate>
<label>Email<input type="email" name="email" required placeholder="you@company.com"></label>
<input type="hidden" name="source" value="ai-adoption-checklist"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad btn-block" type="submit">Get the checklist</button><p class="form-status" aria-live="polite"></p>
<a id="checklistLink" class="btn btn-ghost btn-block" href="{r}ai-adoption-checklist.html" hidden>Open your checklist →</a></form></div></section>

<section class="section"><div class="wrap narrow"><h2>Questions</h2>{faq_html}</div></section>
<script>window.GDT_TOOLS={tools_js};</script>"""
    write("get-matched.html", "Free AI Stack Match — Personalised AI Tool Recommendations",
          "Answer five quick questions and get a free, personalised AI tool stack, rollout plan and cost estimate for your business or career.",
          body, [faq_ld, crld], priority="0.9")


def build_checklist():
    items = ["Write down the 3 most repetitive tasks in your team", "Estimate hours spent on each per week", "Pick one general AI assistant for everyone",
             "Agree which data may be used in which tools", "Turn off training on your data where possible", "Create a shared prompt library",
             "Choose 2 workflows to pilot for 30 days", "Name an owner for each pilot", "Define success metrics (time, quality, cost)",
             "Test 3 tools on the same real task before buying", "Use monthly billing until value is proven", "Set renewal reminders for every subscription",
             "Require human review before anything goes external", "Verify facts, numbers and citations", "Check commercial-use rights for media",
             "Limit agent permissions; require approval for actions", "Log what automations do", "Train the team in a 60-minute session",
             "Share wins and failures weekly", "Measure results after 30 days", "Scale what works, cut what doesn't",
             "Write a one-page AI policy", "Review security settings and SSO", "Revisit tools quarterly", "Keep learning: subscribe to a trusted briefing"]
    li = "".join(f'<li><label><input type="checkbox"> {e(x)}</label></li>' for x in items)
    write("ai-adoption-checklist.html", "The AI Adoption Checklist (25 Points)", "A free 25-point checklist to adopt AI tools safely and profitably in any team.",
          lambda r: f'<section class="page-hero"><div class="wrap narrow"><h1>The AI Adoption Checklist</h1><p class="sub">25 steps to roll out AI safely and profitably. Tick as you go — or print it.</p><button class="btn btn-ghost" onclick="window.print()">🖨 Print</button></div></section><section class="section tight"><div class="wrap narrow"><ol class="checklist">{li}</ol>{ad()}<div class="lead-inline"><div><h3>Want us to tailor this to your team?</h3></div><a class="btn btn-grad" href="{r}get-matched.html">Get matched free</a></div></div></section>',
          noindex=True)


def form_fields_contact(subject_options):
    opts = "".join(f"<option>{e(o)}</option>" for o in subject_options)
    return f"""<div class="grid2"><label>Name<input name="name" required autocomplete="name"></label><label>Email<input type="email" name="email" required autocomplete="email"></label></div>
<label>Topic<select name="topic" required><option value="">Choose…</option>{opts}</select></label>
<label>Message<textarea name="message" rows="5" required></textarea></label>
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">"""


def build_simple_pages():
    # Submit tool
    cr, l = crumbs("", [(None, "Submit an AI Tool")])
    cats_opts = "".join(f"<option>{e(c[1])}</option>" for c in CATEGORIES)
    write("submit-tool.html", "Submit Your AI Tool — Free & Featured Listings", "List your AI tool on GDTai for free, or get featured placement, category sponsorship and newsletter promotion to reach AI buyers.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<h1>Submit your AI tool</h1><p class="sub">Reach founders, creators and teams actively looking for AI tools. Free review queue, or jump the line with a featured listing.</p></div></section>
<section class="section tight" id="featured"><div class="wrap"><div class="plans">
<div class="plan"><h3>Free listing</h3><p class="price">$0</p><ul class="ticks"><li>Manual editorial review</li><li>Tool page with alternatives</li><li>Category placement</li><li>Review in 2–4 weeks</li></ul><a class="btn btn-ghost btn-block" href="#submit" data-plan="Free listing">Submit free</a></div>
<div class="plan hot"><span class="pill pill-hot">Most popular</span><h3>Featured</h3><p class="price">$49<small>/30 days</small></p><ul class="ticks"><li>Priority review (48h)</li><li>"Featured" badge &amp; top of category</li><li>Homepage rotation</li><li>Do-follow link on tool page</li><li>One newsletter mention</li></ul><a class="btn btn-grad btn-block" href="#submit" data-plan="Featured">Get featured</a></div>
<div class="plan"><h3>Spotlight</h3><p class="price">$149<small>/30 days</small></p><ul class="ticks"><li>Everything in Featured</li><li>Category sponsorship banner</li><li>Dedicated newsletter spotlight</li><li>Sponsored review or tutorial (labelled)</li><li>Social promotion</li></ul><a class="btn btn-ghost btn-block" href="#submit" data-plan="Spotlight">Book Spotlight</a></div></div>
<p class="tiny muted center">Paid placements are always labelled "Featured" or "Sponsored" and never influence our editorial picks. After review we email an invoice / secure payment link.</p></div></section>
<section class="section alt" id="submit"><div class="wrap narrow"><h2>Tool details</h2>
<form class="gform card-form" data-form="submit-tool" data-subject="🚀 New AI tool submission — GDTai" novalidate>
<div class="grid2"><label>Tool name<input name="tool_name" required></label><label>Website URL<input name="tool_url" type="url" required placeholder="https://"></label>
<label>Category<select name="category" required><option value="">Choose…</option>{cats_opts}</select></label>
<label>Pricing model<select name="pricing" required><option>Free</option><option>Freemium</option><option>Free trial</option><option>Paid</option></select></label></div>
<label>Short description (max 200 characters)<textarea name="description" rows="3" maxlength="200" required></textarea></label>
<label>Plan<select name="plan" id="planSel"><option>Free listing</option><option>Featured</option><option>Spotlight</option></select></label>
<div class="grid2"><label>Your name<input name="name" required></label><label>Work email<input name="email" type="email" required></label></div>
<label class="row"><input type="checkbox" name="owner" value="yes" required> I am the owner or authorised representative of this tool.</label>
<input type="hidden" name="source" value="submit-tool"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad" type="submit">Submit tool</button><p class="form-status" aria-live="polite"></p></form></div></section>""", [l], priority="0.7")

    # Advertise
    cr, l = crumbs("", [(None, "Advertise")])
    write("advertise.html", "Advertise & Sponsor on GDTai", "Reach an audience of AI buyers, founders and creators with category sponsorships, newsletter placements, sponsored guides and partnerships.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<h1>Advertise &amp; sponsor</h1><p class="sub">Put your product in front of people actively searching for AI tools — at the moment they are deciding what to use.</p></div></section>
<section class="section tight"><div class="wrap"><div class="plans four">
<div class="plan"><h3>Category sponsor</h3><p>Exclusive banner and top slot on one category and its tool pages.</p></div>
<div class="plan"><h3>Newsletter sponsor</h3><p>Primary or featured-tool slot in the twice-weekly AI briefing.</p></div>
<div class="plan"><h3>Sponsored guide</h3><p>An in-depth, clearly labelled tutorial or review written by our editors.</p></div>
<div class="plan"><h3>Contest sponsor</h3><p>Fund prizes in the Monthly AI Build Challenge and get brand exposure to builders.</p></div></div>
<div class="lead-inline"><div><h3>Interested in the domain, a partnership or a larger deal?</h3><p>Talk to the owner directly.</p></div><a class="btn btn-grad" href="{INTEREST_URL}" target="_blank" rel="noopener nofollow">Contact the owner</a></div></div></section>
<section class="section alt"><div class="wrap narrow"><h2>Request the media kit</h2>
<form class="gform card-form" data-form="advertise" data-subject="📣 Advertising enquiry — GDTai" novalidate>
<div class="grid2"><label>Name<input name="name" required></label><label>Work email<input name="email" type="email" required></label>
<label>Company<input name="company" required></label><label>Website<input name="website" type="url" placeholder="https://"></label></div>
<label>Interested in<select name="package"><option>Category sponsor</option><option>Newsletter sponsor</option><option>Sponsored guide</option><option>Contest sponsor</option><option>Display advertising</option><option>Partnership / domain</option></select></label>
<label>Budget<select name="budget"><option>Under $500</option><option>$500–$2,000</option><option>$2,000–$10,000</option><option>$10,000+</option></select></label>
<label>Goals &amp; timing<textarea name="message" rows="4"></textarea></label>
<input type="hidden" name="source" value="advertise"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad" type="submit">Send enquiry</button><p class="form-status" aria-live="polite"></p></form></div></section>""", [l], priority="0.6")

    # Support / donations
    cr, l = crumbs("", [(None, "Support GDTai")])
    write("support.html", "Support GDTai — Donate to Independent AI Curation", "Support GDTai with a one-off or monthly contribution. Funds go to operations, promotion, hiring contributors and contest prizes.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<h1>♥ Support independent AI curation</h1><p class="sub">GDTai is free for everyone. Your support keeps it independent, ad-light and growing — and funds prizes for the community.</p></div></section>
<section class="section tight"><div class="wrap">
<div class="plans four donate">
<div class="plan"><h3>Supporter</h3><p class="price">$5</p><p>Covers a day of hosting, data feeds and tooling.</p><button class="btn btn-ghost btn-block" data-donate="5">Give $5</button></div>
<div class="plan hot"><span class="pill pill-hot">Popular</span><h3>Champion</h3><p class="price">$25</p><p>Funds a new in-depth guide or tool review.</p><button class="btn btn-grad btn-block" data-donate="25">Give $25</button></div>
<div class="plan"><h3>Patron</h3><p class="price">$100</p><p>Adds to the monthly contest prize pool.</p><button class="btn btn-ghost btn-block" data-donate="100">Give $100</button></div>
<div class="plan"><h3>Custom</h3><p class="price">Any</p><p>One-off or monthly — every bit helps.</p><button class="btn btn-ghost btn-block" data-donate="custom">Choose amount</button></div></div>
<div id="donateLinks" class="donate-links"></div>
<h2 class="mt">Where your support goes</h2>
<div class="alloc"><div><b>40%</b><span>Operations — data feeds, tooling, security</span><i style="--w:40%"></i></div><div><b>25%</b><span>Promotion &amp; marketing to grow the community</span><i style="--w:25%"></i></div><div><b>20%</b><span>Hiring contributors — reviewers, writers, editors</span><i style="--w:20%"></i></div><div><b>15%</b><span>Contests &amp; prizes for builders</span><i style="--w:15%"></i></div></div>
</div></section>
<section class="section alt" id="pledge"><div class="wrap narrow"><h2>Pledge your support</h2><p>Choose an amount and a purpose. We'll email you a secure payment link (card, PayPal or UPI) and a thank-you receipt.</p>
<form class="gform card-form" data-form="donation" data-subject="♥ New donation pledge — GDTai" novalidate>
<div class="grid2"><label>Amount<input name="amount" id="donAmt" required placeholder="e.g. 25"></label><label>Currency<select name="currency"><option>USD</option><option>EUR</option><option>GBP</option><option>INR</option><option>Other</option></select></label>
<label>Frequency<select name="frequency"><option>One-off</option><option>Monthly</option><option>Yearly</option></select></label>
<label>Purpose<select name="purpose"><option>Where it's needed most</option><option>Operations</option><option>Promotions &amp; marketing</option><option>Hiring talent</option><option>Contests &amp; prizes</option></select></label>
<label>Name<input name="name" required></label><label>Email<input name="email" type="email" required></label></div>
<label class="row"><input type="checkbox" name="public_thanks" value="yes"> List my name on the supporters wall</label>
<label>Message (optional)<textarea name="message" rows="3"></textarea></label>
<input type="hidden" name="source" value="support"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad" type="submit">Send pledge</button><p class="form-status" aria-live="polite"></p></form>
<h3 class="mt">Supporters wall</h3><p class="muted">Be the first name here. Thank you for keeping GDTai independent.</p>
<h3 class="mt">Corporate sponsorship</h3><p>Companies can sponsor categories, guides or contest prizes — see <a href="{r}advertise.html">advertising options</a>.</p></div></section>""", [l], priority="0.6")

    # Contests
    cr, l = crumbs("", [(None, "Contests & Prizes")])
    write("contests.html", "Monthly AI Build Challenge — Contests & Prizes", "Enter the GDTai Monthly AI Build Challenge: build something useful with AI, win prizes and get featured. Free to enter.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<span class="pill pill-hot">Free to enter</span><h1>🏆 Monthly AI Build Challenge</h1><p class="sub">Build a useful workflow, app, video or prompt pack with AI. The best entries win prizes and get featured to our audience.</p></div></section>
<section class="section tight"><div class="wrap three-cta">
<div class="cta-card static"><span>🥇</span><h3>1st place</h3><p>Largest share of the monthly prize pool, homepage feature and a sponsored-quality review.</p></div>
<div class="cta-card static"><span>🥈</span><h3>2nd place</h3><p>Prize-pool share, newsletter spotlight and social promotion.</p></div>
<div class="cta-card static"><span>🌟</span><h3>Community pick</h3><p>Prize-pool share chosen by reader votes and a "Community pick" badge.</p></div></div>
<div class="wrap content-grid mt"><div class="prose"><h2>This month's theme: "Save someone 5 hours a week"</h2>
<p>Show us an AI-powered workflow, tool or template that saves real time for a real job. Entries can be no-code automations, apps, prompt systems, video tutorials or open-source projects.</p>
<h3>How judging works</h3><ul><li><b>Usefulness (40%)</b> — does it solve a real, frequent problem?</li><li><b>Originality (25%)</b></li><li><b>Execution &amp; clarity (25%)</b></li><li><b>Responsible use (10%)</b> — privacy, accuracy, disclosure</li></ul>
<h3>Prize pool</h3><p>The prize pool is funded by sponsors and reader <a href="{r}support.html">support</a>, and the amount is announced at the start of each round. Want to fund it? <a href="{r}advertise.html">Become a contest sponsor</a>.</p>
<h3>Official rules (summary)</h3><ul class="small"><li>No purchase or payment necessary to enter or win. Void where prohibited.</li><li>Open to individuals 18+ (or the age of majority where they live). One entry per person per round.</li><li>Entries must be your own original work and must not infringe others' rights or contain harmful content.</li><li>You keep ownership of your entry; you grant GDTai permission to showcase it with credit.</li><li>Winners are notified by email and must respond within 14 days. Prizes may be substituted with equal value. Taxes are the winner's responsibility.</li><li>GDTai may disqualify entries that break these rules. Full terms in our <a href="{r}terms.html">Terms of Use</a>.</li></ul></div>
<aside class="side"><div class="side-card"><h3>Timeline</h3><ul class="plain"><li>📅 Submissions: 1st–25th</li><li>🗳 Community voting: 26th–28th</li><li>🏆 Winners: last day of the month</li></ul></div>{ad("Sponsored", "ad-side")}</aside></div></section>
<section class="section alt" id="enter"><div class="wrap narrow"><h2>Submit your entry</h2>
<form class="gform card-form" data-form="contest-entry" data-subject="🏆 New contest entry — GDTai" novalidate>
<div class="grid2"><label>Name<input name="name" required></label><label>Email<input name="email" type="email" required></label>
<label>Project title<input name="project_title" required></label><label>Project link<input name="project_url" type="url" required placeholder="https://"></label></div>
<label>What does it do and who saves time?<textarea name="description" rows="4" required></textarea></label>
<label>AI tools used<input name="tools_used" placeholder="e.g. Claude, Zapier, ElevenLabs"></label>
<label class="row"><input type="checkbox" name="rules" value="accepted" required> I am 18+ and accept the official rules.</label>
<input type="hidden" name="source" value="contest"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad" type="submit">Submit entry</button><p class="form-status" aria-live="polite"></p></form></div></section>""", [l], priority="0.6")

    # Careers
    cr, l = crumbs("", [(None, "Careers")])
    roles = [("AI Tools Reviewer", "Freelance · Remote", "Test AI tools hands-on and write honest, structured reviews."),
             ("Content Writer — AI Guides", "Freelance · Remote", "Write clear, original guides for beginners and professionals."),
             ("Video Editor / Creator", "Contract · Remote", "Produce short tutorials and explainers for our channels."),
             ("Community Moderator", "Part-time · Remote", "Run contests, moderate entries and support members."),
             ("Partnerships &amp; Sales", "Commission · Remote", "Bring in sponsors, featured listings and partners."),
             ("Full-stack Developer", "Contract · Remote", "Improve the site, automations and data pipelines.")]
    cards = "".join(f'<article class="plan"><h3>{t}</h3><p class="muted small">{m}</p><p>{d}</p><a class="btn btn-ghost btn-sm" href="#apply" data-role="{t}">Apply</a></article>' for t, m, d in roles)
    opts = "".join(f"<option>{t}</option>" for t, _, _ in roles)
    ld = [{"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": SITE + "/"}]
    write("careers.html", "Careers & Contributors — Work With GDTai", "Join GDTai as an AI tools reviewer, writer, video creator, moderator, partnerships lead or developer. Remote, flexible roles.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<h1>Work with us</h1><p class="sub">We're building the most useful independent AI resource on the web. Remote, flexible roles for people who love testing and explaining AI.</p></div></section>
<section class="section tight"><div class="wrap"><div class="plans three">{cards}</div></div></section>
<section class="section alt" id="apply"><div class="wrap narrow"><h2>Apply</h2>
<form class="gform card-form" data-form="job-application" data-subject="💼 New application — GDTai" novalidate>
<div class="grid2"><label>Name<input name="name" required></label><label>Email<input name="email" type="email" required></label>
<label>Role<select name="role" id="roleSel" required>{opts}<option>Other</option></select></label><label>Portfolio / LinkedIn<input name="portfolio" type="url" required placeholder="https://"></label>
<label>Country / time zone<input name="location"></label><label>Availability (hours/week)<input name="availability"></label></div>
<label>Why you, in 3–5 sentences<textarea name="message" rows="4" required></textarea></label>
<input type="hidden" name="source" value="careers"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off">
<button class="btn btn-grad" type="submit">Send application</button><p class="form-status" aria-live="polite"></p></form></div></section>""", [l] + ld, priority="0.5")

    # About
    cr, l = crumbs("", [(None, "About")])
    write("about.html", "About GDTai — Guide · Discover · Test AI", "GDTai is an independent, self-updating hub for finding, comparing and learning AI tools. Learn about our mission and editorial policy.",
          lambda r: f"""<section class="page-hero"><div class="wrap narrow">{cr}<h1>About GDTai</h1><p class="sub">{TAGLINE} — an independent hub that helps people and businesses find the right AI tools and use them well.</p></div></section>
<section class="section tight"><div class="wrap narrow prose">
<h2>Our mission</h2><p>There are now more AI products than anyone can test. Most people end up paying for overlapping subscriptions or giving up on tools that would have helped. GDTai exists to make AI adoption simple, honest and profitable: a curated directory, practical guides, free utilities and a personal matching service — all in one place.</p>
<h2>What the name means</h2><p><strong>G</strong>uide, <strong>D</strong>iscover, <strong>T</strong>est — with <strong>ai</strong>. Guide you to the right tools, help you discover what's new, and encourage you to test tools on your own real work before you pay.</p>
<h2 id="editorial">Editorial policy</h2><ul>
<li>We list tools that are live, clearly useful and transparent about what they do and how they charge.</li>
<li>Editor's picks are based on quality, value and reliability. They are never for sale.</li>
<li>Paid placements are always labelled "Featured" or "Sponsored".</li>
<li>Descriptions are written by us in our own words; we link to official sites for current pricing.</li>
<li>Tools submitted by their makers are listed only after an editorial review against these criteria. Their pages show the review date and what we checked.</li>
<li>Found an error? <a href="{r}contact.html">Tell us</a> and we will correct it quickly.</li></ul>
<h2>How we stay free</h2><p>GDTai is funded by display advertising (Google AdSense), clearly labelled sponsorships, featured listings and <a href="{r}support.html">reader support</a>. This lets us keep every guide and utility free.</p>
<h2>Self-updating by design</h2><p>Our news, research, trending repositories and video sections refresh automatically several times a day, so you always see what's new without waiting for a manual update.</p>
<h2>Contact</h2><p>Questions, corrections or ideas? Use our <a href="{r}contact.html">contact form</a>. For domain, sponsorship, advertising or partnership interest, <a href="{INTEREST_URL}" target="_blank" rel="noopener nofollow">contact the owner here</a>.</p>
</div></section>""", [l], priority="0.5")

    # Contact
    cr, l = crumbs("", [(None, "Contact")])
    write("contact.html", "Contact GDTai", "Contact GDTai about corrections, partnerships, advertising, tool listings, privacy or general questions.",
          lambda r: f"""<section class="page-hero"><div class="wrap">{cr}<h1>Contact us</h1><p class="sub">We read every message and usually reply within 2 business days.</p></div></section>
<section class="section tight"><div class="wrap content-grid"><div>
<form class="gform card-form" data-form="contact" data-subject="✉️ New contact message — GDTai" novalidate>
{form_fields_contact(["General question", "Correction / update a listing", "Partnership", "Advertising / sponsorship", "Domain name enquiry", "Privacy request", "Press", "Other"])}
<input type="hidden" name="source" value="contact"><button class="btn btn-grad" type="submit">Send message</button><p class="form-status" aria-live="polite"></p></form></div>
<aside class="side"><div class="side-card"><h3>Faster routes</h3><ul class="plain"><li><a href="{r}get-matched.html">Get AI tool recommendations</a></li><li><a href="{r}submit-tool.html">Submit or feature a tool</a></li><li><a href="{r}advertise.html">Advertising &amp; media kit</a></li><li><a href="{r}careers.html">Work with us</a></li></ul></div>
<div class="side-card lead-side"><h3>Domain, sponsorship or partnership?</h3><p>Talk directly with the owner.</p><a class="btn btn-grad btn-block" href="{INTEREST_URL}" target="_blank" rel="noopener nofollow">Contact the owner</a></div></aside></div></section>""", [l], priority="0.5")

    legal_pages()


def legal_pages():
    upd = "18 November 2026"
    cr, l = crumbs("", [(None, "Privacy Policy")])
    write("privacy.html", "Privacy Policy", "How GDTai collects, uses and protects information, including cookies, Google AdSense advertising, forms and embedded videos.",
          lambda r: f"""<section class="page-hero"><div class="wrap narrow">{cr}<h1>Privacy Policy</h1><p class="meta">Last updated: {upd}</p></div></section>
<section class="section tight"><div class="wrap narrow prose">
<p>This policy explains what information GDTai ("we", "us") collects when you use this website, how we use it, and the choices you have.</p>
<h2>Information we collect</h2><ul>
<li><strong>Information you provide:</strong> when you submit a form (newsletter, AI Stack Match, contact, tool submission, donation pledge, contest entry or job application) we receive the details you enter, such as your name, email address and message.</li>
<li><strong>Usage and device data:</strong> like most websites, our hosting provider and advertising partners may process technical data such as IP address, browser type, pages visited and referring pages.</li>
<li><strong>Local preferences:</strong> we store settings such as theme, saved tools and cookie choices in your browser's local storage. This data stays on your device.</li></ul>
<h2>How we use information</h2><ul><li>To respond to your requests and send what you asked for (for example, your AI stack recommendations or the newsletter).</li><li>To operate, secure and improve the website.</li><li>To show advertising that keeps the site free.</li><li>To comply with legal obligations.</li></ul>
<p>We do not sell your personal information. We share AI Stack Match details with an implementation partner only if you explicitly request partner quotes.</p>
<h2>Advertising and cookies (Google AdSense)</h2>
<p>We use Google AdSense to display ads. Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to this website or other websites. Google's use of advertising cookies enables it and its partners to serve ads to you based on your visit to this site and/or other sites on the Internet.</p>
<p>You may opt out of personalised advertising by visiting <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google Ads Settings</a>, or opt out of some third-party vendors' use of cookies for personalised advertising at <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener">www.aboutads.info</a>. Learn more about <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">how Google uses information from sites that use its services</a>.</p>
<p>Visitors in the European Economic Area, the UK and Switzerland may be shown a consent message so they can choose whether to allow personalised ads. You can change your choice at any time via "Cookie settings" in the footer.</p>
<h2>Form processing</h2><p>Forms on this site are delivered to our inbox through a third-party form-forwarding service (FormSubmit). The information you enter is transmitted securely over HTTPS to that service solely to deliver your message to us.</p>
<h2>Embedded content</h2><p>Videos are embedded from YouTube using privacy-enhanced mode (youtube-nocookie.com) and load only after you click play. Tool logos are loaded from Google's public favicon service. These providers may collect data according to their own policies.</p>
<h2>Data retention</h2><p>We keep form submissions only as long as needed to handle your request and for reasonable record-keeping, then delete them.</p>
<h2>Your rights</h2><p>Depending on where you live (for example under the GDPR, UK GDPR, India's DPDP Act or US state laws such as the CCPA/CPRA), you may have the right to access, correct, delete or export your personal data, to object to or restrict processing, and to withdraw consent. To make a request, use our <a href="{r}contact.html">contact form</a> and choose "Privacy request".</p>
<h2>Children</h2><p>This website is not directed to children under 13 (or the relevant age in your country), and we do not knowingly collect their personal data.</p>
<h2>Security</h2><p>The site is served over HTTPS. No method of transmission or storage is completely secure, but we take reasonable measures to protect your information.</p>
<h2>Changes</h2><p>We may update this policy. Material changes will be reflected by the "Last updated" date above.</p>
<h2>Contact</h2><p>Questions? Reach us through the <a href="{r}contact.html">contact form</a>.</p></div></section>""", [l], priority="0.3")

    cr, l = crumbs("", [(None, "Terms of Use")])
    write("terms.html", "Terms of Use", "The terms that govern use of the GDTai website, forms, contests, listings and content.",
          lambda r: f"""<section class="page-hero"><div class="wrap narrow">{cr}<h1>Terms of Use</h1><p class="meta">Last updated: {upd}</p></div></section>
<section class="section tight"><div class="wrap narrow prose">
<p>By using GDTai you agree to these terms. If you do not agree, please do not use the site.</p>
<h2>Use of the site</h2><p>You may browse and use the site for lawful, personal and internal business purposes. Do not scrape the site at scale, attempt to disrupt it, submit spam, or misuse forms.</p>
<h2>Information only</h2><p>Content is provided for general information. Tool descriptions, pricing models and recommendations may change and may contain errors. Always confirm details on the official vendor website. Nothing on this site is legal, financial, tax or other professional advice.</p>
<h2>Third-party sites</h2><p>We link to third-party websites and tools. We do not control them and are not responsible for their content, products, privacy practices or availability.</p>
<h2>Submissions</h2><p>When you submit content (tool listings, contest entries, applications, messages) you confirm you have the right to do so and that it is accurate and lawful. You grant us a non-exclusive licence to display submitted listing and contest content on the site with credit. We may decline or remove any submission.</p>
<h2>Paid placements</h2><p>Featured and sponsored placements are labelled, run for the purchased period, and do not affect editorial picks. Refunds for placements are available before publication only.</p>
<h2>Contests</h2><p>Contests are free to enter, void where prohibited, and governed by the official rules on the contest page, which form part of these terms.</p>
<h2>Donations</h2><p>Donations are voluntary contributions to support the website and are not payment for goods or services. Unless stated otherwise they are not tax-deductible.</p>
<h2>Intellectual property</h2><p>Original text, design and code on GDTai are protected by copyright. Third-party names, logos and trademarks belong to their owners. See our <a href="{r}disclaimer.html">Disclaimer &amp; Trademark notice</a>.</p>
<h2>Limitation of liability</h2><p>To the fullest extent permitted by law, GDTai is provided "as is" without warranties, and we are not liable for any indirect or consequential loss arising from use of the site or reliance on its content.</p>
<h2>Changes</h2><p>We may update these terms; continued use means you accept the updated terms.</p>
<h2>Contact</h2><p>Use our <a href="{r}contact.html">contact form</a>.</p></div></section>""", [l], priority="0.3")

    cr, l = crumbs("", [(None, "Disclaimer & Trademarks")])
    write("disclaimer.html", "Disclaimer, Trademark & Copyright Disclosure", "GDTai's disclaimer, advertising and affiliate disclosure, and trademark and copyright notice.",
          lambda r: f"""<section class="page-hero"><div class="wrap narrow">{cr}<h1>Disclaimer, trademark &amp; copyright disclosure</h1><p class="meta">Last updated: {upd}</p></div></section>
<section class="section tight"><div class="wrap narrow prose">
<h2>Trademark disclosure</h2>
<p>"GDTai" is used solely as the descriptive name of this independent website — short for "Guide · Discover · Test AI". GDTai is <strong>not affiliated with, endorsed by, sponsored by or otherwise connected to</strong> any company, organisation, product, service or registered or unregistered trademark that uses "GDT", "GDT AI", "GDTai" or any similar name or abbreviation, in any industry or country. Any similarity is coincidental. No claim of trademark rights in "GDT" is made.</p>
<p>All product names, logos, brands and trademarks of third-party AI tools and companies mentioned on this site are the property of their respective owners. They are used for identification and descriptive purposes only (nominative use) and do not imply endorsement. Tool logos are fetched from a public favicon service for recognition.</p>
<h2>Copyright notice</h2>
<p>© {YEAR} GDTai. Unless otherwise stated, original articles, descriptions, glossary entries, prompts, design and code on this website are original works of GDTai. You may share links and short quotations with attribution. Republishing substantial portions without written permission is not allowed.</p>
<p>News headlines link to and remain the property of their original publishers; we display titles and source names only. Embedded videos remain the property of their creators and are shown via YouTube's official embed.</p>
<p>If you believe content on this site infringes your rights, please send a notice through our <a href="{r}contact.html">contact form</a> (topic: "Other") with the URL and details, and we will review and act promptly.</p>
<h2>Advertising &amp; affiliate disclosure</h2>
<p>GDTai earns revenue from display advertising (including Google AdSense), clearly labelled sponsorships and featured listings, and may in future earn commissions from some outbound links. This never changes our editorial picks, and sponsored content is always labelled.</p>
<h2>No professional advice</h2>
<p>Information on this site is general and educational. It is not legal, financial, tax, medical or other professional advice. Verify important details with the official vendor and qualified professionals.</p>
<h2>Accuracy</h2><p>AI products change quickly. We aim to keep information current but cannot guarantee completeness or accuracy at all times. Report errors via our <a href="{r}contact.html">contact form</a>.</p></div></section>""", [l], priority="0.3")


def build_404():
    body = """<section class="page-hero"><div class="wrap narrow center"><h1>404 — Page not found</h1><p class="sub">The page you're looking for moved or never existed.</p>
<p><a class="btn btn-grad" href="index.html">Go home</a> <a class="btn btn-ghost" href="tools/index.html">Browse AI tools</a></p></div></section>"""
    doc = head("404.html", "Page not found", "Page not found.", "", noindex=True)
    # Dynamic base so relative links work from any depth on project or custom-domain hosting
    doc = doc.replace("<head>\n", "<head>\n<script>(function(){var p=location.pathname,b=p.indexOf('/gdtai-com/')===0?'/gdtai-com/':'/';document.write('<base href=\"'+b+'\">');})();</script>\n", 1)
    doc += header("") + f'<main id="main">{body}</main>' + footer("")
    open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(doc)


def build_static_files():
    # tools JSON for client features
    os.makedirs(os.path.join(ROOT, "assets", "data"), exist_ok=True)
    with open(os.path.join(ROOT, "assets", "data", "tools.json"), "w", encoding="utf-8") as f:
        json.dump([{"slug": t["slug"], "name": t["name"], "cat": t["cat"], "catName": CAT[t["cat"]]["name"], "price": t["price"],
                    "desc": t["desc"], "best": t["best"], "tags": t["tags"], "url": t["url"], "domain": t["domain"], **({"ugc": True} if t.get("ugc") else {})} for t in TOOLS] +
                  [{"slug": "guide:" + g["slug"], "name": g["title"], "cat": "guide", "catName": "Guide", "desc": g["description"]} for g in GUIDES],
                  f, ensure_ascii=False)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p, pr, cf in PAGES:
        loc = SITE + "/" + (p[:-10] if p.endswith("index.html") else p)
        sm.append(f"<url><loc>{e(loc)}</loc><lastmod>{TODAY}</lastmod><changefreq>{cf}</changefreq><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm))
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /builder/\nDisallow: /content/\n\nUser-agent: Mediapartners-Google\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    open(os.path.join(ROOT, "ads.txt"), "w").write("google.com, pub-6620975821265271, DIRECT, f08c47fec0942fa0\n")
    open(os.path.join(ROOT, ".nojekyll"), "w").write("")
    json.dump({"name": "GDTai — Guide · Discover · Test AI", "short_name": "GDTai", "start_url": "./index.html", "display": "standalone",
               "background_color": "#0b0d17", "theme_color": "#7c3aed",
               "icons": [{"src": "assets/img/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]},
              open(os.path.join(ROOT, "manifest.webmanifest"), "w"))


if __name__ == "__main__":
    build_home()
    build_tools_index()
    build_tool_pages()
    build_categories()
    build_guides()
    build_news()
    build_videos()
    build_glossary()
    build_prompts()
    build_compare()
    build_free_tools()
    build_get_matched()
    build_checklist()
    build_simple_pages()
    build_404()
    build_static_files()
    print(f"Built {len(PAGES)} indexable pages · site={SITE} · tools={len(TOOLS)} · guides={len(GUIDES)}")
