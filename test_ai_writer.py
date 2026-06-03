from src import ai_writer
from src.content import generate_article


class _FakeBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResp:
    def __init__(self, text):
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    def __init__(self, text):
        self._text = text
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResp(self._text)


class _FakeClient:
    def __init__(self, text="# Topic\n\nBody."):
        self.messages = _FakeMessages(text)


def test_no_key_returns_none(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai_writer.draft_markdown("best shoes", "shoes") is None


def test_with_client_returns_markdown():
    client = _FakeClient("# Best Shoes\n\nGreat, specific content here.")
    md = ai_writer.draft_markdown("Best Shoes", "shoes", client=client)
    assert md.startswith("# Best Shoes")
    # The static system prompt is sent as a cached block.
    assert client.messages.kwargs["system"][0]["cache_control"]["type"] == "ephemeral"
    assert client.messages.kwargs["model"]


def test_adds_h1_when_missing():
    client = _FakeClient("Some body text without any heading.")
    md = ai_writer.draft_markdown("My Topic", "topic", client=client)
    assert md.startswith("# My Topic")


def test_empty_response_falls_back_to_none():
    client = _FakeClient("   ")
    assert ai_writer.draft_markdown("Topic", "kw", client=client) is None


def test_api_error_returns_none():
    class _BoomMessages:
        def create(self, **kwargs):
            raise RuntimeError("network down")

    class _BoomClient:
        messages = _BoomMessages()

    assert ai_writer.draft_markdown("Topic", "kw", client=_BoomClient()) is None


def test_generate_article_uses_client():
    client = _FakeClient("# Custom Title\n\n" + "word " * 400)
    a = generate_article({"topic": "Custom Title", "keyword": "custom"}, client=client)
    assert a["title"] == "Custom Title"
    assert a["word_count"] >= 300
    assert a["markdown"].startswith("# Custom Title")
