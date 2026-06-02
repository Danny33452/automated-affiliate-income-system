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

### GitHub Pages

1. Push the repository to GitHub.
2. Use a GitHub Actions workflow (scheduled with `on: schedule: cron`) to run
   `python3 run.py` and deploy the `public/` folder to the `gh-pages` branch.
3. Enable GitHub Pages in repository settings, serving from `gh-pages`.

GitHub Actions can both run the automation on a schedule **and** deploy the
static output, giving you fully hands-off, zero-cost hosting.

### Netlify

1. Connect your repository to Netlify.
2. Set the build command to `python3 run.py` and the publish directory to
   `public`.
3. Use Netlify scheduled builds (or a build hook triggered by cron) to rebuild
   periodically.

Both GitHub Pages and Netlify offer free tiers suitable for static affiliate
sites and require no server maintenance.
