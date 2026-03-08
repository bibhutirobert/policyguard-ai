# =============================================================================
# PolicyGuard AI — utils/visualization.py
#
# All Plotly chart builders and HTML rendering helpers.
#
# Design rationale:
#   Every chart is a pure function: DataFrame in, Plotly Figure out.
#   This makes charts independently testable and reusable, and keeps
#   app.py free of visualisation logic.
# =============================================================================

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.config import (
    CHART_COLOUR_SCALE,
    ESCALATION_COLOURS,
    RISK_SCORE_THRESHOLDS,
    SENTIMENT_COLOURS,
    URGENCY_COLOURS,
)

# ---------------------------------------------------------------------------
# Shared Plotly layout defaults (dark-navy theme)
# ---------------------------------------------------------------------------

_BASE_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#8B9BB4"),
    margin=dict(l=12, r=20, t=32, b=12),
    height=300,
)

_AXIS_DEFAULTS = dict(
    showgrid=False,
    zeroline=False,
    tickfont=dict(color="#8B9BB4"),
)

_GRID_AXIS = dict(
    showgrid=True,
    gridcolor="rgba(255,255,255,0.06)",
    zeroline=False,
    tickfont=dict(color="#8B9BB4"),
)


def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply the shared dark-navy layout to any Plotly figure."""
    layout = dict(_BASE_LAYOUT)
    if title:
        layout["title"] = dict(
            text=title,
            font=dict(color="#E8EDF5", size=14),
            x=0,
            xanchor="left",
            pad=dict(l=4),
        )
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Individual chart builders
# ---------------------------------------------------------------------------

def chart_category_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart of complaint volume by category.

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``complaint_category`` column.

    Returns
    -------
    go.Figure
    """
    counts = (
        df["complaint_category"]
        .value_counts()
        .reset_index(name="count")
        .rename(columns={"complaint_category": "category"})
        .sort_values("count")
    )

    fig = px.bar(
        counts,
        x="count",
        y="category",
        orientation="h",
        color="count",
        color_continuous_scale=CHART_COLOUR_SCALE,
        text="count",
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#E8EDF5", size=11),
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>%{x} complaints<extra></extra>",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(**_AXIS_DEFAULTS)
    fig.update_yaxes(**dict(_AXIS_DEFAULTS, tickfont=dict(color="#E8EDF5")))
    return _apply_base(fig, "Complaint Categories")


def chart_sentiment_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart of sentiment distribution.

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``sentiment`` column.

    Returns
    -------
    go.Figure
    """
    counts  = df["sentiment"].value_counts()
    colours = [SENTIMENT_COLOURS.get(s, "#6B7A99") for s in counts.index]
    total   = counts.sum()

    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.62,
        marker=dict(colors=colours, line=dict(color="#0B1628", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#E8EDF5", size=11),
        hovertemplate="<b>%{label}</b><br>%{value} complaints (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        annotations=[dict(
            text=f"<b>{total}</b><br><span style='font-size:11px'>total</span>",
            x=0.5, y=0.5,
            font=dict(size=18, color="#E8EDF5"),
            showarrow=False,
        )],
    )
    return _apply_base(fig, "Sentiment Distribution")


def chart_urgency_bar(df: pd.DataFrame) -> go.Figure:
    """
    Vertical bar chart of urgency level distribution.

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``urgency_level`` column.

    Returns
    -------
    go.Figure
    """
    order   = ["Critical", "High", "Medium", "Low", "Unknown"]
    counts  = (
        df["urgency_level"]
        .value_counts()
        .reindex(order, fill_value=0)
        .reset_index(name="count")
        .rename(columns={"urgency_level": "urgency"})
    )

    fig = px.bar(
        counts,
        x="urgency",
        y="count",
        color="urgency",
        color_discrete_map=URGENCY_COLOURS,
        text="count",
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#E8EDF5", size=11),
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>%{y} complaints<extra></extra>",
    )
    fig.update_xaxes(**dict(_AXIS_DEFAULTS, tickfont=dict(color="#E8EDF5")))
    fig.update_yaxes(**_GRID_AXIS)
    fig.update_layout(showlegend=False)
    return _apply_base(fig, "Urgency Levels")


def chart_risk_histogram(df: pd.DataFrame) -> go.Figure:
    """
    Histogram of risk score distribution.

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``risk_score`` column.

    Returns
    -------
    go.Figure
    """
    valid = df[df["risk_score"] > 0]

    fig = px.histogram(
        valid,
        x="risk_score",
        nbins=10,
        color_discrete_sequence=["#00C9B1"],
    )
    fig.update_traces(
        marker_line_width=0,
        opacity=0.85,
        hovertemplate="Score %{x}<br>%{y} complaints<extra></extra>",
    )
    fig.update_xaxes(**dict(_AXIS_DEFAULTS, title="Risk Score",
                            title_font=dict(color="#8B9BB4")))
    fig.update_yaxes(**dict(_GRID_AXIS, title="# Complaints",
                            title_font=dict(color="#8B9BB4")))
    return _apply_base(fig, "Risk Score Distribution")


def chart_escalation_pie(df: pd.DataFrame) -> go.Figure:
    """
    Pie chart of escalation risk breakdown.

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``escalation_risk`` column.

    Returns
    -------
    go.Figure
    """
    counts  = df["escalation_risk"].value_counts().reset_index(name="count")
    counts.rename(columns={"escalation_risk": "level"}, inplace=True)
    colours = [ESCALATION_COLOURS.get(l, "#6B7A99") for l in counts["level"]]

    fig = go.Figure(go.Pie(
        labels=counts["level"],
        values=counts["count"],
        marker=dict(colors=colours, line=dict(color="#0B1628", width=2)),
        textinfo="label+value",
        textfont=dict(color="#E8EDF5", size=11),
        hovertemplate="<b>%{label}</b><br>%{value} complaints<extra></extra>",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(font=dict(color="#E8EDF5", size=11)),
    )
    return _apply_base(fig, "Escalation Risk Breakdown")


def chart_avg_risk_by_category(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart of average risk score per complaint category.

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``complaint_category`` and ``risk_score``.

    Returns
    -------
    go.Figure
    """
    avg = (
        df[df["risk_score"] > 0]
        .groupby("complaint_category")["risk_score"]
        .mean()
        .round(1)
        .sort_values()
        .reset_index(name="avg_risk")
        .rename(columns={"complaint_category": "category"})
    )

    fig = px.bar(
        avg,
        x="avg_risk",
        y="category",
        orientation="h",
        color="avg_risk",
        color_continuous_scale=["#3DD68C", "#F5A623", "#E5534B"],
        text="avg_risk",
        range_color=[0, 100],
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#E8EDF5", size=11),
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Avg risk: %{x}<extra></extra>",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(**dict(_AXIS_DEFAULTS, range=[0, 115]))
    fig.update_yaxes(**dict(_AXIS_DEFAULTS, tickfont=dict(color="#E8EDF5")))
    return _apply_base(fig, "Avg Risk Score by Category")


def chart_risk_over_time(df: pd.DataFrame) -> go.Figure:
    """
    Line chart of average risk score over time (by analysis date).

    Parameters
    ----------
    df : pd.DataFrame  — must contain ``analyzed_at`` and ``risk_score``.

    Returns
    -------
    go.Figure
    """
    valid = df[df["risk_score"] > 0].copy()
    valid["date"] = pd.to_datetime(valid["analyzed_at"], errors="coerce").dt.date
    trend = (
        valid.groupby("date")["risk_score"]
        .mean()
        .round(1)
        .reset_index(name="avg_risk")
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["date"],
        y=trend["avg_risk"],
        mode="lines+markers",
        line=dict(color="#00C9B1", width=2.5),
        marker=dict(color="#00C9B1", size=7),
        fill="tozeroy",
        fillcolor="rgba(0,201,177,0.08)",
        hovertemplate="<b>%{x}</b><br>Avg risk: %{y}<extra></extra>",
        name="Avg Risk",
    ))
    fig.update_xaxes(**dict(_AXIS_DEFAULTS, tickfont=dict(color="#8B9BB4")))
    fig.update_yaxes(**dict(_GRID_AXIS, range=[0, 105]))
    return _apply_base(fig, "Risk Score Trend Over Time")


# ---------------------------------------------------------------------------
# HTML badge and UI component helpers
# ---------------------------------------------------------------------------

def badge(label: str, colour_map: dict[str, str]) -> str:
    """
    Render a coloured HTML pill badge for use in ``st.markdown``.

    Parameters
    ----------
    label : str
        The text to display inside the badge.
    colour_map : dict
        Maps label strings to hex colour codes.

    Returns
    -------
    str
        HTML string; render with ``unsafe_allow_html=True``.
    """
    colour = colour_map.get(label, "#6B7A99")
    return (
        f'<span style="background:{colour};color:#fff;padding:3px 11px;'
        f'border-radius:20px;font-size:12px;font-weight:600;'
        f'letter-spacing:0.03em;">{label}</span>'
    )


def risk_colour(score: int) -> str:
    """
    Map a numeric risk score to a hex colour.

    Parameters
    ----------
    score : int  (1–100)

    Returns
    -------
    str  hex colour code
    """
    for threshold, colour in RISK_SCORE_THRESHOLDS:
        if score >= threshold:
            return colour
    return "#6B7A99"


def risk_gauge_html(score: int) -> str:
    """
    Return an HTML risk gauge bar with the score overlaid.

    Parameters
    ----------
    score : int  (1–100)

    Returns
    -------
    str
        Self-contained HTML block for ``st.markdown``.
    """
    colour = risk_colour(score)
    return f"""
<div style="margin-top:4px;">
  <div style="display:flex;justify-content:space-between;
              align-items:baseline;margin-bottom:6px;">
    <span style="font-size:0.72rem;text-transform:uppercase;
                 letter-spacing:0.1em;color:#8B9BB4;">Escalation Risk Score</span>
    <span style="font-family:'DM Mono',monospace;font-size:1.6rem;
                 font-weight:700;color:{colour};">{score}</span>
  </div>
  <div style="background:#1A3356;border-radius:99px;height:10px;width:100%;">
    <div style="width:{score}%;background:{colour};height:10px;
                border-radius:99px;transition:width .5s ease;"></div>
  </div>
  <div style="display:flex;justify-content:space-between;
              font-size:0.68rem;color:#6B7A99;margin-top:4px;">
    <span>Low Risk (1)</span><span>Critical (100)</span>
  </div>
</div>
"""


def analysis_summary_card(analysis: dict[str, Any]) -> str:
    """
    Build a full HTML summary card for a single analysis result.

    Produces the category/resolution header, risk gauge, key issues pills,
    and recommended response block.  The badges row is rendered separately
    via ``badge()`` so it can sit outside the card.

    Parameters
    ----------
    analysis : dict
        Validated analysis dict from ``utils.analysis.analyze_complaint``.

    Returns
    -------
    str
        HTML string for ``st.markdown(..., unsafe_allow_html=True)``.
    """
    category    = analysis.get("complaint_category", "—")
    res_days    = analysis.get("estimated_resolution_days", "—")
    response    = analysis.get("recommended_response", "No recommendation available.")
    confidence  = analysis.get("confidence_score", 0)
    key_issues  = analysis.get("key_issues", [])
    score       = analysis.get("risk_score", 0)

    # Key issues — normalise to list
    if isinstance(key_issues, str):
        issues_list = [i.strip() for i in key_issues.split(";") if i.strip()]
    else:
        issues_list = list(key_issues)

    issue_pills = "".join(
        f'<span style="display:inline-block;background:rgba(245,166,35,0.15);'
        f'border:1px solid rgba(245,166,35,0.4);color:#F5A623;'
        f'border-radius:20px;padding:2px 12px;font-size:0.77rem;'
        f'margin:3px 3px 3px 0;">{issue}</span>'
        for issue in issues_list
    )

    conf_colour = "#3DD68C" if confidence >= 75 else "#F5A623" if confidence >= 50 else "#E5534B"

    return f"""
<div style="background:rgba(17,34,64,0.85);border:1px solid rgba(0,201,177,0.15);
            border-radius:14px;padding:1.3rem 1.5rem;
            box-shadow:0 4px 24px rgba(0,0,0,0.35);margin-bottom:1rem;">

  <!-- Category / Resolution row -->
  <div style="display:flex;justify-content:space-between;
              align-items:center;margin-bottom:1rem;">
    <div>
      <div style="font-size:0.7rem;text-transform:uppercase;
                  letter-spacing:0.1em;color:#8B9BB4;margin-bottom:3px;">
        Complaint Category
      </div>
      <div style="font-size:1.05rem;font-weight:600;color:#00C9B1;">
        {category}
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:0.7rem;text-transform:uppercase;
                  letter-spacing:0.1em;color:#8B9BB4;margin-bottom:3px;">
        Est. Resolution
      </div>
      <div style="font-size:1.05rem;font-weight:600;color:#F5A623;">
        {res_days} business days
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:0.7rem;text-transform:uppercase;
                  letter-spacing:0.1em;color:#8B9BB4;margin-bottom:3px;">
        AI Confidence
      </div>
      <div style="font-size:1.05rem;font-weight:600;color:{conf_colour};">
        {confidence}%
      </div>
    </div>
  </div>

  <!-- Risk gauge -->
  {risk_gauge_html(score)}

  <!-- Key issues -->
  {f'<div style="margin-top:1rem;"><div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#8B9BB4;margin-bottom:6px;">Key Issues Identified</div>{issue_pills}</div>' if issues_list else ""}

  <!-- Recommended response -->
  <div style="margin-top:1rem;">
    <div style="font-size:0.7rem;text-transform:uppercase;
                letter-spacing:0.1em;color:#8B9BB4;margin-bottom:6px;">
      Recommended Response Strategy
    </div>
    <div style="background:rgba(0,201,177,0.07);border-left:3px solid #00C9B1;
                border-radius:0 10px 10px 0;padding:0.85rem 1.1rem;
                font-size:0.91rem;color:#E8EDF5;line-height:1.65;font-style:italic;">
      {response}
    </div>
  </div>

</div>
"""


def escalation_card_html(row: dict[str, Any]) -> str:
    """
    Render a compact escalation risk card for the Top-5 list.

    Parameters
    ----------
    row : dict
        A single row from the complaint log as a dict.

    Returns
    -------
    str
        HTML string.
    """
    score   = int(row.get("risk_score", 0))
    colour  = risk_colour(score)
    text    = str(row.get("complaint_text", ""))
    snippet = (text[:185] + "…") if len(text) > 185 else text
    cat     = row.get("complaint_category", row.get("category", "—"))
    urg     = row.get("urgency_level", row.get("urgency", "—"))
    cid     = row.get("complaint_id", "")

    return f"""
<div style="background:rgba(17,34,64,0.85);border:1px solid rgba(0,201,177,0.12);
            border-left:4px solid {colour};border-radius:0 12px 12px 0;
            padding:1rem 1.2rem;box-shadow:0 3px 16px rgba(0,0,0,0.3);
            margin-bottom:0.8rem;">
  <div style="display:flex;justify-content:space-between;
              align-items:flex-start;gap:1rem;">
    <div style="flex:1;">
      <div style="font-size:0.68rem;color:#6B7A99;margin-bottom:4px;">
        {cid}
      </div>
      <div style="font-size:0.86rem;color:#E8EDF5;line-height:1.55;">
        "{snippet}"
      </div>
      <div style="margin-top:6px;font-size:0.77rem;color:#8B9BB4;">
        Category: <b style="color:#00C9B1;">{cat}</b>
        &nbsp;·&nbsp;
        Urgency: <b style="color:#F5A623;">{urg}</b>
      </div>
    </div>
    <div style="text-align:center;min-width:56px;">
      <div style="font-family:'DM Mono',monospace;font-size:1.7rem;
                  font-weight:700;color:{colour};line-height:1;">{score}</div>
      <div style="font-size:0.65rem;color:#6B7A99;text-transform:uppercase;
                  letter-spacing:0.07em;margin-top:2px;">risk</div>
    </div>
  </div>
</div>
"""
