"""
News Sources collector — Leeham News and Analysis (leehamnews.com).
Uses the site's public RSS feed, then fetches each article page for fuller
text.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from .base import make_document

FEED_URL = "https://leehamnews.com/feed/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def _fetch_article_text(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        article = soup.find("article") or soup
        paragraphs = [p.get_text(" ", strip=True) for p in article.find_all("p")]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"  [warn] could not fetch full text for {url}: {e}")
        return ""


def collect(max_items=100, fetch_full_text=True):
    feed = feedparser.parse(FEED_URL)
    if feed.bozo:
        print(f"  [warn] feed parse issue: {feed.bozo_exception}")

    docs = []
    for entry in feed.entries[:max_items]:
        content = entry.get("summary", "")
        if fetch_full_text and entry.get("link"):
            full = _fetch_article_text(entry.link)
            if len(full) > len(content):
                content = full

        docs.append(make_document(
            source_name="Leeham News and Analysis",
            source_category="news",
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            published_date=entry.get("published", None),
            content=content,
            metadata={"author": entry.get("author", None)},
        ))
    return docs
