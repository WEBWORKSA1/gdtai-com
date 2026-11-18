#!/usr/bin/env python3
"""Fetch fresh AI news, research papers, trending repos and YouTube videos.

Writes data/news.json, data/videos.json, data/repos.json. Every source is
optional: failures are logged and skipped, and existing data is kept if a
whole section comes back empty. Standard library only.
"""
import datetime as dt
import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "Mozilla/5.0 (compatible; GDTaiBot/1.0; +https://gdtai.com)"}
NOW = dt.datetime.now(dt.timezone.utc)

NEWS_FEEDS = [
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Google AI", "https://blog.google/technology/ai/rss/"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("MarkTechPost", "https://www.marktechpost.com/feed/"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("MIT Technology Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed/"),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed/"),
]
PAPER_FEEDS = [("arXiv cs.AI", "https://rss.arxiv.org/rss/cs.AI"), ("arXiv cs.CL", "https://rss.arxiv.org/rss/cs.CL"), ("arXiv cs.LG", "https://rss.arxiv.org/rss/cs.LG")]
YT_HANDLES = ["@TwoMinutePapers", "@mreflow", "@aiexplained-official", "@Fireship", "@AndrejKarpathy",
              "@3blue1brown", "@googledeepmind", "@YannicKilcher", "@OpenAI", "@anthropic-ai", "@MattVidPro", "@AIJasonZ"]


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(s.replace("Z", "+0000") if "T" in s else s, fmt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=dt.timezone.utc)
            return d
        except Exception:
            continue
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def parse_feed(source, xml_bytes, limit=15):
    out = []
    root = ET.fromstring(xml_bytes)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item")
    if items:
        for it in items[:limit]:
            title = clean(it.findtext("title"))
            link = (it.findtext("link") or "").strip()
            date = parse_date(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date"))
            if title and link.startswith("http"):
                out.append({"title": title[:180], "url": link, "source": source, "date": (date or NOW).isoformat()})
    else:
        for en in root.findall("a:entry", ns)[:limit]:
            title = clean(en.findtext("a:title", namespaces=ns))
            le = en.find("a:link[@rel='alternate']", ns)
            if le is None:
                le = en.find("a:link", ns)
            link = le.get("href") if le is not None else ""
            date = parse_date(en.findtext("a:published", namespaces=ns) or en.findtext("a:updated", namespaces=ns))
            if title and link.startswith("http"):
                out.append({"title": title[:180], "url": link, "source": source, "date": (date or NOW).isoformat()})
    return out


def fetch_feeds(feeds, per=12):
    items = []
    for name, url in feeds:
        try:
            items += parse_feed(name, get(url), per)
            print(f"  ok  {name}")
        except Exception as ex:
            print(f"  skip {name}: {ex}")
        time.sleep(0.4)
    return items


def hn():
    try:
        since = int(time.time()) - 3 * 86400
        url = ("https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=40"
               f"&numericFilters=created_at_i>{since},points>40")
        hits = json.loads(get(url))["hits"]
        print(f"  ok  Hacker News ({len(hits)})")
        return [{"title": h["title"], "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                 "source": "Hacker News", "date": h["created_at"]} for h in hits if h.get("title")]
    except Exception as ex:
        print(f"  skip Hacker News: {ex}")
        return []


def repos():
    since = (NOW - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    hdr = {**UA, "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        hdr["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    seen, out = set(), []
    for topic in ("llm", "ai-agents", "generative-ai", "machine-learning"):
        try:
            q = f"https://api.github.com/search/repositories?q=topic:{topic}+created:%3E{since}&sort=stars&order=desc&per_page=15"
            items = json.loads(urllib.request.urlopen(urllib.request.Request(q, headers=hdr), timeout=25).read())["items"]
            for r in items:
                if r["full_name"] not in seen:
                    seen.add(r["full_name"])
                    out.append({"name": r["full_name"], "url": r["html_url"], "stars": r["stargazers_count"],
                                "lang": r.get("language"), "desc": clean(r.get("description"))[:200]})
            print(f"  ok  GitHub topic:{topic} ({len(items)})")
        except Exception as ex:
            print(f"  skip GitHub topic:{topic}: {ex}")
        time.sleep(1)
    out.sort(key=lambda r: r["stars"], reverse=True)
    return out[:20]


def channel_id(handle, cache):
    if handle in cache:
        return cache[handle]
    html = get(f"https://www.youtube.com/{handle}").decode("utf-8", "ignore")
    m = re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', html) or re.search(r'channel/(UC[\w-]{22})', html)
    if m:
        cache[handle] = m.group(1)
        return m.group(1)
    return None


def youtube():
    cpath = os.path.join(DATA, "channels.json")
    cache = json.load(open(cpath)) if os.path.exists(cpath) else {}
    vids = []
    for h in YT_HANDLES:
        try:
            cid = channel_id(h, cache)
            if not cid:
                raise ValueError("no channel id")
            root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
            ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
            chname = root.findtext("a:title", namespaces=ns) or h
            for en in root.findall("a:entry", ns)[:4]:
                vid = en.findtext("yt:videoId", namespaces=ns)
                title = en.findtext("a:title", namespaces=ns)
                if vid and title and "#shorts" not in title.lower():
                    vids.append({"id": vid, "title": clean(title), "channel": chname,
                                 "date": en.findtext("a:published", namespaces=ns)})
            print(f"  ok  YouTube {h}")
        except Exception as ex:
            print(f"  skip YouTube {h}: {ex}")
        time.sleep(0.4)
    json.dump(cache, open(cpath, "w"), indent=1)
    vids.sort(key=lambda v: v.get("date") or "", reverse=True)
    return vids[:36]


def dedupe(items):
    seen, out = set(), []
    for it in items:
        k = re.sub(r"\W+", "", it["title"].lower())[:70]
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def save(name, payload, key="items"):
    path = os.path.join(DATA, name)
    if not payload.get(key):
        print(f"! {name}: nothing new, keeping previous data")
        return
    payload["updated"] = NOW.isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"✓ wrote {name}")


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    print("News feeds…")
    news = dedupe(sorted(fetch_feeds(NEWS_FEEDS) + hn(), key=lambda x: x["date"], reverse=True))[:80]
    print("Papers…")
    papers = dedupe(fetch_feeds(PAPER_FEEDS, 12))[:36]
    old = {}
    try:
        old = json.load(open(os.path.join(DATA, "news.json")))
    except Exception:
        pass
    save("news.json", {"items": news or old.get("items", []), "papers": papers or old.get("papers", [])})
    print("GitHub…")
    save("repos.json", {"items": repos()})
    print("YouTube…")
    save("videos.json", {"items": youtube()})
