"""Optional Claude-API article drafting with a safe offline fallback.

When ``ANTHROPIC_API_KEY`` is set and the ``anthropic`` package is installed,
:func:`draft_markdown` returns an AI-written SEO article in Markdown. In every
other case -- no key, package missing, empty response, or any API error -- it
returns ``None`` so callers fall back to the deterministic template generator.
This keeps the pipeline working offline at zero cost by default.

Prompt caching: the (static) system prompt is sent as a cached block, so across
a batch of articles in one run only the first call pays full price for it.
"""
import os

# Default to a capable, cost-effective model; override with AFFILIATE_MODEL.
MODEL = os.environ.get("AFFILIATE_MODEL", "claude-sonnet-4-6")
_MAX_TOKENS = 1600

SYSTEM_PROMPT = (
    "You are an expert SEO content writer for an affiliate review website. "
    "Write helpful, accurate, original articles that follow Google's "
    "helpful-content guidelines. Use Markdown: a single H1 title, then 2-4 H2 "
    "sections, and a short conclusion. Be concrete and avoid filler. Do not "
    "invent statistics, prices, or fake user reviews, and never fabricate "
    "medical, legal, or financial claims."
)


def _client():
    """Return an Anthropic client, or ``None`` when AI drafting is unavailable."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except Exception:  # package not installed
        return None
    try:
        return anthropic.Anthropic()
    except Exception:  # misconfigured client
        return None


def draft_markdown(topic, keyword, client=None):
    """Draft an SEO article in Markdown, or return ``None`` to use the fallback.

    Args:
        topic: the article's target search query / title.
        keyword: the primary keyword to emphasize.
        client: optional pre-built Anthropic-style client (used in tests). When
            omitted, a real client is created only if a key is configured.
    """
    client = client or _client()
    if client is None:
        return None

    prompt = (
        f'Write a 600-900 word SEO article for the search query "{topic}".\n'
        f'Primary keyword: "{keyword}".\n'
        f"Start with an H1 titled exactly: # {topic}\n"
        "Include an introduction, 2-4 H2 sections with practical guidance, and "
        "a short conclusion. Output only Markdown, with no preamble."
    )
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=_MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:  # network / API / rate-limit error -> fall back
        return None

    text = "".join(
        getattr(block, "text", "")
        for block in getattr(resp, "content", [])
        if getattr(block, "type", "") == "text"
    ).strip()
    if not text:
        return None
    if not text.lstrip().startswith("#"):
        text = f"# {topic}\n\n{text}"
    return text
