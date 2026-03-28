-- 일별 사용자/프로젝트별 GPU 메트릭 집계 | DB: cost_monitoring | 실행빈도: ~16x/day
SELECT instance_id, p.project, p.username,
       COUNT(*) as samples, SUM(p.gpu_count) as gpu_count,
       AVG(p.cpu_percent) as avg_cpu_percent, AVG(p.gpu_memory_mb) as avg_gpu_mem_mb,
       MAX(p.command) as command,
       ARRAY_JOIN(ARRAY_SORT(ARRAY_DISTINCT(FLATTEN(ARRAY_AGG(p.gpu_devices)))), ',') as gpu_device_list
FROM cost_monitoring.enhanced_metrics_v2
CROSS JOIN UNNEST(processes) AS t(p)
WHERE year='2026' AND month='03' AND day='25'
  AND instance_id != '' AND p.project IS NOT NULL
GROUP BY instance_id, p.project, p.username
