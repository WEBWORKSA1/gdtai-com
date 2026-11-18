# GDTai.com — phase-wise build prompts

**Concept:** GDTai = "Guide · Discover · Test AI": a self-updating AI tools directory + learning hub + free AI utilities, monetised by AdSense, featured listings, sponsorships, donations and a high-intent B2B lead funnel (AI Stack Match).

**Why this idea:** AI tools is a fast-growing, high-search-volume niche with SaaS/B2B advertisers (strong AdSense RPM potential). Directories create hundreds of indexable long-tail pages ("X alternatives", "best X tools"). Tool founders pay for featured listings ($12–$500 per placement among the 38 sites reviewed). Business visitors who are choosing tools are ideal leads for implementation partners and affiliates.

---

## Phase 1 — Foundation & compliance
> Build a static, responsive website for GDTai.com deployable on GitHub Pages (main branch, root). Use a Python generator that writes HTML to the repo root with relative links. Every page: AdSense script `ca-pub-6620975821265271` in `<head>`, `google-adsense-account` meta, canonical, Open Graph, JSON-LD, and a top bar reading "Contact, if you are interested in this website/domain name/Sponsorship/Advertisement/Partnership" linking to web.works/contact without showing the URL. Add ads.txt, robots.txt, sitemap.xml, manifest, 404, cookie consent, Privacy Policy (Google advertising cookie disclosure + opt-out links), Terms, Disclaimer with trademark/copyright disclosure stating GDTai is not affiliated with any "GDT"/"GDTai" mark.

## Phase 2 — Design system
> Create a modern design system: light/dark/auto themes, violet→cyan gradient brand, glass sticky header, mobile drawer menu, global search overlay (press "/"), cards, badges, FAQ accordions, reveal animations, accessible focus states, reduced-motion support, print styles.

## Phase 3 — Directory core
> Add a curated catalogue (15 categories, 120+ tools) with name, URL, pricing model, original description, best-for and tags. Generate a filterable directory page (search, category, pricing, saved), a page per tool (overview, use cases, quick facts, evaluation tips, FAQ schema, alternatives, claim/feature CTA), category pages with FAQ, and a 3-way compare page.

## Phase 4 — Original content for AdSense approval
> Write 8+ original 700–900-word guides (choosing tools, AI for small business, prompting, free vs paid, RAG, agents, video workflow, responsible AI), a 50-term glossary and a 30-prompt library. No copied text. Add Article/FAQ/DefinedTermSet schema.

## Phase 5 — Lead generation engine
> Build a dedicated "Free AI Stack Match" page: 5-step wizard (profile, interests, budget + current tools, timeline + challenge + partner-quotes opt-in, contact + consent), progress bar, auto-advance, instant starter-stack preview on submit. Add a hero quick-lead form on the homepage, sidebar CTAs on every tool/guide page, inline CTAs on categories/calculators, a gated AI Adoption Checklist lead magnet and a newsletter band on every page. All forms submit via AJAX to a form-forwarding service whose address is assembled at runtime so it never appears in markup.

## Phase 6 — Monetisation pages
> Add Submit Tool (Free / Featured $49 / Spotlight $149), Advertise (category, newsletter, sponsored guide, contest sponsor + owner contact), Support/Donate (tiers, purpose allocation for operations, promotion, hiring, prizes, configurable PayPal/Ko-fi/BMC/UPI/GitHub links with pledge-form fallback), Contests (monthly challenge, prizes, judging, official rules, entry form), Careers (6 roles + application form). Add optional manual AdSense slots via config while Auto ads work by default.

## Phase 7 — Free utilities
> Add in-browser tools: token & API cost calculator, prompt builder, AI ROI calculator — each with an inline lead CTA.

## Phase 8 — Self-updating automation
> Write refresh.py (stdlib only) to pull AI news RSS (OpenAI, Google AI, DeepMind, Hugging Face, MarkTechPost, TechCrunch, The Verge, VentureBeat, MIT TR, AWS, NVIDIA) + Hacker News, arXiv cs.AI/CL/LG, trending GitHub AI repos, and YouTube videos from top AI channels (resolve @handles to channel RSS). Keep old data if a source fails. Add a GitHub Actions workflow on a 6-hour cron + manual + push that refreshes, rebuilds, commits and requests a Pages build.

## Phase 9 — Launch & growth
> Connect gdtai.com custom domain, enforce HTTPS, submit sitemap to Google Search Console, apply to AdSense once 15–30 indexed pages show, enable Auto ads + Google's consent message (CMP) for EEA/UK. Submit GDTai to Tier-1 launch directories, publish 2 new guides per week, add 10 tools per week, send the newsletter twice a week, and run the first contest once a sponsor funds the prize pool.
