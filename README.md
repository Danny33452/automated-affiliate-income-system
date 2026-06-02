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

This will fetch/refresh data, inject your affiliate IDs into the generated
links, and write the output (static HTML/assets) into the `public/` directory.

## How to Add Affiliate IDs

Affiliate IDs are stored in `config.json` (never commit real IDs to a public
repo). Add or update them under the `affiliates` section:

```json
{
  "affiliates": {
    "amazon": "yourtag-20",
    "shareasale": "1234567",
    "impact": "your-impact-id"
  }
}
```

Each network expects its own ID format. The script reads these values at run
time and appends them as query parameters / tags to every outbound link, so you
only need to set them once. To add a new network, add a new key/value pair and
reference it in your link templates.

You can also override IDs via environment variables for CI/CD secrets:

```bash
export AMAZON_AFFILIATE_ID="yourtag-20"
python3 run.py
```

## How to Schedule It (Hands-Off Operation)

### Option A: cron

Edit your crontab with `crontab -e` and add the line from
[`schedule.cron`](schedule.cron). For example, to run every day at 6:00 AM:

```cron
0 6 * * * cd /workspace && /usr/bin/python3 run.py >> /workspace/run.log 2>&1
```

### Option B: systemd timer

Create `/etc/systemd/system/affiliate.service`:

```ini
[Unit]
Description=Run affiliate automation

[Service]
Type=oneshot
WorkingDirectory=/workspace
ExecStart=/usr/bin/python3 /workspace/run.py
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
