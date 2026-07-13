-- Bronze: thin view over the raw external table (Redshift Spectrum,
-- pointed at s3://<bucket>/bronze/transactions/). No transformation here
-- on purpose — bronze should be as close to the raw event as possible so
-- you can always re-derive silver/gold if a transformation bug is found.
{{ config(materialized='view', bind=false) }}
select
    event_id,
    user_id,
    card_fingerprint,
    amount,
    billing_location,
    shipping_location,
    timestamp::timestamp as event_ts,
    flagged,
    fraud_score,
    flag_reasons,
    is_synthetic_fraud
from {{ source('raw', 'transactions_external') }}
