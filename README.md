# Real-Time Fraud Detection Pipeline (AWS)

A production-style, end-to-end fraud/anomaly detection pipeline built on AWS —
covering cloud infrastructure, data engineering, and analytics in one system.

## Why this project exists

Built to close three specific gaps: AWS production experience (prior work was
Azure-only), modern data orchestration (Airflow + dbt), and observability
(Prometheus/Grafana beyond a single cloud's native tooling). Everything here
is real and runnable — no fabricated metrics. Numbers in this README are
filled in as the pipeline is built and measured, not estimated upfront.

## Architecture

```
Producer (simulated transactions)
        │
        ▼
   Amazon MSK (managed Kafka)
        │
        ▼
   Consumer  ──────────────►  Fraud scoring (rules + anomaly checks)
        │
        ▼
   S3 data lake (bronze → silver → gold, partitioned by date)
        │
        ▼
   Airflow DAG  ──►  dbt models  ──►  Redshift warehouse
        │
        ▼
   Great Expectations (data quality gates on silver/gold)

Observability: Prometheus + Grafana (pipeline health) + CloudWatch (AWS-native alarms)
Infra: Terraform, deployed via GitHub Actions CI/CD
Output: Tableau / Streamlit dashboard on Redshift — pipeline KPIs, fraud flags
```

## Why MSK over Kinesis

Chose Amazon MSK (managed Kafka) instead of Kinesis: Kafka is the more
transferable, industry-standard skill (Kinesis is AWS-proprietary), and it
lets this project reuse real Kafka experience from an earlier project
(Kafka → Neo4j streaming pipeline) rather than starting from zero.

## Repo layout

| Folder | Purpose |
|---|---|
| `terraform/` | VPC, IAM, MSK, S3 buckets, Redshift cluster — all infra as code |
| `producer/` | Simulates transaction events, publishes to MSK |
| `consumer/` | Reads from MSK, applies fraud rules, writes to S3 bronze |
| `dbt/` | Transformation models: bronze → silver → gold |
| `airflow/dags/` | Orchestrates the consumer → dbt → Redshift load on schedule |
| `great_expectations/` | Data quality checks gating silver/gold promotion |
| `dashboards/` | Streamlit app / Tableau workbook reading from Redshift |
| `monitoring/` | Prometheus config + Grafana dashboard definitions |
| `.github/workflows/` | CI/CD — Terraform plan/apply, Python lint/test |

## Cost note

This is built cost-minimized on purpose: Redshift **Serverless** (bills
per-second only while querying, $0 when idle — likely covered entirely
by AWS's $300 new-account free trial credit) and **no NAT Gateway** (MSK
and Redshift sit on public subnets with security groups locked to your
IP only, via the `my_ip_cidr` variable). This is a deliberate demo-project
tradeoff, not a production pattern — worth saying exactly that if it
comes up in an interview.

**Before running anything: set a billing alarm** (AWS Console → Billing
→ Budgets) and get your IP address (whatismyip.com) for `my_ip_cidr`.

## Setup

```bash
# 1. AWS credentials (one-time)
aws configure

# 2. Terraform variables
cd terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: set my_ip_cidr to your actual IP/32
export TF_VAR_redshift_master_password="ChooseAStrongPassword123!"

# 3. Infra
terraform init
terraform plan     # read this before apply — should show ~20 resources, no NAT Gateway
terraform apply

# 4. Producer/consumer
cd ../producer && pip install -r requirements.txt --break-system-packages
cd ../consumer && pip install -r requirements.txt --break-system-packages

# 5. dbt
cd ../dbt && dbt deps && dbt run

# 6. Airflow (local dev)
astro dev start   # or docker-compose, if not using MWAA

# 7. Dashboard
cd ../dashboards && streamlit run streamlit_app.py

# 8. When done for the session — tear down to stop any billing
cd ../terraform && terraform destroy
```

## Results

_Fill in once measured — do not estimate:_
- Events/sec sustained: TBD
- End-to-end detection latency (event → flagged): TBD
- Fraud rule precision/recall on synthetic test set: TBD
- Data quality check pass rate: TBD

## Status

- [ ] Terraform infra provisioned
- [ ] Producer/consumer streaming end-to-end
- [ ] Fraud scoring rules implemented
- [ ] dbt models (bronze/silver/gold)
- [ ] Airflow DAG scheduled and running
- [ ] Great Expectations checks passing
- [ ] Prometheus/Grafana dashboards live
- [ ] CI/CD deploying Terraform on push
- [ ] Public dashboard (Streamlit/Tableau) published
