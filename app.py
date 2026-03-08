# =============================================================================
# PolicyGuard AI — app.py  (v2.0)
# Entry point for the Streamlit application.
#
# Architecture
# ────────────
# app.py is intentionally thin: it handles only Streamlit page structure,
# session state, and user interactions.  All business logic is delegated to:
#
#   utils/config.py         — constants, colours, prompt
#   utils/analysis.py       — OpenAI API calls & retry logic
#   utils/data_manager.py   — DataFrame I/O and KPI computation
#   utils/visualization.py  — Plotly chart builders and HTML components
#
# Run:  streamlit run app.py
# =============================================================================

import logging
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from utils import (
    APP_ICON,
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    EMPTY_DASHBOARD_MSG,
    ESCALATION_COLOURS,
    PLACEHOLDER_COMPLAINT,
    SENTIMENT_COLOURS,
    URGENCY_COLOURS,
    analyze_batch,
    analyze_complaint,
    append_batch_to_log,
    append_to_log,
    analysis_summary_card,
    badge,
    chart_avg_risk_by_category,
    chart_category_bar,
    chart_escalation_pie,
    chart_risk_histogram,
    chart_risk_over_time,
    chart_sentiment_donut,
    chart_urgency_bar,
    compute_kpis,
    escalation_card_html,
    filter_log,
    get_empty_log,
    load_log,
    load_sample_data,
    save_log,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment — load .env before any st.* call
# ---------------------------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------------------------
# Page config  (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS — dark-navy enterprise theme
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700&display=swap');

:root {
    --navy:       #0B1628;
    --navy-mid:   #112240;
    --navy-light: #1A3356;
    --teal:       #00C9B1;
    --teal-dim:   #00A896;
    --amber:      #F5A623;
    --red:        #E5534B;
    --green:      #3DD68C;
    --blue:       #4A9EFF;
    --text:       #E8EDF5;
    --muted:      #8B9BB4;
    --border:     rgba(0,201,177,0.14);
    --card:       rgba(17,34,64,0.88);
    --shadow:     0 4px 24px rgba(0,0,0,0.38);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--navy) !important;
    color: var(--text) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.6rem 2.2rem 3rem !important; max-width: 1440px; }

section[data-testid="stSidebar"] {
    background: var(--navy-mid) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

.pg-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    box-shadow: var(--shadow);
    backdrop-filter: blur(6px);
    margin-bottom: 1.1rem;
}

.kpi-tile {
    background: var(--navy-mid);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.3rem;
    text-align: center;
    box-shadow: var(--shadow);
    transition: border-color 0.2s;
}
.kpi-tile:hover { border-color: rgba(0,201,177,0.35); }
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--teal);
    line-height: 1.1;
}
.kpi-label {
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}

.pg-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    color: var(--text);
    border-left: 4px solid var(--teal);
    padding-left: 0.7rem;
    margin: 1.4rem 0 0.85rem;
}

div[data-testid="stTabs"] button {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--teal) !important;
    border-bottom-color: var(--teal) !important;
}

textarea, .stTextArea textarea {
    background: var(--navy-mid) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.91rem !important;
}
textarea:focus, .stTextArea textarea:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 2px rgba(0,201,177,0.18) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--teal), var(--teal-dim)) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.52rem 1.6rem !important;
    font-size: 0.88rem !important;
    transition: opacity 0.2s, transform 0.15s !important;
}
.stButton > button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important;
box-shadow: 0 3px 10px rgba(0,201,177,0.35); }

div[data-testid="stSelectbox"] > div > div {
    background: var(--navy-mid) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}

.stDataFrame { border-radius: 10px !important; overflow: hidden; }
.stProgress > div > div > div > div { background: var(--teal) !important; }
.stAlert { border-radius: 10px !important; }
hr { border-color: var(--border) !important; margin: 1.4rem 0 !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--navy-mid); }
::-webkit-scrollbar-thumb { background: var(--navy-light); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--teal-dim); }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_session() -> None:
    defaults = {
        "complaint_log":        get_empty_log(),
        "last_analysis":        None,
        "last_complaint_text":  "",
        "last_policy_type":     "Unknown",
        "sample_prefill":       None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0 0.4rem;">
      <div style="font-size:2.4rem;">{APP_ICON}</div>
      <div style="font-family:'Playfair Display',serif;font-size:1.2rem;
                  font-weight:700;color:#E8EDF5;margin-top:0.3rem;">{APP_NAME}</div>
      <div style="font-size:0.7rem;color:#8B9BB4;letter-spacing:0.1em;
                  text-transform:uppercase;margin-top:0.15rem;">{APP_SUBTITLE}</div>
      <div style="font-size:0.66rem;color:#4A9EFF;margin-top:0.2rem;">v{APP_VERSION}</div>
    </div>
    <hr/>
    """, unsafe_allow_html=True)

    # API key
    st.markdown("**🔑 OpenAI API Key**")
    api_input = st.text_input(
        "api_key_field", type="password",
        placeholder="sk-…",
        help="Stored in session memory only — never logged or persisted.",
        label_visibility="collapsed",
    )
    if api_input:
        os.environ["OPENAI_API_KEY"] = api_input.strip()
        st.success("API key active ✓", icon="✅")
    elif os.getenv("OPENAI_API_KEY"):
        st.success("Key loaded from environment ✓", icon="✅")
    else:
        st.warning("No API key detected", icon="⚠️")
        st.caption("Enter key above or add `OPENAI_API_KEY` to `.env`.")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Session KPIs
    log  = st.session_state.complaint_log
    kpis = compute_kpis(log)

    st.markdown("**📊 Session Overview**")
    sc1, sc2 = st.columns(2)
    sc1.metric("Analysed",     kpis["total"])
    sc2.metric("Avg Risk",     f"{kpis['avg_risk_score']}")
    sc3, sc4 = st.columns(2)
    sc3.metric("High Urgency", kpis["high_urgency_count"])
    sc4.metric("Critical",     kpis["critical_count"])

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Data management
    st.markdown("**💾 Data Management**")
    if st.button("💾 Save Log to CSV", use_container_width=True):
        if log.empty:
            st.warning("Nothing to save yet.")
        elif save_log(log):
            st.success("Saved to `complaints_log.csv` ✓")
        else:
            st.error("Save failed — check file permissions.")

    if st.button("📂 Load Previous Log", use_container_width=True):
        loaded = load_log()
        if loaded.empty:
            st.info("No saved log found.")
        else:
            st.session_state.complaint_log = loaded
            st.success(f"Loaded {len(loaded)} complaints ✓")
            st.rerun()

    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.complaint_log      = get_empty_log()
        st.session_state.last_analysis      = None
        st.session_state.last_complaint_text = ""
        st.rerun()

    st.markdown("""
    <div style="font-size:0.67rem;color:#6B7A99;text-align:center;
                padding-top:1.6rem;line-height:1.7;">
        Powered by OpenAI GPT<br/>
        Built with Streamlit + Plotly<br/>
        © 2024 Insurance Ops Intelligence
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown(f"""
<div style="margin-bottom:0.4rem;">
  <div style="font-family:'Playfair Display',serif;font-size:2rem;
              font-weight:700;color:#E8EDF5;line-height:1.1;">
    PolicyGuard <span style="color:#00C9B1;">AI</span>
  </div>
  <div style="font-size:0.83rem;color:#8B9BB4;margin-top:0.2rem;">
    {APP_SUBTITLE} &nbsp;·&nbsp; Operations Intelligence Dashboard
  </div>
</div>
<hr/>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_analyser, tab_dashboard, tab_log = st.tabs([
    "🔍  Complaint Analyser",
    "📈  Analytics Dashboard",
    "📋  Complaint Log",
])


# ============================================================================
# TAB 1 — COMPLAINT ANALYSER
# ============================================================================

with tab_analyser:

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown('<div class="pg-title">Submit Complaint</div>',
                    unsafe_allow_html=True)

        prefill        = st.session_state.pop("sample_prefill", None) or ""
        complaint_text = st.text_area(
            "complaint_input",
            value=prefill,
            placeholder=PLACEHOLDER_COMPLAINT,
            height=210,
            label_visibility="collapsed",
        )

        policy_type = st.selectbox(
            "Policy Type (optional)",
            ["Unknown", "Health", "Life", "Motor", "Property", "Travel", "General"],
        )

        btn1, btn2   = st.columns(2)
        analyse_btn  = btn1.button(" Analyse",     use_container_width=True)
        sample_btn   = btn2.button(" Load Sample", use_container_width=True)

        if sample_btn:
            sample_df = load_sample_data()
            if not sample_df.empty and "complaint_text" in sample_df.columns:
                row = sample_df.sample(1).iloc[0]
                st.session_state["sample_prefill"] = row["complaint_text"]
                st.rerun()
            else:
                st.error("Could not load `sample_complaints.csv`.")

        # Batch upload
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown('<div class="pg-title">Batch CSV Upload</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Upload a CSV with a `complaint_text` column. "
            "An optional `policy_type` column is supported."
        )

        uploaded = st.file_uploader("batch_csv", type=["csv"],
                                    label_visibility="collapsed")

        if uploaded:
            try:
                batch_df = pd.read_csv(uploaded)
            except Exception as exc:
                st.error(f"Cannot read CSV: {exc}")
                batch_df = pd.DataFrame()

            if not batch_df.empty:
                if "complaint_text" not in batch_df.columns:
                    st.error("CSV must contain a `complaint_text` column.")
                else:
                    st.success(f"✓ Loaded **{len(batch_df)}** complaints.")
                    if st.button("🚀 Run Batch Analysis", use_container_width=True):
                        if not os.getenv("OPENAI_API_KEY"):
                            st.error("Enter your API key in the sidebar first.")
                        else:
                            progress_bar = st.progress(0, text="Starting…")

                            def _cb(cur: int, tot: int) -> None:
                                progress_bar.progress(
                                    cur / tot,
                                    text=f"Analysing {cur} of {tot}…",
                                )

                            with st.spinner("Running batch…"):
                                results = analyze_batch(batch_df, progress_callback=_cb)
                            progress_bar.empty()

                            st.session_state.complaint_log = append_batch_to_log(
                                st.session_state.complaint_log, batch_df, results
                            )
                            errors = sum(1 for r in results if "error" in r)
                            st.success(
                                f"✅ **{len(results) - errors}** analysed, "
                                f"**{errors}** failed."
                            )

    with right_col:
        st.markdown('<div class="pg-title">Analysis Results</div>',
                    unsafe_allow_html=True)

        if analyse_btn:
            if not complaint_text.strip():
                st.warning("Please enter complaint text.", icon="⚠️")
            elif not os.getenv("OPENAI_API_KEY"):
                st.error("No API key — enter it in the sidebar.", icon="🔑")
            else:
                with st.spinner("Analysing with AI…"):
                    result = analyze_complaint(complaint_text)

                if "error" in result:
                    st.error(f"**Analysis failed:** {result['error']}", icon="❌")
                else:
                    st.session_state.last_analysis       = result
                    st.session_state.last_complaint_text = complaint_text
                    st.session_state.last_policy_type    = policy_type
                    st.session_state.complaint_log = append_to_log(
                        st.session_state.complaint_log,
                        complaint_text,
                        result,
                        policy_type,
                    )
                    st.success("Analysis complete ✓", icon="✅")

        analysis = st.session_state.last_analysis

        if analysis and "error" not in analysis:
            # Badges
            st.markdown(
                f"""
                <div style="display:flex;flex-wrap:wrap;gap:10px;margin:0.8rem 0;">
                  <div>
                    <div style="font-size:0.68rem;text-transform:uppercase;
                                letter-spacing:0.09em;color:#8B9BB4;margin-bottom:4px;">
                      Sentiment</div>
                    {badge(analysis.get("sentiment","—"), SENTIMENT_COLOURS)}
                  </div>
                  <div>
                    <div style="font-size:0.68rem;text-transform:uppercase;
                                letter-spacing:0.09em;color:#8B9BB4;margin-bottom:4px;">
                      Urgency Level</div>
                    {badge(analysis.get("urgency_level","—"), URGENCY_COLOURS)}
                  </div>
                  <div>
                    <div style="font-size:0.68rem;text-transform:uppercase;
                                letter-spacing:0.09em;color:#8B9BB4;margin-bottom:4px;">
                      Escalation Risk</div>
                    {badge(analysis.get("escalation_risk","—"), ESCALATION_COLOURS)}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Full summary card
            st.markdown(analysis_summary_card(analysis), unsafe_allow_html=True)

            # Raw JSON
            with st.expander("🔎 View raw AI response JSON"):
                st.json(analysis)

        else:
            st.markdown("""
            <div style="border:2px dashed rgba(0,201,177,0.18);border-radius:14px;
                        padding:3.5rem 2rem;text-align:center;margin-top:0.8rem;">
              <div style="font-size:2.8rem;margin-bottom:0.9rem;">🔍</div>
              <div style="font-size:1rem;color:#8B9BB4;font-weight:500;">
                Submit a complaint to see the AI analysis
              </div>
              <div style="font-size:0.8rem;color:#6B7A99;margin-top:0.5rem;line-height:1.6;">
                Sentiment · Category · Urgency · Risk Score<br/>
                Key Issues · Recommended Response · AI Confidence
              </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# TAB 2 — ANALYTICS DASHBOARD
# ============================================================================

with tab_dashboard:

    log  = st.session_state.complaint_log
    kpis = compute_kpis(log)

    # Primary KPIs
    st.markdown('<div class="pg-title">Key Performance Indicators</div>',
                unsafe_allow_html=True)

    kpi_cols = st.columns(5)
    for col, (val, lbl) in zip(kpi_cols, [
        (kpis["total"],              "Total Complaints"),
        (kpis["avg_risk_score"],     "Avg Risk Score"),
        (kpis["high_urgency_count"], "High / Critical"),
        (kpis["top_category"],       "Top Category"),
        (kpis["dominant_sentiment"], "Dominant Sentiment"),
    ]):
        with col:
            st.markdown(
                f'<div class="kpi-tile">'
                f'<div class="kpi-value">{val}</div>'
                f'<div class="kpi-label">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Secondary KPIs
    st.markdown("<br/>", unsafe_allow_html=True)
    sec_cols = st.columns(4)
    for col, (val, lbl) in zip(sec_cols, [
        (kpis["critical_count"],         "Critical Complaints"),
        (kpis["escalation_high_count"],  "High Escalation Risk"),
        (kpis["avg_resolution_days"],    "Avg Resolution Days"),
        (kpis["avg_confidence"],         "Avg AI Confidence %"),
    ]):
        with col:
            st.markdown(
                f'<div class="kpi-tile">'
                f'<div class="kpi-value">{val}</div>'
                f'<div class="kpi-label">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    if log.empty or kpis["total"] == 0:
        st.info(EMPTY_DASHBOARD_MSG, icon="ℹ️")
    else:
        _no_bar = {"displayModeBar": False}

        r1a, r1b = st.columns(2, gap="large")
        with r1a:
            st.plotly_chart(chart_category_bar(log),    use_container_width=True, config=_no_bar)
        with r1b:
            st.plotly_chart(chart_sentiment_donut(log), use_container_width=True, config=_no_bar)

        r2a, r2b = st.columns(2, gap="large")
        with r2a:
            st.plotly_chart(chart_urgency_bar(log),     use_container_width=True, config=_no_bar)
        with r2b:
            st.plotly_chart(chart_risk_histogram(log),  use_container_width=True, config=_no_bar)

        r3a, r3b = st.columns(2, gap="large")
        with r3a:
            st.plotly_chart(chart_escalation_pie(log),          use_container_width=True, config=_no_bar)
        with r3b:
            st.plotly_chart(chart_avg_risk_by_category(log),    use_container_width=True, config=_no_bar)

        if len(log) >= 3:
            st.plotly_chart(chart_risk_over_time(log), use_container_width=True, config=_no_bar)


# ============================================================================
# TAB 3 — COMPLAINT LOG
# ============================================================================

with tab_log:

    log = st.session_state.complaint_log

    st.markdown('<div class="pg-title">Complaint Log</div>',
                unsafe_allow_html=True)

    if log.empty:
        st.info("No complaints analysed yet. Go to the **Complaint Analyser** tab.", icon="📋")
    else:
        # Filters
        fc1, fc2, fc3, fc4 = st.columns(4)

        all_cats  = ["All"] + sorted(log["complaint_category"].dropna().unique().tolist())
        all_urgs  = ["All"] + [u for u in ["Critical","High","Medium","Low","Unknown"]
                               if u in log["urgency_level"].values]
        all_sents = ["All"] + sorted(log["sentiment"].dropna().unique().tolist())
        all_escs  = ["All"] + sorted(log["escalation_risk"].dropna().unique().tolist())

        sel_cat  = fc1.selectbox("Category",   all_cats)
        sel_urg  = fc2.selectbox("Urgency",    all_urgs)
        sel_sent = fc3.selectbox("Sentiment",  all_sents)
        sel_esc  = fc4.selectbox("Escalation", all_escs)

        min_r, max_r = st.slider(
            "Risk Score Range", 0, 100, (0, 100), step=5
        )

        filtered = filter_log(
            log,
            category=sel_cat,
            urgency=sel_urg,
            sentiment=sel_sent,
            escalation=sel_esc,
            min_risk=min_r,
            max_risk=max_r,
        )

        st.caption(
            f"Showing **{len(filtered)}** of **{len(log)}** complaints "
            f"· sorted by risk score (highest first)"
        )

        display_cols = [c for c in [
            "complaint_id", "complaint_text", "policy_type",
            "sentiment", "complaint_category", "urgency_level",
            "escalation_risk", "risk_score",
            "estimated_resolution_days", "analyzed_at",
        ] if c in filtered.columns]

        st.dataframe(
            filtered[display_cols]
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
            height=400,
        )

        dl1, dl2 = st.columns(2)
        dl1.download_button(
            "⬇️ Export Filtered Log",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="policyguard_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
        dl2.download_button(
            "⬇️ Export Full Log",
            data=log.to_csv(index=False).encode("utf-8"),
            file_name="policyguard_full_log.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Top 5 escalation risks
        st.markdown('<div class="pg-title">🚨 Top 5 Escalation Risks</div>',
                    unsafe_allow_html=True)

        top5 = (
            filtered[filtered["risk_score"] > 0]
            .sort_values("risk_score", ascending=False)
            .head(5)
        )
        if top5.empty:
            st.info("No analysed complaints match the current filter.", icon="🔎")
        else:
            for _, row in top5.iterrows():
                st.markdown(escalation_card_html(row.to_dict()), unsafe_allow_html=True)
