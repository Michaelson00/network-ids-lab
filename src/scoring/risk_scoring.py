# src/scoring/risk_scoring.py

def calculate_risk_score(likelihood, impact, exposure):
    """
    Calculates the NIDS risk score.
    Formula: Risk = Likelihood x Impact x Exposure
    Scale: Each factor is rated 1-10. Maximum possible score is 1000.
    """
    # Ensure inputs are within the 1-10 scale
    likelihood = max(1, min(10, likelihood))
    impact = max(1, min(10, impact))
    exposure = max(1, min(10, exposure))
    
    risk_score = likelihood * impact * exposure
    return risk_score

def determine_severity_label(risk_score):
    """
    Defines what score range counts as low, medium, or high risk.
    Max score = 1000.
    - Low: 1 to 125
    - Medium: 126 to 500
    - High: 501 to 1000
    """
    if risk_score <= 125:
        return "Low"
    elif risk_score <= 500:
        return "Medium"
    else:
        return "High"

def evaluate_event(likelihood, impact, exposure):
    """
    Helper function to calculate the score and return both the score and the severity label.
    """
    score = calculate_risk_score(likelihood, impact, exposure)
    severity = determine_severity_label(score)
    
    return {
        "risk_score": score,
        "severity": severity
    }