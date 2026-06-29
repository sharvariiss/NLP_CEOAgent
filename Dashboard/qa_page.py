"""
Dashboard/qa_page.py
--------------------
Q&A page logic — imported and called by app.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "RAG"))
sys.path.insert(0, str(PROJECT_ROOT / "StrategicIntelligenceEngine"))

import streamlit as st


def render():
    st.markdown("## 🤖 Ask the Agent")
    st.markdown("Ask any strategic question. The agent retrieves evidence and answers using Llama 3.1.")

    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []

    # suggested questions
    suggestions = [
        "What is Airbus doing with hydrogen aircraft?",
        "What are the biggest supply chain risks for Airbus?",
        "How is Airbus competing with Boeing?",
        "What AI initiatives is Airbus pursuing?",
        "What sustainability trends should Airbus monitor?",
    ]

    st.markdown("**Suggested questions:**")
    cols = st.columns(len(suggestions))
    for i, (col, q) in enumerate(zip(cols, suggestions)):
        if col.button(q[:25] + "…", key=f"qa_sugg_{i}", use_container_width=True):
            st.session_state["qa_input"] = q
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    prefill  = st.session_state.pop("qa_prefill", "") if "qa_prefill" in st.session_state else ""
    question = st.text_input(
        "Your question",
        value=prefill,
        placeholder="e.g. What strategic opportunities exist for Airbus in AI?",
        key="qa_input",
    )

    c1, c2 = st.columns([4, 1])
    with c1:
        ask = st.button("🔍 Ask Agent", type="primary", use_container_width=True, key="qa_ask")
    with c2:
        if st.button("🗑️ Clear", use_container_width=True, key="qa_clear"):
            st.session_state.qa_history = []
            st.rerun()

    if ask and question.strip():

        st.markdown(
            f'<div style="background:#1C1C1E;color:#fff;border-radius:16px 16px 4px 16px;'
            f'padding:14px 18px;margin:12px 0 6px;font-size:14px;font-weight:500;">'
            f'🧑 {question}</div>',
            unsafe_allow_html=True)

        with st.spinner("Retrieving evidence and generating answer…"):
            try:
                from RAG.retriever import retrieve
                from RAG.reranker import rerank
                from CEOAgent.llm_agent import generate_response

                chunks = retrieve(question, top_k=12)
                chunks = rerank(query=question, chunks=chunks, top_k=4)

                context = "\n\n".join(
                    f"[{i}] {c['metadata'].get('title','')} "
                    f"({c['metadata'].get('source_name','')})\n{c['content'][:250]}"
                    for i, c in enumerate(chunks, 1)
                )

                prompt = (
                    "You are the Airbus Strategic Intelligence CEO Agent.\n\n"
                    "Answer the following strategic question using ONLY the evidence below.\n"
                    "Be direct and concise. Cite source titles. Answer in 3-5 sentences.\n\n"
                    f"Question: {question}\n\n"
                    f"Evidence:\n{context}\n\n"
                    "Answer:"
                )

                answer = generate_response(prompt)
                if not answer or not answer.strip():
                    answer = "Ollama returned an empty response. Make sure llama3.1:8b is loaded."

                sources = [
                    {"title": c["metadata"].get("title",""),
                     "source": c["metadata"].get("source_name",""),
                     "url": c["metadata"].get("url","")}
                    for c in chunks[:3]
                ]

            except Exception as e:
                import traceback
                answer  = f"Error: {str(e)}"
                sources = []
                st.code(traceback.format_exc())

        st.markdown(
            f'<div style="background:#fff;border:1px solid #E8E8E4;'
            f'border-radius:4px 16px 16px 16px;padding:16px 20px;'
            f'margin-bottom:6px;font-size:14px;line-height:1.75;color:#3A3A3C;">'
            f'🤖 {answer}</div>',
            unsafe_allow_html=True)

        if sources:
            src_parts = []
            for s in sources:
                if s.get("title"):
                    t = s["title"][:50]
                    src_parts.append(
                        f'<a href="{s["url"]}" target="_blank" style="color:#636366;">{t}</a>'
                        if s.get("url") else
                        f'<span style="color:#636366;">{t}</span>'
                    )
            if src_parts:
                st.markdown(
                    f'<div style="font-size:11px;color:#AEAEB2;padding:4px 0 16px;">'
                    f'📎 Sources: {" · ".join(src_parts)}</div>',
                    unsafe_allow_html=True)

        st.session_state.qa_history.append({
            "question": question,
            "answer":   answer,
            "sources":  sources,
        })

    # history
    if st.session_state.qa_history:
        st.markdown("---")
        st.markdown("**Previous questions**")
        for chat in reversed(st.session_state.qa_history):
            st.markdown(
                f'<div style="background:#1C1C1E;color:#fff;border-radius:16px 16px 4px 16px;'
                f'padding:12px 16px;margin:10px 0 6px;font-size:13px;font-weight:500;">'
                f'🧑 {chat["question"]}</div>',
                unsafe_allow_html=True)
            st.markdown(
                f'<div style="background:#fff;border:1px solid #E8E8E4;'
                f'border-radius:4px 16px 16px 16px;padding:14px 18px;'
                f'margin-bottom:4px;font-size:13px;line-height:1.7;color:#3A3A3C;">'
                f'🤖 {chat["answer"]}</div>',
                unsafe_allow_html=True)