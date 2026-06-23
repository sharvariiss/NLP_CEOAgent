import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "RAG"))
sys.path.append(str(PROJECT_ROOT / "StrategicIntelligenceEngine"))

from retriever import retrieve
from strategic_analyzer import analyze_chunks


question = "What is Airbus doing with AI?"

chunks = retrieve(question, top_k=5)

intelligence = analyze_chunks(chunks)

print("\nOPPORTUNITIES")
for item in intelligence["opportunities"]:
    print("-", item["title"], item["scores"])

print("\nRISKS")
for item in intelligence["risks"]:
    print("-", item["title"], item["scores"])

print("\nTRENDS")
for item in intelligence["trends"]:
    print("-", item["title"], item["scores"])