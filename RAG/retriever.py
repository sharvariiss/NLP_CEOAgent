from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_ROOT / "VectorDB" / "chroma_store"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "airbus_knowledge_base"


model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_collection(
    COLLECTION_NAME
)

def deduplicate_results(chunks):
    seen_titles = set()
    unique = []

    for chunk in chunks:
        title = chunk["metadata"].get("title")

        if title not in seen_titles:
            seen_titles.add(title)
            unique.append(chunk)

    return unique

def retrieve(query: str, top_k: int = 5) -> list:
    embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k * 3  
    )

    chunks = []

    for i in range(len(results["documents"][0])):
        chunks.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    chunks = deduplicate_results(chunks)

    return chunks[:top_k]