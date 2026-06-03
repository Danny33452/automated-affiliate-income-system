import io
import json

from src import trends
from src.trends import fetch_topics


class _FakeHTTP:
    """Minimal context-manager response object for urlopen monkeypatching."""

    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._payload


def _fake_urlopen_factory(suggestions):
    def _fake(req, timeout=None):
        body = json.dumps(["seed", suggestions]).encode("utf-8")
        return _FakeHTTP(body)

    return _fake


def test_remote_parses_suggestions(monkeypatch):
    suggestions = ["running shoes for flat feet", "running shoes sale", "running shoes men"]
    monkeypatch.setattr(trends.urllib.request, "urlopen", _fake_urlopen_factory(suggestions))
    topics = fetch_topics(["running shoes"], limit=10, provider=trends._remote_provider)
    returned = [t["topic"] for t in topics]
    assert returned == suggestions  # rank order preserved (highest score first)
    assert all(t["keyword"] == "running shoes" for t in topics)
    assert topics[0]["score"] >= topics[-1]["score"]


def test_remote_falls_back_on_error(monkeypatch):
    def _boom(req, timeout=None):
        raise OSError("no network")

    monkeypatch.setattr(trends.urllib.request, "urlopen", _boom)
    topics = fetch_topics(["coffee maker"], limit=5, provider=trends._remote_provider)
    # Falls back to the deterministic local templates.
    assert len(topics) == 5
    assert topics == fetch_topics(["coffee maker"], limit=5, provider=trends._local_provider)


def test_remote_empty_suggestions_uses_templates(monkeypatch):
    monkeypatch.setattr(trends.urllib.request, "urlopen", _fake_urlopen_factory([]))
    topics = fetch_topics(["yoga"], limit=10, provider=trends._remote_provider)
    assert len(topics) == 10
    assert all(t["keyword"] == "yoga" for t in topics)


def test_env_selects_remote(monkeypatch):
    suggestions = ["best yoga mat", "yoga mat thick"]
    monkeypatch.setattr(trends.urllib.request, "urlopen", _fake_urlopen_factory(suggestions))
    monkeypatch.setenv("AFFILIATE_TRENDS", "remote")
    topics = fetch_topics(["yoga mat"], limit=10)
    assert [t["topic"] for t in topics] == suggestions


def test_env_defaults_to_local(monkeypatch):
    monkeypatch.delenv("AFFILIATE_TRENDS", raising=False)
    topics = fetch_topics(["yoga mat"], limit=10)
    # Local templates, not live suggestions.
    assert any("for beginners" in t["topic"] for t in topics)
