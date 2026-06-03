"""Validate the Markdown articles in the content store.

Quality gate for the review-gate flow: the content-review workflow runs this on
freshly generated content *before* opening a PR (so broken output never becomes
a PR), and the test suite runs it against the committed ``content/`` baseline.

Each article must have frontmatter (title/slug/keyword), a slug that matches its
filename and is URL-safe, an H1, a minimum length, and the FTC affiliate
disclosure.
"""
import os
import re
import sys

from src.store import parse

_MIN_WORDS = 100
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_article(article, filename=None):
    """Return a list of human-readable problems with one article (empty = ok)."""
    errors = []
    title = (article.get("title") or "").strip()
    slug = (article.get("slug") or "").strip()
    keyword = (article.get("keyword") or "").strip()
    body = article.get("markdown") or ""
    name = filename or (f"{slug}.md" if slug else "<unknown>.md")

    if not title:
        errors.append(f"{name}: missing frontmatter 'title'")
    if not slug:
        errors.append(f"{name}: missing frontmatter 'slug'")
    elif not _SLUG_RE.match(slug):
        errors.append(f"{name}: slug '{slug}' is not URL-safe")
    if not keyword:
        errors.append(f"{name}: missing frontmatter 'keyword'")
    if filename and slug and filename != f"{slug}.md":
        errors.append(f"{name}: filename does not match slug '{slug}'")

    if not re.search(r"^#\s", body, re.MULTILINE):
        errors.append(f"{name}: missing an H1 heading")
    if "affiliate links" not in body.lower():
        errors.append(f"{name}: missing affiliate disclosure")
    words = len(re.findall(r"\b\w+\b", body))
    if words < _MIN_WORDS:
        errors.append(f"{name}: body too short ({words} words, need >= {_MIN_WORDS})")
    return errors


def validate_content_dir(content_dir):
    """Return a list of problems across all ``*.md`` files in ``content_dir``."""
    if not os.path.isdir(content_dir):
        return [f"content dir not found: {content_dir}"]
    names = sorted(n for n in os.listdir(content_dir) if n.endswith(".md"))
    if not names:
        return [f"no Markdown articles found in {content_dir}"]
    errors = []
    for name in names:
        with open(os.path.join(content_dir, name)) as f:
            errors.extend(validate_article(parse(f.read()), filename=name))
    return errors


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    content_dir = argv[0] if argv else "content"
    errors = validate_content_dir(content_dir)
    if errors:
        print(f"Content validation FAILED ({len(errors)} issue(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    count = len([n for n in os.listdir(content_dir) if n.endswith(".md")])
    print(f"Content validation passed: {count} article(s) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
