import os

import run
from src.roundup import generate_roundup

SPEC = {
    "title": "Best Espresso Machines for Home Baristas",
    "keyword": "espresso machine",
    "products": [
        {
            "name": "Breville Bambino Plus",
            "url": "https://www.amazon.com/s?k=Breville+Bambino+Plus&tag=danny33452-20",
            "best_for": "Best for small kitchens",
            "price": "$$",
            "pros": ["Fast heat-up", "Auto milk"],
            "cons": ["Small tank"],
        },
        {
            "name": "Gaggia Classic Pro",
            "url": "https://www.amazon.com/s?k=Gaggia+Classic+Pro&tag=danny33452-20",
            "best_for": "Best for tinkerers",
            "price": "$$",
            "pros": ["58mm portafilter"],
            "cons": ["No PID stock"],
        },
    ],
}


def test_schema():
    a = generate_roundup(SPEC)
    assert set(a.keys()) == {"title", "slug", "markdown", "word_count"}
    assert a["title"] == SPEC["title"]
    assert a["slug"].replace("-", "").isalnum()
    assert a["word_count"] > 100


def test_contains_table_products_and_disclosure():
    md = generate_roundup(SPEC)["markdown"]
    assert "<table>" in md and "</table>" in md
    for p in SPEC["products"]:
        assert p["name"] in md
        assert p["url"] in md
    assert "rel=\"nofollow sponsored\"" in md  # comparison-table CTA
    assert "Check price on Amazon" in md       # per-product CTA
    assert "affiliate links" in md.lower()     # FTC disclosure


def test_empty_products_still_valid():
    a = generate_roundup({"title": "Best Grinders", "keyword": "grinder", "products": []})
    assert a["word_count"] > 0
    assert "How to Choose" in a["markdown"]


def test_build_site_renders_roundup_table(tmp_path):
    config = {
        "site_title": "Home Barista Gear",
        "base_url": "https://example.com",
        "roundups": [SPEC],
        "affiliates": {},
        "keywords": ["espresso machine"],
    }
    out = tmp_path / "public"
    # count=0 -> only the roundup money page is produced
    run.build_site(config, 0, str(out))
    pages = [p for p in os.listdir(out) if p.endswith(".html") and p != "index.html"]
    assert pages, "expected a roundup page"
    page = (out / pages[0]).read_text()
    assert "<table>" in page  # raw HTML table survived rendering
    assert "tag=danny33452-20" in page
    assert 'rel="nofollow sponsored"' in page
