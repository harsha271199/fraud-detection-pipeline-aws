-- Gold: hourly business-ready KPIs. This is what the dashboard queries
-- directly — never queries silver/bronze — so dashboard load stays fast
-- regardless of how much raw data has accumulated.

select
    event_hour,
    count(*) as total_transactions,
    sum(case when flagged then 1 else 0 end) as flagged_transactions,
    round(
        100.0 * sum(case when flagged then 1 else 0 end) / nullif(count(*), 0), 2
    ) as flagged_rate_pct,
    sum(amount) as total_amount,
    sum(case when flagged then amount else 0 end) as flagged_amount,
    -- precision proxy: of events we flagged, how many were actually the
    -- synthetic-fraud events the producer injected. Only meaningful while
    -- testing against the producer's synthetic labels.
    round(
        100.0 * sum(case when flagged and is_synthetic_fraud then 1 else 0 end)
        / nullif(sum(case when flagged then 1 else 0 end), 0), 2
    ) as precision_pct,
    round(
        100.0 * sum(case when flagged and is_synthetic_fraud then 1 else 0 end)
        / nullif(sum(case when is_synthetic_fraud then 1 else 0 end), 0), 2
    ) as recall_pct
from {{ ref('silver_transactions') }}
group by event_hour
order by event_hour
