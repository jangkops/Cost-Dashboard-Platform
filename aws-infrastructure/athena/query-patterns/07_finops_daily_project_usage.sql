-- FinOps 일별 프로젝트/사용자별 GPU/CPU 사용량 | DB: cost_monitoring
SELECT
    p.project,
    p.username,
    instance_type,
    SUM(p.gpu_count) as total_gpu_samples,
    SUM(p.cpu_percent) as total_cpu_seconds
FROM enhanced_metrics_v2
CROSS JOIN UNNEST(processes) AS t(p)
WHERE year='2026'
  AND month='03'
  AND day='25'
  AND p.project != 'unknown'
  AND p.project IS NOT NULL
GROUP BY p.project, p.username, instance_type
