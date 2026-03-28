-- 월간 EC2 총 비용 (RI/SP/OD 통합) | DB: cur_database | 실행빈도: ~16x/day
SELECT SUM(CASE
    WHEN line_item_line_item_type = 'Usage' THEN line_item_unblended_cost
    WHEN line_item_line_item_type = 'DiscountedUsage' THEN reservation_effective_cost
    WHEN line_item_line_item_type = 'SavingsPlanCoveredUsage' THEN savings_plan_savings_plan_effective_cost
    ELSE 0 END) as cost
FROM cur_database.mogam_hourly_cur
WHERE year='2026' AND month='3'
  AND DATE(line_item_usage_start_date) <= CURRENT_DATE
  AND line_item_product_code = 'AmazonEC2'
  AND line_item_resource_id LIKE 'i-%'
