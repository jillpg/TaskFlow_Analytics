WITH monthly_activity AS (
    -- Expand subscription periods into months using generate_series (Calendar Spine)
    -- This handles users active across multiple months
    SELECT 
        s.user_id,
        date_trunc('month', series_month)::date AS month_date,
        s.status,
        s.end_date
    FROM subscriptions s,
    generate_series(
        date_trunc('month', s.start_date),
        date_trunc('month', COALESCE(s.end_date, '2025-12-31'::date)),
        '1 month'::interval
    ) AS series_month
),
churn_calculation AS (
    SELECT
        month_date,
        COUNT(DISTINCT user_id) AS total_active_users,
        COUNT(DISTINCT CASE 
            WHEN status = 'Churned' AND date_trunc('month', end_date) = month_date 
            THEN user_id 
        END) AS churned_users
    FROM monthly_activity
    GROUP BY month_date
)
SELECT
    month_date,
    total_active_users,
    churned_users,
    ROUND((churned_users::decimal / NULLIF(total_active_users, 0)) * 100, 2) AS churn_rate_pct
FROM churn_calculation
ORDER BY month_date;
