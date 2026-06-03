"""Trend / keyword topic fetching.

Two providers are available:

* ``_local_provider`` -- a deterministic, zero-cost template expansion used by
  default so the pipeline works offline and tests stay stable.
* ``_remote_provider`` -- real related search queries from Google Autocomplete
  (``suggestqueries.google.com``), a free endpoint that needs no API key. It is
  opt-in and always degrades gracefully to the local provider on any error.

Selection is controlled by the ``AFFILIATE_TRENDS`` environment variable
(``local`` by default, ``remote`` to enable the live source) or by passing an
explicit ``provider`` to :func:`fetch_topics`.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional, Sequence

# Local fallback dataset: topic templates expanded per keyword.
_TOPIC_TEMPLATES = [
    "best {kw} tips",
    "{kw} for beginners",
    "advanced {kw} techniques",
    "{kw} trends this year",
    "common {kw} mistakes",
    "{kw} gear and tools",
    "{kw} routines",
    "science of {kw}",
    "{kw} myths debunked",
    "how to start {kw}",
]

_AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
_HTTP_TIMEOUT = 6


def _score(topic: str, keyword: str) -> float:
    """Deterministic pseudo-score in [0, 100] derived from the text."""
    digest = hashlib.sha256(f"{keyword}:{topic}".encode("utf-8")).hexdigest()
    return round(int(digest[:8], 16) % 10000 / 100.0, 2)


def _local_provider(seed_keywords: Sequence[str]) -> List[Dict]:
    results: List[Dict] = []
    for keyword in seed_keywords:
        kw = str(keyword).strip()
        for template in _TOPIC_TEMPLATES:
            topic = template.format(kw=kw)
            results.append(
                {"topic": topic, "keyword": kw, "score": _score(topic, kw)}
            )
    # Stable, deterministic ordering: highest score first, then topic.
    results.sort(key=lambda r: (-r["score"], r["topic"]))
    return results


def _fetch_suggestions(keyword: str) -> List[str]:
    """Return Google Autocomplete suggestions for a keyword (may raise)."""
    query = urllib.parse.urlencode({"client": "firefox", "q": keyword})
    req = urllib.request.Request(
        f"{_AUTOCOMPLETE_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0 (affiliate-trends)"},
    )
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", "replace")
    # Response shape: ["<query>", ["suggestion 1", "suggestion 2", ...], ...]
    data = json.loads(raw)
    suggestions = data[1] if len(data) > 1 else []
    return [str(s) for s in suggestions if str(s).strip()]


def _remote_provider(seed_keywords: Sequence[str]) -> List[Dict]:
    """Real related-query provider; falls back to local on any failure."""
    results: List[Dict] = []
    any_remote = False
    for keyword in seed_keywords:
        kw = str(keyword).strip()
        try:
            suggestions = _fetch_suggestions(kw)
        except Exception:
            suggestions = []
        if not suggestions:
            # Per-keyword fallback so one bad lookup doesn't drop the keyword.
            for template in _TOPIC_TEMPLATES:
                topic = template.format(kw=kw)
                results.append(
                    {"topic": topic, "keyword": kw, "score": _score(topic, kw)}
                )
            continue
        any_remote = True
        n = len(suggestions)
        for rank, topic in enumerate(suggestions):
            # Earlier suggestions are more popular -> higher score.
            score = round(100.0 * (n - rank) / n, 2)
            results.append({"topic": topic, "keyword": kw, "score": score})

    if not any_remote:
        # Nothing came back from the network at all: use the local ordering.
        return _local_provider(seed_keywords)

    results.sort(key=lambda r: (-r["score"], r["topic"]))
    return results


# Swap this out to plug in a different data source.
_provider: Callable[[Sequence[str]], List[Dict]] = _local_provider

_PROVIDERS: Dict[str, Callable[[Sequence[str]], List[Dict]]] = {
    "local": _local_provider,
    "remote": _remote_provider,
}


def _select_provider() -> Callable[[Sequence[str]], List[Dict]]:
    """Pick a provider from the AFFILIATE_TRENDS env var (default: module default)."""
    name = os.environ.get("AFFILIATE_TRENDS", "").strip().lower()
    return _PROVIDERS.get(name, _provider)


def fetch_topics(
    seed_keywords: Sequence[str],
    limit: int = 10,
    provider: Optional[Callable[[Sequence[str]], List[Dict]]] = None,
) -> List[Dict]:
    """Return a list of trend topic dicts.

    Each dict contains the keys ``topic``, ``keyword`` and ``score``.

    Parameters
    ----------
    seed_keywords:
        Iterable of seed keyword strings.
    limit:
        Maximum number of topics to return.
    provider:
        Optional explicit provider callable (overrides env selection). Useful
        for testing and for plugging in custom data sources.
    """
    if seed_keywords is None:
        raise ValueError("seed_keywords must be provided")
    if isinstance(seed_keywords, str):
        seed_keywords = [seed_keywords]
    if limit < 0:
        raise ValueError("limit must be non-negative")

    chosen = provider or _select_provider()
    topics = chosen(seed_keywords)
    return topics[:limit]
