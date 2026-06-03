import os

import run

CONFIG = {
    "site_title": "Home Barista Gear",
    "author": "Home Barista Gear",
    "base_url": "https://example.com/coffee",
    "description": "Espresso gear reviews for home baristas.",
    "google_site_verification": "verifytoken123",
    "keywords": ["espresso grinder"],
    "affiliates": {
        "espresso grinder": "https://www.amazon.com/s?k=espresso+grinder&tag=danny33452-20"
    },
}


def _article_pages(out):
    return [p for p in os.listdir(out) if p.endswith(".html") and p != "index.html"]


def test_build_emits_seo_files(tmp_path):
    out = tmp_path / "public"
    n = run.build_site(CONFIG, 3, str(out))
    assert n == 3
    for name in ("index.html", "sitemap.xml", "robots.txt"):
        assert (out / name).exists(), name


def test_robots_points_to_sitemap(tmp_path):
    out = tmp_path / "public"
    run.build_site(CONFIG, 1, str(out))
    robots = (out / "robots.txt").read_text()
    assert "Sitemap: https://example.com/coffee/sitemap.xml" in robots


def test_sitemap_lists_home_and_articles(tmp_path):
    out = tmp_path / "public"
    run.build_site(CONFIG, 2, str(out))
    sm = (out / "sitemap.xml").read_text()
    assert "<loc>https://example.com/coffee/</loc>" in sm
    assert sm.count("<url>") >= 3  # home + 2 articles


def test_article_has_seo_tags_and_affiliate(tmp_path):
    out = tmp_path / "public"
    run.build_site(CONFIG, 1, str(out))
    page = (out / _article_pages(out)[0]).read_text()
    assert '<meta name="description"' in page
    assert 'property="og:title"' in page
    assert 'rel="canonical" href="https://example.com/coffee/' in page
    assert 'application/ld+json' in page
    assert '"@type": "Article"' in page
    assert 'google-site-verification' in page
    assert "tag=danny33452-20" in page  # affiliate link survives into HTML


def test_meta_description_skips_headings_and_truncates():
    md = "# Title\n\n" + ("espresso " * 60).strip() + "\n"
    desc = run.meta_description(md, "fallback")
    assert not desc.startswith("#")
    assert len(desc) <= 155
    assert desc.endswith("…")


def test_meta_description_fallback_when_empty():
    assert run.meta_description("# Only a heading\n", "the fallback") == "the fallback"
