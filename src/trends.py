"""Trend topic fetching with a deterministic offline fallback.

The public function :func:`fetch_topics` is structured so a real data
source (e.g. an external trends API) can be swapped in by replacing the
``_provider`` callable, while defaulting to a zero-cost deterministic
local dataset.
"""
from __future__ import annotations

import hashlib
from typing import Callable, Dict, List, Sequence

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


# Swap this out to plug in a real data source.
_provider: Callable[[Sequence[str]], List[Dict]] = _local_provider


def fetch_topics(seed_keywords: Sequence[str], limit: int = 10) -> List[Dict]:
    """Return a list of trend topic dicts.

    Each dict contains the keys ``topic``, ``keyword`` and ``score``.

    Parameters
    ----------
    seed_keywords:
        Iterable of seed keyword strings.
    limit:
        Maximum number of topics to return.
    """
    if seed_keywords is None:
        raise ValueError("seed_keywords must be provided")
    if isinstance(seed_keywords, str):
        seed_keywords = [seed_keywords]
    if limit < 0:
        raise ValueError("limit must be non-negative")

    topics = _provider(seed_keywords)
    return topics[:limit]
