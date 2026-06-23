from sentence_transformers import CrossEncoder


RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

reranker = CrossEncoder(RERANKER_MODEL)


def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    if not chunks:
        return []

    pairs = [
        (query, chunk["content"])
        for chunk in chunks
    ]

    scores = reranker.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    reranked_chunks = sorted(
        chunks,
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return reranked_chunks[:top_k]