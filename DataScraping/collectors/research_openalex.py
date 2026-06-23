"""
Research Sources collector — OpenAlex API.
OpenAlex is a free, open catalog of scholarly works, authors, venues, and institutions.
"""
import requests
from .base import make_document

BASE_URL = "https://api.openalex.org/works"
HEADERS = {"User-Agent": "airbus-strategic-intel-agent (mailto:you@example.com)"}

QUERIES = [
    "airbus hydrogen propulsion",
    "airbus sustainable aviation fuel",
    "airbus A320 manufacturing",
    "commercial aircraft electrification",
]


def _reconstruct_abstract(inverted_index):
    """OpenAlex stores abstracts as an inverted index {word: [positions]} —
    this rebuilds the plain-text abstract from it."""
    if not inverted_index:
        return ""
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def collect(per_page=20, pages_per_query=1):
    docs = []
    seen_ids = set()

    for query in QUERIES:
        cursor = "*"
        for _ in range(pages_per_query):
            
            params = {"search": query, "per-page": per_page, "cursor": cursor}
            try:
                resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  [error] OpenAlex request failed for '{query}': {e}")
                break

            results = data.get("results", [])[:per_page] 
            for work in results:
                wid = work.get("id")
                if not wid or wid in seen_ids:
                    continue
                seen_ids.add(wid)
                abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
                docs.append(make_document(
                    source_name="OpenAlex",
                    source_category="research",
                    title=work.get("title", "") or "",
                    url=work.get("doi") or work.get("id"),
                    published_date=work.get("publication_date"),
                    content=abstract,
                    metadata={
                        "cited_by_count": work.get("cited_by_count"),
                        "query": query,
                    },
                ))

            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break

    return docs