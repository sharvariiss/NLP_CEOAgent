import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "RAG"))
sys.path.insert(0, str(PROJECT_ROOT / "StrategicIntelligenceEngine"))

from RAG.retriever import retrieve
from RAG.reranker import rerank
from RAG.prompt_builder import build_prompt
from StrategicIntelligenceEngine.strategic_analyzer import analyze_chunks
from CEOAgent.llm_agent import generate_response

AGENT_QUERY = (
    "Airbus strategic opportunities risks trends competitors "
    "hydrogen AI supply chain aviation aerospace defence innovation"
)


def ask_ceo_agent(top_k: int = 5) -> dict:
    
    chunks       = retrieve(AGENT_QUERY, top_k=top_k * 3)
    chunks       = rerank(query=AGENT_QUERY, chunks=chunks, top_k=top_k)
    intelligence = analyze_chunks(chunks)
    prompt       = build_prompt(
        retrieved_chunks=chunks,
        intelligence=intelligence,
    )
    report = generate_response(prompt)

    return {
        "rag_result": {
            "chunks":       chunks,
            "intelligence": intelligence,
            "prompt":       prompt,
        },
        "report": report,
    }


if __name__ == "__main__":
    print("\nRunning Airbus CEO Agent...\n")
    result = ask_ceo_agent(top_k=5)
    print("=" * 80)
    print(result["report"])
    print("=" * 80)