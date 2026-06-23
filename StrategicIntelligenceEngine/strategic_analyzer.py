OPPORTUNITY_KEYWORDS = {
    "partnership": 4,
    "collaboration": 4,
    "innovation": 3,
    "ai": 4,
    "artificial intelligence": 5,
    "automation": 3,
    "hydrogen": 4,
    "fuel cell": 4,
    "orders": 3,
    "growth": 2,
    "market": 1,
}

RISK_KEYWORDS = {
    "risk": 3,
    "challenge": 3,
    "delay": 4,
    "supply chain": 6,
    "supplier": 4,
    "disruption": 5,
    "crisis": 5,
    "problem": 4,
    "shortage": 4,
    "competition": 2,
    "boeing": 2,
    "cost": 2,
    "security": 2,
    "regulatory": 3,
}

TREND_KEYWORDS = {
    "future": 2,
    "next-generation": 3,
    "sustainable": 3,
    "hydrogen": 3,
    "fuel cell": 3,
    "ai": 3,
    "artificial intelligence": 4,
    "automation": 3,
    "digital": 2,
    "autonomous": 3,
    "decarbonisation": 3,
    "space": 2,
    "defence": 2,
}

AIRBUS_RELEVANCE_TERMS = [
    "airbus",
    "aerospace",
    "aircraft",
    "aviation",
    "defence",
    "defense",
    "space",
    "helicopter",
]


def is_airbus_relevant(item: dict) -> bool:
    title = (item.get("title") or "").lower()
    evidence = (item.get("evidence") or "").lower()

    text = title + " " + evidence

    return any(term in text for term in AIRBUS_RELEVANCE_TERMS)


def deduplicate_by_title(items: list) -> list:
    seen = set()
    unique = []

    for item in items:
        title = item.get("title")

        if title not in seen:
            seen.add(title)
            unique.append(item)

    return unique


def score_text(text: str, keyword_weights: dict) -> int:
    text = text.lower()
    score = 0

    for keyword, weight in keyword_weights.items():
        if keyword in text:
            score += weight

    return score


def calculate_priority(item):
    scores = item["scores"]

    return (
        scores["opportunity"] * 2 +
        scores["trend"] -
        scores["risk"]
    )


def classify_chunk(chunk: dict) -> dict:
    content = chunk["content"]
    metadata = chunk["metadata"]

    opportunity_score = score_text(content, OPPORTUNITY_KEYWORDS)
    risk_score = score_text(content, RISK_KEYWORDS)
    trend_score = score_text(content, TREND_KEYWORDS)
    priority = calculate_priority({
        "scores": {
            "opportunity": opportunity_score,
            "risk": risk_score,
            "trend": trend_score
        }
    })

    return {
        "title": metadata.get("title"),
        "source": metadata.get("source_name"),
        "topic": metadata.get("topic"),
        "url": metadata.get("url"),
        "evidence": content,
        "scores": {
            "opportunity": opportunity_score,
            "risk": risk_score,
            "trend": trend_score,
        },
        "priority": priority,
    }


def analyze_chunks(retrieved_chunks: list) -> dict:
    intelligence = {
        "opportunities": [],
        "risks": [],
        "trends": []
    }

    for chunk in retrieved_chunks:
        item = classify_chunk(chunk)
        if not is_airbus_relevant(item):
            continue    
        scores = item["scores"]

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        if best_score < 4:
            continue

        if best_category == "opportunity":
            intelligence["opportunities"].append(item)

        elif best_category == "risk":
            intelligence["risks"].append(item)

        elif best_category == "trend":
            intelligence["trends"].append(item)


    intelligence["opportunities"] = deduplicate_by_title(
        sorted(
            intelligence["opportunities"],
            key=lambda x: x["scores"]["opportunity"],
            reverse=True
        )
    )

    intelligence["risks"] = deduplicate_by_title(
        sorted(
            intelligence["risks"],
            key=lambda x: x["scores"]["risk"],
            reverse=True
        )
    )

    intelligence["trends"] = deduplicate_by_title(
        sorted(
            intelligence["trends"],
            key=lambda x: x["scores"]["trend"],
            reverse=True
        )
    )

    

    return intelligence