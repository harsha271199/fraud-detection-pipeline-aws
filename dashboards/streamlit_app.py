"""
Public dashboard on top of a static snapshot of gold_fraud_kpis_hourly.
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fraud Pipeline KPIs", layout="wide")


@st.cache_data
def load_kpis() -> pd.DataFrame:
    return pd.read_csv("data/gold_snapshot.csv", parse_dates=["event_hour"])


st.title("Real-time fraud pipeline — KPI snapshot")
st.caption(
    "AWS pipeline: MSK -> S3 (bronze/silver/gold) -> Airflow + dbt -> Redshift. "
    "Precision/recall computed against synthetic fraud labels injected by the producer."
)
st.info(
    "This dashboard shows a **static snapshot** captured from a real, live run "
    "of the full pipeline — not a live connection. The AWS infrastructure "
    "(MSK, Redshift) was intentionally torn down after capturing this data "
    "to avoid ongoing cloud costs. See the project README for the full "
    "architecture and how to re-provision the live infrastructure.",
    icon="ℹ️",
)

df = load_kpis()

if df.empty:
    st.warning("No snapshot data found.")
else:
    latest = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions (last snapshot hour)", int(latest["total_transactions"]))
    col2.metric("Flagged rate", f"{latest['flagged_rate_pct']}%")
    col3.metric("Precision", f"{latest['precision_pct']}%")
    col4.metric("Recall", f"{latest['recall_pct']}%")

    st.subheader("Transaction volume over time")
    st.line_chart(df.set_index("event_hour")["total_transactions"])

    st.subheader("Flagged rate over time")
    st.line_chart(df.set_index("event_hour")["flagged_rate_pct"])

    st.subheader("Precision / recall over time")
    st.line_chart(df.set_index("event_hour")[["precision_pct", "recall_pct"]])

    st.subheader("Raw hourly KPIs (snapshot)")
    st.dataframe(df, use_container_width=True)

st.caption("Full source code, Terraform infrastructure, and architecture: see the [GitHub repo](https://github.com/harsha271199/fraud-detection-pipeline-aws).")