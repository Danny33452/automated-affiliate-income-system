import json
import os

from src.monetize import inject_affiliate, load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_link_injected():
    out = inject_affiliate(
        "Buy running shoes today.",
        {"running shoes": "https://aff.example/x?id=ME"},
    )
    assert "[running shoes](https://aff.example/x?id=ME)" in out


def test_disclosure_present():
    out = inject_affiliate("Some text.", {"text": "https://aff.example/z"})
    assert "disclos" in out.lower()


def test_no_keyword_still_has_disclosure():
    out = inject_affiliate("Nothing here.", {"missing": "https://aff.example/q"})
    assert "disclos" in out.lower()
    assert "https://aff.example/q" not in out


def test_load_config_example():
    cfg = load_config(os.path.join(ROOT, "config.example.json"))
    assert isinstance(cfg, dict)
    assert all(v.startswith("http") for v in cfg.values())


def test_keyword_only_linked_once():
    out = inject_affiliate(
        "shoes and shoes", {"shoes": "https://aff.example/s"}
    )
    assert out.count("https://aff.example/s") == 1
