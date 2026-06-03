"""Automatic internal linking between related articles.

Internal links help SEO (they spread crawl/link equity and keep readers on the
site) and improve UX. :func:`related_links` scores every other article against
the current one by shared primary keyword and overlapping title words, and
returns the best matches as ``(title, slug)`` pairs.
"""
import re

# Common words that shouldn't count toward topical similarity.
_STOP = {
    "the", "a", "an", "for", "and", "to", "of", "in", "on", "best", "how",
    "your", "you", "with", "what", "need", "know", "this", "that", "guide",
    "tips", "are", "is", "it", "from", "about",
}


def _tokens(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def related_links(records, index, max_links=3):
    """Return up to ``max_links`` ``(title, slug)`` pairs related to ``records[index]``.

    ``records`` is a list of dicts with at least ``title`` and ``slug`` keys and
    an optional ``keyword``. Scoring: +3 for a shared primary keyword, +1 per
    overlapping significant title word. Ties keep the original order so output
    is deterministic.
    """
    current = records[index]
    cur_kw = (current.get("keyword") or "").lower().strip()
    cur_tokens = _tokens(current.get("title", ""))

    scored = []
    for i, rec in enumerate(records):
        if i == index:
            continue
        score = 0
        kw = (rec.get("keyword") or "").lower().strip()
        if cur_kw and kw == cur_kw:
            score += 3
        score += len(cur_tokens & _tokens(rec.get("title", "")))
        if score > 0:
            scored.append((score, i, rec))

    scored.sort(key=lambda t: (-t[0], t[1]))
    return [(rec["title"], rec["slug"]) for _, _, rec in scored[:max_links]]
