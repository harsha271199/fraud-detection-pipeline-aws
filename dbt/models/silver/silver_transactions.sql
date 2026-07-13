-- Silver: cleaned and de-duplicated. This is the layer Great Expectations
-- validates before anything is allowed to promote to gold.

with deduped as (
    select
        *,
        row_number() over (
            partition by event_id order by event_ts desc
        ) as rn
    from {{ ref('bronze_transactions') }}
)

select
    event_id,
    user_id,
    card_fingerprint,
    amount,
    billing_location,
    shipping_location,
    event_ts,
    date_trunc('hour', event_ts) as event_hour,
    flagged,
    fraud_score,
    flag_reasons,
    is_synthetic_fraud,
    (billing_location != shipping_location) as location_mismatch
from deduped
where rn = 1
  and amount > 0            -- drop malformed/negative amounts
  and event_ts is not null
