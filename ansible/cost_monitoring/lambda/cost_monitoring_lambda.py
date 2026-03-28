import json
import boto3
import time
import os

athena = boto3.client('athena')
s3 = boto3.client('s3')

DATABASE = 'cost_monitoring'
OUTPUT_LOCATION = 's3://mogam-or-cur-data/athena-results/'

def lambda_handler(event, context):
    params = event.get('queryStringParameters', {})
    year = params.get('year')
    month = params.get('month')
    
    if not year or not month:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'year and month required'})
        }
    
    query = f"""
    WITH user_activity AS (
        SELECT 
            username,
            project_code,
            SUM(gpu_utilization * 1.0 + cpu_utilization * 0.5) as activity_score
        FROM cost_monitoring.instance_metrics
        WHERE year = '{year}' AND month = '{month}'
        GROUP BY username, project_code
    ),
    instance_costs AS (
        SELECT 
            line_item_resource_id as instance_id,
            SUM(
                CASE 
                    WHEN line_item_line_item_type = 'DiscountedUsage' THEN reservation_effective_cost
                    WHEN line_item_line_item_type = 'SavingsPlanCoveredUsage' THEN savings_plan_savings_plan_effective_cost
                    ELSE line_item_unblended_cost
                END
            ) as total_cost
        FROM cost_monitoring.cur_data
        WHERE year = '{year}' AND month = '{month}'
        AND line_item_product_code = 'AmazonEC2'
        AND line_item_resource_id != ''
        GROUP BY line_item_resource_id
    )
    SELECT 
        ua.project_code,
        SUM(ic.total_cost * ua.activity_score / NULLIF(SUM(ua.activity_score) OVER (PARTITION BY ic.instance_id), 0)) as allocated_cost
    FROM user_activity ua
    JOIN instance_costs ic ON ua.username IN (
        SELECT username FROM cost_monitoring.instance_metrics WHERE instance_id = ic.instance_id
    )
    GROUP BY ua.project_code
    ORDER BY allocated_cost DESC
    """
    
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': OUTPUT_LOCATION}
    )
    
    query_id = response['QueryExecutionId']
    
    for _ in range(60):
        result = athena.get_query_execution(QueryExecutionId=query_id)
        state = result['QueryExecution']['Status']['State']
        
        if state == 'SUCCEEDED':
            results = athena.get_query_results(QueryExecutionId=query_id)
            rows = []
            for row in results['ResultSet']['Rows'][1:]:
                rows.append({
                    'project_code': row['Data'][0].get('VarCharValue', ''),
                    'cost': float(row['Data'][1].get('VarCharValue', '0'))
                })
            
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(rows)
            }
        elif state in ['FAILED', 'CANCELLED']:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Query failed'})
            }
        
        time.sleep(1)
    
    return {
        'statusCode': 504,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Query timeout'})
    }
