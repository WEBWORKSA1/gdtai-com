# GDTai — Guide · Discover · Test AI

A self-updating AI tools directory and learning hub, built as a fast static site for **GitHub Pages (main branch, root)**.

- 123 curated AI tools with individual pages, 15 categories, compare tool, saved favourites
- 8 original long-form guides, 50-term glossary, 30-prompt library
- Free utilities: token & API cost calculator, prompt builder, AI ROI calculator
- **Lead generation:** multi-step "AI Stack Match" wizard, hero quick-lead form, lead magnet (AI Adoption Checklist), newsletter
- **Monetisation:** Google AdSense (Auto ads + optional manual slots), featured listings, advertising/sponsorship, donations, contests, careers
- **Auto-refresh:** GitHub Action every 6 hours pulls AI news (lab blogs, publications, Hacker News), arXiv papers, trending GitHub repos and YouTube videos, then rebuilds every page
- AdSense-ready: ads.txt, privacy policy with Google cookie disclosure, terms, disclaimer + trademark notice, cookie consent, sitemap, robots, structured data

## Structure
```
builder/build.py        static site generator (writes HTML to repo root)
builder/refresh.py      fetches news/papers/repos/videos into data/*.json
builder/tools_data.py   tool catalogue — add tools here
builder/content_data.py glossary + prompt library
content/guides/*.html   guide articles (front-matter in the top comment)
assets/                 CSS, JS, images, generated tools.json
assets/js/config.js     ad-slot IDs and donation links (edit without rebuilding)
.github/workflows/      auto-refresh job
```

## Local build
```
python3 builder/refresh.py   # optional, needs internet
python3 builder/build.py
python3 -m http.server       # open http://localhost:8000
```

## Custom domain (gdtai.com)
Settings → Pages → Custom domain → `gdtai.com`, then at your DNS provider add A records to
185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 and a `www` CNAME to `webworksa1.github.io`.
GitHub writes a `CNAME` file; the next build switches canonical URLs, sitemap and robots to the custom domain automatically. Enable "Enforce HTTPS".

## Forms
All forms post via a form-forwarding service to the owner's inbox; the address is assembled at runtime and never appears in page markup. The very first submission triggers a one-time activation email that must be confirmed.

## Legal
"GDTai" is used only as this website's descriptive name and is not affiliated with any company or mark using "GDT", "GDTai" or similar names. Third-party names and logos belong to their owners.
