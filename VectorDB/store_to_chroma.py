import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# =====================================================
# Paths
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "DataCleaning"
    / "data"
    / "processed"
    / "clean_documents.jsonl"
)

CHROMA_DIR = (
    PROJECT_ROOT
    / "VectorDB"
    / "chroma_store"
)

COLLECTION_NAME = "airbus_knowledge_base"

# =====================================================
# Embedding Model
# =====================================================

MODEL_NAME = "BAAI/bge-small-en-v1.5"

print(f"Loading embedding model: {MODEL_NAME}")

model = SentenceTransformer(MODEL_NAME)

# =====================================================
# Chroma
# =====================================================

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={
        "description": "Airbus CEO Assistant Knowledge Base"
    }
)


def load_documents():
    docs = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))

    return docs


def create_embeddings(texts):
    return model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )


def main():

    docs = load_documents()

    print(f"Loaded {len(docs)} chunks")

    documents = []
    metadatas = []
    ids = []

    for doc in docs:

        documents.append(doc["content"])

        ids.append(doc["id"])

        metadatas.append({
            "parent_id": doc["parent_id"],
            "title": doc["title"],
            "source_name": doc["source_name"],
            "source_category": doc["source_category"],
            "topic": doc["topic"],
            "importance_score": doc["importance_score"],
            "url": doc["url"] or "",
            "published_date": str(doc["published_date"] or "")
        })

    print("Generating embeddings...")

    embeddings = create_embeddings(documents)

    print("Storing in ChromaDB...")

    BATCH_SIZE = 500

    for i in range(0, len(documents), BATCH_SIZE):

        existing = collection.get()["ids"]
        existing_ids = set(existing)

        new_docs = []
        new_ids = []
        new_metadatas = []
        new_embeddings = []

        for doc, doc_id, metadata, embedding in zip(documents, ids, metadatas, embeddings):
            if doc_id not in existing_ids:
                new_docs.append(doc)
                new_ids.append(doc_id)
                new_metadatas.append(metadata)
                new_embeddings.append(embedding)

        collection.add(
            ids=ids[i:i+BATCH_SIZE],
            documents=documents[i:i+BATCH_SIZE],
            embeddings=embeddings[i:i+BATCH_SIZE].tolist(),
            metadatas=metadatas[i:i+BATCH_SIZE]
        )

        print(
            f"Stored {min(i+BATCH_SIZE, len(documents))}/{len(documents)}"
        )

    print("\nDone")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total chunks: {collection.count()}")
    print(f"Chroma path: {CHROMA_DIR}")


if __name__ == "__main__":
    main()