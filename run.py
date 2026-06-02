#!/usr/bin/env python3
"""End-to-end static site pipeline: trends -> content -> monetization -> site.

Runs entirely offline with zero external paid services. Trend selection,
content generation and monetization injection are deterministic local
operations. Markdown is rendered to HTML (using the `markdown` package when
available, otherwise a small built-in fallback).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone

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
        # inline links and bold
        out = "\n".join(html_lines)
        out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', out)
        out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
        return out


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------
def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "article"


def get_trends(config, count):
    """Select `count` trending topics deterministically from config."""
    trends = list(config.get("trends", []))
    if not trends:
        trends = ["technology", "science", "business", "health", "culture"]
    # deterministic rotation by day so it "refreshes" without paid APIs
    seed = int(datetime.now(timezone.utc).strftime("%Y%m%d"))
    rotated = trends[seed % len(trends):] + trends[: seed % len(trends)]
    selected = []
    i = 0
    while len(selected) < count:
        selected.append(rotated[i % len(rotated)])
        i += 1
    return selected[:count]


def generate_content(topic, config):
    """Generate article markdown for a topic (offline, template-based)."""
    author = config.get("author", "Editorial Team")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"The Rise of {topic.title()}: What You Need to Know"
    md = []
    md.append(f"# {title}")
    md.append("")
    md.append(f"*By {author} — {now}*")
    md.append("")
    md.append(
        f"{topic.title()} is shaping conversations across the industry. "
        f"In this article we break down why {topic} matters and how you can "
        f"stay ahead of the curve."
    )
    md.append("")
    md.append("## Why It Matters")
    md.append("")
    md.append(
        f"Interest in {topic} has grown rapidly. Here are the key drivers:"
    )
    md.append("")
    md.append(f"- Increasing demand and adoption of {topic}")
    md.append("- Strong long-term outlook and investment")
    md.append("- Real-world impact on everyday life")
    md.append("")
    md.append("## Getting Started")
    md.append("")
    md.append(
        f"Whether you are a beginner or an expert, understanding {topic} "
        "gives you an edge. Start small, learn continuously, and apply "
        "what you discover."
    )
    md.append("")
    md.append("## Conclusion")
    md.append("")
    md.append(
        f"{topic.title()} is here to stay. Bookmark this page and check back "
        "for ongoing updates."
    )
    md.append("")
    return title, "\n".join(md)


def monetize(markdown_text, config):
    """Inject monetization blocks (affiliate links + ad slots) offline."""
    mon = config.get("monetization", {})
    blocks = []
    ad_slot = mon.get("ad_slot")
    if ad_slot:
        blocks.append(f"\n> **Sponsored** — Ad slot `{ad_slot}`\n")
    products = mon.get("products", [])
    tag = mon.get("affiliate_tag", "")
    if products:
        blocks.append("## Recommended Products")
        blocks.append("")
        for p in products:
            url = p.get("url", "#")
            sep = "&" if "?" in url else "?"
            aff_url = f"{url}{sep}tag={tag}" if tag else url
            blocks.append(f"- [{p.get('name', 'Product')}]({aff_url})")
        blocks.append("")
    if not blocks:
        return markdown_text
    return markdown_text + "\n\n" + "\n".join(blocks) + "\n"


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


def build_site(config, count, out_dir, md_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)
    site_title = config.get("site_title", "My Site")
    footer = f"© {datetime.now(timezone.utc).year} {config.get('author', '')}".strip()

    topics = get_trends(config, count)
    articles = []
    for topic in topics:
        title, md_text = generate_content(topic, config)
        md_text = monetize(md_text, config)
        slug = slugify(title)[:60] or hashlib.md5(title.encode()).hexdigest()[:8]
        # write markdown
        with open(os.path.join(md_dir, f"{slug}.md"), "w") as f:
            f.write(md_text)
        # render html page
        body_html = md_to_html(md_text)
        page = PAGE_TEMPLATE.format(title=title, body=body_html, footer=footer)
        with open(os.path.join(out_dir, f"{slug}.html"), "w") as f:
            f.write(page)
        articles.append((title, f"{slug}.html"))

    links = "\n".join(
        f'<li><a href="{href}">{title}</a></li>' for title, href in articles
    )
    index = INDEX_TEMPLATE.format(site_title=site_title, links=links, footer=footer)
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(index)
    return len(articles)


def main():
    ap = argparse.ArgumentParser(description="Static trends->content->money site pipeline")
    ap.add_argument("--config", required=True, help="Path to JSON config file")
    ap.add_argument("--count", type=int, default=5, help="Number of articles to generate")
    args = ap.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(args.config)), "site")
    md_dir = os.path.join(os.path.dirname(os.path.abspath(args.config)), "content")
    # clean previous build
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)

    n = build_site(config, args.count, out_dir, md_dir)
    print(f"Generated {n} articles into {out_dir}")
    print(f"Open: {os.path.join(out_dir, 'index.html')}")


if __name__ == "__main__":
    main()
