-- Seed data for Data Explorer
-- Creates a demo user via Supabase auth, then populates datasets, queries, and results.
--
-- Run with:  npx supabase db reset   (applies migrations + seed)
-- Or:        psql $DATABASE_URL -f supabase/seed.sql

-- ==========================================================================
-- Demo user (Supabase auth)
-- The handle_new_user trigger auto-creates the profile row.
-- ==========================================================================
INSERT INTO auth.users (
    id, instance_id, aud, role, email,
    encrypted_password, email_confirmed_at,
    raw_user_meta_data, created_at, updated_at
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '00000000-0000-0000-0000-000000000000',
    'authenticated', 'authenticated',
    'demo@data-explorer.local',
    crypt('demo-password-123', gen_salt('bf')),
    now(),
    '{"full_name": "Demo User"}'::jsonb,
    now(), now()
) ON CONFLICT (id) DO NOTHING;

-- Ensure profile exists (trigger may have fired)
INSERT INTO public.profiles (id, email, full_name, plan)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'demo@data-explorer.local',
    'Demo User',
    'free'
) ON CONFLICT (id) DO NOTHING;


-- ==========================================================================
-- Datasets (3 realistic examples)
-- ==========================================================================

-- 1. E-commerce sales data
INSERT INTO public.datasets (id, owner_id, name, description, schema, row_count, source)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'ecommerce_sales',
    'Monthly e-commerce sales data across product categories (Jan-Dec 2024)',
    '{
        "columns": [
            {"name": "month", "type": "text"},
            {"name": "category", "type": "text"},
            {"name": "revenue", "type": "numeric"},
            {"name": "orders", "type": "integer"},
            {"name": "avg_order_value", "type": "numeric"},
            {"name": "return_rate", "type": "numeric"}
        ]
    }'::jsonb,
    48,
    'upload'
);

-- 2. Weather station observations
INSERT INTO public.datasets (id, owner_id, name, description, schema, row_count, source)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'weather_stations',
    'Daily temperature and precipitation from 5 weather stations (Q1 2024)',
    '{
        "columns": [
            {"name": "date", "type": "date"},
            {"name": "station_id", "type": "text"},
            {"name": "station_name", "type": "text"},
            {"name": "temp_high_f", "type": "numeric"},
            {"name": "temp_low_f", "type": "numeric"},
            {"name": "precipitation_in", "type": "numeric"},
            {"name": "humidity_pct", "type": "integer"}
        ]
    }'::jsonb,
    450,
    'upload'
);

-- 3. Employee survey responses
INSERT INTO public.datasets (id, owner_id, name, description, schema, row_count, source)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'employee_survey',
    'Annual employee engagement survey with satisfaction scores by department',
    '{
        "columns": [
            {"name": "department", "type": "text"},
            {"name": "role_level", "type": "text"},
            {"name": "satisfaction", "type": "integer"},
            {"name": "work_life_balance", "type": "integer"},
            {"name": "growth_opportunity", "type": "integer"},
            {"name": "manager_rating", "type": "integer"},
            {"name": "tenure_years", "type": "numeric"}
        ]
    }'::jsonb,
    215,
    'upload'
);


-- ==========================================================================
-- Saved queries (8 queries across the 3 datasets)
-- ==========================================================================

-- Queries on ecommerce_sales
INSERT INTO public.saved_queries (id, owner_id, dataset_id, name, sql_query, description)
VALUES
(
    'aaaa1111-0000-0000-0000-000000000001',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '11111111-1111-1111-1111-111111111111',
    'Revenue by Category',
    'SELECT category, SUM(revenue) as total_revenue, SUM(orders) as total_orders FROM data GROUP BY category ORDER BY total_revenue DESC',
    'Total revenue and order count grouped by product category'
),
(
    'aaaa1111-0000-0000-0000-000000000002',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '11111111-1111-1111-1111-111111111111',
    'Monthly Revenue Trend',
    'SELECT month, SUM(revenue) as monthly_revenue FROM data GROUP BY month ORDER BY month',
    'Monthly revenue trend across all categories'
),
(
    'aaaa1111-0000-0000-0000-000000000003',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '11111111-1111-1111-1111-111111111111',
    'High Return Rate Products',
    'SELECT category, month, return_rate FROM data WHERE return_rate > 0.05 ORDER BY return_rate DESC',
    'Categories with return rates above 5%'
);

-- Queries on weather_stations
INSERT INTO public.saved_queries (id, owner_id, dataset_id, name, sql_query, description)
VALUES
(
    'aaaa2222-0000-0000-0000-000000000001',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '22222222-2222-2222-2222-222222222222',
    'Average Temp by Station',
    'SELECT station_name, AVG(temp_high_f) as avg_high, AVG(temp_low_f) as avg_low FROM data GROUP BY station_name',
    'Average high and low temperatures per weather station'
),
(
    'aaaa2222-0000-0000-0000-000000000002',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '22222222-2222-2222-2222-222222222222',
    'Rainy Days Count',
    'SELECT station_name, COUNT(*) as rainy_days FROM data WHERE precipitation_in > 0 GROUP BY station_name ORDER BY rainy_days DESC',
    'Number of days with precipitation by station'
);

-- Queries on employee_survey
INSERT INTO public.saved_queries (id, owner_id, dataset_id, name, sql_query, description)
VALUES
(
    'aaaa3333-0000-0000-0000-000000000001',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '33333333-3333-3333-3333-333333333333',
    'Satisfaction by Department',
    'SELECT department, AVG(satisfaction) as avg_satisfaction, AVG(work_life_balance) as avg_wlb FROM data GROUP BY department ORDER BY avg_satisfaction DESC',
    'Average satisfaction and work-life balance scores by department'
),
(
    'aaaa3333-0000-0000-0000-000000000002',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '33333333-3333-3333-3333-333333333333',
    'Tenure vs Satisfaction',
    'SELECT tenure_years, AVG(satisfaction) as avg_satisfaction FROM data GROUP BY tenure_years ORDER BY tenure_years',
    'Correlation between employee tenure and satisfaction'
),
(
    'aaaa3333-0000-0000-0000-000000000003',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '33333333-3333-3333-3333-333333333333',
    'Manager Ratings Distribution',
    'SELECT manager_rating, COUNT(*) as count FROM data GROUP BY manager_rating ORDER BY manager_rating',
    'Distribution of manager rating scores'
);


-- ==========================================================================
-- Query results (5 cached snapshots)
-- ==========================================================================

INSERT INTO public.query_results (id, query_id, result_data, row_count, execution_time_ms)
VALUES
(
    'bbbb0000-0000-0000-0000-000000000001',
    'aaaa1111-0000-0000-0000-000000000001',
    '[
        {"category": "Electronics", "total_revenue": 284500, "total_orders": 1420},
        {"category": "Clothing", "total_revenue": 198200, "total_orders": 2650},
        {"category": "Home & Garden", "total_revenue": 142800, "total_orders": 890},
        {"category": "Books", "total_revenue": 67300, "total_orders": 3200}
    ]'::jsonb,
    4,
    23
),
(
    'bbbb0000-0000-0000-0000-000000000002',
    'aaaa1111-0000-0000-0000-000000000002',
    '[
        {"month": "2024-01", "monthly_revenue": 48200},
        {"month": "2024-02", "monthly_revenue": 52100},
        {"month": "2024-03", "monthly_revenue": 61400},
        {"month": "2024-04", "monthly_revenue": 55800},
        {"month": "2024-05", "monthly_revenue": 67300},
        {"month": "2024-06", "monthly_revenue": 71900}
    ]'::jsonb,
    6,
    18
),
(
    'bbbb0000-0000-0000-0000-000000000003',
    'aaaa2222-0000-0000-0000-000000000001',
    '[
        {"station_name": "Downtown", "avg_high": 72.3, "avg_low": 54.1},
        {"station_name": "Airport", "avg_high": 74.8, "avg_low": 56.2},
        {"station_name": "Harbor", "avg_high": 68.9, "avg_low": 52.7},
        {"station_name": "Mountain View", "avg_high": 65.4, "avg_low": 45.3},
        {"station_name": "Valley Station", "avg_high": 76.1, "avg_low": 58.9}
    ]'::jsonb,
    5,
    31
),
(
    'bbbb0000-0000-0000-0000-000000000004',
    'aaaa3333-0000-0000-0000-000000000001',
    '[
        {"department": "Engineering", "avg_satisfaction": 4.2, "avg_wlb": 3.8},
        {"department": "Marketing", "avg_satisfaction": 4.0, "avg_wlb": 4.1},
        {"department": "Sales", "avg_satisfaction": 3.6, "avg_wlb": 3.2},
        {"department": "Operations", "avg_satisfaction": 3.9, "avg_wlb": 3.5},
        {"department": "HR", "avg_satisfaction": 4.3, "avg_wlb": 4.4}
    ]'::jsonb,
    5,
    15
),
(
    'bbbb0000-0000-0000-0000-000000000005',
    'aaaa3333-0000-0000-0000-000000000003',
    '[
        {"manager_rating": 1, "count": 8},
        {"manager_rating": 2, "count": 22},
        {"manager_rating": 3, "count": 65},
        {"manager_rating": 4, "count": 78},
        {"manager_rating": 5, "count": 42}
    ]'::jsonb,
    5,
    12
);
