import os

import run
from src.linking import related_links

RECORDS = [
    {"title": "Best Espresso Machines for Home Baristas", "slug": "best-espresso-machines", "keyword": "espresso machine"},
    {"title": "Espresso Machine for Beginners", "slug": "espresso-machine-beginners", "keyword": "espresso machine"},
    {"title": "Espresso Grinder Routines", "slug": "espresso-grinder-routines", "keyword": "espresso grinder"},
    {"title": "Milk Frothing Pitcher Tips", "slug": "milk-frothing-pitcher", "keyword": "milk frothing pitcher"},
]


def test_same_keyword_ranks_first():
    rel = related_links(RECORDS, 0, max_links=3)
    slugs = [s for _, s in rel]
    # Shared "espresso machine" keyword beats the others.
    assert slugs[0] == "espresso-machine-beginners"


def test_excludes_self():
    rel = related_links(RECORDS, 0)
    assert all(slug != "best-espresso-machines" for _, slug in rel)


def test_respects_max_links():
    assert len(related_links(RECORDS, 0, max_links=2)) == 2


def test_returns_title_and_slug_pairs():
    rel = related_links(RECORDS, 2)
    for item in rel:
        assert len(item) == 2
        title, slug = item
        assert isinstance(title, str) and isinstance(slug, str)


def test_unrelated_returns_empty():
    records = [
        {"title": "Espresso Machine Guide", "slug": "a", "keyword": "espresso machine"},
        {"title": "Camping Tent Reviews", "slug": "b", "keyword": "tent"},
    ]
    assert related_links(records, 0) == []


def test_build_site_adds_related_links(tmp_path):
    config = {
        "site_title": "Home Barista Gear",
        "base_url": "https://example.com",
        "keywords": ["espresso machine"],
        "affiliates": {"espresso machine": "https://www.amazon.com/s?k=espresso+machine&tag=danny33452-20"},
    }
    out = tmp_path / "public"
    # Several articles share the "espresso machine" keyword -> they cross-link.
    run.build_site(config, 5, str(out))
    pages = [p for p in os.listdir(out) if p.endswith(".html") and p != "index.html"]
    joined = "".join((out / p).read_text() for p in pages)
    assert "Related articles" in joined
    # At least one page links to another article page.
    linked = any(
        f'href="{other[:-5]}.html"' in (out / p).read_text()
        for p in pages for other in pages if other != p
    )
    assert linked
