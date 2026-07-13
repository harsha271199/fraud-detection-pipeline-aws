"""
Rule-based fraud scoring. Deliberately simple and explainable (not a black
box) — this is the same kind of scoring logic real fraud teams start with
before layering ML on top. Each rule returns a score contribution and a
reason string, so every flag is auditable, which is a real thing recruiters
and interviewers care about for fraud systems.

Extend with an anomaly-detection layer (e.g. z-score on rolling amount
per user, isolation forest on transaction vectors) once the rule-based
baseline is measured — that comparison is itself a good interview story
("rules caught X%, anomaly model added Y% more recall").
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta

# Rolling per-card event history for velocity checks.
# In production this state would live in Redis; in-memory here keeps the
# consumer dependency-light for a portfolio project — call this out
# explicitly if asked in an interview, don't present it as production-grade.
_card_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

HIGH_AMOUNT_THRESHOLD = 1500.0
VELOCITY_WINDOW_SECONDS = 60
VELOCITY_MAX_EVENTS = 3
SCORE_FLAG_THRESHOLD = 30


def score_event(event: dict) -> dict:
    """Returns the event enriched with fraud_score, flagged, and reasons."""
    score = 0
    reasons = []

    if event["billing_location"] != event["shipping_location"]:
        score += 30
        reasons.append("billing_shipping_mismatch")

    if event["amount"] >= HIGH_AMOUNT_THRESHOLD:
        score += 40
        reasons.append("high_amount")

    card = event["card_fingerprint"]
    now = datetime.fromisoformat(event["timestamp"])
    _card_history[card].append(now)
    recent = [
        t for t in _card_history[card]
        if now - t <= timedelta(seconds=VELOCITY_WINDOW_SECONDS)
    ]
    if len(recent) >= VELOCITY_MAX_EVENTS:
        score += 35
        reasons.append("card_velocity_spike")

    event["fraud_score"] = score
    event["flagged"] = score >= SCORE_FLAG_THRESHOLD
    event["flag_reasons"] = ",".join(reasons)
    return event
