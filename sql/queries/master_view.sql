CREATE OR REPLACE VIEW analytics_master_view AS
SELECT
    u.user_id,
    u.signup_date,
    u.country,
    u.acquisition_source,
    u.device,
    s.plan_type,
    s.status,
    s.start_date AS sub_start_date,
    s.end_date AS sub_end_date,
    s.amount AS monthly_revenue,
    
    -- Calculated Fields
    CASE 
        WHEN s.status = 'Churned' AND s.end_date IS NOT NULL 
        THEN (EXTRACT(YEAR FROM age(s.end_date, s.start_date)) * 12 + 
              EXTRACT(MONTH FROM age(s.end_date, s.start_date)))
        ELSE (EXTRACT(YEAR FROM age('2025-12-31', s.start_date)) * 12 + 
              EXTRACT(MONTH FROM age('2025-12-31', s.start_date)))
    END AS tenure_months,
    
    (CASE 
        WHEN s.status = 'Churned' AND s.end_date IS NOT NULL 
        THEN (EXTRACT(YEAR FROM age(s.end_date, s.start_date)) * 12 + 
              EXTRACT(MONTH FROM age(s.end_date, s.start_date)))
        ELSE (EXTRACT(YEAR FROM age('2025-12-31', s.start_date)) * 12 + 
              EXTRACT(MONTH FROM age('2025-12-31', s.start_date)))
    END * s.amount) AS estimated_ltv
    
FROM users u
JOIN subscriptions s ON u.user_id = s.user_id;
