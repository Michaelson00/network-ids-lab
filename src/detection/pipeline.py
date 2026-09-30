# src/detection/pipeline.py

"""
Connect model predictions, deterministic security rules,
and risk scoring.
"""

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

    event = event or {}

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
        "category": final_category,
        "risk_score": score["risk_score"],
        "risk_level": score["severity"],
        "detection_source": source,
        "rule_matches": rule_matches,
    }