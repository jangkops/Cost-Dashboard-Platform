-- S3 인벤토리 프로젝트별 용량 집계 | DB: cost_monitoring
SELECT split_part(key,'/',2), SUM(size)
FROM cost_monitoring.s3_inventory_mogam_or
WHERE split_part(key,'/',2)!=''
GROUP BY 1
