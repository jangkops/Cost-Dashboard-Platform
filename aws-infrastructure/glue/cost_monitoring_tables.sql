-- Glue Database: cost_monitoring
-- CatalogId: 107650139384
-- Description: Cost monitoring database for CUR data

-- ============================================================
-- Table: enhanced_metrics_v2 (GPU/CPU 메트릭 - 파티션 프로젝션)
-- ============================================================
CREATE EXTERNAL TABLE cost_monitoring.enhanced_metrics_v2 (
    `timestamp`         STRING,
    instance_id         STRING,
    instance_type       STRING,
    mode                STRING,
    agent_version       STRING,
    processes           ARRAY<STRUCT<
        pid:            INT,
        username:       STRING,
        project:        STRING,
        command:        STRING,
        cpu_percent:    DOUBLE,
        gpu_devices:    ARRAY<INT>,
        gpu_count:      INT,
        gpu_memory_mb:  DOUBLE
    >>,
    gpu_stats           ARRAY<STRUCT<
        gpu_id:         INT,
        gpu_util:       DOUBLE,
        mem_util:       DOUBLE,
        mem_used_mb:    DOUBLE,
        mem_total_mb:   DOUBLE
    >>,
    tmux_paths_loaded   INT,
    vscode_paths_loaded INT
)
PARTITIONED BY (year STRING, month STRING, day STRING, hour STRING)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
         OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://mogam-or-cur-stg/metrics/enhanced_v2'
TBLPROPERTIES (
    'projection.enabled'              = 'true',
    'projection.year.type'            = 'integer',
    'projection.year.range'           = '2025,2030',
    'projection.year.digits'          = '4',
    'projection.month.type'           = 'integer',
    'projection.month.range'          = '1,12',
    'projection.month.digits'         = '2',
    'projection.day.type'             = 'integer',
    'projection.day.range'            = '1,31',
    'projection.day.digits'           = '2',
    'projection.hour.type'            = 'integer',
    'projection.hour.range'           = '0,23',
    'projection.hour.digits'          = '2',
    'storage.location.template'       = 's3://mogam-or-cur-stg/metrics/enhanced_v2/${year}/${month}/${day}/${hour}'
);

-- ============================================================
-- Table: mogam_hourly_cur (AWS CUR 전체 - 220 columns)
-- ============================================================
CREATE EXTERNAL TABLE cost_monitoring.mogam_hourly_cur (
    identity_line_item_id                              STRING,
    identity_time_interval                             STRING,
    bill_invoice_id                                    STRING,
    bill_invoicing_entity                              STRING,
    bill_billing_entity                                STRING,
    bill_bill_type                                     STRING,
    bill_payer_account_id                              STRING,
    bill_billing_period_start_date                     TIMESTAMP,
    bill_billing_period_end_date                       TIMESTAMP,
    line_item_usage_account_id                         STRING,
    line_item_line_item_type                           STRING,
    line_item_usage_start_date                         TIMESTAMP,
    line_item_usage_end_date                           TIMESTAMP,
    line_item_product_code                             STRING,
    line_item_usage_type                               STRING,
    line_item_operation                                STRING,
    line_item_availability_zone                        STRING,
    line_item_resource_id                              STRING,
    line_item_usage_amount                             DOUBLE,
    line_item_normalization_factor                     DOUBLE,
    line_item_normalized_usage_amount                  DOUBLE,
    line_item_currency_code                            STRING,
    line_item_unblended_rate                           STRING,
    line_item_unblended_cost                           DOUBLE,
    line_item_blended_rate                             STRING,
    line_item_blended_cost                             DOUBLE,
    line_item_line_item_description                    STRING,
    line_item_tax_type                                 STRING,
    line_item_legal_entity                             STRING,
    product_product_name                               STRING,
    product_instance_type                              STRING,
    pricing_public_on_demand_cost                      DOUBLE,
    pricing_public_on_demand_rate                      STRING,
    pricing_term                                       STRING,
    pricing_unit                                       STRING,
    reservation_effective_cost                         DOUBLE,
    reservation_reservation_a_r_n                      STRING,
    savings_plan_savings_plan_effective_cost           DOUBLE,
    savings_plan_savings_plan_a_r_n                    STRING,
    savings_plan_savings_plan_rate                     DOUBLE,
    savings_plan_used_commitment                       DOUBLE,
    resource_tags_user_name                            STRING,
    resource_tags_user_service                         STRING,
    resource_tags_user_map_migrated                    STRING
    -- ... 220 columns total (full schema in Glue catalog)
)
PARTITIONED BY (year STRING, month STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
         OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://mogam-or-cur-stg/cur/mogam-hourly-cur/mogam-hourly-cur';

-- ============================================================
-- Table: cur_temp (CUR 경량 테이블)
-- ============================================================
CREATE EXTERNAL TABLE cost_monitoring.cur_temp (
    line_item_usage_start_date  STRING,
    line_item_product_code      STRING,
    line_item_resource_id       STRING,
    line_item_unblended_cost    DOUBLE
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
         OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://mogam-or-cur-stg/cur/mogam-hourly-cur/mogam-hourly-cur';

-- ============================================================
-- Table: s3_inventory_mogam_or (S3 인벤토리)
-- ============================================================
CREATE EXTERNAL TABLE cost_monitoring.s3_inventory_mogam_or (
    bucket              STRING,
    `key`               STRING,
    size                BIGINT,
    last_modified_date  TIMESTAMP,
    storage_class       STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
         OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://mogam-or-cur-stg/inventory/mogam-or/project-weekly-inventory/data';
