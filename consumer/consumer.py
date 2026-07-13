"""
Consumes transaction events from MSK, applies fraud scoring, and writes
batches to S3 as partitioned JSON-lines (bronze layer). Also emits basic
CloudWatch metrics so the pipeline is observable from minute one, before
Prometheus/Grafana are wired up.

This is the AWS port of the Kafka-to-Neo4j connector pattern from the
earlier graph-analytics project — same batching/flush logic, different
sink (S3 instead of Neo4j) and added scoring step.

Usage:
    python consumer.py --bootstrap-servers <msk-bootstrap-string> \
                        --bucket <data-lake-bucket-name>
"""
import argparse
import json
import time
from datetime import datetime, timezone

import boto3
from kafka import KafkaConsumer

from fraud_rules import score_event

TOPIC = "transactions"
BATCH_SIZE = 100
BATCH_FLUSH_SECONDS = 10


def flush_batch(s3_client, bucket: str, batch: list[dict]):
    if not batch:
        return
    now = datetime.now(timezone.utc)
    key = (
        f"bronze/transactions/"
        f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"batch-{now.strftime('%H%M%S')}-{len(batch)}.jsonl"
    )
    body = "\n".join(json.dumps(e) for e in batch)
    s3_client.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"))

    flagged = sum(1 for e in batch if e["flagged"])
    print(f"Flushed {len(batch)} events ({flagged} flagged) -> s3://{bucket}/{key}")

    cloudwatch = boto3.client("cloudwatch")
    cloudwatch.put_metric_data(
        Namespace="FraudPipeline",
        MetricData=[
            {"MetricName": "EventsProcessed", "Value": len(batch), "Unit": "Count"},
            {"MetricName": "EventsFlagged", "Value": flagged, "Unit": "Count"},
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", required=True)
    parser.add_argument("--sasl-username", required=True)
    parser.add_argument("--sasl-password", required=True)
    parser.add_argument("--bucket", required=True)
    args = parser.parse_args()

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=args.bootstrap_servers,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=args.sasl_username,
        sasl_plain_password=args.sasl_password,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="fraud-pipeline-consumer",
    )
    s3_client = boto3.client("s3")

    batch: list[dict] = []
    last_flush = time.time()

    print(f"Consuming from '{TOPIC}', writing to s3://{args.bucket}/bronze/")

    for message in consumer:
        scored = score_event(message.value)
        batch.append(scored)

        if len(batch) >= BATCH_SIZE or (time.time() - last_flush) >= BATCH_FLUSH_SECONDS:
            flush_batch(s3_client, args.bucket, batch)
            batch = []
            last_flush = time.time()


if __name__ == "__main__":
    main()
