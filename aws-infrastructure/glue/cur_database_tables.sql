-- Glue Database: cur_database
-- CatalogId: 107650139384
-- Description: AWS Cost and Usage Report
-- LocationUri: s3://mogam-or-cur-stg/athena-cur/

CREATE EXTERNAL TABLE cur_database.mogam_hourly_cur (
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
    line_item_unblended_cost                           DOUBLE,
    line_item_blended_cost                             DOUBLE,
    product_product_name                               STRING,
    product_instance_type                              STRING,
    pricing_public_on_demand_cost                      DOUBLE,
    pricing_term                                       STRING,
    reservation_effective_cost                         DOUBLE,
    savings_plan_savings_plan_effective_cost           DOUBLE
    -- ... 178 columns total (full schema in Glue catalog)
)
PARTITIONED BY (year STRING, month STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
         OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://mogam-or-cur-stg/cur/mogam-hourly-cur/mogam-hourly-cur';
