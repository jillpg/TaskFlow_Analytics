-- Create Tables
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    signup_date DATE,
    country VARCHAR(50),
    acquisition_source VARCHAR(50),
    device VARCHAR(50),
    email VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    sub_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    plan_type VARCHAR(20),
    amount DECIMAL(10, 2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS activity_logs (
    event_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    timestamp TIMESTAMP,
    event_name VARCHAR(50)
);

-- Copy Data (Assumes CSVs are in /data/ via Docker volume)
-- Note: 'DELIMITER' matches the pandas to_csv default (comma)
-- 'HEADER' skips the first row

COPY users(user_id, signup_date, country, acquisition_source, device, email)
FROM '/data/users.csv'
DELIMITER ','
CSV HEADER;

COPY subscriptions(sub_id, user_id, plan_type, amount, start_date, end_date, status)
FROM '/data/subscriptions.csv'
DELIMITER ','
CSV HEADER;

COPY activity_logs(event_id, user_id, timestamp, event_name)
FROM '/data/activity_logs.csv'
DELIMITER ','
CSV HEADER;
