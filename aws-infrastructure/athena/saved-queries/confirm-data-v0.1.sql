-- Saved Query: confirm-data-v0.1
-- WorkGroup: cost-monitoring | Database: cost_monitoring
-- 사용자/프로젝트별 일별 비용 산출 검증 쿼리

WITH
user_daily_stats AS (
    SELECT instance_id, project_code, username,
        DATE(from_iso8601_timestamp(timestamp) + INTERVAL '9' HOUR) as usage_date,
        SUM((COALESCE(CAST(gpu_utilization AS DOUBLE), 0) * 1.0) +
            (COALESCE(CAST(cpu_utilization AS DOUBLE), 0) * 0.5)) as activity_score,
        COUNT(*) as metric_count
    FROM "cost_monitoring"."instance_metrics_new"
    WHERE year = '2025' AND month = '12' AND day IN ('03','04','05') AND instance_id LIKE 'i-%'
    GROUP BY 1, 2, 3, 4
),
instance_daily_total AS (
    SELECT instance_id, usage_date, SUM(activity_score) as total_score
    FROM user_daily_stats GROUP BY 1, 2
),
cur_daily_cost AS (
    SELECT line_item_resource_id as instance_id,
        DATE(line_item_usage_start_date + INTERVAL '9' HOUR) as usage_date,
        SUM(COALESCE(reservation_effective_cost,0) + COALESCE(savings_plan_savings_plan_effective_cost,0) + COALESCE(line_item_unblended_cost,0)) as real_cost_usd,
        SUM(COALESCE(pricing_public_on_demand_cost,0)) as on_demand_cost_usd,
        MAX(product_instance_type) as instance_type
    FROM "cost_monitoring"."mogam_hourly_cur"
    WHERE year = '2025' AND month = '12' AND line_item_resource_id LIKE 'i-%'
    GROUP BY 1, 2
)
SELECT u.usage_date as "Date (KST)", u.project_code as "Project", u.username as "User",
    u.instance_id as "Instance ID", c.instance_type as "Type",
    ROUND((u.activity_score / t.total_score) * c.real_cost_usd, 4) as allocated_cost_usd,
    ROUND((u.activity_score / t.total_score) * c.on_demand_cost_usd, 4) as on_demand_equivalent_usd,
    ROUND((u.activity_score / t.total_score) * 100, 2) as usage_percent,
    u.metric_count as "Active Minutes"
FROM user_daily_stats u
JOIN instance_daily_total t ON u.instance_id = t.instance_id AND u.usage_date = t.usage_date
JOIN cur_daily_cost c ON u.instance_id = c.instance_id AND u.usage_date = c.usage_date
ORDER BY allocated_cost_usd DESC;
