# src/detection/pipeline.py

"""
Connect model predictions, deterministic security rules,
and risk scoring.
"""

import math

from rules.detection_rules import (
    detect_brute_force,
    detect_dos_traffic,
    detect_port_scan,
)

from src.scoring.risk_scoring import (
    evaluate_prediction,
    normalise_prediction_label,
)


def _run_rules(event):
    """
    Run applicable deterministic rules.

    Rules are only executed when the required event data
    has been supplied.
    """

    matches = []

    # Port scan rule
    if (
        "connection_count" in event
        and "connection_window_seconds" in event
    ):

        triggered, message = detect_port_scan(
            event["connection_count"],
            event["connection_window_seconds"]
        )

        if triggered:
            matches.append({
                "rule": "port_scan",
                "message": message
            })

    # Brute-force rule
    if (
        "failed_logins" in event
        and "login_window_seconds" in event
    ):

        triggered, message = detect_brute_force(
            event["failed_logins"],
            event["login_window_seconds"]
        )

        if triggered:
            matches.append({
                "rule": "brute_force",
                "message": message
            })

    # DoS rule
    if (
        "request_count" in event
        and "request_window_seconds" in event
    ):

        triggered, message = detect_dos_traffic(
            event["request_count"],
            event["request_window_seconds"]
        )

        if triggered:
            matches.append({
                "rule": "dos",
                "message": message
            })

    return matches


def _rule_category(rule_matches):
    """
    Convert the first rule match into the project's
    broad attack category.
    """

    mapping = {
        "port_scan": "PORT_SCAN",
        "brute_force": "BRUTE_FORCE",
        "dos": "DOS",
    }

    if not rule_matches:
        return None

    return mapping[rule_matches[0]["rule"]]


def build_alert(
    predicted_label,
    event=None,
    confidence=None,
    exposure=5
):
    """
    Build the final structured IDS alert.

    Combines:
        1. ML prediction
        2. Detection rules
        3. Risk scoring

    Args:
        predicted_label:
            Label returned by the ML model.

        event:
            Rule-related network/event information.

        confidence:
            Optional ML probability/confidence.

        exposure:
            Target exposure from 1-10.

    Returns:
        Structured alert dictionary.
    """

    if event is None:
        event = {}
    if not isinstance(event, dict):
        raise ValueError("event must be an object")
    for count, window in (("connection_count", "connection_window_seconds"),
                          ("failed_logins", "login_window_seconds"),
                          ("request_count", "request_window_seconds")):
        if (count in event) != (window in event):
            raise ValueError(f"Supply both {count} and {window}")
        for key in (count, window):
            if key in event:
                value = event[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError(f"{key} must be finite numeric data")
                if value < 0 or (key == window and value == 0):
                    raise ValueError(f"{key} is outside its valid range")
    if isinstance(exposure, bool) or not isinstance(exposure, (int, float)) or not math.isfinite(exposure) or not 1 <= exposure <= 10:
        raise ValueError("exposure must be between 1 and 10")
    if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1):
        raise ValueError("confidence must be between 0 and 1")

    rule_matches = _run_rules(event)

    ml_category = normalise_prediction_label(
        predicted_label
    )

    matched_category = _rule_category(
        rule_matches
    )

    # If ML says benign but a deterministic rule detects
    # an attack, use the rule category for the final alert.
    if rule_matches and ml_category == "BENIGN":
        final_category = matched_category
    else:
        final_category = ml_category

    score = evaluate_prediction(
        final_category,
        confidence=confidence,
        rule_triggered=bool(rule_matches),
        exposure=exposure,
    )

    # Determine where the detection came from.
    if rule_matches and ml_category != "BENIGN":
        source = "both"

    elif rule_matches:
        source = "rule"

    else:
        source = "ml"

    return {
        "label": predicted_label,
        "confidence": confidence,
        "category": final_category,
        "risk_score": score["risk_score"],
        "risk_level": score["severity"],
        "detection_source": source,
        "rule_matches": rule_matches,
    }
