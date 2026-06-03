import run
from src import store

CONFIG = {
    "site_title": "Home Barista Gear",
    "base_url": "https://example.com",
    "roundups": [
        {
            "title": "Best Espresso Machines",
            "keyword": "espresso machine",
            "products": [
                {"name": "Breville Bambino Plus",
                 "url": "https://www.amazon.com/s?k=bambino&tag=danny33452-20",
                 "best_for": "Small kitchens", "price": "$$"}
            ],
        }
    ],
    "keywords": ["espresso machine", "espresso grinder"],
    "affiliates": {
        "espresso machine": "https://www.amazon.com/s?k=espresso+machine&tag=danny33452-20"
    },
}


def test_serialize_parse_round_trip():
    art = {"title": "T: A Guide", "slug": "t-guide", "keyword": "kw",
           "markdown": "# T\n\nBody with a colon: here.\n"}
    parsed = store.parse(store.serialize(art))
    assert parsed["title"] == "T: A Guide"
    assert parsed["slug"] == "t-guide"
    assert parsed["keyword"] == "kw"
    assert parsed["markdown"].strip() == art["markdown"].strip()


def test_write_then_read(tmp_path):
    articles = run.generate_articles(CONFIG, 3)
    cdir = tmp_path / "content"
    store.write_articles(articles, str(cdir))
    assert len(list(cdir.glob("*.md"))) == len(articles)

    loaded = store.read_articles(str(cdir))
    assert len(loaded) == len(articles)
    by_slug = {a["slug"]: a for a in articles}
    for la in loaded:
        orig = by_slug[la["slug"]]
        assert la["title"] == orig["title"]
        assert la["keyword"] == orig["keyword"]
        assert la["markdown"].strip() == orig["markdown"].strip()


def test_write_replaces_previous(tmp_path):
    cdir = tmp_path / "content"
    store.write_articles([{"slug": "old", "title": "Old", "markdown": "x"}], str(cdir))
    store.write_articles([{"slug": "new", "title": "New", "markdown": "y"}], str(cdir))
    names = {p.name for p in cdir.glob("*.md")}
    assert names == {"new.md"}


def test_read_missing_dir(tmp_path):
    assert store.read_articles(str(tmp_path / "nope")) == []


def test_from_content_render_matches(tmp_path):
    articles = run.generate_articles(CONFIG, 2)
    cdir = tmp_path / "content"
    store.write_articles(articles, str(cdir))
    out = tmp_path / "public"
    n = run.render_site(store.read_articles(str(cdir)), CONFIG, str(out))
    assert n == len(articles)
    assert (out / "index.html").exists()
    assert (out / "sitemap.xml").exists()
    # Affiliate tag survives the store round-trip into the published HTML.
    joined = "".join(p.read_text() for p in out.glob("*.html"))
    assert "tag=danny33452-20" in joined
