from src.content import generate_article


def test_schema():
    a = generate_article({"topic": "Best Running Shoes", "keyword": "running shoes", "score": 9})
    assert set(a.keys()) == {"title", "slug", "markdown", "word_count"}
    assert isinstance(a["title"], str)
    assert isinstance(a["markdown"], str)
    assert isinstance(a["word_count"], int)


def test_word_count():
    a = generate_article({"topic": "Best Running Shoes", "keyword": "running shoes"})
    assert a["markdown"].strip()
    assert a["word_count"] >= 300
    assert "#" in a["markdown"]


def test_slug_url_safe():
    a = generate_article({"topic": "Best Running Shoes!! 2024", "keyword": "shoes"})
    assert a["slug"].replace("-", "").isalnum()
    assert " " not in a["slug"]


def test_defaults():
    a = generate_article({})
    assert a["word_count"] >= 300
