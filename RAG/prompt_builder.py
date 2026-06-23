def format_intelligence_section(intelligence: dict) -> str:
    sections = []
    for category in ["opportunities", "risks", "trends"]:
        items = intelligence.get(category, [])
        sections.append(f"\n{category.upper()}:")
        if not items:
            sections.append("- None detected")
            continue
        for item in items[:3]:          # max 3 per category
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
            f"{chunk['content'][:450]}"
        )
    context              = "\n\n".join(context_parts)
    intelligence_section = format_intelligence_section(intelligence)

    return f"""You are the Airbus Strategic Intelligence CEO Agent.
Analyze the evidence below and write a full executive report.

INTELLIGENCE SIGNALS:
{intelligence_section}

EVIDENCE:
{context}

Write the report using EXACTLY this structure and headings:

1. EXECUTIVE SUMMARY
(3 sentences on the strategic situation)

2. OPPORTUNITIES
For each: title | why it matters | evidence source | recommended action | business impact

3. RISKS & THREATS
For each: title | threat nature | evidence source | severity (High/Medium/Low) | mitigation

4. EMERGING TRENDS
For each: title | driver | evidence source | strategic meaning | time horizon

5. COMPETITOR INTELLIGENCE
What competitors are doing, where Airbus leads or lags, immediate threats.

6. STRATEGIC RECOMMENDATIONS
For each: recommendation | priority (High/Medium/Low) | justification | expected impact | risk if ignored

7. CEO BRIEFING SUMMARY
- What happened?
- Why does it matter?
- What should Airbus management do next?

Rules: 
- use only retrieved evidence, cite source titles, be concise and direct.
- Do NOT invent facts, risks, competitors, or market claims.
- Do NOT write "Supporting evidence: None".
- If there is not enough evidence, write: "No strong evidence found in retrieved documents."
- Keep the total report under 550 words.
"""