"""
Simulates e-commerce checkout events and publishes them to MSK.

Each event mimics a real checkout: user, amount, card fingerprint, billing/
shipping location, timestamp. A small fraction of events are deliberately
generated as "suspicious" patterns (velocity spikes, mismatched locations,
repeated card attempts) so the downstream fraud rules have something real
to catch — this is what makes the precision/recall numbers in the README
measurable instead of made up.

Usage:
    python producer.py --bootstrap-servers <msk-bootstrap-string> --rate 50
"""
import argparse
import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

TOPIC = "transactions"

CARD_POOL = [str(uuid.uuid4())[:8] for _ in range(5000)]
USER_POOL = [str(uuid.uuid4())[:8] for _ in range(2000)]
LOCATIONS = ["US-CA", "US-NY", "US-TX", "US-AZ", "UK-LON", "DE-BER", "IN-BLR"]


def make_normal_event() -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(USER_POOL),
        "card_fingerprint": random.choice(CARD_POOL),
        "amount": round(random.uniform(5, 300), 2),
        "billing_location": (loc := random.choice(LOCATIONS)),
        "shipping_location": loc,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_synthetic_fraud": False,
    }


def make_fraud_event() -> dict:
    """Injects one of a few known-suspicious patterns for the scoring
    engine to catch. Keeping the pattern list here (not hidden) so the
    fraud rules and the injected patterns can be compared directly for
    a real precision/recall calculation."""
    pattern = random.choice(["mismatched_location", "high_amount", "repeated_card"])
    event = make_normal_event()
    event["is_synthetic_fraud"] = True

    if pattern == "mismatched_location":
        event["shipping_location"] = random.choice(
            [l for l in LOCATIONS if l != event["billing_location"]]
        )
    elif pattern == "high_amount":
        event["amount"] = round(random.uniform(2000, 9000), 2)
    elif pattern == "repeated_card":
        event["card_fingerprint"] = CARD_POOL[0]  # reuse same card rapidly

    event["fraud_pattern"] = pattern
    return event


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", required=True)
    parser.add_argument("--sasl-username", required=True)
    parser.add_argument("--sasl-password", required=True)
    parser.add_argument("--rate", type=int, default=20, help="events per second")
    parser.add_argument("--fraud-ratio", type=float, default=0.03)
    args = parser.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=args.sasl_username,
        sasl_plain_password=args.sasl_password,
    )

    print(f"Producing to topic '{TOPIC}' at ~{args.rate} events/sec")
    interval = 1.0 / args.rate

    try:
        while True:
            event = (
                make_fraud_event()
                if random.random() < args.fraud_ratio
                else make_normal_event()
            )
            producer.send(TOPIC, value=event)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopping producer.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
