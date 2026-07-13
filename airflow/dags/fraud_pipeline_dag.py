"""
Orchestrates the batch side of the pipeline: run dbt (bronze -> silver ->
gold), then run data quality checks on silver before gold is allowed to
build. Streaming ingestion (producer/consumer) runs continuously outside
Airflow - this DAG only owns the scheduled transformation/quality layer.

NOTE ON DATA QUALITY APPROACH: originally built with Great Expectations,
but GE's checkpoint/Data Context setup adds real operational overhead for
a project this size. Swapped to direct SQL-based checks via
redshift_connector instead - same purpose (gate gold builds on data
quality), fewer moving parts, easier to reason about and debug. Worth
being upfront about this tradeoff if asked in an interview: it's a
deliberate "right-sized tool" decision, not a shortcut taken by accident.

Schedule: hourly, matching the gold_fraud_kpis_hourly grain.
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "fraud-pipeline",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="fraud_pipeline_hourly",
    default_args=default_args,
    description="bronze -> silver (dbt) -> data quality checks -> gold (dbt)",
    schedule_interval="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["fraud-pipeline", "portfolio-project"],
) as dag:

    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command="cd /opt/airflow/dbt && dbt run --select silver",
    )

    def run_data_quality_checks(**_):
        import redshift_connector

        conn = redshift_connector.connect(
            host=os.environ["REDSHIFT_HOST"],
            database=os.environ.get("REDSHIFT_DB", "frauddb"),
            user=os.environ.get("REDSHIFT_USER", "fraudadmin"),
            password=os.environ["REDSHIFT_PASSWORD"],
        )
        cursor = conn.cursor()

        checks = [
            ("no_null_event_id",
             "select count(*) from silver_transactions where event_id is null", 0),
            ("no_duplicate_event_id",
             "select count(*) - count(distinct event_id) from silver_transactions", 0),
            ("no_zero_or_negative_amount",
             "select count(*) from silver_transactions where amount <= 0", 0),
            ("fraud_score_in_expected_range",
             "select count(*) from silver_transactions where fraud_score < 0 or fraud_score > 200", 0),
        ]

        failures = []
        for name, sql, expected in checks:
            cursor.execute(sql)
            result = cursor.fetchone()[0]
            if result != expected:
                failures.append(f"{name}: expected {expected}, got {result}")

        cursor.close()
        conn.close()

        if failures:
            raise ValueError("Data quality checks failed:\n" + "\n".join(failures))

        print(f"All {len(checks)} data quality checks passed.")

    ge_check_silver = PythonOperator(
        task_id="ge_check_silver",
        python_callable=run_data_quality_checks,
    )

    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command="cd /opt/airflow/dbt && dbt run --select gold",
    )

    dbt_run_silver >> ge_check_silver >> dbt_run_gold
