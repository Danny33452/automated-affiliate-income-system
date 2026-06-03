"""Persist generated articles as reviewable Markdown files.

Each article is stored as ``<slug>.md`` with a small ``---`` frontmatter block
(``title`` / ``slug`` / ``keyword``) followed by the Markdown body. This makes
the content stage's output reviewable and editable in a pull request before the
publish stage renders it, which is what enables the review-gate workflow.
"""
import os

_FENCE = "---"


def serialize(article):
    lines = [
        _FENCE,
        f"title: {article.get('title', '')}",
        f"slug: {article.get('slug', '')}",
        f"keyword: {article.get('keyword', '')}",
        _FENCE,
        "",
    ]
    return "\n".join(lines) + article.get("markdown", "")


def parse(text):
    lines = text.splitlines()
    meta = {}
    body_start = 0
    if lines and lines[0].strip() == _FENCE:
        i = 1
        while i < len(lines) and lines[i].strip() != _FENCE:
            if ":" in lines[i]:
                key, value = lines[i].split(":", 1)
                meta[key.strip()] = value.strip()
            i += 1
        body_start = i + 1  # skip the closing fence
    body = "\n".join(lines[body_start:]).lstrip("\n")
    return {
        "title": meta.get("title", ""),
        "slug": meta.get("slug", ""),
        "keyword": meta.get("keyword", ""),
        "markdown": body,
    }


def write_articles(articles, content_dir):
    """Replace the Markdown files in ``content_dir`` with ``articles``."""
    os.makedirs(content_dir, exist_ok=True)
    for name in os.listdir(content_dir):
        if name.endswith(".md"):
            os.remove(os.path.join(content_dir, name))
    for article in articles:
        slug = article.get("slug") or "article"
        with open(os.path.join(content_dir, f"{slug}.md"), "w") as f:
            f.write(serialize(article))
    return len(articles)


def read_articles(content_dir):
    """Load all Markdown articles from ``content_dir`` (sorted by filename)."""
    if not os.path.isdir(content_dir):
        return []
    articles = []
    for name in sorted(os.listdir(content_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(content_dir, name)) as f:
            articles.append(parse(f.read()))
    return articles
