"""
CEOAgent/ceo_agent.py
---------------------
Autonomous Strategic Intelligence Agent

Workflow: Goal → Plan → Retrieve → Analyze → Decide → Recommend → Validate

"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "RAG"))
sys.path.insert(0, str(PROJECT_ROOT / "StrategicIntelligenceEngine"))

from RAG.retriever import retrieve
from RAG.reranker import rerank
from RAG.prompt_builder import build_prompt
from CEOAgent.llm_agent import generate_response


# ── AGENT MEMORY ──────────────────────────────────────────────────────────────

class AgentMemory:
    def __init__(self):
        self.goal         = ""
        self.plan         = []
        self.all_chunks   = []
        self.intelligence = {"opportunities": [], "risks": [], "trends": []}
        self.decisions    = []
        self.report       = ""
        self.validated    = False
        self.log          = []

    def add_log(self, step: str, detail: str):
        entry = f"[{step}] {detail}"
        self.log.append(entry)
        print(f"  {entry}")


# ── TOOL 1-4: RETRIEVAL ───────────────────────────────────────────────────────

def tool_retrieve_opportunities(memory: AgentMemory, top_k: int = 5) -> list:
    memory.add_log("TOOL", "retrieve_opportunities → searching ChromaDB")
    query  = "Airbus opportunities partnerships AI hydrogen innovation growth orders"
    chunks = retrieve(query, top_k=top_k * 3)
    chunks = rerank(query=query, chunks=chunks, top_k=top_k)
    memory.add_log("TOOL", f"retrieve_opportunities → {len(chunks)} chunks")
    return chunks


def tool_retrieve_risks(memory: AgentMemory, top_k: int = 5) -> list:
    memory.add_log("TOOL", "retrieve_risks → searching ChromaDB")
    query  = "Airbus risks supply chain disruption regulatory challenge competitor Boeing delay"
    chunks = retrieve(query, top_k=top_k * 3)
    chunks = rerank(query=query, chunks=chunks, top_k=top_k)
    memory.add_log("TOOL", f"retrieve_risks → {len(chunks)} chunks")
    return chunks


def tool_retrieve_trends(memory: AgentMemory, top_k: int = 5) -> list:
    memory.add_log("TOOL", "retrieve_trends → searching ChromaDB")
    query  = "Airbus trends sustainable aviation hydrogen digital autonomous decarbonisation"
    chunks = retrieve(query, top_k=top_k * 3)
    chunks = rerank(query=query, chunks=chunks, top_k=top_k)
    memory.add_log("TOOL", f"retrieve_trends → {len(chunks)} chunks")
    return chunks


def tool_retrieve_competitors(memory: AgentMemory, top_k: int = 5) -> list:
    memory.add_log("TOOL", "retrieve_competitors → searching ChromaDB")
    query  = "Boeing competitor aerospace rivalry market share aircraft orders threat"
    chunks = retrieve(query, top_k=top_k * 3)
    chunks = rerank(query=query, chunks=chunks, top_k=top_k)
    memory.add_log("TOOL", f"retrieve_competitors → {len(chunks)} chunks")
    return chunks


# ── TOOL 5: LLM SIGNAL CLASSIFICATION ────────────────────────────────────────

def tool_llm_classify_signals(memory: AgentMemory, chunks: list) -> dict:
    """
    Tool: uses the LLM to classify retrieved chunks into
    opportunities, risks, and trends with a strict structured prompt.
    Much more accurate than keyword scoring alone.
    """
    memory.add_log("TOOL", f"llm_classify_signals → sending {len(chunks)} chunks to Llama")

    # build a compact evidence block — just enough for classification
    evidence_block = ""
    for i, chunk in enumerate(chunks[:12], 1):
        meta    = chunk["metadata"]
        content = chunk["content"][:200]
        evidence_block += (
            f"[{i}] Title: {meta.get('title','')}\n"
            f"Source: {meta.get('source_name','')}\n"
            f"Content: {content}\n\n"
        )

    classification_prompt = f"""You are a strategic analyst for Airbus.

Read each evidence chunk below and classify it strictly.

For EACH chunk decide:
- Is it an OPPORTUNITY for Airbus? (growth, innovation, partnership, new market, technology advantage)
- Is it a RISK for Airbus? (supply chain, competitor threat, regulation, delay, disruption, cost)
- Is it a TREND? (industry shift, emerging technology, behavioural change, long-term direction)
- Or IRRELEVANT? (not related to Airbus strategy)

A chunk can only belong to ONE category. Choose the strongest signal.

EVIDENCE:
{evidence_block}

Respond ONLY with valid JSON in this exact format, no explanation:
{{
  "opportunities": [
    {{"chunk_id": 1, "title": "...", "reason": "one sentence why this is an opportunity", "impact": "High/Medium/Low"}}
  ],
  "risks": [
    {{"chunk_id": 2, "title": "...", "reason": "one sentence why this is a risk", "severity": "High/Medium/Low"}}
  ],
  "trends": [
    {{"chunk_id": 3, "title": "...", "reason": "one sentence why this is a trend", "horizon": "Short/Mid/Long-term"}}
  ]
}}

Rules:
- Only include chunks with clear strategic signal. Skip irrelevant ones.
- Do not invent titles. Use the exact title from the evidence.
- Respond with JSON only. No markdown, no explanation.
"""

    raw = generate_response(classification_prompt)

    # parse LLM JSON response
    try:
        # strip markdown fences if present
        cleaned = raw.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        classified = json.loads(cleaned.strip())
    except (json.JSONDecodeError, IndexError) as e:
        memory.add_log("TOOL", f"llm_classify_signals → JSON parse failed ({e}), falling back to keywords")
        return _keyword_fallback(chunks)

    # enrich with full evidence from original chunks
    chunk_map = {i+1: chunks[i] for i in range(len(chunks))}

    def enrich(items: list, score_key: str) -> list:
        enriched = []
        for item in items:
            cid   = item.get("chunk_id", 0)
            chunk = chunk_map.get(cid, {})
            meta  = chunk.get("metadata", {})
            enriched.append({
                "title":    item.get("title", meta.get("title", "Untitled")),
                "source":   meta.get("source_name", ""),
                "topic":    meta.get("topic", ""),
                "url":      meta.get("url", ""),
                "evidence": chunk.get("content", ""),
                "reason":   item.get("reason", ""),
                "scores":   {
                    "opportunity": 8 if score_key == "opportunity" else 2,
                    "risk":        8 if score_key == "risk"        else 2,
                    "trend":       8 if score_key == "trend"       else 2,
                },
                "llm_classified": True,
                "impact":   item.get("impact", item.get("severity", item.get("horizon", "Medium"))),
            })
        return enriched

    intelligence = {
        "opportunities": enrich(classified.get("opportunities", []), "opportunity"),
        "risks":         enrich(classified.get("risks", []),         "risk"),
        "trends":        enrich(classified.get("trends", []),        "trend"),
    }

    opp = len(intelligence["opportunities"])
    rsk = len(intelligence["risks"])
    trd = len(intelligence["trends"])
    memory.add_log("TOOL",
        f"llm_classify_signals → ✓ {opp} opportunities · {rsk} risks · {trd} trends (LLM-classified)")

    return intelligence


def _keyword_fallback(chunks: list) -> dict:
    """Fallback to keyword scoring if LLM JSON parsing fails."""
    from StrategicIntelligenceEngine.strategic_analyzer import analyze_chunks
    return analyze_chunks(chunks)


# ── TOOL 6: VALIDATION ────────────────────────────────────────────────────────

def tool_validate_recommendations(memory: AgentMemory, report: str) -> dict:
    memory.add_log("TOOL", "validate_recommendations → checking report")

    report_lower = report.lower()
    issues    = []
    strengths = []

    # check opportunities covered
    opp_found = any(
        any(w in report_lower for w in item["title"].lower().split() if len(w) > 4)
        for item in memory.intelligence.get("opportunities", [])
    )
    opp_terms = ["opportunit","partnership","hydrogen","innovation","growth","ai","automation"]
    if not opp_found:
        opp_found = any(t in report_lower for t in opp_terms)
    if opp_found:
        strengths.append("Report covers detected opportunity signals")
    else:
        issues.append("Opportunity signals not addressed in report")

    # check risks covered
    risk_found = any(
        any(w in report_lower for w in item["title"].lower().split() if len(w) > 4)
        for item in memory.intelligence.get("risks", [])
    )
    risk_terms = ["risk","challenge","delay","supply chain","disruption","shortage","threat"]
    if not risk_found:
        risk_found = any(t in report_lower for t in risk_terms)
    if risk_found:
        strengths.append("Report addresses detected risk signals")
    else:
        issues.append("Risk signals not addressed in report")

    # check length
    word_count = len(report.split())
    if word_count < 150:
        issues.append(f"Report appears truncated ({word_count} words)")
    else:
        strengths.append(f"Report length acceptable ({word_count} words)")

    # check all sections present
    required = ["executive summary", "opportunit", "risk", "recommendation"]
    missing  = [s for s in required if s not in report_lower]
    if not missing:
        strengths.append("All required report sections present")
    else:
        issues.append(f"Missing sections: {', '.join(missing)}")

    # check LLM classification was used
    llm_classified = any(
        item.get("llm_classified", False)
        for group in memory.intelligence.values()
        for item in group
    )
    if llm_classified:
        strengths.append("Signals classified by LLM (not just keywords)")
    else:
        strengths.append("Signals classified by keyword scoring (fallback)")

    passed = len(issues) == 0
    memory.add_log("TOOL",
        f"validate → {'PASSED' if passed else 'ISSUES FOUND'}: "
        f"{len(strengths)} strengths · {len(issues)} issues")

    return {"passed": passed, "strengths": strengths, "issues": issues}


# ── AGENT STEPS ───────────────────────────────────────────────────────────────

def step_set_goal(memory: AgentMemory):
    memory.goal = (
        "Produce a complete strategic intelligence briefing for the Airbus CEO "
        "covering opportunities, risks, emerging trends, competitor activity, "
        "and evidence-backed strategic recommendations."
    )
    memory.add_log("GOAL", memory.goal)


def step_plan(memory: AgentMemory):
    memory.plan = [
        "retrieve_opportunities",
        "retrieve_risks",
        "retrieve_trends",
        "retrieve_competitors",
        "llm_classify_signals",
        "decide_sufficiency",
        "generate_report",
        "validate_recommendations",
    ]
    memory.add_log("PLAN", " → ".join(memory.plan))


def step_retrieve(memory: AgentMemory, top_k: int = 5):
    opp_chunks  = tool_retrieve_opportunities(memory, top_k)
    risk_chunks = tool_retrieve_risks(memory, top_k)
    trend_chunks= tool_retrieve_trends(memory, top_k)
    comp_chunks = tool_retrieve_competitors(memory, top_k)

    seen, unique = set(), []
    for chunk in opp_chunks + risk_chunks + trend_chunks + comp_chunks:
        key = chunk["content"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(chunk)

    memory.all_chunks = unique
    memory.add_log("RETRIEVE", f"Total unique chunks after dedup: {len(memory.all_chunks)}")


def step_analyze(memory: AgentMemory):
    """Analyze step now uses LLM classification instead of keyword scoring."""
    memory.intelligence = tool_llm_classify_signals(memory, memory.all_chunks)


def step_decide(memory: AgentMemory) -> bool:
    opp = len(memory.intelligence["opportunities"])
    rsk = len(memory.intelligence["risks"])
    trd = len(memory.intelligence["trends"])

    sufficient = opp >= 1 and rsk >= 1
    decision   = "PROCEED" if sufficient else "INSUFFICIENT — proceeding with available evidence"

    memory.decisions.append({
        "decision":      decision,
        "opportunities": opp,
        "risks":         rsk,
        "trends":        trd,
        "reasoning": (
            f"LLM classified {opp} opportunities, {rsk} risks, {trd} trends from retrieved evidence. "
            f"{'Sufficient to generate report.' if sufficient else 'Limited signals — proceeding anyway.'}"
        )
    })
    memory.add_log("DECIDE", f"{decision} — {opp} opp · {rsk} risk · {trd} trend")
    return sufficient


def step_generate(memory: AgentMemory):
    memory.add_log("GENERATE", "Building executive prompt → calling Llama 3.1")
    prompt = build_prompt(
        retrieved_chunks=memory.all_chunks[:5],
        intelligence=memory.intelligence,
    )
    memory.report = generate_response(prompt)
    memory.add_log("GENERATE", f"Report generated ({len(memory.report.split())} words)")


def step_validate(memory: AgentMemory):
    result           = tool_validate_recommendations(memory, memory.report)
    memory.validated = result["passed"]

    summary  = "\n\n---\n**Agent Validation**\n"
    summary += "\n".join(f"✅ {s}" for s in result["strengths"])
    if result["issues"]:
        summary += "\n" + "\n".join(f"⚠️ {i}" for i in result["issues"])
    memory.report += summary


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def ask_ceo_agent(top_k: int = 5) -> dict:
    """
    Full autonomous agent loop:
    Goal → Plan → Retrieve → LLM Classify → Decide → Recommend → Validate
    """
    print("\n" + "="*55)
    print("  Airbus CEO Agent — Autonomous Agent Loop")
    print("="*55)

    memory = AgentMemory()

    step_set_goal(memory)
    step_plan(memory)
    step_retrieve(memory, top_k=top_k)
    step_analyze(memory)    # ← LLM classification happens here
    step_decide(memory)

    # retry loop — agent reruns until validation passes or max attempts reached
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        memory.add_log("GENERATE", f"Attempt {attempt}/{max_attempts}")
        step_generate(memory)
        step_validate(memory)

        if memory.validated:
            memory.add_log("AGENT", f"✓ Validation passed on attempt {attempt} — finalizing report")
            break
        elif attempt < max_attempts:
            memory.add_log("AGENT",
                f"✗ Validation failed (attempt {attempt}) — broadening retrieval and retrying")
            # retrieve more evidence each retry
            new_top_k = top_k + (attempt * 3)
            step_retrieve(memory, top_k=new_top_k)
            step_analyze(memory)
            memory.report = ""   # clear previous attempt
            memory.add_log("AGENT",
                f"Retrieved {len(memory.all_chunks)} chunks for retry {attempt + 1}")
        else:
            memory.add_log("AGENT",
                f"Max attempts ({max_attempts}) reached — saving best available report")

    print("="*55)
    print(f"  Agent completed. Validated: {memory.validated}")
    print("="*55 + "\n")

    return {
        "rag_result": {
            "chunks":       memory.all_chunks,
            "intelligence": memory.intelligence,
            "prompt":       "",
        },
        "report":    memory.report,
        "agent_log": memory.log,
        "decisions": memory.decisions,
        "goal":      memory.goal,
        "plan":      memory.plan,
        "validated": memory.validated,
    }


if __name__ == "__main__":
    result = ask_ceo_agent(top_k=5)
    print(result["report"])