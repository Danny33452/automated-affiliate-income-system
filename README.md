# Affiliate Automation

This project runs an automated workflow (`run.py`) that generates affiliate
content/links and publishes them as a static site for hands-off operation.

## Setup

1. Install Python 3.9+.
2. Clone or copy this repository into a working directory.
3. (Recommended) Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Copy `config.example.json` to `config.json` and fill in your values.

## How to Run the Automation

Run the main script manually to verify everything works:

```bash
python3 run.py
```

This runs the full pipeline — pick trending topics from your seed keywords
(`src/trends.py`), draft SEO articles (`src/content.py`), inject your affiliate
links plus an FTC disclosure (`src/monetize.py`), and render a static site into
the `public/` directory with an `index.html` linking every article.

With no arguments it loads `config.json` if present, otherwise the committed
`config.example.json`. You can also pass options explicitly:

```bash
python3 run.py --config config.json --count 10 --out public
```

### Running the tests

```bash
pip install pytest
python3 -m pytest
```

## Configuration via environment variables

All of these are optional — with none set, the pipeline runs fully offline at
zero per-run cost using deterministic templates.

| Variable | Effect |
|----------|--------|
| `ANTHROPIC_API_KEY` | Enables real AI article drafting via the Claude API. Without it, articles use the offline template. |
| `AFFILIATE_MODEL` | Claude model id for drafting (default `claude-sonnet-4-6`). |
| `AFFILIATE_TRENDS` | `remote` pulls real related search queries from Google Autocomplete (free, no key); `local` (default) uses the offline template expansion. Remote always falls back to local on any network error. |

Example — fully "live" run:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export AFFILIATE_TRENDS=remote
python3 run.py --count 10
```

## Site config fields

The JSON config (`config.json`, falling back to `config.example.json`) supports:

| Field | Purpose |
|-------|---------|
| `site_title` / `author` | Branding shown on pages and in structured data. |
| `description` | Site meta description and fallback for article descriptions. |
| `base_url` | Public site URL. Required for absolute canonical/Open Graph URLs and the sitemap (e.g. `https://USER.github.io/REPO`). |
| `google_site_verification` | Optional token; rendered as the Search Console verification `<meta>` tag. |
| `keywords` | Seed keywords for topic selection (defaults to the affiliate keys). |
| `affiliates` | Keyword → affiliate URL map (see below). |

## SEO output

Every build writes, alongside the article pages and `index.html`:

- **`sitemap.xml`** and **`robots.txt`** (submit the sitemap to Google Search Console).
- Per-page **meta description**, **canonical** link, and **Open Graph** tags.
- **`Article` JSON-LD** structured data for rich results.
- **Automatic internal links** — each page gets a "Related articles" section
  linking the most topically-related pages (shared keyword + title overlap),
  which spreads SEO link equity and keeps readers on the site.

Set `base_url` so these contain absolute URLs, and paste your Search Console
token into `google_site_verification` to verify ownership.

## Comparison roundups (money pages)

The highest-converting affiliate format is a "best X" roundup: an at-a-glance
comparison table plus a section per product with pros/cons and a call to action.
Define these under a `roundups` array in your config — each is rendered as its
own page (in addition to the keyword articles) with an HTML comparison table and
`rel="nofollow sponsored"` affiliate links:

```json
"roundups": [
  {
    "title": "Best Espresso Machines for Home Baristas",
    "keyword": "espresso machine",
    "products": [
      {
        "name": "Breville Bambino Plus",
        "url": "https://www.amazon.com/s?k=Breville+Bambino+Plus&tag=danny33452-20",
        "best_for": "Best for small kitchens",
        "price": "$$",
        "summary": "Compact single-boiler machine with fast heat-up.",
        "pros": ["Heats up in ~3s", "Automatic milk frothing"],
        "cons": ["Small water tank", "No built-in grinder"],
        "rating": 4.6
      }
    ]
  }
]
```

`rating` is optional. The product copy is editorial — **review it for accuracy
and current pricing before publishing.** Swapping the search URLs for specific
product/ASIN links typically converts better.

## How to Add Affiliate Links

Affiliate links live in `config.json` (never commit real links/IDs to a public
repo). The `affiliates` section maps a **keyword** to the **full affiliate URL**
you want that keyword to link to. When a keyword appears in a generated article,
the first occurrence is turned into a link (once per keyword), and an FTC
disclosure line is appended automatically:

```json
{
  "site_title": "My Affiliate Site",
  "author": "Editorial Team",
  "keywords": ["running shoes", "coffee maker"],
  "affiliates": {
    "running shoes": "https://www.amazon.com/dp/XXXX?tag=yourtag-20",
    "coffee maker": "https://www.example.com/track?id=1234567"
  }
}
```

Put your network's tag/ID directly in the URL (for example Amazon's
`?tag=yourtag-20`). The `keywords` list seeds topic selection; if you omit it,
the keys of `affiliates` are used instead.

## Content review gate

Generation and publishing are separate stages so AI content can be reviewed
before it goes live (Google penalizes unreviewed bulk AI content):

1. **Generate** — `python run.py --write-content` writes articles as Markdown
   into `content/` (with frontmatter). No HTML is rendered.
2. **Review** — edit the Markdown in `content/`. The
   `Generate content for review` workflow runs this on a schedule, validates the
   output (`python -m src.validate content`), and opens a pull request with the
   changes; nothing publishes until you merge it. Validation also runs in the
   test suite against the committed `content/`.
3. **Publish** — `python run.py --from-content` renders the site from the
   committed Markdown in `content/` (no AI/generation), so what you approved is
   exactly what ships. The deploy workflow runs this on merge to `main`.

`content/` is tracked in git (it is the reviewed source of truth);
`public/` (rendered HTML) is not. `python run.py` with no flags still does the
old one-shot generate-and-render for local previews.

## How to Schedule It (Hands-Off Operation)

### Option A: cron

Edit your crontab with `crontab -e` and add the line from
[`schedule.cron`](schedule.cron). For example, to run every day at 6:00 AM:

```cron
0 6 * * * cd /path/to/automated-affiliate-income-system && /usr/bin/python3 run.py >> run.log 2>&1
```

### Option B: systemd timer

Create `/etc/systemd/system/affiliate.service`:

```ini
[Unit]
Description=Run affiliate automation

[Service]
Type=oneshot
WorkingDirectory=/path/to/automated-affiliate-income-system
ExecStart=/usr/bin/python3 /path/to/automated-affiliate-income-system/run.py
```

Create `/etc/systemd/system/affiliate.timer`:

```ini
[Unit]
Description=Daily affiliate automation timer

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now affiliate.timer
```

## Free / Low-Cost Deployment

Because the output is a static site in `public/`, you can host it for free.

### GitHub Pages (included workflow)

This repo ships a ready-to-use workflow at
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) that runs the
tests, generates the site, and deploys it to GitHub Pages. It triggers daily
(`cron: 0 6 * * *`), on pushes to `main`, and manually via **Run workflow**.

One-time setup:

1. Push this repository to GitHub.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. (Optional, to go "live") In **Settings → Secrets and variables → Actions**:
   - add secret `ANTHROPIC_API_KEY` to enable AI drafting;
   - add repository variable `AFFILIATE_TRENDS=remote` for live keyword trends;
   - optionally `AFFILIATE_MODEL` to pick a Claude model.

Without those, the scheduled deploy still works — it just uses the offline
templates and local trends, giving you fully hands-off, zero-cost hosting.

> The build uses `config.json` if present, otherwise `config.example.json`.
> `config.json` is git-ignored by default; affiliate tags are public on the
> live page anyway, so for a deployed site either commit a `config.json`
> (remove it from `.gitignore`) or edit `config.example.json` with your links.

### Netlify

1. Connect your repository to Netlify.
2. Set the build command to `python3 run.py` and the publish directory to
   `public`.
3. Use Netlify scheduled builds (or a build hook triggered by cron) to rebuild
   periodically.

Both GitHub Pages and Netlify offer free tiers suitable for static affiliate
sites and require no server maintenance.
