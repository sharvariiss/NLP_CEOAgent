"""
Master orchestration script — runs all 5 collectors, saves a per-source
JSONL file under data/raw/, then merges everything into
data/raw/all_documents.jsonl with cross-source deduplication.

4 of these 5 need zero setup. The 5th (Guardian) needs one free, instant
API key.
"""
from dotenv import load_dotenv
load_dotenv()  # pulls GUARDIAN_API_KEY from .env into os.environ, if present

from collectors import (
    company_airbus,
    news_leeham,
    news_guardian,
    research_openalex,
    stock_yfinance,
)
from collectors.base import save_jsonl

COLLECTORS = [
    ("Airbus.com (company)", company_airbus.collect,    "company_airbus.jsonl"),
    ("Leeham News",          news_leeham.collect,        "news_leeham.jsonl"),
    ("The Guardian",         news_guardian.collect,      "news_guardian.jsonl"),
    ("OpenAlex",             research_openalex.collect,  "research_openalex.jsonl"),
    ("yfinance",             stock_yfinance.collect,     "stock_yfinance.jsonl"),
]


def main():
    all_docs = []
    summary = []

    for label, fn, filename in COLLECTORS:
        print(f"\n=== Collecting: {label} ===")
        try:
            docs = fn()
        except Exception as e:
            print(f"  [error] collector crashed: {e}")
            docs = []
        save_jsonl(docs, filename)
        all_docs.extend(docs)
        summary.append((label, len(docs)))

    # Cross-source dedup
    seen = set()
    deduped = []
    for doc in all_docs:
        if doc["doc_id"] not in seen:
            seen.add(doc["doc_id"])
            deduped.append(doc)

    save_jsonl(deduped, "all_documents.jsonl")

    print("\n" + "=" * 55)
    print("COLLECTION SUMMARY")
    print("=" * 55)
    for label, count in summary:
        print(f"  {label:<25} {count:>6} documents")
    print("-" * 55)
    print(f"  {'TOTAL (raw)':<25} {len(all_docs):>6}")
    print(f"  {'TOTAL (deduped)':<25} {len(deduped):>6}")

    active_sources = sum(1 for _, c in summary if c > 0)
    print(f"\n  Active sources: {active_sources} / {len(COLLECTORS)}")
    print(f"  Spec minimum:   100 documents, 3+ independent sources")
    ok = len(deduped) >= 100 and active_sources >= 3
    print(f"  Status: {'PASS' if ok else 'BELOW MINIMUM — check GUARDIAN_API_KEY / connectivity'}")


if __name__ == "__main__":
    main()
