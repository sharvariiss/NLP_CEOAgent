def format_intelligence_section(intelligence: dict) -> str:
    sections = []
    for category in ["opportunities", "risks", "trends"]:
        items = intelligence.get(category, [])
        sections.append(f"\n{category.upper()}:")
        if not items:
            sections.append("- None detected")
            continue
        for item in items[:3]:
            sections.append(
                f"- {item.get('title')} [{item.get('source')}] "
                f"(score: {item.get('scores',{}).get(category[:-1] if category != 'trends' else 'trend', 0)})"
            )
    return "\n".join(sections)


def build_prompt(retrieved_chunks: list, intelligence: dict) -> str:
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks[:5], 1):
        meta = chunk["metadata"]
        context_parts.append(
            f"[{i}] {meta.get('title')} ({meta.get('source_name')}, {meta.get('topic')})\n"
            f"{chunk['content'][:300]}"
        )
    context              = "\n\n".join(context_parts)
    intelligence_section = format_intelligence_section(intelligence)

    return f"""You are the Airbus Strategic Intelligence CEO Agent.
Analyze the evidence and write a structured executive report.

INTELLIGENCE SIGNALS:
{intelligence_section}

EVIDENCE:
{context}

Write the report using EXACTLY these headings:

1. EXECUTIVE SUMMARY
3 sentences: current situation, biggest opportunity, biggest risk.

2. OPPORTUNITIES
For each: title | why it matters | source | recommended action | business impact

3. RISKS & THREATS
For each: title | nature of threat | source | severity (High/Medium/Low) | mitigation

4. EMERGING TRENDS
For each: title | what is driving it | source | strategic meaning | time horizon

5. COMPETITOR INTELLIGENCE
What competitors are doing, where Airbus leads or lags, immediate threats.

6. STRATEGIC RECOMMENDATIONS
For each: recommendation | priority (High/Medium/Low) | justification | expected impact | risk if ignored

7. CEO BRIEFING SUMMARY
Answer all three questions with at least 2-3 sentences each:

What happened?
(Summarize the most important recent developments from the evidence — market moves, technology shifts, competitor actions.)

Why does it matter?
(Explain the strategic implications for Airbus — revenue impact, competitive position, long-term relevance.)

What should Airbus management do next?
(Give 3 specific, prioritized actions management should take immediately, in the next quarter, and in the next year.)

Rules:
- Use only retrieved evidence. Cite source titles.
- Do not invent facts or competitors.
- If evidence is insufficient, state it clearly.
- Keep total report under 600 words.
"""