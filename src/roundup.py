"""'Best X' comparison / roundup articles with affiliate product tables.

A roundup is the highest-converting affiliate format: a short intro, an
at-a-glance comparison table, then a section per product with pros/cons and a
call-to-action link. Specs come from the config (see ``roundups`` in
``config.example.json``); product copy is editorial and meant to be reviewed.

The comparison table is emitted as raw HTML (each row on its own line) so it
renders correctly with both the ``markdown`` package and the built-in fallback
renderer in ``run.py``.
"""
import html
import re

from src.content import slugify
from src.monetize import DISCLOSURE


def _cta(product):
    url = product.get("url", "#")
    return f"[Check price on Amazon]({url})"


def _comparison_table(products):
    rows = [
        "<table>",
        "<thead>",
        "<tr><th>Product</th><th>Best for</th><th>Price</th><th>Where to buy</th></tr>",
        "</thead>",
        "<tbody>",
    ]
    for p in products:
        name = html.escape(str(p.get("name", "Product")))
        best_for = html.escape(str(p.get("best_for", "")))
        price = html.escape(str(p.get("price", "")))
        url = html.escape(str(p.get("url", "#")), quote=True)
        rating = p.get("rating")
        if rating:
            name = f"{name} <small>({html.escape(str(rating))}/5)</small>"
        rows.append(
            f'<tr><td>{name}</td><td>{best_for}</td><td>{price}</td>'
            f'<td><a href="{url}" rel="nofollow sponsored">View &rarr;</a></td></tr>'
        )
    rows += ["</tbody>", "</table>"]
    return "\n".join(rows)


def _product_section(product):
    name = product.get("name", "Product")
    parts = [f"### {name}"]
    best_for = product.get("best_for")
    if best_for:
        parts.append(f"*{best_for}.*")
    summary = product.get("summary")
    if summary:
        parts.append(summary)
    pros = product.get("pros", [])
    cons = product.get("cons", [])
    if pros:
        parts.append("**Pros**")
        parts.extend(f"- {p}" for p in pros)
    if cons:
        parts.append("**Cons**")
        parts.extend(f"- {c}" for c in cons)
    parts.append(_cta(product))
    return "\n\n".join(parts)


def generate_roundup(spec):
    """Build a roundup article dict from a spec.

    Returns ``{"title", "slug", "markdown", "word_count"}`` (same schema as
    :func:`src.content.generate_article`).
    """
    title = str(spec.get("title", "Best Picks")).strip() or "Best Picks"
    keyword = str(spec.get("keyword", title)).strip() or title
    products = spec.get("products", [])
    intro = spec.get("intro") or (
        f"Looking for the best {keyword}? We compared the top options for home "
        f"baristas and rounded up our favorites below. Here is how they stack "
        f"up, who each one is best for, and the trade-offs to weigh before you "
        f"buy."
    )

    parts = [f"# {title}", intro]
    if products:
        parts.append("## At a Glance")
        parts.append(_comparison_table(products))
        parts.append("## Our Picks")
        for product in products:
            parts.append(_product_section(product))

    parts.append("## How to Choose")
    parts.append(
        f"When comparing {keyword}, weigh build quality, ease of use, and how "
        f"much you want to tinker versus get consistent results out of the box. "
        f"Consider your budget, available counter space, and whether you need a "
        f"built-in grinder. The right {keyword} is the one that matches your "
        f"routine and the drinks you make most often."
    )
    parts.append("## Final Verdict")
    parts.append(
        f"Any of these {keyword} options is a solid choice; the best pick comes "
        f"down to your budget and priorities. Use the comparison table above to "
        f"match a model to your needs, then check current pricing before you buy."
    )
    parts.append(DISCLOSURE)

    markdown = "\n\n".join(parts) + "\n"
    word_count = len(re.findall(r"\b\w+\b", markdown))
    return {
        "title": title,
        "slug": slugify(title),
        "markdown": markdown,
        "word_count": word_count,
    }
