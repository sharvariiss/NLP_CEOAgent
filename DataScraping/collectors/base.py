"""
Shared utilities used by every collector: a common document schema,
stable IDs (for dedup), text cleaning, and JSONL persistence.

Every collector returns a list of dicts shaped exactly like
`make_document()` below, so run_collection.py can merge them all
into one unified knowledge repository without per-source special-casing.
"""
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(*parts: str) -> str:
    """Stable hash id from one or more strings (e.g. url + source name).
    Used both as the document's primary key and for cross-source dedup."""
    joined = "||".join(p.strip().lower() for p in parts if p)
    return hashlib.md5(joined.encode("utf-8")).hexdigest()


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_document(source_name, source_category, title, url, published_date,
                   content, metadata=None):
    """
    source_category should be one of:
      'company' | 'news' | 'market_risk' | 'community' | 'research' | 'stock'
    (matches the categories in the project spec's Functional Requirements)
    """
    return {
        "doc_id": make_id(url or title, source_name),
        "source_name": source_name,
        "source_category": source_category,
        "title": clean_text(title),
        "url": url,
        "published_date": published_date,
        "content": clean_text(content),
        "collected_at": now_iso(),
        "metadata": metadata or {},
    }


def save_jsonl(records, filename):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  saved {len(records)} records -> {path}")
    return path


def polite_sleep(seconds=1.0):
    time.sleep(seconds)
