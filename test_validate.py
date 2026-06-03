import os

from src.validate import validate_article, validate_content_dir

ROOT = os.path.dirname(os.path.abspath(__file__))

GOOD = {
    "title": "espresso machine",
    "slug": "espresso-machine",
    "keyword": "espresso machine",
    "markdown": "# espresso machine\n\n" + ("word " * 120).strip()
    + "\n\n_Disclosure: This article contains affiliate links._",
}


def test_good_article_passes():
    assert validate_article(GOOD, filename="espresso-machine.md") == []


def test_missing_disclosure():
    art = dict(GOOD, markdown="# t\n\n" + ("word " * 120))
    errs = validate_article(art, filename="espresso-machine.md")
    assert any("disclosure" in e.lower() for e in errs)


def test_too_short():
    art = dict(GOOD, markdown="# t\n\nshort _affiliate links_")
    errs = validate_article(art, filename="espresso-machine.md")
    assert any("too short" in e for e in errs)


def test_missing_h1():
    art = dict(GOOD, markdown="no heading here " + ("word " * 120) + " affiliate links")
    errs = validate_article(art, filename="espresso-machine.md")
    assert any("H1" in e for e in errs)


def test_filename_slug_mismatch():
    errs = validate_article(GOOD, filename="other.md")
    assert any("does not match slug" in e for e in errs)


def test_bad_slug_and_missing_frontmatter():
    art = {"title": "", "slug": "Not_A_Slug", "keyword": "", "markdown": GOOD["markdown"]}
    errs = validate_article(art, filename="Not_A_Slug.md")
    assert any("title" in e for e in errs)
    assert any("keyword" in e for e in errs)
    assert any("URL-safe" in e for e in errs)


def test_dir_missing_and_empty(tmp_path):
    assert validate_content_dir(str(tmp_path / "nope"))
    (tmp_path / "content").mkdir()
    assert validate_content_dir(str(tmp_path / "content"))  # empty -> error


def test_repo_content_baseline_is_valid():
    # The committed content/ must always pass (this runs in CI).
    errors = validate_content_dir(os.path.join(ROOT, "content"))
    assert errors == [], errors
