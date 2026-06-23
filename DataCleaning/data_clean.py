import json
import re
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = PROJECT_ROOT / "DataScraping" / "data" / "raw" / "all_documents.jsonl"
OUT_FILE = PROJECT_ROOT / "DataCleaning" / "data" / "processed" / "clean_documents.jsonl"

MIN_WORDS = 50

WORD_COUNT_EXEMPT = {"stock"}

CHUNK_SIZE_WORDS = 150
CHUNK_OVERLAP_WORDS = 30
MAX_CHUNKS_PER_DOC = 8

TOPIC_KEYWORDS = {
    "sustainability": {
        "hydrogen": 4,
        "fuel cell": 4,
        "saf": 3,
        "decarbon": 3,
        "emissions": 2,
        "climate": 2,
        "sustainable aviation": 3,
    },

    "defense": {
        "military": 4,
        "missile": 4,
        "battlefield": 4,
        "defense": 3,
        "satellite": 2,
        "space": 2,
        "security": 1,
    },

    "competition": {
        "boeing": 4,
        "comac": 4,
        "embraer": 4,
        "competitor": 3,
        "market share": 2,
    },

    "supply_chain": {
        "supply chain": 4,
        "supplier": 3,
        "production": 3,
        "delivery": 3,
        "engine": 2,
        "manufacturing": 2,
        "ramp-up": 2,
    },

    "finance": {
        "revenue": 4,
        "profit": 4,
        "earnings": 4,
        "guidance": 3,
        "orders": 2,
        "cash flow": 3,
        "financial results": 4,
    },

    "technology": {
        "artificial intelligence": 5,
        "machine learning": 5,
        "ai": 4,
        "software": 3,
        "automation": 3,
        "digital twin": 4,
        "autonomous": 3,
        "simulation": 2,
    },
}

RELEVANT_KEYWORDS = [
    "airbus", "aviation", "aircraft", "aerospace", "airline",
    "hydrogen", "sustainable aviation", "saf", "boeing",
    "comac", "embraer", "defense", "space"
]

BOILERPLATE_PATTERNS = [
    r"Related news.*",
    r"Related Pages.*",
    r"Related documentation.*",
    r"Watch the Webcast Replay",
    r"Click here.*",
    r"Discover Airbus.*",
    r"Discover more.*",
    r"Latest Defence news.*",
    r"Latest Helicopters news.*",
    r"For Airbus Summit \d+.*",
]

NOISE_TERMS = [
    "related news",
    "related pages",
    "watch the webcast",
    "click here",
    "contact us",
    "discover airbus",
    "airbus facebook",
    "airbus linkedin",
]

FOOTER_PATTERNS = [
    "register to receive",
    "related assets",
    "download documents",
    "documents contacts",
    "contacts for the media",
    "contact for the media",
    "press release and pictures",
    "downloads assets",
    "related keywords",
    "email address sign me up",
    "click to subscribe",
    "copyright ©",
    "all rights reserved",
    "sitemap",
    "rss feed",
    "log in",
    "your email address will not be published",
    "required fields are marked",
    "notify me of follow-up comments",
    "notify me of new posts",
]


def clean_text(text: str) -> str:
    # Remove HTML
    text = re.sub(r"<.*?>", " ", text)

    # Remove boilerplate
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Remove emails
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        " ",
        text
    )

    # Remove phone numbers
    text = re.sub(
        r"\+?\d[\d\s\-\(\)]{7,}",
        " ",
        text
    )

    text = text.replace("\u00a0", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_repeated_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    seen = set()
    unique = []

    for sentence in sentences:
        key = sentence.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(sentence)

    return " ".join(unique)

def remove_duplicate_lines(text):
    lines = text.split("\n")

    seen = set()
    cleaned = []

    for line in lines:
        key = line.strip().lower()

        if key and key not in seen:
            seen.add(key)
            cleaned.append(line)

    return "\n".join(cleaned)

def is_footer_or_contact_chunk(chunk: str) -> bool:
    chunk_lower = chunk.lower()

    matches = sum(1 for pattern in FOOTER_PATTERNS if pattern in chunk_lower)

    if matches >= 2:
        return True

    # contact-heavy chunks
    if "contacts" in chunk_lower and ("airbus |" in chunk_lower or "@" in chunk_lower):
        return True

    # subscription/footer-heavy chunks
    if "email address" in chunk_lower and "sign me up" in chunk_lower:
        return True

    return False

def chunk_text(text: str, chunk_size=CHUNK_SIZE_WORDS, overlap=CHUNK_OVERLAP_WORDS):
    """Sentence-aware, word-counted chunking. Packs whole sentences into
    ~chunk_size-word windows, carrying the last `overlap` words of a chunk
    into the next one so a fact split across a boundary isn't lost."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current_words = []

    for sentence in sentences:
        sentence_words = sentence.split()
        if len(current_words) + len(sentence_words) <= chunk_size:
            current_words.extend(sentence_words)
        else:
            if current_words:
                chunks.append(" ".join(current_words))
            carry = current_words[-overlap:] if current_words else []
            current_words = carry + sentence_words

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def assign_topic(text: str) -> str:
    text = text.lower()

    scores = {}

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0

        for keyword, weight in keywords.items():
            if keyword in text:
                score += weight

        scores[topic] = score

    best_topic = max(scores, key=scores.get)

    # print(title)
    # print(scores)
    # print("Assigned:", best_topic)
    # print("-" * 50)

    return best_topic if scores[best_topic] > 0 else "general"


def is_relevant(doc: dict, text: str) -> bool:
    category = doc.get("source_category", "")

    if category in ["company", "news", "market", "stock"]:
        return True

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in RELEVANT_KEYWORDS)


def importance_score(doc: dict, text: str) -> int:
    score = 0

    category = doc.get("source_category", "")

    if category == "company":
        score += 5
    elif category == "news":
        score += 4
    elif category == "research":
        score += 2
    elif category == "stock":
        score += 1

    text_lower = text.lower()

    for keyword in ["airbus", "boeing", "comac", "hydrogen", "defense", "supply chain"]:
        if keyword in text_lower:
            score += 1

    return score


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    clean_docs = []
    seen_titles = set()

    with open(RAW_FILE, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            category = doc.get("source_category", "")

            title = clean_text(doc.get("title") or "")
            content = clean_text(doc.get("content") or "")

            if not content:
                continue

            content = remove_repeated_sentences(content)

            word_count = len(content.split())
            if word_count < MIN_WORDS and category not in WORD_COUNT_EXEMPT:
                continue

            title_key = title.lower().strip()

            # only dedup on a non-empty title — two blank-title docs aren't
            # necessarily the same document
            if title_key and title_key in seen_titles:
                continue
            if title_key:
                seen_titles.add(title_key)

            if not is_relevant(doc, title + " " + content):
                continue

            full_text = title + "\n" + content
            topic = assign_topic(full_text)
            score = importance_score(doc, full_text)

            doc_id = doc.get("doc_id")
            chunks = chunk_text(content)
            if len(chunks) > MAX_CHUNKS_PER_DOC:
                chunks = chunks[:MAX_CHUNKS_PER_DOC]

            for i, chunk in enumerate(chunks):
                chunk_lower = chunk.lower()

                noise_count = sum(
                    term in chunk_lower
                    for term in NOISE_TERMS
                )

                if noise_count >= 2:
                    continue

                if is_footer_or_contact_chunk(chunk):
                    continue

                clean_docs.append({
                    "id": f"{doc_id}_{i}",
                    "parent_id": doc_id,
                    "chunk_index": i,
                    "n_chunks": len(chunks),
                    "title": title,
                    "content": chunk,
                    "source_name": doc.get("source_name"),
                    "source_category": category,
                    "topic": topic,
                    "url": doc.get("url"),
                    "published_date": doc.get("published_date"),
                    "collected_at": doc.get("collected_at"),
                    "importance_score": score
                })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for doc in clean_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print("Raw documents processed.")
    print("Clean chunks:", len(clean_docs))
    print("Saved to:", OUT_FILE)
    print("Source distribution:", Counter(d["source_category"] for d in clean_docs))
    print("Topic distribution:", Counter(d["topic"] for d in clean_docs))


    

if __name__ == "__main__":
    main()