"""
News Sources collector — The Guardian Open Platform (Content API).

Free key: https://open-platform.theguardian.com/access/

Deliberately using query q="Airbus" rather than pulling the whole Business
section feed, so every document returned is actually about the company.
"""
import os
import requests
from .base import make_document

API_URL = "https://content.guardianapis.com/search"


def collect(query="Airbus", pages=2, page_size=30):
    api_key = os.environ.get("GUARDIAN_API_KEY")
    if not api_key:
        print("  [error] GUARDIAN_API_KEY not set — skipping Guardian collection. "
              "Get a free key at https://open-platform.theguardian.com/access/")
        return []

    docs = []
    for page in range(1, pages + 1):
        params = {
            "q": query,
            "api-key": api_key,
            "page": page,
            "page-size": page_size,
            "show-fields": "headline,bodyText,byline",
            "order-by": "newest",
        }
        try:
            resp = requests.get(API_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [error] Guardian API request failed on page {page}: {e}")
            break

        results = data.get("response", {}).get("results", [])
        if not results:
            break

        for item in results:
            fields = item.get("fields", {})
            docs.append(make_document(
                source_name="The Guardian",
                source_category="news",
                title=fields.get("headline", item.get("webTitle", "")),
                url=item.get("webUrl", ""),
                published_date=item.get("webPublicationDate", None),
                content=fields.get("bodyText", ""),
                metadata={"section": item.get("sectionName"), "byline": fields.get("byline")},
            ))

        total_pages = data.get("response", {}).get("pages", 1)
        if page >= total_pages:
            break

    return docs
