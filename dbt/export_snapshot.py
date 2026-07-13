"""
Exports the gold_fraud_kpis_hourly table to a static CSV file, so the
dashboard can run forever on Streamlit Cloud without a live Redshift
connection.
"""
import argparse

import redshift_connector
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--database", default="frauddb")
    parser.add_argument("--user", default="fraudadmin")
    parser.add_argument("--password", required=True)
    parser.add_argument("--output", default="../dashboards/data/gold_snapshot.csv")
    args = parser.parse_args()

    conn = redshift_connector.connect(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password,
    )

    df = pd.read_sql(
        "select * from gold_fraud_kpis_hourly order by event_hour", conn
    )
    conn.close()

    if df.empty:
        print("WARNING: no rows found.")
        return

    df.to_csv(args.output, index=False)
    print(f"Exported {len(df)} rows to {args.output}")
    print(df[["event_hour", "total_transactions", "flagged_rate_pct",
              "precision_pct", "recall_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()