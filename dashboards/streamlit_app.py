"""
Public-facing dashboard on top of the gold_fraud_kpis_hourly table.
Deploy via Streamlit Community Cloud (free) for a live, clickable link to
put in the resume/README — this is the "recruiter can actually click it"
piece that a static screenshot doesn't give you.

Run locally:
    streamlit run streamlit_app.py

Requires REDSHIFT_HOST / REDSHIFT_DB / REDSHIFT_USER / REDSHIFT_PASSWORD
as environment variables (or Streamlit secrets when deployed).
"""
import os

import pandas as pd
import redshift_connector
import streamlit as st

st.set_page_config(page_title="Fraud Pipeline KPIs", layout="wide")


@st.cache_data(ttl=300)
def load_kpis() -> pd.DataFrame:
    conn = redshift_connector.connect(
        host=os.environ["REDSHIFT_HOST"],
        database=os.environ.get("REDSHIFT_DB", "frauddb"),
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )
    query = "select * from gold_fraud_kpis_hourly order by event_hour desc limit 168"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


st.title("Real-time fraud pipeline — live KPIs")
st.caption(
    "AWS pipeline: MSK -> S3 (bronze/silver/gold) -> Airflow + dbt -> Redshift. "
    "Precision/recall computed against synthetic fraud labels injected by the producer."
)

df = load_kpis()

if df.empty:
    st.warning("No data yet — pipeline may still be starting up.")
else:
    latest = df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions (last hour)", int(latest["total_transactions"]))
    col2.metric("Flagged rate", f"{latest['flagged_rate_pct']}%")
    col3.metric("Precision", f"{latest['precision_pct']}%")
    col4.metric("Recall", f"{latest['recall_pct']}%")

    st.subheader("Transaction volume over time")
    st.line_chart(df.set_index("event_hour")["total_transactions"])

    st.subheader("Flagged rate over time")
    st.line_chart(df.set_index("event_hour")["flagged_rate_pct"])

    st.subheader("Precision / recall over time")
    st.line_chart(df.set_index("event_hour")[["precision_pct", "recall_pct"]])

    st.subheader("Raw hourly KPIs")
    st.dataframe(df, use_container_width=True)
