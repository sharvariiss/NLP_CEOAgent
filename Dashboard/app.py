import sys
import json
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob

sys.path.insert(0, str(Path(__file__).resolve().parent))  
from qa_page import render as render_qa  

PROJECT_ROOT  = Path(__file__).resolve().parents[1]
DATA_FILE     = PROJECT_ROOT / "DataCleaning" / "data" / "processed" / "clean_documents.jsonl"
REPORT_PATH   = PROJECT_ROOT / "reports" / "latest_report.json"
STOCK_CSV     = PROJECT_ROOT / "DataScraping" / "data" / "raw" / "airbus_price_history.csv"

st.set_page_config(
    page_title="Airbus · Strategic Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── design tokens ─────────────────────────────────────────────────────────────
# Palette: off-white canvas, warm slate text, single accent (Airbus red), 
# muted teal for positive signals, soft amber for warnings
# Typography: Inter for UI, system mono for data
# Signature: left-border accent bars that pulse with signal strength

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif;
    color: #1C1C1E;
}

/* canvas */
.stApp { background: #F7F7F5; }
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E8E8E4; }

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* always show sidebar — prevent collapse */
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { 
    min-width: 240px !important; 
    max-width: 240px !important;
    transform: none !important;
    visibility: visible !important;
    display: block !important;
}
[data-testid="stSidebarNav"] { display: none; }
div[data-testid="stSidebarContent"] { padding-top: 2rem; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1200px; }

/* sidebar */
.sidebar-logo {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #8E8E93;
    padding: 0 0 20px; border-bottom: 1px solid #E8E8E4;
    margin-bottom: 20px;
}
.nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; border-radius: 8px;
    font-size: 14px; font-weight: 500; color: #3A3A3C;
    cursor: pointer; margin-bottom: 2px;
    transition: background .15s;
    text-decoration: none;
}
.nav-item:hover { background: #F2F2F0; }
.nav-item.active { background: #1C1C1E; color: #FFFFFF; }
.nav-section {
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #AEAEB2;
    padding: 16px 14px 6px; 
}

/* page title */
.page-eyebrow {
    font-size: 11px; font-weight: 600; letter-spacing: 2px;
    text-transform: uppercase; color: #AEAEB2; margin-bottom: 6px;
}
.page-title {
    font-size: 28px; font-weight: 700; color: #1C1C1E;
    letter-spacing: -0.5px; margin: 0 0 4px;
    line-height: 1.2;
}
.page-meta {
    font-size: 13px; color: #8E8E93; margin: 0 0 28px;
}

/* stat cards */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 28px; }
.stat-card { margin-bottom: 0; }
.stat-card {
    background: #FFFFFF; border-radius: 12px;
    padding: 18px 20px; border: 1px solid #E8E8E4;
}
.stat-label { font-size: 11px; font-weight: 600; letter-spacing: .8px; text-transform: uppercase; color: #AEAEB2; margin-bottom: 6px; }
.stat-value { font-size: 26px; font-weight: 700; color: #1C1C1E; letter-spacing: -0.5px; line-height: 1; }
.stat-sub   { font-size: 12px; color: #8E8E93; margin-top: 4px; }
.stat-card.accent-red  .stat-value { color: #C41E3A; }
.stat-card.accent-teal .stat-value { color: #0E7A6E; }
.stat-card.accent-amber .stat-value { color: #B45309; }

/* signal cards (opp/risk/trend) */
.signal-card {
    background: #FFFFFF; border-radius: 12px;
    border: 1px solid #E8E8E4; padding: 20px 22px;
    margin-bottom: 12px; position: relative; overflow: hidden;
}
.signal-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 4px;
}
.signal-card.opp::before  { background: #0E7A6E; }
.signal-card.risk::before { background: #C41E3A; }
.signal-card.trend::before{ background: #B45309; }

.signal-title { font-size: 15px; font-weight: 600; color: #1C1C1E; margin-bottom: 4px; }
.signal-meta  { font-size: 12px; color: #8E8E93; margin-bottom: 10px; }
.signal-body  { font-size: 13.5px; color: #3A3A3C; line-height: 1.65; margin-bottom: 12px; }
.signal-badge {
    display: inline-block; font-size: 11px; font-weight: 600;
    padding: 3px 10px; border-radius: 20px; letter-spacing: .3px;
}
.badge-high   { background: #FEE2E2; color: #991B1B; }
.badge-medium { background: #FEF3C7; color: #92400E; }
.badge-low    { background: #D1FAE5; color: #065F46; }
.badge-score  { background: #F2F2F0; color: #3A3A3C; margin-left: 6px; }

/* feed cards */
.feed-card {
    background: #FFFFFF; border-radius: 10px;
    border: 1px solid #E8E8E4; padding: 14px 16px;
    margin-bottom: 10px;
}
.feed-card a { color: #1C1C1E; font-weight: 600; font-size: 13px; text-decoration: none; }
.feed-card a:hover { color: #C41E3A; }
.feed-meta { font-size: 11px; color: #AEAEB2; margin: 4px 0 6px; }
.feed-snip { font-size: 12px; color: #636366; line-height: 1.55; }

/* sentiment pill */
.sent-pill {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
}
.sent-pos { background: #D1FAE5; color: #065F46; }
.sent-neu { background: #F2F2F0; color: #636366; }
.sent-neg { background: #FEE2E2; color: #991B1B; }

/* section label */
.section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 1.8px;
    text-transform: uppercase; color: #AEAEB2;
    margin: 28px 0 14px; padding-bottom: 10px;
    border-bottom: 1px solid #E8E8E4;
}

/* report box */
.report-box {
    background: #FFFFFF; border-radius: 12px;
    border: 1px solid #E8E8E4; padding: 28px 32px;
    font-size: 14px; line-height: 1.8; color: #3A3A3C;
    height: 520px; overflow-y: auto;
}

/* agent summary */
.agent-row {
    display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;
}
.agent-chip {
    background: #F2F2F0; border-radius: 8px;
    padding: 8px 12px; font-size: 12px; font-weight: 500; color: #3A3A3C;
    display: flex; align-items: center; gap: 6px;
}
.agent-chip.active { background: #1C1C1E; color: #FFF; }

/* status bar */
.status-bar {
    background: #FFFFFF; border: 1px solid #E8E8E4; border-radius: 8px;
    padding: 10px 16px; font-size: 12px; color: #8E8E93;
    display: flex; gap: 20px; align-items: center; margin-bottom: 24px;
    flex-wrap: wrap;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #0E7A6E; display: inline-block; margin-right: 6px; }
</style>
<script>
// keep sidebar expanded
window.addEventListener("load", function() {
    const btn = window.parent.document.querySelector("[data-testid=\'collapsedControl\']");
    if (btn) btn.style.display = "none";
});
</script>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    df = pd.read_json(DATA_FILE, lines=True)
    df["sentiment"]    = df["content"].apply(lambda t: TextBlob(str(t)).sentiment.polarity)
    df["subjectivity"] = df["content"].apply(lambda t: TextBlob(str(t)).sentiment.subjectivity)
    return df

@st.cache_data
def load_stock():
    if STOCK_CSV.exists():
        try:
            df = pd.read_csv(STOCK_CSV)
            df.columns = [c.strip() for c in df.columns]
            dc = next((c for c in df.columns if "date" in c.lower()), None)
            if dc:
                df[dc] = pd.to_datetime(df[dc], errors="coerce")
                df = df.rename(columns={dc: "Date"}).sort_values("Date")
            return df
        except Exception:
            pass
    return pd.DataFrame()

@st.cache_data
def load_report():
    if REPORT_PATH.exists():
        try: return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except Exception: return None
    return None

def s_label(score):
    if score > 0.08: return "Positive"
    if score < -0.08: return "Negative"
    return "Neutral"

def s_color(score):
    if score > 0.08: return "#0E7A6E"
    if score < -0.08: return "#C41E3A"
    return "#B45309"

def s_class(score):
    if score > 0.08: return "sent-pos"
    if score < -0.08: return "sent-neg"
    return "sent-neu"

def badge_class(score):
    if score >= 8: return "badge-high", "High"
    if score >= 4: return "badge-medium", "Medium"
    return "badge-low", "Low"

def fmt_ts(iso):
    try: return datetime.datetime.fromisoformat(iso).strftime("%d %b %Y · %H:%M")
    except: return iso

def extract_recommendations(report):
    if not report: return "No recommendations found."
    vm = "---\nAgent Validation"
    clean = report[:report.find(vm)].strip() if vm in report else report
    rec_start = None
    for p in ["6. STRATEGIC RECOMMENDATIONS","6. Strategic Recommendation","Strategic Recommendation","Recommendations"]:
        if p.lower() in clean.lower():
            rec_start = clean.lower().find(p.lower()); break
    if rec_start is None:
        lines = clean.strip().split("\n")
        return "\n".join(lines[len(lines)//2:]).strip() or clean
    rec_end = None
    for p in ["7. CEO BRIEFING SUMMARY","7. CEO Briefing Summary","7. CEO Briefing","CEO BRIEFING"]:
        if p.lower() in clean.lower():
            idx = clean.lower().find(p.lower())
            if idx > rec_start: rec_end = idx; break
    return clean[rec_start:rec_end].strip() if rec_end else clean[rec_start:].strip()

def extract_ceo_briefing(report):
    if not report: return "No briefing found."
    vm = "---\nAgent Validation"
    clean = report[:report.find(vm)].strip() if vm in report else report
    for p in ["7. CEO BRIEFING SUMMARY","7. CEO Briefing Summary","7. CEO Briefing","CEO BRIEFING SUMMARY","CEO Briefing"]:
        if p.lower() in clean.lower():
            idx = clean.lower().find(p.lower())
            b = clean[idx:].strip()
            if b: return b
    lines = clean.strip().split("\n")
    return "\n".join(lines[len(lines)*3//4:]).strip() or clean

def scrollable(text, height=520):
    import re
    safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
    safe = safe.replace("\n","<br>")
    st.markdown(f'<div class="report-box" style="height:{height}px;">{safe}</div>', unsafe_allow_html=True)

def signal_card(item, kind):
    cls_map  = {"opportunity":"opp","risk":"risk","trend":"trend"}
    key_map  = {"opportunity":"opportunity","risk":"risk","trend":"trend"}
    lbl_map  = {"opportunity":"Impact","risk":"Severity","trend":"Strength"}
    cls   = cls_map.get(kind,"")
    key   = key_map.get(kind, kind)
    lbl   = lbl_map.get(kind,"Score")
    score = item.get("scores",{}).get(key,0)
    bc, bl= badge_class(score)
    url   = item.get("url","")
    src   = f'<a href="{url}" target="_blank" style="color:#636366;">{item.get("source","")}</a>' if url else item.get("source","")
    ev    = item.get("evidence","")[:380] + ("…" if len(item.get("evidence",""))>380 else "")
    st.markdown(f"""
    <div class="signal-card {cls}">
      <div class="signal-title">{item.get("title","Untitled")}</div>
      <div class="signal-meta">{src} &nbsp;·&nbsp; {item.get("topic","").replace("_"," ").title()}</div>
      <div class="signal-body">{ev}</div>
      <span class="signal-badge {bc}">{lbl}: {bl}</span>
      <span class="signal-badge badge-score">Score {score}</span>
    </div>""", unsafe_allow_html=True)

def feed_card(row):
    url  = str(row.get("url",""))
    t    = str(row.get("title","Untitled"))[:72]
    src  = str(row.get("source_name",""))
    date = str(row.get("published_date",""))[:10]
    snip = str(row.get("content",""))[:110]+"…"
    sent = row.get("sentiment",0.0)
    link = f'<a href="{url}" target="_blank">{t}</a>' if url else f'<b>{t}</b>'
    st.markdown(f"""
    <div class="feed-card">
      <div>{link}</div>
      <div class="feed-meta">{src} · {date}
        <span class="sent-pill {s_class(sent)}" style="margin-left:6px;">{s_label(sent)}</span>
      </div>
      <div class="feed-snip">{snip}</div>
    </div>""", unsafe_allow_html=True)


# ── load ──────────────────────────────────────────────────────────────────────
df       = load_data()
stock_df = load_stock()
report   = load_report()
rag      = report.get("rag",{})          if report else {}
corpus   = report.get("corpus_stats",{}) if report else {}
intel    = rag.get("intelligence",{})
llm_rep  = rag.get("report","")
llm_ok   = rag.get("llm_success",False)
llm_err  = rag.get("llm_error","")
ag_log   = rag.get("agent_log",[])
ag_dec   = rag.get("decisions",[])
ag_goal  = rag.get("goal","")
ag_plan  = rag.get("plan",[])
ag_valid = rag.get("validated",False)

opps   = intel.get("opportunities",[])
risks  = intel.get("risks",[])
trends = intel.get("trends",[])
avg_s  = df["sentiment"].mean()

close_col = next((c for c in stock_df.columns if "close" in c.lower()),None) if not stock_df.empty else None

news_df = df[df["source_category"]=="news"].sort_values("collected_at",ascending=False).drop_duplicates("title").head(6)
comp_df = df[df["content"].str.lower().str.contains("boeing|competitor|competition|rival",na=False)].drop_duplicates("title").head(6)
tech_df = df[df["topic"]=="technology"].sort_values("collected_at",ascending=False).drop_duplicates("title").head(6)
ann_df  = df[df["source_category"]=="company"].sort_values("collected_at",ascending=False).drop_duplicates("title").head(6)

news_s = df[df["source_category"]=="news"]["sentiment"].mean() if "source_category" in df.columns else 0.0
res_s  = df[df["source_category"]=="research"]["sentiment"].mean() if "source_category" in df.columns else 0.0
com_s  = df[df["source_category"]=="company"]["sentiment"].mean() if "source_category" in df.columns else 0.0


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">✈️ &nbsp; Airbus </div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Overview", "Market Intelligence", "Opportunities",
         "Risks & Trends", "Sentiment", "Recommendations", "CEO Briefing", "💬 Ask the Agent"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # status
    if report:
        gen_at = report.get("generated_at","")
        st.markdown(f'<div style="font-size:11px;color:#AEAEB2;">Last report<br>'
                    f'<span style="color:#1C1C1E;font-weight:600;">{fmt_ts(gen_at)}</span></div>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:11px;color:#AEAEB2;">Chunks indexed<br>'
                    f'<span style="color:#1C1C1E;font-weight:600;">{corpus.get("total_chunks",0):,}</span></div>',
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        val = "✅ Validated" if ag_valid else "⚠️ Unvalidated"
        st.markdown(f'<div style="font-size:11px;color:#AEAEB2;">Agent status<br>'
                    f'<span style="color:#1C1C1E;font-weight:600;">{val}</span></div>',
                    unsafe_allow_html=True)
    else:
        st.warning("No report. Run generate_report.py", icon="⚠️")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reload", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── page: Overview ────────────────────────────────────────────────────────────
if page == "Overview":
    st.markdown('<div class="page-eyebrow">Strategic Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Airbus Executive Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-meta">Aerospace & Defence &nbsp;·&nbsp; AIR.PA &nbsp;·&nbsp; '
        f'{corpus.get("total_sources",0)} sources &nbsp;·&nbsp; '
        f'{corpus.get("total_documents",0)} documents</div>',
        unsafe_allow_html=True)

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    def stat(col, label, value, sub="", cls=""):
        col.markdown(f'<div class="stat-card {cls}"><div class="stat-label">{label}</div>'
                     f'<div class="stat-value">{value}</div>'
                     f'<div class="stat-sub">{sub}</div></div>', unsafe_allow_html=True)

    stat(c1, "Documents", corpus.get("total_documents",0), f'{corpus.get("total_chunks",0)} chunks')
    stat(c2, "Opportunities", len(opps), "detected signals", "accent-teal")
    stat(c3, "Risks", len(risks), "detected signals", "accent-red")
    stat(c4, "Sentiment", f"{avg_s:.2f}", s_label(avg_s))

    st.markdown("<br>", unsafe_allow_html=True)

    # # stock — recalculate close_col here to avoid None bug
    # close_col_ov = next((c for c in stock_df.columns if "close" in c.lower()), None) if not stock_df.empty else None
    # if not stock_df.empty and close_col_ov and "Date" in stock_df.columns:
    #     close_col = close_col_ov
    #     st.markdown('<div class="section-label">Stock Performance · AIR.PA</div>', unsafe_allow_html=True)
    #     latest = stock_df.iloc[-1]; prev = stock_df.iloc[-2] if len(stock_df)>1 else latest
    #     price = latest[close_col]; chg = price - prev[close_col]
    #     pct   = (chg/prev[close_col])*100 if prev[close_col] else 0
    #     s1,s2,s3,s4 = st.columns(4)
    #     s1.metric("Latest Close", f"€{price:.2f}", f"{chg:+.2f} ({pct:+.2f}%)")
    #     s2.metric("As of", str(latest["Date"])[:10])
    #     hc = next((c for c in stock_df.columns if "high" in c.lower()),None)
    #     lc = next((c for c in stock_df.columns if "low"  in c.lower()),None)
    #     if hc: s3.metric("52W High", f"€{stock_df[hc].max():.2f}")
    #     if lc: s4.metric("52W Low",  f"€{stock_df[lc].min():.2f}")

    #     fig = px.area(stock_df, x="Date", y=close_col)
    #     fig.update_traces(line_color="#C41E3A", line_width=1.5,
    #                       fillcolor="rgba(196,30,58,0.06)")
    #     fig.update_layout(height=280, margin=dict(t=0,b=0,l=0,r=0),
    #                       xaxis_title="", yaxis_title="",
    #                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    #     fig.update_xaxes(gridcolor="#F2F2F0", showline=False)
    #     fig.update_yaxes(gridcolor="#F2F2F0", showline=False)
    #     st.plotly_chart(fig, use_container_width=True)

    # # agent summary
    # if ag_goal:
    #     st.markdown('<div class="section-label">Agent Execution Summary</div>', unsafe_allow_html=True)
    #     st.markdown(f'<div style="font-size:13px;color:#636366;margin-bottom:12px;">{ag_goal}</div>',
    #                 unsafe_allow_html=True)
    #     chips = "".join(
    #         f'<div class="agent-chip active">'
    #         f'{"✅" if i < len(ag_plan)-1 else "🔒"} {s.replace("_"," ").title()}</div>'
    #         for i,s in enumerate(ag_plan)
    #     )
    #     st.markdown(f'<div class="agent-row">{chips}</div>', unsafe_allow_html=True)
    #     if ag_dec:
    #         d = ag_dec[0]; color = "#0E7A6E" if "PROCEED" in d.get("decision","") else "#B45309"
    #         st.markdown(
    #             f'<div style="font-size:12px;color:{color};font-weight:600;">'
    #             f'{d["decision"]}</div>'
    #             f'<div style="font-size:12px;color:#8E8E93;">{d["reasoning"]}</div>',
    #             unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Source breakdown"):
        sdc = df.groupby("source_name")["parent_id"].nunique().reset_index()
        sdc.columns = ["Source","Documents"]
        sdc = sdc.sort_values("Documents",ascending=False)
        st.dataframe(sdc, use_container_width=True, hide_index=True)


# ── page: Market Intelligence ─────────────────────────────────────────────────
elif page == "Market Intelligence":
    st.markdown('<div class="page-eyebrow">Section 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Market Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-meta">Live feeds from news, company, research and competitor sources.</div>', unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        tdc = df.groupby("topic")["parent_id"].nunique().reset_index().sort_values("parent_id",ascending=True)
        tdc.columns = ["Topic","Documents"]
        fig = px.bar(tdc, x="Documents", y="Topic", orientation="h",
                     color="Documents", color_continuous_scale=["#E8E8E4","#1C1C1E"])
        fig.update_layout(title="Documents by Topic", height=300, coloraxis_showscale=False,
                          margin=dict(t=30,b=0,l=0,r=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(gridcolor="#F2F2F0"); fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if close_col and "Date" in stock_df.columns:
            fig = px.line(stock_df.tail(90), x="Date", y=close_col)
            fig.update_traces(line_color="#C41E3A", line_width=1.5)
            fig.update_layout(title="AIR.PA — 90 Day", height=300,
                              margin=dict(t=30,b=0,l=0,r=0), xaxis_title="", yaxis_title="€",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(gridcolor="#F2F2F0"); fig.update_yaxes(gridcolor="#F2F2F0")
            st.plotly_chart(fig, use_container_width=True)

    f1,f2,f3,f4 = st.columns(4)
    with f1:
        st.markdown('<div class="section-label">Recent News</div>', unsafe_allow_html=True)
        for _,r in news_df.iterrows(): feed_card(r)
    with f2:
        st.markdown('<div class="section-label">Competitor Activity</div>', unsafe_allow_html=True)
        if not comp_df.empty:
            for _,r in comp_df.iterrows(): feed_card(r)
        else:
            st.caption("No competitor mentions found.")
    with f3:
        st.markdown('<div class="section-label">Emerging Technology</div>', unsafe_allow_html=True)
        for _,r in tech_df.iterrows(): feed_card(r)
    with f4:
        st.markdown('<div class="section-label">Company Announcements</div>', unsafe_allow_html=True)
        for _,r in ann_df.iterrows(): feed_card(r)


# ── page: Opportunities ───────────────────────────────────────────────────────
elif page == "Opportunities":
    st.markdown('<div class="page-eyebrow">Section 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Opportunity Monitor</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-meta">{len(opps)} opportunities detected from retrieved evidence.</div>', unsafe_allow_html=True)
    if opps:
        for item in opps[:5]: signal_card(item,"opportunity")
    else:
        st.info("No opportunities detected — run generate_report.py first.")


# ── page: Risks & Trends ──────────────────────────────────────────────────────
elif page == "Risks & Trends":
    st.markdown('<div class="page-eyebrow">Section 4</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Risks & Trends</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-meta">{len(risks)} risks · {len(trends)} trends detected.</div>',
        unsafe_allow_html=True)

    rt1, rt2 = st.tabs(["⚠️ Risk Monitor", "📈 Trend Monitor"])

    with rt1:
        st.markdown("<br>", unsafe_allow_html=True)
        if risks:
            for item in risks[:5]: signal_card(item, "risk")
        else:
            st.info("No risks detected — run generate_report.py first.")

    with rt2:
        st.markdown("<br>", unsafe_allow_html=True)
        if trends:
            for item in trends[:5]: signal_card(item, "trend")
        else:
            st.info("No trends detected — run generate_report.py first.")


# ── page: Sentiment ───────────────────────────────────────────────────────────
elif page == "Sentiment":
    st.markdown('<div class="page-eyebrow">Section 5</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Sentiment Analysis</div>', unsafe_allow_html=True)

    s1,s2,s3,s4 = st.columns(4)
    def sent_stat(col, score, label):
        color = s_color(score)
        col.markdown(
            f'<div class="stat-card"><div class="stat-label">{label}</div>'
            f'<div class="stat-value" style="color:{color};font-size:22px;">{score:.3f}</div>'
            f'<div class="stat-sub">{s_label(score)}</div></div>',
            unsafe_allow_html=True)
    sent_stat(s1, avg_s,  "Overall")
    sent_stat(s2, news_s, "News")
    sent_stat(s3, res_s,  "Research")
    sent_stat(s4, com_s,  "Company")

    st.markdown("<br>", unsafe_allow_html=True)
    ch2,ch3 = st.columns(2)

    # with ch1:
    #     st_topic = df.groupby("topic")["sentiment"].mean().reset_index().sort_values("sentiment")
    #     st_topic.columns = ["Topic","Sentiment"]
    #     fig = go.Figure(go.Bar(
    #         x=st_topic["Sentiment"], y=st_topic["Topic"], orientation="h",
    #         marker_color=[s_color(s) for s in st_topic["Sentiment"]],
    #         text=[f"{s:.2f}" for s in st_topic["Sentiment"]], textposition="outside"))
    #     fig.add_vline(x=0, line_dash="dot", line_color="#E8E8E4")
    #     fig.update_layout(title="By Topic", height=340, margin=dict(t=30,b=0,l=0,r=0),
    #                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    #     st.plotly_chart(fig, use_container_width=True)

    with ch2:
        df["sc"] = df["sentiment"].apply(lambda s: "Positive" if s>0.08 else ("Negative" if s<-0.08 else "Neutral"))
        dist = df["sc"].value_counts().reset_index(); dist.columns = ["s","c"]
        fig = px.pie(dist, names="s", values="c", hole=0.55,
                     color="s", color_discrete_map={"Positive":"#0E7A6E","Negative":"#C41E3A","Neutral":"#AEAEB2"})
        fig.update_traces(textinfo="label+percent", textfont_size=12)
        fig.update_layout(title="Distribution", height=340, showlegend=False,
                          margin=dict(t=30,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with ch3:
        if "source_category" in df.columns:
            ss = df.groupby("source_category")["sentiment"].mean().reset_index()
            ss.columns = ["Source","Sentiment"]
            fig = go.Figure(go.Bar(
                x=ss["Source"], y=ss["Sentiment"],
                marker_color=[s_color(s) for s in ss["Sentiment"]],
                text=[f"{s:.2f}" for s in ss["Sentiment"]], textposition="outside"))
            fig.add_hline(y=0, line_dash="dot", line_color="#E8E8E4")
            fig.update_layout(title="By Source", height=340, margin=dict(t=30,b=0,l=0,r=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    # stock + sentiment overlay
    if not stock_df.empty and close_col and "Date" in stock_df.columns:
        st.markdown('<div class="section-label">Stock Price vs News Sentiment</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df[close_col],
                                 name="AIR.PA (€)", line=dict(color="#C41E3A",width=1.5), yaxis="y1"))
        if "published_date" in df.columns:
            st2 = df.copy()
            st2["published_date"] = pd.to_datetime(st2["published_date"],errors="coerce")
            st2 = st2.dropna(subset=["published_date"]).sort_values("published_date")
            sr  = st2.set_index("published_date")["sentiment"].resample("W").mean().reset_index()
            sr.columns = ["Date","Sentiment"]
            fig.add_trace(go.Scatter(x=sr["Date"],y=sr["Sentiment"],
                                     name="Weekly Sentiment",
                                     line=dict(color="#0E7A6E",width=1.5,dash="dot"), yaxis="y2"))
        fig.update_layout(height=300, margin=dict(t=0,b=0,l=0,r=0),
                          yaxis=dict(title="Price (€)",side="left"),
                          yaxis2=dict(title="Sentiment",side="right",overlaying="y",zeroline=True,zerolinecolor="#E8E8E4"),
                          legend=dict(orientation="h",y=1.08),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(gridcolor="#F2F2F0"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label">Coverage Highlights</div>', unsafe_allow_html=True)
    h1,h2 = st.columns(2)
    with h1:
        st.caption("Most positive")
        for _,r in df.nlargest(5,"sentiment")[["title","sentiment","url"]].iterrows():
            url=str(r.get("url","")); t=str(r.get("title",""))[:65]; sc=r["sentiment"]
            link = f'<a href="{url}" target="_blank">{t}</a>' if url else t
            st.markdown(f'<span class="sent-pill sent-pos">+{sc:.2f}</span> '
                        f'<span style="font-size:13px;color:#3A3A3C;">{link}</span><br>',
                        unsafe_allow_html=True)
    with h2:
        st.caption("Most negative")
        for _,r in df.nsmallest(5,"sentiment")[["title","sentiment","url"]].iterrows():
            url=str(r.get("url","")); t=str(r.get("title",""))[:65]; sc=r["sentiment"]
            link = f'<a href="{url}" target="_blank">{t}</a>' if url else t
            st.markdown(f'<span class="sent-pill sent-neg">{sc:.2f}</span> '
                        f'<span style="font-size:13px;color:#3A3A3C;">{link}</span><br>',
                        unsafe_allow_html=True)


# ── page: Recommendations ─────────────────────────────────────────────────────
elif page == "Recommendations":
    st.markdown('<div class="page-eyebrow">Section 6</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Strategic Recommendations</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-meta">Evidence-backed recommendations generated by the CEO Agent.</div>', unsafe_allow_html=True)

    if llm_rep:
        rec = extract_recommendations(llm_rep)
        scrollable(rec)
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇️ Download", data=rec,
                           file_name="airbus_recommendations.txt", mime="text/plain")
    elif not llm_ok and llm_err:
        st.error(f"LLM failed: `{llm_err}`\n\nEnsure Ollama is running then re-run generate_report.py", icon="🚫")
    else:
        st.info("Run `python generate_report.py` first.")


# ── page: CEO Briefing ────────────────────────────────────────────────────────
elif page == "CEO Briefing":
    st.markdown('<div class="page-eyebrow">Section 7</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">CEO Briefing</div>', unsafe_allow_html=True)

    q1,q2,q3 = st.columns(3)
    for col, eyebrow, body, bg, border in [
        (q1, "What happened?",              "Latest signals from news, research & market data.", "#F2F2F0", "#AEAEB2"),
        (q2, "Why does it matter?",         "Strategic implications for Airbus's position.",    "#F0FDF4", "#0E7A6E"),
        (q3, "What should management do?",  "Prioritized actions with evidence backing.",        "#FEF3C7", "#B45309"),
    ]:
        col.markdown(
            f'<div style="background:{bg};border-left:3px solid {border};'
            f'border-radius:10px;padding:14px 16px;">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:1px;'
            f'text-transform:uppercase;color:{border};margin-bottom:4px;">{eyebrow}</div>'
            f'<div style="font-size:13px;color:#3A3A3C;">{body}</div></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if llm_rep:
        briefing = extract_ceo_briefing(llm_rep)
        scrollable(briefing)
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇️ Download CEO Briefing", data=briefing,
                           file_name="airbus_ceo_briefing.txt", mime="text/plain")
    elif not llm_ok and llm_err:
        st.error(f"LLM failed: `{llm_err}`", icon="🚫")
    else:
        st.info("Run `python generate_report.py` first.")


# ── page: Ask the Agent ───────────────────────────────────────────────────────
elif page == "💬 Ask the Agent":
    render_qa()