-- Create database
CREATE DATABASE IF NOT EXISTS cost_monitoring;

-- Create metrics table (from Firehose/S3)
CREATE EXTERNAL TABLE IF NOT EXISTS cost_monitoring.activity_metrics (
    timestamp STRING,
    instance_id STRING,
    username STRING,
    project STRING,
    gpu_id INT,
    gpu_util DOUBLE,
    cpu_util DOUBLE,
    activity_score DOUBLE
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://your-bucket/cost-monitoring/metrics/'
TBLPROPERTIES ('has_encrypted_data'='false');

-- Cost allocation query with CUR integration
CREATE OR REPLACE VIEW cost_monitoring.monthly_cost_allocation AS
WITH 
-- Step 1: Calculate total activity score per instance per day
instance_scores AS (
    SELECT 
        instance_id,
        project,
        year,
        month,
        day,
        SUM(activity_score) as project_score
    FROM cost_monitoring.activity_metrics
    WHERE year = '2025' AND month = '12'  -- Parameterize this
    GROUP BY instance_id, project, year, month, day
),
-- Step 2: Calculate total score per instance per day
instance_totals AS (
    SELECT 
        instance_id,
        year,
        month,
        day,
        SUM(project_score) as total_score
    FROM instance_scores
    GROUP BY instance_id, year, month, day
),
-- Step 3: Get actual costs from CUR
instance_costs AS (
    SELECT 
        line_item_resource_id as instance_id,
        DATE_FORMAT(line_item_usage_start_date, '%Y') as year,
        DATE_FORMAT(line_item_usage_start_date, '%m') as month,
        DATE_FORMAT(line_item_usage_start_date, '%d') as day,
        SUM(
            CASE 
                WHEN line_item_line_item_type = 'DiscountedUsage' 
                    THEN reservation_effective_cost
                WHEN line_item_line_item_type = 'SavingsPlanCoveredUsage' 
                    THEN savings_plan_savings_plan_effective_cost
                ELSE line_item_unblended_cost
            END
        ) as daily_cost
    FROM cur_database.cur_table  -- Replace with your CUR table
    WHERE year = '2025' 
        AND month = '12'
        AND line_item_product_code = 'AmazonEC2'
        AND line_item_resource_id LIKE 'i-%'
    GROUP BY line_item_resource_id, 
        DATE_FORMAT(line_item_usage_start_date, '%Y'),
        DATE_FORMAT(line_item_usage_start_date, '%m'),
        DATE_FORMAT(line_item_usage_start_date, '%d')
)
-- Step 4: Allocate costs proportionally
SELECT 
    s.project,
    s.instance_id,
    CONCAT(s.year, '-', s.month) as month,
    SUM(
        CASE 
            WHEN t.total_score > 0 
            THEN (s.project_score / t.total_score) * c.daily_cost
            ELSE c.daily_cost / (SELECT COUNT(DISTINCT project) 
                                 FROM instance_scores s2 
                                 WHERE s2.instance_id = s.instance_id 
                                   AND s2.year = s.year 
                                   AND s2.month = s.month 
                                   AND s2.day = s.day)
        END
    ) as total_cost,
    COUNT(DISTINCT s.day) as active_days
FROM instance_scores s
JOIN instance_totals t 
    ON s.instance_id = t.instance_id 
    AND s.year = t.year 
    AND s.month = t.month 
    AND s.day = t.day
JOIN instance_costs c 
    ON s.instance_id = c.instance_id 
    AND s.year = c.year 
    AND s.month = c.month 
    AND s.day = c.day
GROUP BY s.project, s.instance_id, CONCAT(s.year, '-', s.month)
ORDER BY total_cost DESC;
