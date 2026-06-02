"""Template-based SEO article generator (no paid API)."""
import re


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def generate_article(topic_dict):
    topic = str(topic_dict.get("topic", "Untitled")).strip() or "Untitled"
    keyword = str(topic_dict.get("keyword", topic)).strip() or topic
    title = topic

    sections = [
        ("Introduction",
         f"Welcome to this comprehensive guide on {topic}. In this article we "
         f"explore everything you need to know about {keyword}, why it matters, "
         f"and how to make the most informed decision. Whether you are a "
         f"beginner or an experienced enthusiast, understanding {keyword} can "
         f"save you time, money, and frustration. We have carefully researched "
         f"this subject so you get practical, actionable insight."),
        (f"What You Need to Know About {keyword.title()}",
         f"When it comes to {keyword}, several factors deserve your attention. "
         f"Quality, value, and suitability for your specific needs all play a "
         f"central role. Many people overlook the importance of {keyword} until "
         f"they experience the difference firsthand. By focusing on the "
         f"essentials of {topic}, you build a strong foundation for smarter "
         f"choices and long-term satisfaction."),
        (f"Key Benefits of {topic}",
         f"There are many benefits associated with {topic}. First, it improves "
         f"your overall experience and confidence. Second, choosing the right "
         f"{keyword} enhances performance and reduces common problems. Third, a "
         f"thoughtful approach to {keyword} delivers lasting value. These "
         f"benefits compound over time, making your initial research well worth "
         f"the effort and attention you invest today."),
        (f"How to Choose the Best {keyword.title()}",
         f"Selecting the best option requires balancing your budget, goals, and "
         f"preferences. Start by listing what matters most to you about "
         f"{keyword}. Compare available choices, read trusted reviews, and "
         f"prioritize features that align with your needs. Avoid rushing the "
         f"decision; a measured evaluation of {topic} ensures you end up with a "
         f"result that truly fits your lifestyle and expectations."),
        ("Conclusion",
         f"In summary, {topic} is an important subject worth understanding in "
         f"detail. By keeping the principles of {keyword} in mind, you can make "
         f"confident, informed decisions. We hope this guide has given you the "
         f"clarity and direction you were looking for. Take what you have "
         f"learned about {keyword} and put it into practice for the best "
         f"possible outcome."),
    ]

    md_parts = [f"# {title}\n"]
    for heading, body in sections:
        md_parts.append(f"## {heading}\n\n{body}\n")
    markdown = "\n".join(md_parts)

    word_count = len(re.findall(r"\b\w+\b", markdown))

    return {
        "title": title,
        "slug": slugify(title),
        "markdown": markdown,
        "word_count": word_count,
    }
