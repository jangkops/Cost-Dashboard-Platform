import json
import boto3
from datetime import datetime, timedelta
import re

def lambda_handler(event, context):
    try:
        # S3 클라이언트 초기화
        s3 = boto3.client('s3')
        bucket_name = 'mogam-or-cur-stg'
        
        # 기본 프로젝트 정의
        default_projects = {
            'mogam-research': {'description': '목암 연구 프로젝트', 'instances': []},
            'cluster-head': {'description': '클러스터 헤드 노드', 'instances': []},
            'cluster-compute': {'description': '클러스터 컴퓨트 노드', 'instances': []},
            'ai-training': {'description': 'AI 모델 훈련', 'instances': []},
            'data-processing': {'description': '데이터 처리', 'instances': []},
            'development': {'description': '개발 환경', 'instances': []},
            'production': {'description': '운영 환경', 'instances': []}
        }
        
        # 실제 메트릭 데이터 수집
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        # S3에서 최근 메트릭 파일들 조회
        prefix = 'metrics/'
        try:
            response = s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                StartAfter=f"{prefix}{yesterday.strftime('%Y-%m-%d')}"
            )
        except Exception as e:
            print(f"S3 list error: {e}")
            response = {}
        
        # 프로젝트별 메트릭 데이터 수집
        project_metrics = {}
        total_instances = 0
        
        # 기본 프로젝트 초기화
        for project_name, project_info in default_projects.items():
            project_metrics[project_name] = {
                'description': project_info['description'],
                'instances': set(),
                'total_cpu_util': 0,
                'total_gpu_util': 0,
                'gpu_instances': 0,
                'cpu_instances': 0,
                'weekly_cost': 0,  # 주간 비용 (가상)
                'monthly_cost': 0  # 월간 비용 (가상)
            }
        
        # 실제 메트릭 데이터가 있으면 처리
        if 'Contents' in response and len(response['Contents']) > 0:
            for obj in response['Contents'][-10:]:  # 최근 10개 파일만 처리
                try:
                    file_response = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
                    content = file_response['Body'].read().decode('utf-8')
                    
                    for line in content.strip().split('\n'):
                        if line:
                            metric = json.loads(line)
                            instance_id = metric.get('instance_id', 'unknown')
                            
                            # 프로젝트 분류 로직 개선
                            project = 'development'  # 기본값
                            if 'mogam-or-g5' in instance_id:
                                project = 'mogam-research'
                            elif 'head' in instance_id:
                                project = 'cluster-head'
                            elif 'compute' in instance_id:
                                project = 'cluster-compute'
                            elif 'gpu' in instance_id or metric.get('gpu_util', 0) > 0:
                                project = 'ai-training'
                            elif 'data' in instance_id:
                                project = 'data-processing'
                            elif 'prod' in instance_id:
                                project = 'production'
                            
                            if project not in project_metrics:
                                project_metrics[project] = {
                                    'description': f'{project} 프로젝트',
                                    'instances': set(),
                                    'total_cpu_util': 0,
                                    'total_gpu_util': 0,
                                    'gpu_instances': 0,
                                    'cpu_instances': 0,
                                    'weekly_cost': 0,
                                    'monthly_cost': 0
                                }
                            
                            project_metrics[project]['instances'].add(instance_id)
                            project_metrics[project]['total_cpu_util'] += metric.get('cpu_util', 0)
                            
                            if metric.get('gpu_util', 0) > 0:
                                project_metrics[project]['gpu_instances'] += 1
                                project_metrics[project]['total_gpu_util'] += metric.get('gpu_util', 0)
                            else:
                                project_metrics[project]['cpu_instances'] += 1
                            
                            total_instances += 1
                                
                except Exception as e:
                    print(f"Error processing file {obj['Key']}: {e}")
        
        # 프로젝트별 데이터 정리 및 비용 계산
        project_summary = {}
        for project, data in project_metrics.items():
            instance_count = len(data['instances'])
            
            # 가상 비용 계산 (인스턴스 수 기반)
            base_cost_per_instance = 50  # 인스턴스당 기본 비용 (USD/주)
            gpu_multiplier = 5  # GPU 인스턴스 비용 배수
            
            weekly_cost = instance_count * base_cost_per_instance
            if data['gpu_instances'] > 0:
                weekly_cost += data['gpu_instances'] * base_cost_per_instance * gpu_multiplier
            
            monthly_cost = weekly_cost * 4.33  # 주간 비용 * 4.33 (월평균 주수)
            
            project_summary[project] = {
                'description': data['description'],
                'instance_count': instance_count,
                'avg_cpu_util': round(data['total_cpu_util'] / instance_count, 2) if instance_count > 0 else 0,
                'avg_gpu_util': round(data['total_gpu_util'] / data['gpu_instances'], 2) if data['gpu_instances'] > 0 else 0,
                'gpu_instances': data['gpu_instances'],
                'cpu_instances': data['cpu_instances'],
                'weekly_cost': round(weekly_cost, 2),
                'monthly_cost': round(monthly_cost, 2)
            }
        
        # 빈 프로젝트 제거
        project_summary = {k: v for k, v in project_summary.items() if v['instance_count'] > 0}
        
        # CUR 데이터 확인
        cur_data_available = False
        try:
            cur_response = s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix='cur-data/',
                MaxKeys=1
            )
            cur_data_available = 'Contents' in cur_response and len(cur_response['Contents']) > 0
        except:
            cur_data_available = False
        
        dashboard_data = {
            'total_instances': total_instances,
            'project_metrics': project_summary,
            'cur_data_available': cur_data_available,
            'metrics_data_available': total_instances > 0,
            'total_weekly_cost': sum(p['weekly_cost'] for p in project_summary.values()),
            'total_monthly_cost': sum(p['monthly_cost'] for p in project_summary.values()),
            'last_updated': now.isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(dashboard_data)
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e), 'metrics_data_available': False})
        }
