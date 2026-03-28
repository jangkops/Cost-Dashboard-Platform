-- S3/FSx 스토리지 월간 비용 | DB: cost_monitoring
SELECT CASE WHEN product_product_name='Amazon Simple Storage Service' THEN 'S3'
            WHEN product_product_name LIKE '%FSx%' THEN 'FSx' END AS svc,
  SUM(CASE WHEN line_item_line_item_type='SavingsPlanCoveredUsage' THEN savings_plan_savings_plan_effective_cost
           WHEN line_item_line_item_type='SavingsPlanNegation' THEN 0
           WHEN line_item_line_item_type='DiscountedUsage' THEN reservation_effective_cost
           ELSE line_item_unblended_cost END)
FROM cur_database.mogam_hourly_cur
WHERE year='2026' AND month='3'
  AND (product_product_name='Amazon Simple Storage Service' OR product_product_name LIKE '%FSx%')
GROUP BY 1
