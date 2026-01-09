WITH user_cohorts AS (
    SELECT
        user_id,
        date_trunc('month', signup_date)::date AS cohort_month
    FROM users
),
active_months AS (
    -- Determine which months each user was active based on subscription dates
    SELECT
        s.user_id,
        date_trunc('month', series_month)::date AS activity_month
    FROM subscriptions s,
    generate_series(
        date_trunc('month', s.start_date),
        date_trunc('month', COALESCE(s.end_date, '2025-12-31'::date)),
        '1 month'::interval
    ) AS series_month
),
cohort_retention AS (
    SELECT
        uc.cohort_month,
        -- Calculate month number (0 = signup month, 1 = next month, etc.)
        (EXTRACT(YEAR FROM am.activity_month) - EXTRACT(YEAR FROM uc.cohort_month)) * 12 +
        (EXTRACT(MONTH FROM am.activity_month) - EXTRACT(MONTH FROM uc.cohort_month)) AS month_number,
        COUNT(DISTINCT uc.user_id) AS active_users
    FROM user_cohorts uc
    JOIN active_months am ON uc.user_id = am.user_id
    GROUP BY uc.cohort_month, month_number
),
cohort_sizes AS (
    -- Get the initial size of each cohort (Month 0)
    SELECT cohort_month, active_users AS initial_users
    FROM cohort_retention
    WHERE month_number = 0
)
SELECT
    cr.cohort_month,
    cs.initial_users,
    cr.month_number,
    cr.active_users,
    ROUND((cr.active_users::decimal / cs.initial_users) * 100, 1) AS retention_pct
FROM cohort_retention cr
JOIN cohort_sizes cs ON cr.cohort_month = cs.cohort_month
ORDER BY cr.cohort_month, cr.month_number;
