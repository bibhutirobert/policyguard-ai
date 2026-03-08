# =============================================================================
# PolicyGuard AI — utils/data_manager.py
#
# Responsible for all data I/O and in-memory state management:
#   • Creating and validating the complaint log schema
#   • Appending new analysis results to the log
#   • Persisting and reloading from CSV
#   • Loading the sample dataset
#   • Computing KPI summary statistics
#
# Design rationale:
#   Keeping all DataFrame operations here means app.py and the analysis
#   module remain free of pandas logic and the data contract is enforced
#   in one place.
# =============================================================================

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from utils.config import (
    CATEGORY_OPTIONS,
    COMPLAINT_LOG_COLUMNS,
    COMPLAINTS_LOG_PATH,
    ESCALATION_OPTIONS,
    SAMPLE_DATA_PATH,
    SENTIMENT_OPTIONS,
    URGENCY_OPTIONS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema defaults — applied when a key is missing from an analysis result
# ---------------------------------------------------------------------------

_FIELD_DEFAULTS: dict[str, Any] = {
    "complaint_id":               "",
    "complaint_text":             "",
    "policy_type":                "Unknown",
    "sentiment":                  "Unknown",
    "complaint_category":         "Other",
    "urgency_level":              "Unknown",
    "escalation_risk":            "Unknown",
    "risk_score":                 0,
    "recommended_response":       "",
    "key_issues":                 "",
    "estimated_resolution_days":  0,
    "confidence_score":           0,
    "analyzed_at":                "",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_str() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _new_complaint_id() -> str:
    """Generate a short, sortable complaint identifier (e.g. CMP-3f2a)."""
    return f"CMP-{uuid.uuid4().hex[:6].upper()}"


def _serialise_key_issues(key_issues: list[str] | str) -> str:
    """
    Normalise key_issues to a comma-separated string for CSV storage.

    Parameters
    ----------
    key_issues : list[str] | str
        Raw value from the AI analysis dict.

    Returns
    -------
    str
        Comma-separated string, or the original if already a string.
    """
    if isinstance(key_issues, list):
        return "; ".join(str(i).strip() for i in key_issues if str(i).strip())
    return str(key_issues).strip()


# ---------------------------------------------------------------------------
# DataFrame construction
# ---------------------------------------------------------------------------

def get_empty_log() -> pd.DataFrame:
    """
    Return an empty DataFrame with the canonical complaint log schema.

    Using a typed empty frame ensures that concat operations never produce
    unexpected column mismatches or mixed dtypes.

    Returns
    -------
    pd.DataFrame
        Zero-row DataFrame with all COMPLAINT_LOG_COLUMNS present.
    """
    return pd.DataFrame(columns=COMPLAINT_LOG_COLUMNS)


def build_log_row(
    complaint_text: str,
    analysis: dict[str, Any],
    policy_type: str = "Unknown",
) -> dict[str, Any]:
    """
    Construct a single log row dict from raw analysis output.

    Applies defaults for any missing fields, generates a unique complaint ID,
    and normalises the key_issues field to a string.

    Parameters
    ----------
    complaint_text : str
        The original complaint submitted by the user.
    analysis : dict
        Result dict from ``utils.analysis.analyze_complaint``.
        May contain an ``"error"`` key if the analysis failed.
    policy_type : str
        Optional policy type label (Motor, Health, Life, etc.).

    Returns
    -------
    dict
        Row-ready dict matching the COMPLAINT_LOG_COLUMNS schema.
    """
    row = dict(_FIELD_DEFAULTS)          # start from defaults
    row.update(analysis)                 # overlay real values

    # Always set these regardless of what the AI returned
    row["complaint_id"]   = _new_complaint_id()
    row["complaint_text"] = complaint_text.strip()
    row["policy_type"]    = policy_type or "Unknown"
    row["analyzed_at"]    = _now_str()
    row["key_issues"]     = _serialise_key_issues(row.get("key_issues", ""))

    # Map renamed AI keys → log column names if needed
    # (AI returns "complaint_category"; old schema used "category")
    if "category" in row and "complaint_category" not in row:
        row["complaint_category"] = row.pop("category")
    if "urgency" in row and "urgency_level" not in row:
        row["urgency_level"] = row.pop("urgency")
    if "suggested_response" in row and "recommended_response" not in row:
        row["recommended_response"] = row.pop("suggested_response")

    # Keep only known columns
    return {k: row.get(k, _FIELD_DEFAULTS.get(k, "")) for k in COMPLAINT_LOG_COLUMNS}


def append_to_log(
    log_df: pd.DataFrame,
    complaint_text: str,
    analysis: dict[str, Any],
    policy_type: str = "Unknown",
) -> pd.DataFrame:
    """
    Append a single analysed complaint to the in-memory session log.

    Parameters
    ----------
    log_df : pd.DataFrame
        Current session log.
    complaint_text : str
        Raw complaint text.
    analysis : dict
        Analysis result from ``analyze_complaint``.
    policy_type : str
        Optional policy type label.

    Returns
    -------
    pd.DataFrame
        Updated log with the new row appended.
    """
    row = build_log_row(complaint_text, analysis, policy_type)
    new_df = pd.DataFrame([row])
    return pd.concat([log_df, new_df], ignore_index=True)


def append_batch_to_log(
    log_df: pd.DataFrame,
    source_df: pd.DataFrame,
    results: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Merge a list of batch analysis results into the session log.

    Parameters
    ----------
    log_df : pd.DataFrame
        Current session log.
    source_df : pd.DataFrame
        Original uploaded CSV (used to extract policy_type if available).
    results : list[dict]
        One result dict per row from ``analyze_batch``.

    Returns
    -------
    pd.DataFrame
        Updated log with all batch rows appended.
    """
    rows: list[dict] = []
    for i, result in enumerate(results):
        text = result.get("complaint_text", "")
        policy = ""
        if "policy_type" in source_df.columns and i < len(source_df):
            policy = str(source_df.iloc[i].get("policy_type", ""))
        rows.append(build_log_row(text, result, policy))

    if not rows:
        return log_df

    batch_df = pd.DataFrame(rows)
    return pd.concat([log_df, batch_df], ignore_index=True)


# ---------------------------------------------------------------------------
# CSV persistence
# ---------------------------------------------------------------------------

def save_log(log_df: pd.DataFrame, path: str = COMPLAINTS_LOG_PATH) -> bool:
    """
    Persist the current complaint log to a CSV file.

    Creates the file if it does not exist; appends if it does — so previous
    session data is never overwritten.

    Parameters
    ----------
    log_df : pd.DataFrame
        DataFrame to persist.
    path : str
        Destination file path.

    Returns
    -------
    bool
        True on success, False on I/O error.
    """
    try:
        file_path = Path(path)
        write_header = not file_path.exists() or file_path.stat().st_size == 0
        log_df.to_csv(path, mode="a", header=write_header, index=False)
        logger.info("Complaint log saved to %s (%d rows)", path, len(log_df))
        return True
    except OSError as exc:
        logger.error("Failed to save complaint log: %s", exc)
        return False


def load_log(path: str = COMPLAINTS_LOG_PATH) -> pd.DataFrame:
    """
    Load a previously saved complaint log CSV.

    Returns an empty log frame if the file does not exist or cannot be parsed.

    Parameters
    ----------
    path : str
        CSV file path to load.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame, or an empty log frame on failure.
    """
    file_path = Path(path)
    if not file_path.exists():
        logger.debug("No existing log at %s — starting fresh.", path)
        return get_empty_log()

    try:
        df = pd.read_csv(path)
        # Ensure all expected columns exist (handles schema migrations)
        for col in COMPLAINT_LOG_COLUMNS:
            if col not in df.columns:
                df[col] = _FIELD_DEFAULTS.get(col, "")
        logger.info("Loaded %d complaints from %s", len(df), path)
        return df[COMPLAINT_LOG_COLUMNS]
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load complaint log from %s: %s", path, exc)
        return get_empty_log()


# ---------------------------------------------------------------------------
# Sample dataset loader
# ---------------------------------------------------------------------------

def load_sample_data(path: str = SAMPLE_DATA_PATH) -> pd.DataFrame:
    """
    Load the bundled sample complaints CSV.

    Parameters
    ----------
    path : str
        Path to the sample CSV file.

    Returns
    -------
    pd.DataFrame
        Sample complaints, or an empty DataFrame on error.
    """
    try:
        df = pd.read_csv(path)
        logger.info("Loaded %d sample complaints from %s", len(df), path)
        return df
    except FileNotFoundError:
        logger.error("Sample data file not found: %s", path)
        return pd.DataFrame()
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load sample data: %s", exc)
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# KPI & summary statistics
# ---------------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute high-level KPI metrics from the complaint log DataFrame.

    All metrics gracefully handle empty DataFrames and missing columns.

    Parameters
    ----------
    df : pd.DataFrame
        Analysed complaint log.

    Returns
    -------
    dict with keys:
        total, avg_risk_score, high_urgency_count, critical_count,
        escalation_high_count, top_category, dominant_sentiment,
        avg_resolution_days, avg_confidence
    """
    empty_kpis: dict[str, Any] = {
        "total":                0,
        "avg_risk_score":       0.0,
        "high_urgency_count":   0,
        "critical_count":       0,
        "escalation_high_count":0,
        "top_category":         "N/A",
        "dominant_sentiment":   "N/A",
        "avg_resolution_days":  0.0,
        "avg_confidence":       0.0,
    }

    if df is None or df.empty:
        return empty_kpis

    # Filter to rows that were successfully analysed
    valid = df[df["risk_score"] > 0].copy()
    if valid.empty:
        return empty_kpis

    def _mode_col(col: str) -> str:
        if col not in valid.columns:
            return "N/A"
        vc = valid[col].value_counts()
        return vc.idxmax() if not vc.empty else "N/A"

    def _count_where(col: str, values: list[str]) -> int:
        if col not in valid.columns:
            return 0
        return int(valid[col].isin(values).sum())

    return {
        "total":                 len(df),
        "avg_risk_score":        round(float(valid["risk_score"].mean()), 1),
        "high_urgency_count":    _count_where("urgency_level", ["High", "Critical"]),
        "critical_count":        _count_where("urgency_level", ["Critical"]),
        "escalation_high_count": _count_where("escalation_risk", ["High"]),
        "top_category":          _mode_col("complaint_category"),
        "dominant_sentiment":    _mode_col("sentiment"),
        "avg_resolution_days":   round(
            float(valid["estimated_resolution_days"].mean()), 1
        ) if "estimated_resolution_days" in valid.columns else 0.0,
        "avg_confidence":        round(
            float(valid["confidence_score"].mean()), 1
        ) if "confidence_score" in valid.columns else 0.0,
    }


# ---------------------------------------------------------------------------
# Filtering helper
# ---------------------------------------------------------------------------

def filter_log(
    df: pd.DataFrame,
    category: str = "All",
    urgency: str = "All",
    sentiment: str = "All",
    escalation: str = "All",
    min_risk: int = 0,
    max_risk: int = 100,
) -> pd.DataFrame:
    """
    Apply multi-dimensional filters to the complaint log DataFrame.

    "All" means no filter is applied for that dimension.

    Parameters
    ----------
    df : pd.DataFrame
    category : str
    urgency : str
    sentiment : str
    escalation : str
    min_risk : int
    max_risk : int

    Returns
    -------
    pd.DataFrame
        Filtered subset of the input DataFrame.
    """
    result = df.copy()

    col_map = {
        "complaint_category": category,
        "urgency_level":      urgency,
        "sentiment":          sentiment,
        "escalation_risk":    escalation,
    }
    for col, val in col_map.items():
        if val != "All" and col in result.columns:
            result = result[result[col] == val]

    if "risk_score" in result.columns:
        result = result[
            result["risk_score"].between(min_risk, max_risk)
        ]

    return result
