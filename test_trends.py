import pytest

from src.trends import fetch_topics


def test_schema():
    topics = fetch_topics(["running shoes"], limit=3)
    assert len(topics) == 3
    for t in topics:
        assert set(t.keys()) == {"topic", "keyword", "score"}
        assert t["keyword"] == "running shoes"
        assert isinstance(t["topic"], str) and t["topic"]
        assert 0 <= t["score"] <= 100


def test_limit_respected():
    assert len(fetch_topics(["a", "b", "c"], limit=4)) == 4
    assert fetch_topics(["a"], limit=0) == []


def test_deterministic():
    assert fetch_topics(["coffee maker"], limit=5) == fetch_topics(
        ["coffee maker"], limit=5
    )


def test_sorted_by_score_desc():
    topics = fetch_topics(["camping gear"], limit=10)
    scores = [t["score"] for t in topics]
    assert scores == sorted(scores, reverse=True)


def test_string_input_is_wrapped():
    topics = fetch_topics("yoga", limit=2)
    assert all(t["keyword"] == "yoga" for t in topics)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        fetch_topics(None)
    with pytest.raises(ValueError):
        fetch_topics(["x"], limit=-1)
