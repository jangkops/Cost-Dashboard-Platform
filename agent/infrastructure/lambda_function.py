import json
import boto3
import time
from datetime import datetime

athena = boto3.client('athena')
s3 = boto3.client('s3')

DATABASE = 'cost_monitoring'
OUTPUT_LOCATION = 's3://your-athena-results-bucket/queries/'

def lambda_handler(event, context):
    """
    Query monthly cost allocation from Athena
    Query params: year, month
    """
    try:
        # Parse parameters
        params = event.get('queryStringParameters', {})
        year = params.get('year', datetime.now().strftime('%Y'))
        month = params.get('month', datetime.now().strftime('%m'))
        
        # Build query
        query = f"""
        WITH 
        instance_scores AS (
            SELECT 
                instance_id, project, year, month, day,
                SUM(activity_score) as project_score
            FROM {DATABASE}.activity_metrics
            WHERE year = '{year}' AND month = '{month}'
            GROUP BY instance_id, project, year, month, day
        ),
        instance_totals AS (
            SELECT 
                instance_id, year, month, day,
                SUM(project_score) as total_score
            FROM instance_scores
            GROUP BY instance_id, year, month, day
        ),
        instance_costs AS (
            SELECT 
                line_item_resource_id as instance_id,
                DATE_FORMAT(line_item_usage_start_date, '%Y') as year,
                DATE_FORMAT(line_item_usage_start_date, '%m') as month,
                DATE_FORMAT(line_item_usage_start_date, '%d') as day,
                SUM(
                    CASE 
                        WHEN line_item_line_item_type = 'DiscountedUsage' 
                            THEN reservation_effective_cost
                        WHEN line_item_line_item_type = 'SavingsPlanCoveredUsage' 
                            THEN savings_plan_savings_plan_effective_cost
                        ELSE line_item_unblended_cost
                    END
                ) as daily_cost
            FROM cur_database.cur_table
            WHERE year = '{year}' AND month = '{month}'
                AND line_item_product_code = 'AmazonEC2'
                AND line_item_resource_id LIKE 'i-%'
            GROUP BY line_item_resource_id, 
                DATE_FORMAT(line_item_usage_start_date, '%Y'),
                DATE_FORMAT(line_item_usage_start_date, '%m'),
                DATE_FORMAT(line_item_usage_start_date, '%d')
        )
        SELECT 
            s.project,
            s.instance_id,
            CONCAT(s.year, '-', s.month) as month,
            ROUND(SUM(
                CASE 
                    WHEN t.total_score > 0 
                    THEN (s.project_score / t.total_score) * c.daily_cost
                    ELSE 0
                END
            ), 2) as total_cost,
            COUNT(DISTINCT s.day) as active_days
        FROM instance_scores s
        JOIN instance_totals t 
            ON s.instance_id = t.instance_id 
            AND s.year = t.year AND s.month = t.month AND s.day = t.day
        JOIN instance_costs c 
            ON s.instance_id = c.instance_id 
            AND s.year = c.year AND s.month = c.month AND s.day = c.day
        GROUP BY s.project, s.instance_id, CONCAT(s.year, '-', s.month)
        ORDER BY total_cost DESC
        """
        
        # Start query execution
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': DATABASE},
            ResultConfiguration={'OutputLocation': OUTPUT_LOCATION}
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Poll for completion (max 60 seconds)
        max_attempts = 60
        for attempt in range(max_attempts):
            query_status = athena.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            status = query_status['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                break
            elif status in ['FAILED', 'CANCELLED']:
                error_msg = query_status['QueryExecution']['Status'].get(
                    'StateChangeReason', 'Query failed'
                )
                raise Exception(f"Query failed: {error_msg}")
            
            time.sleep(1)
        
        if status != 'SUCCEEDED':
            raise Exception("Query timeout")
        
        # Get results
        results = athena.get_query_results(
            QueryExecutionId=query_execution_id,
            MaxResults=1000
        )
        
        # Parse results
        columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        rows = results['ResultSet']['Rows'][1:]  # Skip header
        
        data = []
        for row in rows:
            values = [field.get('VarCharValue', '') for field in row['Data']]
            data.append(dict(zip(columns, values)))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'success': True,
                'data': data,
                'year': year,
                'month': month
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
