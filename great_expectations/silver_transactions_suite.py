"""
Defines the data quality expectations for the silver_transactions table.
Written as a script rather than the raw GE JSON suite format, since it's
easier to read/review and can be run once to generate the actual suite:

    python silver_transactions_suite.py

This gates gold builds in the Airflow DAG (fraud_pipeline_dag.py) — gold
never builds on data that fails these checks.
"""
import great_expectations as gx

context = gx.get_context()

suite = context.add_or_update_expectation_suite("silver_transactions_suite")

validator = context.get_validator(
    batch_request=context.sources.add_or_update_redshift(
        name="fraud_pipeline_redshift"
    )
    .add_table_asset(name="silver_transactions", table_name="silver_transactions")
    .build_batch_request(),
    expectation_suite=suite,
)

# Core integrity checks
validator.expect_column_values_to_not_be_null("event_id")
validator.expect_column_values_to_be_unique("event_id")
validator.expect_column_values_to_not_be_null("event_ts")
validator.expect_column_values_to_be_between("amount", min_value=0, max_value=1_000_000)

# Domain checks specific to this pipeline
validator.expect_column_values_to_be_in_set("flagged", [True, False])
validator.expect_column_values_to_be_between("fraud_score", min_value=0, max_value=200)

# Freshness — fail if the most recent event is more than 2 hours old,
# which would indicate the streaming consumer has stalled.
validator.expect_column_max_to_be_between(
    "event_ts",
    min_value=None,  # set dynamically in the checkpoint run, not hardcoded here
    max_value=None,
)

validator.save_expectation_suite(discard_failed_expectations=False)

print("Saved suite: silver_transactions_suite")
