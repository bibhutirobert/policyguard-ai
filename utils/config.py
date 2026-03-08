# =============================================================================
# PolicyGuard AI — utils/config.py
#
# Single source of truth for all application-wide constants, enumerations,
# colour palettes, and OpenAI prompt templates.
#
# Design rationale:
#   Centralising configuration here means that changing a label, colour, or
#   prompt requires editing exactly ONE file, not hunting across the codebase.
# =============================================================================

from __future__ import annotations

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------

APP_NAME        = "PolicyGuard AI"
APP_VERSION     = "2.0.0"
APP_SUBTITLE    = "Insurance Complaint Intelligence System"
APP_ICON        = "🛡️"

# ---------------------------------------------------------------------------
# OpenAI settings
# ---------------------------------------------------------------------------

OPENAI_MODEL        = "gpt-3.5-turbo"
OPENAI_TEMPERATURE  = 0.2       # Low = deterministic, consistent categorisation
OPENAI_MAX_TOKENS   = 600

# ---------------------------------------------------------------------------
# Data schema
# ---------------------------------------------------------------------------

# Canonical column order for the complaint log DataFrame and CSV exports.
COMPLAINT_LOG_COLUMNS: list[str] = [
    "complaint_id",
    "complaint_text",
    "policy_type",
    "sentiment",
    "complaint_category",
    "urgency_level",
    "escalation_risk",
    "risk_score",
    "recommended_response",
    "key_issues",
    "estimated_resolution_days",
    "confidence_score",
    "analyzed_at",
]

# Default CSV path for persisting the session log between reruns
COMPLAINTS_LOG_PATH = "complaints_log.csv"

# Path to the bundled sample dataset
SAMPLE_DATA_PATH = "sample_complaints.csv"

# ---------------------------------------------------------------------------
# Controlled vocabularies  (must match the AI prompt exactly)
# ---------------------------------------------------------------------------

SENTIMENT_OPTIONS: list[str] = [
    "Positive",
    "Neutral",
    "Negative",
    "Very Negative",
]

CATEGORY_OPTIONS: list[str] = [
    "Claim Delay",
    "Policy Mis-selling",
    "Documentation Issue",
    "Service Complaint",
    "Premium Dispute",
    "Coverage Dispute",
    "Fraud Suspicion",
    "Settlement Dispute",
    "Other",
]

URGENCY_OPTIONS: list[str] = ["Low", "Medium", "High", "Critical"]

ESCALATION_OPTIONS: list[str] = ["Low", "Medium", "High"]

# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------

# Used for HTML badges and Plotly charts — dark-navy theme
SENTIMENT_COLOURS: dict[str, str] = {
    "Positive":      "#3DD68C",
    "Neutral":       "#4A9EFF",
    "Negative":      "#F5A623",
    "Very Negative": "#E5534B",
    "Unknown":       "#6B7A99",
}

URGENCY_COLOURS: dict[str, str] = {
    "Low":      "#3DD68C",
    "Medium":   "#F5A623",
    "High":     "#FF7043",
    "Critical": "#E5534B",
    "Unknown":  "#6B7A99",
}

ESCALATION_COLOURS: dict[str, str] = {
    "Low":     "#3DD68C",
    "Medium":  "#F5A623",
    "High":    "#E5534B",
    "Unknown": "#6B7A99",
}

# Plotly continuous scale for category/risk charts
CHART_COLOUR_SCALE = ["#1A3356", "#00C9B1"]

# Risk gauge thresholds → (min_score, hex_colour)
RISK_SCORE_THRESHOLDS: list[tuple[int, str]] = [
    (86, "#E5534B"),   # Critical
    (61, "#FF7043"),   # High
    (31, "#F5A623"),   # Medium
    (0,  "#3DD68C"),   # Low
]

# ---------------------------------------------------------------------------
# OpenAI system prompt
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM_PROMPT: str = """
You are a senior insurance complaints analyst at a large multi-line insurance company.
Your role is to triage incoming customer complaints and produce structured intelligence
reports that help the operations team prioritise, escalate, and resolve issues.

INSTRUCTIONS
────────────
• Read the complaint carefully before classifying.
• Return ONLY a valid JSON object — no preamble, no commentary, no markdown fences.
• Every field is mandatory. Never omit a key or return null.
• All string fields must match the allowed values exactly (case-sensitive).

OUTPUT SCHEMA
─────────────
{
  "sentiment": <one of: "Positive" | "Neutral" | "Negative" | "Very Negative">,

  "complaint_category": <one of:
      "Claim Delay" | "Policy Mis-selling" | "Documentation Issue" |
      "Service Complaint" | "Premium Dispute" | "Coverage Dispute" |
      "Fraud Suspicion" | "Settlement Dispute" | "Other">,

  "urgency_level": <one of: "Low" | "Medium" | "High" | "Critical">,

  "escalation_risk": <one of: "Low" | "Medium" | "High">,

  "risk_score": <integer 1–100, see scoring guide below>,

  "recommended_response": <string — 2–3 sentence action plan for the ops team,
      including who should act and within what timeframe>,

  "key_issues": <array of 3–5 short strings, each under 8 words,
      identifying the distinct problems raised>,

  "estimated_resolution_days": <integer — realistic business-day estimate>,

  "confidence_score": <integer 1–100 — your confidence in this classification>
}

RISK SCORE GUIDE
────────────────
 1 –  30 → Routine complaint; standard SLA, no escalation needed.
31 –  60 → Moderate concern; supervisor review within 3 days.
61 –  85 → High risk; prompt action, possible legal or regulatory exposure.
86 – 100 → Critical; immediate escalation, churn risk, potential litigation.

URGENCY vs ESCALATION RISK
───────────────────────────
• urgency_level   = how quickly the customer's issue needs to be resolved.
• escalation_risk = how likely this complaint is to escalate to regulator /
                    legal / media if not handled promptly.
These may differ: a routine claim delay (High urgency) may carry Low
escalation risk; a mis-selling accusation may be Medium urgency but
High escalation risk.

Be precise, professional, and consistent across all complaints.
"""

# ---------------------------------------------------------------------------
# UI copy strings (keeps app.py clean)
# ---------------------------------------------------------------------------

PLACEHOLDER_COMPLAINT = (
    "Paste or type the customer complaint here…\n\n"
    "Example: My hospitalisation claim was filed six weeks ago. "
    "Despite submitting all documents twice, I keep receiving automated "
    "rejection emails with no explanation. I am now considering legal action."
)

EMPTY_DASHBOARD_MSG = (
    "📊 No data yet — analyse some complaints in the **Complaint Analyser** "
    "tab to populate the dashboard."
)
