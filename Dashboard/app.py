import sys
import json
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob

PROJECT_ROOT  = Path(__file__).resolve().parents[1]
DATA_FILE     = PROJECT_ROOT / "DataCleaning" / "data" / "processed" / "clean_documents.jsonl"
REPORT_PATH   = PROJECT_ROOT / "reports" / "latest_report.json"
STOCK_CSV     = PROJECT_ROOT / "DataScraping" / "data" / "raw" / "airbus_price_history.csv"

st.set_page_config(page_title="Airbus Executive Intelligence Dashboard", layout="wide")

st.markdown("""
<style>
.main { background-color: #f7f9fc; }
.stButton > button {
    background-color: #D71920; color: white;
    font-size: 18px; font-weight: 700;
    border-radius: 12px; padding: 0.8rem 1rem; border: none;
}
.stButton > button:hover { background-color: #a90000; color: white; }
.section-title {
    font-size: 22px; font-weight: 800;
    margin-top: 20px; margin-bottom: 12px;
    padding-bottom: 6px; border-bottom: 3px solid #D71920;
}
.news-card     { background:white;   border-left:5px solid #2F80ED; padding:14px 16px; border-radius:10px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.comp-card     { background:#FFF8F8; border-left:5px solid #D71920; padding:14px 16px; border-radius:10px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.tech-card     { background:#F3EDFF; border-left:5px solid #7B61FF; padding:14px 16px; border-radius:10px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.announce-card { background:#E8F7EF; border-left:5px solid #1E9E5A; padding:14px 16px; border-radius:10px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.sent-card { background:white; border-radius:12px; padding:18px; text-align:center; box-shadow:0 2px 10px rgba(0,0,0,0.07); margin-bottom:12px; }
.sent-score { font-size:32px; font-weight:800; margin:6px 0; }
.sent-label { font-size:13px; color:#666; text-transform:uppercase; letter-spacing:0.5px; }
</style>
""", unsafe_allow_html=True)


# =========================
# Helpers
# =========================

@st.cache_data
def load_data():
    df = pd.read_json(DATA_FILE, lines=True)
    df["sentiment"]    = df["content"].apply(lambda t: TextBlob(str(t)).sentiment.polarity)
    df["subjectivity"] = df["content"].apply(lambda t: TextBlob(str(t)).sentiment.subjectivity)
    return df

@st.cache_data
def load_stock() -> pd.DataFrame:
    if STOCK_CSV.exists():
        try:
            df = pd.read_csv(STOCK_CSV)
            df.columns = [c.strip() for c in df.columns]
            date_col = next((c for c in df.columns if "date" in c.lower()), None)
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                df = df.rename(columns={date_col: "Date"}).sort_values("Date")
            return df
        except Exception:
            pass
    return pd.DataFrame()

@st.cache_data
def load_report() -> dict | None:
    if REPORT_PATH.exists():
        try:
            return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

def sentiment_label(score):
    if score > 0.08:  return "Positive 😊"
    if score < -0.08: return "Negative ⚠️"
    return "Neutral 😐"

def sentiment_color(score):
    if score > 0.08:  return "#1E9E5A"
    if score < -0.08: return "#D71920"
    return "#F5A623"

def impact_level(score):
    if score >= 8: return "High 🔴"
    if score >= 4: return "Medium 🟠"
    return "Low 🟢"

def extract_recommendations(report: str) -> str:
    """Return ONLY section 6 — Strategic Recommendations."""
    if not report: return "No recommendations found."
    # find start of recommendations
    rec_start = None
    for p in ["6. Strategic Recommendation", "5. Strategic Recommendation",
              "Strategic Recommendation", "Recommendations"]:
        if p.lower() in report.lower():
            rec_start = report.lower().find(p.lower())
            break
    if rec_start is None:
        lines = report.strip().split("\n")
        return "\n".join(lines[len(lines) // 2:]).strip() or report

    # find start of CEO briefing to use as end boundary
    rec_end = None
    for p in ["7. CEO Briefing", "CEO Briefing Summary", "CEO Briefing"]:
        if p.lower() in report.lower():
            idx = report.lower().find(p.lower())
            if idx > rec_start:
                rec_end = idx
                break

    if rec_end:
        return report[rec_start:rec_end].strip()
    return report[rec_start:].strip()


def extract_ceo_briefing(report: str) -> str:
    """Return ONLY section 7 — CEO Briefing (everything after recommendations)."""
    if not report: return "No briefing found."
    # CEO briefing is section 7 — find it directly
    for p in ["7. CEO Briefing", "CEO Briefing Summary", "CEO Briefing"]:
        if p.lower() in report.lower():
            idx = report.lower().find(p.lower())
            briefing = report[idx:].strip()
            if briefing: return briefing

    # fallback: return last quarter of report (likely the briefing)
    lines = report.strip().split("\n")
    return "\n".join(lines[len(lines) * 3 // 4:]).strip() or report


def scrollable_report(text: str, height: int = 500):
    """Display report text in a scrollable styled box."""
    # convert newlines to <br> and bold **text**
    import re
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
    safe = safe.replace("\n", "<br>")
    st.markdown(f"""
    <div style="
        height:{height}px; overflow-y:auto;
        background:#FAFAFA; border:1px solid #E2E8F0;
        border-radius:12px; padding:24px 28px;
        font-size:14.5px; line-height:1.8; color:#1a1a1a;
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.04);
    ">{safe}</div>
    """, unsafe_allow_html=True)

def card(title, subtitle, body, badge=None, card_type="info"):
    colors = {
        "opportunity": "#E8F7EF", "risk": "#FFF3E6",
        "trend": "#EAF2FF", "recommendation": "#F3EDFF", "info": "#FFFFFF",
    }
    border_colors = {
        "opportunity": "#1E9E5A", "risk": "#E67E22",
        "trend": "#2F80ED", "recommendation": "#7B61FF", "info": "#CCCCCC",
    }
    st.markdown(f"""
    <div style="background-color:{colors.get(card_type)};
        border-left:6px solid {border_colors.get(card_type)};
        padding:18px; border-radius:14px; margin-bottom:16px;
        box-shadow:0 2px 10px rgba(0,0,0,0.07);">
        <h4 style="margin-bottom:4px;">{title}</h4>
        <p style="color:#555; margin-top:0;">{subtitle}</p>
        <p style="font-size:15px;">{body}</p>
        {f'<b>{badge}</b>' if badge else ''}
    </div>""", unsafe_allow_html=True)

def feed_item(row, css_class):
    url    = str(row.get("url",""))
    title  = str(row.get("title","Untitled"))[:80]
    source = str(row.get("source_name",""))
    topic  = str(row.get("topic","")).title()
    date   = str(row.get("published_date",""))[:10]
    snip   = str(row.get("content",""))[:130] + "…"
    link   = (f'<a href="{url}" target="_blank" style="color:#1a1a1a;font-weight:600;'
              f'font-size:13px;text-decoration:none;">{title}</a>'
              if url else f'<b style="font-size:13px;">{title}</b>')
    st.markdown(
        f'<div class="{css_class}">{link}'
        f'<div style="font-size:11px;color:#888;margin:3px 0;">{source} · {topic} · {date}</div>'
        f'<div style="font-size:12px;color:#555;">{snip}</div></div>',
        unsafe_allow_html=True)

def sent_kpi(col, score, label):
    color = sentiment_color(score)
    emoji = "😊" if score > 0.08 else ("😟" if score < -0.08 else "😐")
    lbl   = sentiment_label(score).split(" ")[0]
    col.markdown(f"""
    <div class="sent-card">
        <div class="sent-label">{label}</div>
        <div class="sent-score" style="color:{color};">{emoji} {score:.3f}</div>
        <div style="font-size:13px;color:{color};font-weight:600;">{lbl}</div>
    </div>""", unsafe_allow_html=True)


# =========================
# Load Data
# =========================
df          = load_data()
stock_df    = load_stock()
report      = load_report()
rag         = report.get("rag", {})          if report else {}
corpus      = report.get("corpus_stats", {}) if report else {}
intel       = rag.get("intelligence", {})
llm_report  = rag.get("report", "")
llm_success = rag.get("llm_success", False)
llm_error   = rag.get("llm_error", "")

opportunities = intel.get("opportunities", [])
risks         = intel.get("risks", [])
trends        = intel.get("trends", [])
avg_sentiment = df["sentiment"].mean()

news_df    = df[df["source_category"]=="news"].sort_values("collected_at",ascending=False).drop_duplicates("title").head(5)
company_df = df[df["source_category"]=="company"].sort_values("collected_at",ascending=False).drop_duplicates("title").head(5)
tech_df    = df[df["topic"]=="technology"].sort_values("collected_at",ascending=False).drop_duplicates("title").head(5)
comp_df    = df[df["content"].str.lower().str.contains("boeing|competitor|competition|rival",na=False)].drop_duplicates("title").head(5)

news_sent    = df[df["source_category"]=="news"]["sentiment"].mean()     if "source_category" in df.columns else 0.0
public_sent  = df[df["source_category"]=="research"]["sentiment"].mean() if "source_category" in df.columns else 0.0
company_sent = df[df["source_category"]=="company"]["sentiment"].mean()  if "source_category" in df.columns else 0.0
close_col    = next((c for c in stock_df.columns if "close" in c.lower()), None) if not stock_df.empty else None


# =========================
# Header
# =========================
st.markdown("""
<h1 style="margin-bottom:0;">✈️ Airbus Executive Intelligence Dashboard</h1>
<p style="color:#666; font-size:18px;">
Strategic monitoring of opportunities, risks, trends, sentiment, and AI-generated executive recommendations.
</p>
""", unsafe_allow_html=True)

# if report:
#     gen_at = report.get("generated_at","")
#     try:    ts = datetime.datetime.fromisoformat(gen_at).strftime("%d %b %Y · %H:%M")
#     except: ts = gen_at
#     st.caption(f"📁 Report loaded · Generated: {ts}")
# else:
#     st.warning("⚠️ No report found. Run `python generate_report.py` first.", icon="⚠️")

col_btn, col_info = st.columns([1,5])
with col_btn:
    if st.button("🔄 Reload Report"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")


# =========================
# TABS — top 3 + sub 4
# =========================
tab1, tab2, tab3 = st.tabs([
    "📌 Company Overview",
    "📊 Market Intelligence",
    "😊 Sentiment Analysis",
])

st.markdown("---")
st.markdown("#### 📋 Intelligence Reports")
tab4, tab5, tab6, tab7 = st.tabs([
    "🚀 Opportunities",
    "⚠️ Risks & Trends",
    "🎯 Recommendations",
    "🧠 CEO Briefing",
])


# ── TAB 1: Company Overview ───────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">📌 Company Overview</div>', unsafe_allow_html=True)

    k1,k3,k4,k5,k6 = st.columns(5)
    k1.metric("🏢 Company",       "Airbus")
    # k2.metric("🏭 Industry",      "Aerospace & Defense")
    k3.metric("📄 Documents",     df["parent_id"].nunique())
    k4.metric("🌐 Data Sources",  df["source_name"].nunique())
    k5.metric("🚀 Opportunities", len(opportunities))
    k6.metric("⚠️ Risks",         len(risks))

    # st.caption(f"🕒 Last data collected: {str(df['collected_at'].max())[:19]}")
    st.caption(f"📊 Overall market sentiment: {sentiment_label(avg_sentiment)} ({round(avg_sentiment,3)})")

    if not stock_df.empty and close_col and "Date" in stock_df.columns:
        st.markdown("#### 📈 Stock Overview")
        latest = stock_df.iloc[-1]; prev = stock_df.iloc[-2] if len(stock_df)>1 else latest
        price  = latest[close_col]; change = price - prev[close_col]
        pct    = (change/prev[close_col])*100 if prev[close_col] else 0
        sc1,sc2,sc3,sc4 = st.columns(4)
        sc1.metric("AIR.PA Latest Close", f"€{price:.2f}", f"{change:+.2f} ({pct:+.2f}%)")
        sc2.metric("📅 As of", str(latest["Date"])[:10])
        high_col = next((c for c in stock_df.columns if "high" in c.lower()), None)
        low_col  = next((c for c in stock_df.columns if "low"  in c.lower()), None)
        if high_col and low_col:
            sc3.metric("📊 52W High", f"€{stock_df[high_col].max():.2f}")
            sc4.metric("📊 52W Low",  f"€{stock_df[low_col].min():.2f}")

        fig = px.line(stock_df, x="Date", y=close_col, title="📈 Airbus AIR.PA — Full Price History")
        fig.update_traces(line_color="#D71920", line_width=2)
        fig.update_layout(xaxis_title="", yaxis_title="Price (€)",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(gridcolor="#E2E8F0"); fig.update_yaxes(gridcolor="#E2E8F0")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Source breakdown"):
        sdc = df.groupby("source_name")["parent_id"].nunique().reset_index().sort_values("parent_id",ascending=False)
        sdc.columns = ["Source","Documents"]
        st.dataframe(sdc, use_container_width=True, hide_index=True)


# ── TAB 2: Market Intelligence ────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">📊 Market Intelligence</div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1.2,1,1])
    with c1:
        tdc = df.groupby("topic")["parent_id"].nunique().reset_index().sort_values("parent_id",ascending=True)
        tdc.columns = ["Topic","Documents"]
        fig = px.bar(tdc, x="Documents", y="Topic", orientation="h",
                     title="📌 Documents by Strategic Topic", text="Documents",
                     color="Documents", color_continuous_scale=["#93C5FD","#1D4ED8","#00205B"])
        fig.update_layout(xaxis_title="Unique documents", yaxis_title="", height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        sdc = df.groupby("source_name")["parent_id"].nunique().reset_index().sort_values("parent_id",ascending=False)
        sdc.columns = ["Source","Documents"]
        fig = px.pie(sdc, names="Source", values="Documents", title="🌐 Evidence Source Mix", hole=0.45)
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    with c3:
        if close_col and "Date" in stock_df.columns:
            fig = px.line(stock_df.tail(90), x="Date", y=close_col, title="📈 AIR.PA — 90 Day Price")
            fig.update_traces(line_color="#D71920", line_width=2)
            fig.update_layout(height=360, xaxis_title="", yaxis_title="Price (€)",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(gridcolor="#E2E8F0"); fig.update_yaxes(gridcolor="#E2E8F0")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📰 Live Intelligence Feeds")
    mi1,mi2,mi3,mi4 = st.columns(4)

    with mi1:
        st.markdown("##### 📰 Recent News")
        for _,row in news_df.iterrows(): feed_item(row,"news-card")

    with mi2:
        st.markdown("##### 🏁 Competitor Activities")
        if not comp_df.empty:
            for _,row in comp_df.iterrows(): feed_item(row,"comp-card")
        else:
            st.info("No competitor mentions found.")

    with mi3:
        st.markdown("##### 🔬 Emerging Technologies")
        for _,row in tech_df.iterrows(): feed_item(row,"tech-card")

    with mi4:
        st.markdown("##### 📢 Company Announcements")
        for _,row in company_df.iterrows(): feed_item(row,"announce-card")

    with st.expander("📋 All recent intelligence items"):
        recent_df = df.sort_values("collected_at",ascending=False)[
            ["title","source_name","topic","published_date"]].drop_duplicates().head(20)
        st.dataframe(recent_df, use_container_width=True)


# ── TAB 4: Opportunities ─────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">🚀 Opportunity Monitor</div>', unsafe_allow_html=True)
    if opportunities:
        for item in opportunities[:5]:
            score = item["scores"]["opportunity"]
            card(
                title=f"🚀 {item['title']}",
                subtitle=f"Source: {item['source']} | Topic: {item['topic']}",
                body=item["evidence"][:420] + "...",
                badge=f"Impact: {impact_level(score)} | Confidence Score: {score}",
                card_type="opportunity"
            )
    else:
        st.info("No opportunities found — run `python generate_report.py` first.")


# ── TAB 5: Risks & Trends ────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">⚠️ Risk Monitor</div>', unsafe_allow_html=True)
    if risks:
        for item in risks[:5]:
            score = item["scores"]["risk"]
            card(
                title=f"⚠️ {item['title']}",
                subtitle=f"Category: {item['topic']} | Source: {item['source']}",
                body=item["evidence"][:420] + "...",
                badge=f"Severity: {impact_level(score)} | Confidence Score: {score}",
                card_type="risk"
            )
    else:
        st.info("No major risks detected.")

    st.markdown('<div class="section-title">📈 Trend Monitor</div>', unsafe_allow_html=True)
    if trends:
        for item in trends[:5]:
            score = item["scores"]["trend"]
            card(
                title=f"📈 {item['title']}",
                subtitle=f"Source: {item['source']} | Topic: {item['topic']}",
                body=item["evidence"][:420] + "...",
                badge=f"Trend Strength: {impact_level(score)} | Confidence Score: {score}",
                card_type="trend"
            )
    else:
        st.info("No trends detected.")


# ── TAB 3: Sentiment Analysis ────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">😊 Sentiment Analysis</div>', unsafe_allow_html=True)

    sa1,sa2,sa3,sa4 = st.columns(4)
    sent_kpi(sa1, avg_sentiment,  "Overall Sentiment")
    sent_kpi(sa2, news_sent,      "News Sentiment")
    sent_kpi(sa3, public_sent,    "Research / Public")
    sent_kpi(sa4, company_sent,   "Company Sentiment")

    st.markdown("<br>", unsafe_allow_html=True)
    sv2,sv3 = st.columns(2)

  
    with sv2:
        df["sent_cat"] = df["sentiment"].apply(
            lambda s: "Positive 😊" if s>0.08 else ("Negative ⚠️" if s<-0.08 else "Neutral 😐"))
        dist = df["sent_cat"].value_counts().reset_index()
        dist.columns = ["Sentiment","Count"]
        cmap = {"Positive 😊":"#1E9E5A","Negative ⚠️":"#D71920","Neutral 😐":"#F5A623"}
        fig  = px.pie(dist, names="Sentiment", values="Count",
                      title="📊 Sentiment Distribution", hole=0.45,
                      color="Sentiment", color_discrete_map=cmap)
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(showlegend=False, height=360, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with sv3:
        if "source_category" in df.columns:
            st_src = df.groupby("source_category")["sentiment"].mean().reset_index()
            st_src.columns = ["Source","Sentiment"]
            colors_src = [sentiment_color(s) for s in st_src["Sentiment"]]
            fig = go.Figure(go.Bar(x=st_src["Source"], y=st_src["Sentiment"],
                                   marker_color=colors_src,
                                   text=[f"{s:.2f}" for s in st_src["Sentiment"]],
                                   textposition="outside"))
            fig.add_hline(y=0, line_dash="dash", line_color="#999")
            fig.update_layout(title="🌐 Sentiment by Source", height=360,
                              yaxis_title="Sentiment Score", xaxis_title="",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    # stock + sentiment overlay
    # if not stock_df.empty and close_col and "Date" in stock_df.columns:
    #     st.markdown("#### 📈 Stock Price & Sentiment Trend")
    #     fig = go.Figure()
    #     fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df[close_col],
    #                              name="AIR.PA Close (€)",
    #                              line=dict(color="#D71920",width=2), yaxis="y1"))
    #     if "published_date" in df.columns:
    #         st2 = df.copy()
    #         st2["published_date"] = pd.to_datetime(st2["published_date"], errors="coerce")
    #         st2 = st2.dropna(subset=["published_date"]).sort_values("published_date")
    #         sr  = st2.set_index("published_date")["sentiment"].resample("W").mean().reset_index()
    #         sr.columns = ["Date","Sentiment"]
    #         fig.add_trace(go.Scatter(x=sr["Date"], y=sr["Sentiment"],
    #                                  name="Weekly Avg Sentiment",
    #                                  line=dict(color="#2F80ED",width=2,dash="dot"), yaxis="y2"))
    #     fig.update_layout(
    #         height=400,
    #         yaxis =dict(title="Stock Price (€)", side="left"),
    #         yaxis2=dict(title="Sentiment Score", side="right", overlaying="y",
    #                     zeroline=True, zerolinecolor="#ccc"),
    #         legend=dict(orientation="h", y=1.1),
    #         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    #         xaxis=dict(gridcolor="#E2E8F0"),
    #     )
    #     st.plotly_chart(fig, use_container_width=True)

    # headlines
    st.markdown("#### 🔍 Sentiment Highlights")
    sh1,sh2 = st.columns(2)
    with sh1:
        st.markdown("**Most Positive Coverage**")
        for _,row in df.nlargest(5,"sentiment")[["title","source_name","sentiment","url"]].iterrows():
            url=str(row.get("url","")); title=str(row.get("title",""))[:70]; score=row["sentiment"]
            color=sentiment_color(score); link=f'<a href="{url}" target="_blank">{title}</a>' if url else title
            st.markdown(f'<span style="background:{color};color:white;padding:2px 8px;border-radius:10px;'
                        f'font-size:12px;font-weight:700;">+{score:.2f}</span> {link}<br>',
                        unsafe_allow_html=True)
    with sh2:
        st.markdown("**Most Negative Coverage**")
        for _,row in df.nsmallest(5,"sentiment")[["title","source_name","sentiment","url"]].iterrows():
            url=str(row.get("url","")); title=str(row.get("title",""))[:70]; score=row["sentiment"]
            color=sentiment_color(score); link=f'<a href="{url}" target="_blank">{title}</a>' if url else title
            st.markdown(f'<span style="background:{color};color:white;padding:2px 8px;border-radius:10px;'
                        f'font-size:12px;font-weight:700;">{score:.2f}</span> {link}<br>',
                        unsafe_allow_html=True)



# ── TAB 6: Strategic Recommendations ─────────────────────────────────────────
with tab6:
    st.markdown('<div class="section-title">🎯 Strategic Recommendations</div>', unsafe_allow_html=True)
    if llm_report:
        rec = extract_recommendations(llm_report)
        scrollable_report(rec, height=520)
        st.download_button(label="⬇️ Download Recommendations", data=rec,
                           file_name="airbus_recommendations.txt", mime="text/plain",
                           use_container_width=True)
    elif not llm_success and llm_error:
        st.error(f"LLM failed: `{llm_error}`\n\nRun `ollama run llama3.1:8b` then regenerate.", icon="🚫")
    else:
        st.info("Run `python generate_report.py` first.")


# ── TAB 7: CEO Briefing ───────────────────────────────────────────────────────
with tab7:
    st.markdown('<div class="section-title">🧠 CEO Briefing</div>', unsafe_allow_html=True)

    q1,q2,q3 = st.columns(3)
    q1.info("**What happened?**\nLatest signals from news, research & market data.")
    q2.success("**Why does it matter?**\nStrategic implications for Airbus's position.")
    q3.warning("**What should management do next?**\nSee prioritized actions below.")

    st.markdown("<br>", unsafe_allow_html=True)

    if llm_report:
        briefing = extract_ceo_briefing(llm_report)
        scrollable_report(briefing, height=520)
        st.download_button(label="⬇️ Download CEO Briefing", data=briefing,
                           file_name="airbus_ceo_briefing.txt", mime="text/plain",
                           use_container_width=True)
    elif not llm_success and llm_error:
        st.error(f"LLM failed: `{llm_error}`\n\nRun `ollama run llama3.1:8b` then regenerate.", icon="🚫")
    else:
        st.info("Run `python generate_report.py` first.")