"""Affiliate link injection for article markdown."""
import json
import re

DISCLOSURE = (
    "_Disclosure: This article contains affiliate links. "
    "We may earn a commission at no extra cost to you._"
)


def load_config(path="config.example.json"):
    """Load affiliate config (keyword -> URL) from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("affiliates", data)


def inject_affiliate(markdown, config, disclosure=DISCLOSURE):
    """Insert affiliate links for keywords and append a disclosure notice.

    Args:
        markdown: the article markdown text.
        config: dict mapping keyword -> affiliate URL.
        disclosure: disclosure line appended to the article.

    Returns:
        Modified markdown with affiliate links and a disclosure notice.
    """
    result = markdown
    # Replace longer keywords first to avoid partial overlaps.
    for keyword in sorted(config, key=len, reverse=True):
        url = config[keyword]
        pattern = re.compile(
            r"(?<!\])\b" + re.escape(keyword) + r"\b(?!\])",
            re.IGNORECASE,
        )

        def repl(m):
            return f"[{m.group(0)}]({url})"

        result, n = pattern.subn(repl, result, count=1)

    if disclosure not in result:
        result = result.rstrip() + "\n\n" + disclosure + "\n"
    return result
