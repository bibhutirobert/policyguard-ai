# =============================================================================
# PolicyGuard AI — utils/analysis.py
#
# OpenAI integration layer.  All API calls, prompt construction, response
# parsing, and retry logic live here so that the rest of the application
# never imports openai directly.
#
# Design rationale:
#   Isolating the AI layer makes it trivial to swap models, mock responses
#   in tests, or add caching without touching any other module.
# =============================================================================

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError

from utils.config import (
    ANALYSIS_SYSTEM_PROMPT,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

AnalysisResult = dict[str, Any]

# ---------------------------------------------------------------------------
# Required keys returned by the AI — used for validation
# ---------------------------------------------------------------------------

_REQUIRED_KEYS: frozenset[str] = frozenset({
    "sentiment",
    "complaint_category",
    "urgency_level",
    "escalation_risk",
    "risk_score",
    "recommended_response",
    "key_issues",
    "estimated_resolution_days",
    "confidence_score",
})

# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def get_client() -> OpenAI:
    """
    Initialise and return a singleton OpenAI client.

    The API key is read from the ``OPENAI_API_KEY`` environment variable.
    Raises ``EnvironmentError`` with a human-readable message when the key
    is absent so that the Streamlit UI can surface it gracefully.

    Returns
    -------
    OpenAI
        Authenticated OpenAI client instance.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set.\n"
            "• Add it to a .env file in the project root, or\n"
            "• Paste it into the sidebar API Key field, or\n"
            "• Export it in your terminal before running the app."
        )
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------

def _strip_fences(raw: str) -> str:
    """Remove markdown code fences that models occasionally emit despite instructions."""
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _validate_and_coerce(data: dict) -> dict:
    """
    Validate that all required keys are present and coerce types where safe.

    Parameters
    ----------
    data : dict
        Raw parsed JSON from the AI response.

    Returns
    -------
    dict
        Validated and coerced analysis dict.

    Raises
    ------
    ValueError
        When a required key is missing.
    """
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"AI response missing required keys: {missing}")

    # Coerce numeric fields to correct Python types
    data["risk_score"]                 = max(1, min(100, int(data["risk_score"])))
    data["confidence_score"]           = max(1, min(100, int(data["confidence_score"])))
    data["estimated_resolution_days"]  = max(1, int(data["estimated_resolution_days"]))

    # Ensure key_issues is always a list of strings
    if isinstance(data["key_issues"], str):
        data["key_issues"] = [i.strip() for i in data["key_issues"].split(",") if i.strip()]

    return data


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------

def analyze_complaint(complaint_text: str, retries: int = 2) -> AnalysisResult:
    """
    Analyse a single customer complaint using the OpenAI Chat API.

    The function:
    1. Validates input is non-empty.
    2. Sends the complaint to GPT with a structured system prompt.
    3. Strips any markdown fences from the response.
    4. Parses and validates the JSON structure.
    5. Retries up to ``retries`` times on transient API errors.

    Parameters
    ----------
    complaint_text : str
        Raw complaint string from the user or CSV upload.
    retries : int
        Number of additional attempts on RateLimitError or APIConnectionError.

    Returns
    -------
    dict
        On success: validated analysis dict with all schema keys.
        On failure: ``{"error": "<human-readable message>"}``
    """
    complaint_text = complaint_text.strip()
    if not complaint_text:
        return {"error": "Complaint text is empty. Please enter a valid complaint."}

    if len(complaint_text) < 15:
        return {"error": "Complaint text is too short to analyse meaningfully."}

    attempt = 0
    last_error: str = ""

    while attempt <= retries:
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Analyse the following insurance customer complaint "
                            f"and return the structured JSON report:\n\n"
                            f"---\n{complaint_text}\n---"
                        ),
                    },
                ],
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                response_format={"type": "text"},   # keep control; we parse manually
            )

            raw_content = response.choices[0].message.content
            cleaned     = _strip_fences(raw_content)
            parsed      = json.loads(cleaned)
            validated   = _validate_and_coerce(parsed)

            logger.info(
                "Complaint analysed successfully. Category=%s Risk=%s",
                validated.get("complaint_category"),
                validated.get("risk_score"),
            )
            return validated

        except RateLimitError:
            wait = 2 ** attempt
            logger.warning("Rate limit hit — retrying in %ds (attempt %d)", wait, attempt + 1)
            time.sleep(wait)
            last_error = "OpenAI rate limit reached. Please wait a moment and try again."

        except APIConnectionError as exc:
            logger.error("API connection error: %s", exc)
            last_error = f"Could not connect to OpenAI: {exc}"
            break

        except APIStatusError as exc:
            logger.error("OpenAI API error %s: %s", exc.status_code, exc.message)
            last_error = f"OpenAI API returned an error ({exc.status_code}): {exc.message}"
            break

        except json.JSONDecodeError as exc:
            logger.error("JSON parse error: %s", exc)
            last_error = (
                "The AI returned a response that could not be parsed as JSON. "
                "Try again — this is usually a transient issue."
            )
            break

        except ValueError as exc:
            logger.error("Validation error: %s", exc)
            last_error = str(exc)
            break

        except EnvironmentError as exc:
            # Missing API key — no point retrying
            return {"error": str(exc)}

        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error during complaint analysis")
            last_error = f"Unexpected error: {exc}"
            break

        attempt += 1

    return {"error": last_error or "Analysis failed after multiple attempts."}


# ---------------------------------------------------------------------------
# Batch analysis
# ---------------------------------------------------------------------------

def analyze_batch(
    df,
    text_column: str = "complaint_text",
    progress_callback=None,
) -> list[AnalysisResult]:
    """
    Analyse every row in a DataFrame and return a list of result dicts.

    A ``progress_callback(current, total)`` can be supplied so the caller
    (e.g., Streamlit) can update a progress bar.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a column named ``text_column``.
    text_column : str
        Name of the column containing complaint text.
    progress_callback : callable | None
        Optional ``(int, int) -> None`` progress hook.

    Returns
    -------
    list[AnalysisResult]
        One dict per row; failed rows contain ``{"error": "..."}``
        plus the original complaint text under ``"complaint_text"``.
    """
    results: list[AnalysisResult] = []
    total = len(df)

    for idx, (_, row) in enumerate(df.iterrows()):
        complaint = str(row.get(text_column, "")).strip()
        result    = analyze_complaint(complaint)
        result["complaint_text"] = complaint       # ensure text is always present
        results.append(result)

        if progress_callback:
            progress_callback(idx + 1, total)

    return results
