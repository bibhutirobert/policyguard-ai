# =============================================================================
# PolicyGuard AI — utils/__init__.py
#
# Exposes a clean, flat public API for the utils package so that app.py
# can use simple imports without knowing the internal module layout.
#
# Example:
#   from utils import analyze_complaint, compute_kpis, chart_category_bar
# =============================================================================

from utils.analysis import analyze_complaint, analyze_batch
from utils.config import (
    APP_ICON,
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    CATEGORY_OPTIONS,
    COMPLAINT_LOG_COLUMNS,
    COMPLAINTS_LOG_PATH,
    EMPTY_DASHBOARD_MSG,
    ESCALATION_COLOURS,
    ESCALATION_OPTIONS,
    PLACEHOLDER_COMPLAINT,
    SAMPLE_DATA_PATH,
    SENTIMENT_COLOURS,
    SENTIMENT_OPTIONS,
    URGENCY_COLOURS,
    URGENCY_OPTIONS,
)
from utils.data_manager import (
    append_batch_to_log,
    append_to_log,
    compute_kpis,
    filter_log,
    get_empty_log,
    load_log,
    load_sample_data,
    save_log,
)
from utils.visualization import (
    analysis_summary_card,
    badge,
    chart_avg_risk_by_category,
    chart_category_bar,
    chart_escalation_pie,
    chart_risk_histogram,
    chart_risk_over_time,
    chart_sentiment_donut,
    chart_urgency_bar,
    escalation_card_html,
    risk_colour,
    risk_gauge_html,
    SENTIMENT_COLOURS,
    URGENCY_COLOURS,
    ESCALATION_COLOURS,
)

__all__ = [
    # analysis
    "analyze_complaint",
    "analyze_batch",
    # config
    "APP_ICON", "APP_NAME", "APP_SUBTITLE", "APP_VERSION",
    "CATEGORY_OPTIONS", "COMPLAINT_LOG_COLUMNS", "COMPLAINTS_LOG_PATH",
    "EMPTY_DASHBOARD_MSG", "ESCALATION_COLOURS", "ESCALATION_OPTIONS",
    "PLACEHOLDER_COMPLAINT", "SAMPLE_DATA_PATH",
    "SENTIMENT_COLOURS", "SENTIMENT_OPTIONS",
    "URGENCY_COLOURS", "URGENCY_OPTIONS",
    # data_manager
    "append_batch_to_log", "append_to_log", "compute_kpis",
    "filter_log", "get_empty_log", "load_log", "load_sample_data", "save_log",
    # visualization
    "analysis_summary_card", "badge",
    "chart_avg_risk_by_category", "chart_category_bar",
    "chart_escalation_pie", "chart_risk_histogram",
    "chart_risk_over_time", "chart_sentiment_donut", "chart_urgency_bar",
    "escalation_card_html", "risk_colour", "risk_gauge_html",
]
