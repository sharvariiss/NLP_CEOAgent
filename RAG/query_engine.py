import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "StrategicIntelligenceEngine"))

from RAG.retriever import retrieve
from RAG.reranker import rerank
from RAG.prompt_builder import build_prompt
from StrategicIntelligenceEngine.strategic_analyzer import analyze_chunks


def build_rag_query(question: str, top_k: int = 5) -> dict:
    chunks = retrieve(
        question,
        top_k=top_k * 3
    )

    chunks = rerank(
        query=question,
        chunks=chunks,
        top_k=top_k
    )

    intelligence = analyze_chunks(chunks)

    prompt = build_prompt(
        # question=question,
        retrieved_chunks=chunks,
        intelligence=intelligence
    )

    return {
        "question": question,
        "chunks": chunks,
        "intelligence": intelligence,
        "prompt": prompt
    }


if __name__ == "__main__":
    question = "What is Airbus doing with AI?"

    result = build_rag_query(
        question=question,
        top_k=5
    )

    print(result["prompt"])