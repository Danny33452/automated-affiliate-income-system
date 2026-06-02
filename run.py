#!/usr/bin/env python3
"""End-to-end static-site pipeline: trends -> content -> monetization -> site.

Runs entirely offline at zero per-run cost. Each stage delegates to the tested
modules in ``src/`` so the code that runs is the code that is covered by tests:

* :func:`src.trends.fetch_topics`    -- pick trending topics from seed keywords
* :func:`src.content.generate_article` -- draft a 300+ word SEO article
* :func:`src.monetize.inject_affiliate` -- inject affiliate links + disclosure

Markdown is rendered to HTML with the optional ``markdown`` package, falling
back to a small built-in renderer when it is not installed.
"""
import argparse
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


# ---------------------------------------------------------------------------
# Site rendering
# ---------------------------------------------------------------------------
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>body{{font-family:system-ui,Arial,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;line-height:1.6}}a{{color:#0366d6}}</style>
</head>
<body>
<nav><a href="index.html">&larr; Home</a></nav>
<article>
{body}
</article>
<footer><hr><p>{footer}</p></footer>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{site_title}</title>
<style>body{{font-family:system-ui,Arial,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;line-height:1.6}}a{{color:#0366d6}}li{{margin:.5rem 0}}</style>
</head>
<body>
<h1>{site_title}</h1>
<p>Latest articles:</p>
<ul>
{links}
</ul>
<footer><hr><p>{footer}</p></footer>
</body>
</html>
"""


def load_config(path):
    """Load the site config, returning an empty dict when no file is given."""
    if not path:
        return {}
    with open(path) as f:
        return json.load(f)


def seed_keywords(config):
    """Resolve seed keywords from explicit `keywords` or the affiliate map."""
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
    footer = f"© {datetime.now(timezone.utc).year} {config.get('author', '')}".strip()
    affiliates = config.get("affiliates", {})

    topics = fetch_topics(seed_keywords(config), limit=count)
    seen_slugs = set()
    articles = []
    for topic in topics:
        article = generate_article(topic)
        md_text = inject_affiliate(article["markdown"], affiliates)

        slug = article["slug"] or "article"
        # Guard against duplicate slugs producing overwritten pages.
        unique = slug
        n = 2
        while unique in seen_slugs:
            unique = f"{slug}-{n}"
            n += 1
        seen_slugs.add(unique)

        body_html = md_to_html(md_text)
        page = PAGE_TEMPLATE.format(
            title=article["title"], body=body_html, footer=footer
        )
        with open(os.path.join(out_dir, f"{unique}.html"), "w") as f:
            f.write(page)
        articles.append((article["title"], f"{unique}.html"))

    links = "\n".join(
        f'<li><a href="{href}">{title}</a></li>' for title, href in articles
    )
    index = INDEX_TEMPLATE.format(
        site_title=site_title, links=links, footer=footer
    )
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(index)
    return len(articles)


def default_config_path(base_dir):
    """Prefer a real config.json, else fall back to the committed example."""
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
