import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_ROOT / "VectorDB" / "chroma_store"

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_collection("airbus_knowledge_base")

query = "What is Airbus doing with hydrogen aircraft?"

embedding = model.encode(
    query,
    normalize_embeddings=True
).tolist()

results = collection.query(
    query_embeddings=[embedding],
    n_results=5
)

for i, doc in enumerate(results["documents"][0], 1):
    metadata = results["metadatas"][0][i - 1]

    print("\n" + "=" * 80)
    print(f"Result {i}")
    print("Title:", metadata["title"])
    print("Topic:", metadata["topic"])
    print("Source:", metadata["source_name"])
    print("=" * 80)
    print(doc[:1000])