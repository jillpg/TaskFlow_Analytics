import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Configuration
NUM_USERS = 5000  # Adjust as needed
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)
SEED = 42

fake = Faker()
Faker.seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

def generate_data():
    print("Generating Users...")
    users = []
    
    # Seasonality weights (Higher in Q1/Q4, dip in Summer)
    # Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
    month_weights = [0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.08, 0.09, 0.08, 0.07]
    
    countries = ['US', 'UK', 'CA', 'DE', 'FR', 'BR', 'ES', 'IN', 'JP']
    country_weights = [0.4, 0.15, 0.05, 0.05, 0.05, 0.15, 0.05, 0.05, 0.05] # BR high for the "Portuguese issue"
    
    sources = ['Organic', 'Ads', 'Referral', 'Social']
    source_weights = [0.3, 0.4, 0.2, 0.1]
    
    for _ in range(NUM_USERS):
        # Pick signup month based on weights
        month_idx = np.random.choice(range(12), p=month_weights)
        month = month_idx + 1
        
        # Random day in that month
        if month == 2:
            day = random.randint(1, 28)
        elif month in [4, 6, 9, 11]:
            day = random.randint(1, 30)
        else:
            day = random.randint(1, 31)
            
        signup_date = datetime(2025, month, day)
        
        users.append({
            'user_id': fake.uuid4(),
            'signup_date': signup_date,
            'country': np.random.choice(countries, p=country_weights),
            'acquisition_source': np.random.choice(sources, p=source_weights),
            'device': np.random.choice(['Desktop', 'Mobile', 'Tablet'], p=[0.7, 0.25, 0.05]),
            'email': fake.email()
        })
    
    users_df = pd.DataFrame(users)
    users_df = users_df.sort_values('signup_date').reset_index(drop=True)
    
    print("Generating Subscriptions...")
    subscriptions = []
    
    # Plans
    plans = ['Free', 'Pro', 'Enterprise']
    
    for _, user in users_df.iterrows():
        # Conversion logic
        # 60% stay Free, 35% Pro, 5% Enterprise
        plan = np.random.choice(plans, p=[0.60, 0.35, 0.05])
        
        amount = 0
        if plan == 'Pro': amount = 29
        elif plan == 'Enterprise': amount = 99
        
        # Churn Logic
        # Normal churn rate ~5-8%
        # March Incident: High churn for users active in March
        
        start_date = user['signup_date']
        
        # Determine if/when they churn
        # Base churn probability
        churn_prob = 0.10 if plan == 'Free' else 0.04
        
        # BRAZIL High Churn scenario
        if user['country'] == 'BR':
            churn_prob += 0.15
            
        is_churned = random.random() < churn_prob
        
        status = 'Active'
        end_date = None
        
        if is_churned:
            status = 'Churned'
            # Random duration before churn (1 to 6 months)
            days_active = random.randint(30, 180)
            potential_end_date = start_date + timedelta(days=days_active)
            
            # MARCH INCIDENT ENFORCER
            # If they were active during March (month 3), increase chance they quit right after March
            if start_date.month <= 3 and potential_end_date.month >= 3:
                if random.random() < 0.4: # 40% of vulnerable users rage-quit in March
                    # Quit end of March
                    potential_end_date = datetime(2025, 3, random.randint(25, 31))
            
            if potential_end_date > END_DATE:
                status = 'Active' # Didn't churn yet in our window
                end_date = None
            else:
                end_date = potential_end_date
        
        subscriptions.append({
            'sub_id': fake.uuid4(),
            'user_id': user['user_id'],
            'plan_type': plan,
            'amount': amount,
            'start_date': start_date,
            'end_date': end_date,
            'status': status
        })
        
    subs_df = pd.DataFrame(subscriptions)
    
    print("Generating Activity Logs (This might take a moment)...")
    # Simplify: Generate logs for a subset of users or aggregated daily? 
    # Request says: event_id, user_id, timestamp, event_name
    # To keep it performant, let's generate ~50-100 events per user over their lifetime
    
    logs = []
    event_types = ['login', 'create_task', 'invite_user', 'view_report']
    event_weights = [0.5, 0.3, 0.05, 0.15]
    
    # We process in batches/users to manage memory if needed, but 5000 users is small enough
    for _, sub in subs_df.iterrows():
        user_start = sub['start_date']
        user_end = sub['end_date'] if pd.notnull(sub['end_date']) else END_DATE
        
        # Calculate active days
        delta_days = (user_end - user_start).days
        if delta_days < 1: continue
        
        # Pick random active days (e.g., user is active 40% of days)
        active_days_count = int(delta_days * 0.4) 
        if active_days_count < 1: active_days_count = 1
        
        active_days_offsets = sorted(random.sample(range(delta_days), active_days_count))
        
        for offset in active_days_offsets:
            current_date = user_start + timedelta(days=offset)
            
            # Weekend Drop
            if current_date.weekday() >= 5: # Sat/Sun
                if random.random() > 0.2: # 80% skip weekends
                    continue
            
            # Generate 1-5 events per active day
            num_events = random.randint(1, 5)
            for _ in range(num_events):
                # Random time during day (weighted towards work hours 9-17)
                hour = int(np.random.normal(14, 3)) # Mean 14:00 (2PM), std 3
                hour = max(0, min(23, hour))
                
                event_time = current_date + timedelta(hours=hour, minutes=random.randint(0, 59))
                
                logs.append({
                    'event_id': fake.uuid4(),
                    'user_id': sub['user_id'],
                    'timestamp': event_time,
                    'event_name': np.random.choice(event_types, p=event_weights)
                })

    logs_df = pd.DataFrame(logs)
    
    # Output
    output_dir = 'output_data'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Saving to {output_dir}...")
    users_df.to_csv(f'{output_dir}/users.csv', index=False)
    subs_df.to_csv(f'{output_dir}/subscriptions.csv', index=False)
    logs_df.to_csv(f'{output_dir}/activity_logs.csv', index=False)
    
    print("Done! Data Generated:")
    print(f"Users: {len(users_df)}")
    print(f"Subscriptions: {len(subs_df)}")
    print(f"Logs: {len(logs_df)}")

if __name__ == "__main__":
    generate_data()
