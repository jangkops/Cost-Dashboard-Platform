-- 일별 인스턴스별 비용 상세 (pricing type) | DB: cur_database | 실행빈도: ~16x/day
SELECT line_item_resource_id,
       SUM(CASE
           WHEN line_item_line_item_type = 'Usage' THEN line_item_unblended_cost
           WHEN line_item_line_item_type = 'DiscountedUsage' THEN reservation_effective_cost
           WHEN line_item_line_item_type = 'SavingsPlanCoveredUsage' THEN savings_plan_savings_plan_effective_cost
           ELSE 0 END) as cost,
       MAX(product_instance_type) as inst_type,
       SUM(pricing_public_on_demand_cost) as ondemand_cost,
       MAX(CASE WHEN line_item_line_item_type='DiscountedUsage' THEN 'RI'
                WHEN line_item_line_item_type='SavingsPlanCoveredUsage' THEN 'SP'
                WHEN line_item_line_item_type='Usage' THEN 'OD' ELSE '' END) as pricing_type
FROM cur_database.mogam_hourly_cur
WHERE DATE(line_item_usage_start_date) = CURRENT_DATE
  AND line_item_product_code = 'AmazonEC2' AND line_item_resource_id LIKE 'i-%'
GROUP BY line_item_resource_id
