#!/usr/bin/env python3
"""End-to-end static-site pipeline: trends -> content -> monetization -> site.

Runs entirely offline at zero per-run cost. Each stage delegates to the tested
modules in ``src/`` so the code that runs is the code that is covered by tests:

* :func:`src.trends.fetch_topics`       -- pick topics from seed keywords
* :func:`src.content.generate_article`  -- draft a 300+ word SEO article
* :func:`src.monetize.inject_affiliate` -- inject affiliate links + disclosure

In addition to the article pages it emits the SEO essentials needed to get
indexed and earn: per-page meta description / canonical / Open Graph tags,
``Article`` JSON-LD structured data, a ``sitemap.xml`` and a ``robots.txt``.
"""
import argparse
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone

from src.content import generate_article
from src.monetize import inject_affiliate
from src.trends import fetch_topics

# ---------------------------------------------------------------------------
# Markdown rendering (optional dependency with a safe fallback)
# ---------------------------------------------------------------------------
try:
    import markdown as _md

    def md_to_html(text):
        return _md.markdown(text, extensions=["extra", "toc"])
except Exception:  # pragma: no cover - fallback path
    def md_to_html(text):
        html_lines = []
        in_list = False
        for line in text.splitlines():
            line = line.rstrip()
            if line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line[2:]}</li>")
            elif not line:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
            else:
                html_lines.append(f"<p>{line}</p>")
        if in_list:
            html_lines.append("</ul>")
        out = "\n".join(html_lines)
        out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', out)
        out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
        return out


_STYLE = (
    "body{font-family:system-ui,Arial,sans-serif;max-width:720px;margin:2rem "
    "auto;padding:0 1rem;line-height:1.6}a{color:#0366d6}li{margin:.5rem 0}"
)


# ---------------------------------------------------------------------------
# SEO helpers
# ---------------------------------------------------------------------------
def _strip_md(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links -> text
    text = re.sub(r"[#*_`>]", "", text)
    return text.strip()


def meta_description(markdown, fallback, limit=155):
    """First real paragraph, cleaned and truncated, for the meta description."""
    for line in markdown.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        clean = _strip_md(line)
        if clean:
            if len(clean) > limit:
                clean = clean[: limit - 1].rsplit(" ", 1)[0] + "…"
            return clean
    return fallback


def _verification_meta(token):
    if not token:
        return ""
    return f'\n<meta name="google-site-verification" content="{html.escape(token)}">'


def render_page(title, body_html, *, description, canonical, footer,
                author, date, verification):
    ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "author": {"@type": "Organization", "name": author},
        "datePublished": date,
        "dateModified": date,
    }
    if canonical:
        ld["url"] = canonical
    ld_json = json.dumps(ld, ensure_ascii=False)
    canonical_tags = ""
    if canonical:
        canonical_tags = (
            f'\n<link rel="canonical" href="{html.escape(canonical)}">'
            f'\n<meta property="og:url" content="{html.escape(canonical)}">'
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">{canonical_tags}{_verification_meta(verification)}
<script type="application/ld+json">{ld_json}</script>
<style>{_STYLE}</style>
</head>
<body>
<nav><a href="index.html">&larr; Home</a></nav>
<article>
{body_html}
</article>
<footer><hr><p>{footer}</p></footer>
</body>
</html>
"""


def render_index(site_title, description, links, footer, *, verification):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(site_title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(site_title)}">
<meta property="og:description" content="{html.escape(description)}">{_verification_meta(verification)}
<style>{_STYLE}</style>
</head>
<body>
<h1>{html.escape(site_title)}</h1>
<p>{html.escape(description)}</p>
<p>Latest articles:</p>
<ul>
{links}
</ul>
<footer><hr><p>{footer}</p></footer>
</body>
</html>
"""


def render_sitemap(base_url, slugs, date):
    urls = [f"  <url><loc>{base_url}/</loc><lastmod>{date}</lastmod></url>"]
    for slug in slugs:
        loc = f"{base_url}/{slug}.html" if base_url else f"{slug}.html"
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{date}</lastmod></url>")
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )


def render_robots(base_url):
    lines = ["User-agent: *", "Allow: /"]
    if base_url:
        lines += ["", f"Sitemap: {base_url}/sitemap.xml"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def load_config(path):
    if not path:
        return {}
    with open(path) as f:
        return json.load(f)


def seed_keywords(config):
    keywords = config.get("keywords")
    if keywords:
        return list(keywords)
    affiliates = config.get("affiliates", {})
    if affiliates:
        return list(affiliates.keys())
    return ["technology", "health", "home office", "fitness", "cooking"]


def build_site(config, count, out_dir):
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    site_title = config.get("site_title", "My Affiliate Site")
    author = config.get("author") or site_title
    site_desc = config.get("description", site_title)
    base_url = config.get("base_url", "").rstrip("/")
    verification = config.get("google_site_verification", "")
    affiliates = config.get("affiliates", {})
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    footer = f"© {datetime.now(timezone.utc).year} {author}".strip()

    topics = fetch_topics(seed_keywords(config), limit=count)
    seen_slugs = set()
    articles = []
    for topic in topics:
        article = generate_article(topic)
        md_text = inject_affiliate(article["markdown"], affiliates)

        slug = article["slug"] or "article"
        unique = slug
        n = 2
        while unique in seen_slugs:
            unique = f"{slug}-{n}"
            n += 1
        seen_slugs.add(unique)

        canonical = f"{base_url}/{unique}.html" if base_url else ""
        description = meta_description(md_text, site_desc)
        page = render_page(
            article["title"],
            md_to_html(md_text),
            description=description,
            canonical=canonical,
            footer=footer,
            author=author,
            date=date,
            verification=verification,
        )
        with open(os.path.join(out_dir, f"{unique}.html"), "w") as f:
            f.write(page)
        articles.append((article["title"], unique))

    links = "\n".join(
        f'<li><a href="{slug}.html">{html.escape(title)}</a></li>'
        for title, slug in articles
    )
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(render_index(site_title, site_desc, links, footer,
                             verification=verification))

    with open(os.path.join(out_dir, "sitemap.xml"), "w") as f:
        f.write(render_sitemap(base_url, [s for _, s in articles], date))
    with open(os.path.join(out_dir, "robots.txt"), "w") as f:
        f.write(render_robots(base_url))
    return len(articles)


def default_config_path(base_dir):
    for name in ("config.json", "config.example.json"):
        candidate = os.path.join(base_dir, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        description="Static trends->content->monetization site pipeline"
    )
    ap.add_argument(
        "--config",
        default=default_config_path(base_dir),
        help="Path to JSON config (defaults to config.json or config.example.json)",
    )
    ap.add_argument(
        "--count", type=int, default=5, help="Number of articles to generate"
    )
    ap.add_argument(
        "--out",
        default=os.path.join(base_dir, "public"),
        help="Output directory for the static site (default: ./public)",
    )
    args = ap.parse_args()

    config = load_config(args.config)
    n = build_site(config, args.count, args.out)
    print(f"Generated {n} articles into {args.out}")
    print(f"Open: {os.path.join(args.out, 'index.html')}")


if __name__ == "__main__":
    main()
