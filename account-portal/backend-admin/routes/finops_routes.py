from flask import Blueprint, jsonify, request
import boto3
import json
from datetime import datetime, timedelta
from collections import defaultdict

finops_bp = Blueprint('finops', __name__, url_prefix='/api/finops')

s3_client = boto3.client('s3')
BUCKET_NAME = 'mogam-or-cur-stg'

GPU_WEIGHT = 9
CPU_WEIGHT = 0.9
MEMORY_WEIGHT = 0.1

INSTANCE_SPECS = {
    'p4de.24xlarge': {'vcpu': 96, 'memory_gb': 1152, 'gpu_count': 8, 'hourly_ri': 40.96},
    'p4d.24xlarge': {'vcpu': 96, 'memory_gb': 1152, 'gpu_count': 8, 'hourly_ri': 32.77},
    'g5.12xlarge': {'vcpu': 48, 'memory_gb': 192, 'gpu_count': 4, 'hourly_ri': 5.67},
    'r7i.4xlarge': {'vcpu': 16, 'memory_gb': 128, 'gpu_count': 0, 'hourly_ri': 0.6651},
    'g4dn.xlarge': {'vcpu': 4, 'memory_gb': 16, 'gpu_count': 1, 'hourly_ri': 0.3144}
}

def calculate_unit_costs(instance_type):
    spec = INSTANCE_SPECS.get(instance_type)
    if not spec:
        return None
    
    hourly_cost = spec['hourly_ri']
    gpu_count = spec['gpu_count']
    vcpu_count = spec['vcpu']
    memory_gb = spec['memory_gb']
    
    if gpu_count > 0:
        unit_cost = hourly_cost / ((GPU_WEIGHT * gpu_count) + (CPU_WEIGHT * vcpu_count) + (MEMORY_WEIGHT * memory_gb))
        return {
            'cost_per_gpu_hour': GPU_WEIGHT * unit_cost,
            'cost_per_vcpu_hour': CPU_WEIGHT * unit_cost,
            'cost_per_gb_hour': MEMORY_WEIGHT * unit_cost,
            'total_gpu': gpu_count,
            'total_vcpu': vcpu_count,
            'total_memory': memory_gb
        }
    else:
        unit_cost = hourly_cost / ((9 * vcpu_count) + (1 * memory_gb))
        return {
            'cost_per_gpu_hour': 0,
            'cost_per_vcpu_hour': 9 * unit_cost,
            'cost_per_gb_hour': 1 * unit_cost,
            'total_gpu': 0,
            'total_vcpu': vcpu_count,
            'total_memory': memory_gb
        }

@finops_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    try:
        metrics_data = get_recent_metrics()
        project_costs = calculate_project_costs(metrics_data)
        usage_stats = calculate_usage_statistics(metrics_data)
        
        return jsonify({
            'success': True,
            'data': {
                'project_costs': project_costs,
                'usage_stats': usage_stats,
                'last_updated': datetime.now().isoformat(),
                'metrics_count': len(metrics_data)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_recent_metrics():
    """최근 1시간 전체 데이터 수집"""
    try:
        now = datetime.utcnow()
        dt = now
        prefix = f"metrics/enhanced_v2/{dt.year}/{dt.month:02d}/{dt.day:02d}/{dt.hour:02d}/"
        
        metrics_data = []
        continuation_token = None
        
        while True:
            if continuation_token:
                response = s3_client.list_objects_v2(
                    Bucket=BUCKET_NAME,
                    Prefix=prefix,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3_client.list_objects_v2(
                    Bucket=BUCKET_NAME,
                    Prefix=prefix
                )
            
            if 'Contents' not in response:
                break
            
            for obj in response['Contents']:
                try:
                    file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    content = file_response['Body'].read().decode('utf-8')
                    
                    for line in content.strip().split('\n'):
                        if line:
                            data = json.loads(line)
                            metrics_data.append(data)
                except:
                    continue
            
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        
        return metrics_data
    except Exception as e:
        print(f"Error getting metrics: {e}")
        return []

def calculate_project_costs(metrics_data):
    project_costs = defaultdict(lambda: {
        'gpu_cost': 0, 'cpu_cost': 0, 'memory_cost': 0, 'total_cost': 0,
        'users': set(), 'gpu_hours': 0, 'cpu_hours': 0
    })
    
    unit_costs_cache = {}
    
    for metric in metrics_data:
        if 'processes' not in metric:
            continue
            
        instance_type = metric.get('instance_type', '')
        
        if instance_type not in unit_costs_cache:
            unit_costs = calculate_unit_costs(instance_type)
            if not unit_costs:
                continue
            unit_costs_cache[instance_type] = unit_costs
        else:
            unit_costs = unit_costs_cache[instance_type]
        
        for process in metric['processes']:
            project = process.get('project', 'unknown')
            user = process.get('username', 'unknown')
            
            if project == 'unknown':
                continue
            
            gpu_count = process.get('gpu_count', 0)
            if gpu_count > 0 and unit_costs['total_gpu'] > 0:
                gpu_utilization = gpu_count / unit_costs['total_gpu']
                gpu_cost = gpu_utilization * unit_costs['total_gpu'] * unit_costs['cost_per_gpu_hour'] / 60
                project_costs[project]['gpu_cost'] += gpu_cost
                project_costs[project]['gpu_hours'] += gpu_count / 60
            
            cpu_time_seconds = process.get('cpu_percent', 0)
            if cpu_time_seconds > 0:
                cpu_time_hours = cpu_time_seconds / 3600
                cpu_cost = cpu_time_hours * unit_costs['cost_per_vcpu_hour']
                project_costs[project]['cpu_cost'] += cpu_cost
                project_costs[project]['cpu_hours'] += cpu_time_hours
            
            project_costs[project]['users'].add(user)
    
    result = {}
    for project, costs in project_costs.items():
        costs['total_cost'] = costs['gpu_cost'] + costs['cpu_cost'] + costs['memory_cost']
        costs['users'] = len(costs['users'])
        result[project] = {
            'gpu_cost': round(costs['gpu_cost'], 4),
            'cpu_cost': round(costs['cpu_cost'], 4),
            'memory_cost': round(costs['memory_cost'], 4),
            'total_cost': round(costs['total_cost'], 4),
            'users': costs['users'],
            'gpu_hours': round(costs['gpu_hours'], 4),
            'cpu_hours': round(costs['cpu_hours'], 4)
        }
    
    return result

def calculate_usage_statistics(metrics_data):
    stats = {
        'total_gpus': 21,
        'active_gpus': 0,
        'avg_cpu_usage': 0,
        'active_projects': set(),
        'active_users': set()
    }
    
    total_cpu_time = 0
    process_count = 0
    gpu_set = set()
    
    for metric in metrics_data:
        if 'processes' in metric:
            instance_id = metric.get('instance_id', '')
            for process in metric['processes']:
                gpu_devices = process.get('gpu_devices', [])
                for gpu_id in gpu_devices:
                    gpu_set.add(f"{instance_id}_{gpu_id}")
                
                cpu_time = process.get('cpu_percent', 0)
                if cpu_time > 0:
                    total_cpu_time += cpu_time
                    process_count += 1
                
                project = process.get('project', 'unknown')
                user = process.get('username', 'unknown')
                
                if project != 'unknown':
                    stats['active_projects'].add(project)
                if user != 'unknown':
                    stats['active_users'].add(user)
    
    stats['active_gpus'] = len(gpu_set)
    
    if process_count > 0:
        stats['avg_cpu_time_seconds'] = round(total_cpu_time / process_count, 2)
    else:
        stats['avg_cpu_time_seconds'] = 0
    
    stats['active_projects'] = len(stats['active_projects'])
    stats['active_users'] = len(stats['active_users'])
    
    return stats

@finops_bp.route('/daily/<date>', methods=['GET'])

def daily_costs(date):

    try:
        result = get_daily_costs(date)
        return jsonify(result)
    except Exception as e:
        print(f"Error in daily_costs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_daily_costs(date):
    """특정 날짜의 일일 비용 조회"""
    try:
        from datetime import datetime
        import time
        
        dt = datetime.strptime(date, '%Y-%m-%d')
        
        # 시간대 필터 추가 (00-23 모두 포함하되, 존재하는 시간만)
        query = f"""
        SELECT 
            p.project,
            p.username,
            instance_type,
            SUM(p.gpu_count) as total_gpu_samples,
            SUM(p.cpu_percent) as total_cpu_seconds
        FROM enhanced_metrics_v2
        CROSS JOIN UNNEST(processes) AS t(p)
        WHERE year='{dt.year}' 
          AND month='{dt.month:02d}' 
          AND day='{dt.day:02d}'
          AND p.project != 'unknown'
          AND p.project IS NOT NULL
        GROUP BY p.project, p.username, instance_type
        """
        
        athena_client = boto3.client('athena', region_name='us-west-2')
        
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': 'cost_monitoring'},
            ResultConfiguration={'OutputLocation': 's3://mogam-or-cur-stg/athena-results/'}
        )
        
        query_execution_id = response['QueryExecutionId']
        
        max_wait = 60  # 30초 -> 60초로 증가
        waited = 0
        while waited < max_wait:
            status_response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = status_response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                break
            elif status in ['FAILED', 'CANCELLED']:
                error_msg = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                print(f"Query failed for {date}: {error_msg}")
                return {'success': False, 'error': f'Query failed: {error_msg}', 'date': date}
            
            time.sleep(1)
            waited += 1
        
        if waited >= max_wait:
            return {'success': False, 'error': 'Query timeout', 'date': date}
        
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        
        project_costs = defaultdict(lambda: {
            'gpu_cost': 0, 'cpu_cost': 0, 'total_cost': 0,
            'gpu_hours': 0, 'cpu_hours': 0, 'users': set()
        })
        
        instance_costs = defaultdict(lambda: {
            'gpu_cost': 0, 'cpu_cost': 0, 'total_cost': 0,
            'gpu_hours': 0, 'cpu_hours': 0
        })
        
        unit_costs_cache = {}
        
        for row in results['ResultSet']['Rows'][1:]:
            values = [col.get('VarCharValue', '') for col in row['Data']]
            if len(values) < 5:
                continue
                
            project = values[0]
            username = values[1]
            instance_type = values[2]
            gpu_samples = float(values[3]) if values[3] else 0
            cpu_seconds = float(values[4]) if values[4] else 0
            
            if instance_type not in unit_costs_cache:
                unit_costs = calculate_unit_costs(instance_type)
                if not unit_costs:
                    continue
                unit_costs_cache[instance_type] = unit_costs
            else:
                unit_costs = unit_costs_cache[instance_type]
            
            if gpu_samples > 0:
                gpu_hours = gpu_samples / 60
                gpu_cost = gpu_hours * unit_costs['cost_per_gpu_hour']
                project_costs[project]['gpu_cost'] += gpu_cost
                project_costs[project]['gpu_hours'] += gpu_hours
                instance_costs[instance_type]['gpu_cost'] += gpu_cost
                instance_costs[instance_type]['gpu_hours'] += gpu_hours
            
            if cpu_seconds > 0:
                cpu_hours = cpu_seconds / 3600
                cpu_cost = cpu_hours * unit_costs['cost_per_vcpu_hour']
                project_costs[project]['cpu_cost'] += cpu_cost
                project_costs[project]['cpu_hours'] += cpu_hours
                instance_costs[instance_type]['cpu_cost'] += cpu_cost
                instance_costs[instance_type]['cpu_hours'] += cpu_hours
            
            project_costs[project]['users'].add(username)
        
        result = {}
        total_cost = 0
        for project, costs in project_costs.items():
            costs['total_cost'] = costs['gpu_cost'] + costs['cpu_cost']
            costs['users'] = len(costs['users'])
            result[project] = {
                'gpu_cost': round(costs['gpu_cost'], 4),
                'cpu_cost': round(costs['cpu_cost'], 4),
                'total_cost': round(costs['total_cost'], 4),
                'gpu_hours': round(costs['gpu_hours'], 2),
                'cpu_hours': round(costs['cpu_hours'], 2),
                'users': costs['users']
            }
            total_cost += costs['total_cost']
        
        instance_result = {}
        for inst, costs in instance_costs.items():
            costs['total_cost'] = costs['gpu_cost'] + costs['cpu_cost']
            instance_result[inst] = {
                'gpu_cost': round(costs['gpu_cost'], 4),
                'cpu_cost': round(costs['cpu_cost'], 4),
                'total_cost': round(costs['total_cost'], 4),
                'gpu_hours': round(costs['gpu_hours'], 2),
                'cpu_hours': round(costs['cpu_hours'], 2)
            }
        
        return {
            'success': True,
            'date': date,
            'project_costs': result,
            'instance_costs': instance_result,
            'total_cost': round(total_cost, 4),
            'projects_count': len(result),
            'instances_count': len(instance_result)
        }
        
    except Exception as e:
        print(f"Error in get_daily_costs: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e), 'date': date}


