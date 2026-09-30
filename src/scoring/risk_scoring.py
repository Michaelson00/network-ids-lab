# src/scoring/risk_scoring.py

"""
Risk scoring helpers for the NIDS detection pipeline.

The project uses the documented formula:
    Risk = Likelihood x Impact x Exposure

Each factor is kept on a 1-10 scale, so the final score is 1-1000.
"""

# Impact values for the current prototype.
ATTACK_IMPACT = {
    "BENIGN": 1,
    "PORT_SCAN": 4,
    "BRUTE_FORCE": 7,
    "DOS": 9,
    "OTHER_ATTACK": 6,
}


def calculate_risk_score(likelihood, impact, exposure):
    """
    Calculate Risk = Likelihood x Impact x Exposure.
    """

    likelihood = max(1, min(10, int(round(likelihood))))
    impact = max(1, min(10, int(round(impact))))
    exposure = max(1, min(10, int(round(exposure))))

    return likelihood * impact * exposure


def determine_severity_label(risk_score):
    """
    Convert the numerical risk score into Low, Medium, or High.
    """

    if risk_score <= 125:
        return "Low"

    if risk_score <= 500:
        return "Medium"

    return "High"


def evaluate_event(likelihood, impact, exposure):
    """
    Calculate the risk score and severity for explicit risk factors.
    """

    score = calculate_risk_score(
        likelihood,
        impact,
        exposure
    )

    return {
        "risk_score": score,
        "severity": determine_severity_label(score),
    }


def normalise_prediction_label(label):
    """
    Convert ML labels into the threat categories used by the
    cybersecurity/risk-scoring layer.

    Examples:
        PortScan -> PORT_SCAN
        DDoS -> DOS
        SSH-Patator -> BRUTE_FORCE
        BENIGN -> BENIGN
    """

    value = str(label).strip().lower()

    if value in {"benign", "normal"}:
        return "BENIGN"

    if (
        "portscan" in value
        or "port scan" in value
        or "recon" in value
    ):
        return "PORT_SCAN"

    if (
        "patator" in value
        or "brute force" in value
        or "bruteforce" in value
    ):
        return "BRUTE_FORCE"

    if (
        "ddos" in value
        or value.startswith("dos ")
        or value == "dos"
    ):
        return "DOS"

    return "OTHER_ATTACK"


def _confidence_to_likelihood(confidence, is_benign=False):
    """
    Convert ML confidence from 0-1 into the project's 1-10
    likelihood scale.
    """

    if confidence is None:
        return 1 if is_benign else 6

    confidence = max(
        0.0,
        min(1.0, float(confidence))
    )

    if is_benign:
        return 1

    return max(
        1,
        min(10, int(round(confidence * 10)))
    )


def evaluate_prediction(
    label,
    confidence=None,
    rule_triggered=False,
    exposure=5
):
    """
    Risk-score a model prediction.

    Args:
        label:
            Model prediction such as BENIGN, PortScan,
            DDoS or SSH-Patator.

        confidence:
            Optional model confidence between 0.0 and 1.0.

        rule_triggered:
            True if a deterministic security rule also detected
            suspicious behaviour.

        exposure:
            Criticality/exposure of the target from 1-10.

    Returns:
        Dictionary containing category, likelihood, impact,
        exposure, risk score and severity.
    """

    category = normalise_prediction_label(label)

    is_benign = category == "BENIGN"

    likelihood = _confidence_to_likelihood(
        confidence,
        is_benign=is_benign
    )

    # A matching deterministic rule strengthens confidence
    # that the event is genuinely suspicious.
    if rule_triggered:
        likelihood = max(likelihood, 9)

    impact = ATTACK_IMPACT[category]

    # If ML says BENIGN but a security rule detects suspicious
    # behaviour, do not keep the event at benign impact.
    if is_benign and rule_triggered:
        impact = ATTACK_IMPACT["OTHER_ATTACK"]

    result = evaluate_event(
        likelihood,
        impact,
        exposure
    )

    result.update({
        "category": category,
        "likelihood": likelihood,
        "impact": impact,
        "exposure": max(
            1,
            min(10, int(round(exposure)))
        ),
    })

    return result