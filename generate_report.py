"""
generate_report.py  —  place at project root
Runs the autonomous CEO Agent and saves to reports/latest_report.json

Run before the demo:
    python generate_report.py
"""

import sys
import json
import datetime
from pathlib import Path

PROJECT_ROOT    = Path(__file__).resolve().parent
REPORTS_DIR     = PROJECT_ROOT / "reports"
REPORT_PATH     = REPORTS_DIR / "latest_report.json"
PROGRESS_PATH   = REPORTS_DIR / "progress.json"
CLEAN_DOCS_PATH = PROJECT_ROOT / "DataCleaning" / "data" / "processed" / "clean_documents.jsonl"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "RAG"))
sys.path.insert(0, str(PROJECT_ROOT / "StrategicIntelligenceEngine"))

REPORTS_DIR.mkdir(exist_ok=True)


def save_progress(step: str):
    with open(PROGRESS_PATH, "w") as f:
        json.dump({"step": step, "ts": datetime.datetime.now().isoformat()}, f)


def load_clean_docs() -> list:
    docs = []
    if not CLEAN_DOCS_PATH.exists():
        return docs
    with open(CLEAN_DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return docs


def compute_corpus_stats(docs: list) -> dict:
    from collections import Counter
    topic_counts    = Counter(d.get("topic", "general")           for d in docs)
    src_cat_counts  = Counter(d.get("source_category", "unknown") for d in docs)
    src_name_counts = Counter(d.get("source_name", "unknown")     for d in docs)
    parent_ids      = {d.get("parent_id") for d in docs if d.get("parent_id")}
    return {
        "total_chunks":        len(docs),
        "total_documents":     len(parent_ids),
        "total_sources":       len(src_name_counts),
        "topic_distribution":  dict(topic_counts),
        "source_category_mix": dict(src_cat_counts),
        "source_name_mix":     dict(src_name_counts),
        "last_collected_at":   max((d.get("collected_at", "") for d in docs), default=""),
    }


def main():
    print("\n" + "=" * 60)
    print("  Airbus CEO Agent — Report Generator")
    print("=" * 60)

    save_progress("Loading corpus…")
    print("\n[1/3] Loading corpus stats…")
    docs         = load_clean_docs()
    corpus_stats = compute_corpus_stats(docs)
    print(f"      {corpus_stats['total_chunks']} chunks · "
          f"{corpus_stats['total_documents']} docs · "
          f"{corpus_stats['total_sources']} sources")

    save_progress("Running CEO Agent…")
    print("\n[2/3] Running autonomous CEO Agent…")

    try:
        from CEOAgent.ceo_agent import ask_ceo_agent
        result = ask_ceo_agent(top_k=5)

        intel = result["rag_result"]["intelligence"]
        print(f"      ✓ {len(intel['opportunities'])} opportunities · "
              f"{len(intel['risks'])} risks · "
              f"{len(intel['trends'])} trends")
        print(f"      ✓ Report generated · Validated: {result['validated']}")

        rag_result = {
            "chunks_used":  len(result["rag_result"]["chunks"]),
            "intelligence": intel,
            "report":       result["report"],
            "llm_success":  True,
            "llm_error":    "",
            "agent_log":    result.get("agent_log", []),
            "decisions":    result.get("decisions", []),
            "goal":         result.get("goal", ""),
            "plan":         result.get("plan", []),
            "validated":    result.get("validated", False),
            "chunks": [
                {"content": c["content"], "metadata": c["metadata"], "distance": float(c["distance"])}
                for c in result["rag_result"]["chunks"]
            ],
        }

    except Exception as exc:
        print(f"      ✗ Agent failed: {exc}")
        rag_result = {
            "chunks_used":  0,
            "intelligence": {"opportunities": [], "risks": [], "trends": []},
            "report":       "",
            "llm_success":  False,
            "llm_error":    str(exc),
            "agent_log":    [],
            "decisions":    [],
            "goal":         "",
            "plan":         [],
            "validated":    False,
            "chunks":       [],
        }

    save_progress("Saving report…")
    print("\n[3/3] Saving report…")

    report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "corpus_stats": corpus_stats,
        "rag":          rag_result,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    save_progress("done")
    print(f"      ✓ Saved → {REPORT_PATH}")
    print("\n  Run:  streamlit run Dashboard/app.py\n")


if __name__ == "__main__":
    main()