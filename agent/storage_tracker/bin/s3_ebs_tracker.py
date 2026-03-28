#!/usr/bin/env python3
"""
FinOps 0티어 S3/EBS 실제 비용 수집 시스템
30분 간격 실행, Enhanced Agent v2.0과 통합
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/app/ansible/cost_monitoring/storage_tracker/logs/tracker.log'),
        logging.StreamHandler()
    ]
)

class S3EBSCostTracker:
    """S3/EBS 실제 비용 추적"""
    
    def __init__(self):
        self.s3 = boto3.client('s3', region_name='us-west-2')
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-west-2')
        self.ec2 = boto3.client('ec2', region_name='us-west-2')
        
        # 프로젝트 매핑 (Enhanced Agent v2.0 기반)
        self.project_patterns = {
            'cds_bart_v2': ['cds', 'bart', 'hermee'],
            'UTR_diffusion': ['utr', 'diffusion', 'jwlee'],
            'P240003_MGC_DEV': ['mgc', 'dev', 'hslee', 'ckkang'],
            'DuET': ['duet', 'sbkim'],
            'GEMORNA': ['gemorna', 'ymbaek']
        }
    
    def get_s3_costs_by_project(self):
        """프로젝트별 S3 비용 수집"""
        try:
            project_costs = {}
            
            # 모든 버킷 조회
            buckets = self.s3.list_buckets()['Buckets']
            logging.info(f"S3 버킷 {len(buckets)}개 발견")
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                # 버킷 크기 조회 (CloudWatch)
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=datetime.utcnow() - timedelta(days=1),
                        EndTime=datetime.utcnow(),
                        Period=86400,  # 1일
                        Statistics=['Average']
                    )
                    
                    if response['Datapoints']:
                        size_bytes = response['Datapoints'][-1]['Average']
                        size_gb = size_bytes / (1024**3)
                        
                        # 프로젝트 매핑
                        project = self.map_bucket_to_project(bucket_name)
                        
                        if project not in project_costs:
                            project_costs[project] = {
                                'storage_gb': 0,
                                'monthly_cost': 0,
                                'buckets': []
                            }
                        
                        # S3 Standard 요금: $0.023/GB/월
                        monthly_cost = size_gb * 0.023
                        
                        project_costs[project]['storage_gb'] += size_gb
                        project_costs[project]['monthly_cost'] += monthly_cost
                        project_costs[project]['buckets'].append({
                            'name': bucket_name,
                            'size_gb': round(size_gb, 2),
                            'cost': round(monthly_cost, 2)
                        })
                        
                        logging.info(f"S3 {bucket_name}: {size_gb:.2f}GB → {project}")
                
                except Exception as e:
                    logging.warning(f"S3 버킷 {bucket_name} 메트릭 조회 실패: {e}")
                    continue
            
            return project_costs
            
        except Exception as e:
            logging.error(f"S3 비용 수집 실패: {e}")
            return {}
    
    def get_ebs_costs_by_project(self):
        """프로젝트별 EBS 비용 수집"""
        try:
            project_costs = {}
            
            # 모든 EBS 볼륨 조회
            volumes = self.ec2.describe_volumes()['Volumes']
            logging.info(f"EBS 볼륨 {len(volumes)}개 발견")
            
            for volume in volumes:
                volume_id = volume['VolumeId']
                volume_type = volume['VolumeType']
                size_gb = volume['Size']
                
                # 인스턴스 연결 확인
                instance_id = None
                if volume['Attachments']:
                    instance_id = volume['Attachments'][0]['InstanceId']
                
                # 프로젝트 매핑 (인스턴스 기반)
                project = self.map_instance_to_project(instance_id)
                
                if project not in project_costs:
                    project_costs[project] = {
                        'storage_gb': 0,
                        'monthly_cost': 0,
                        'volumes': []
                    }
                
                # EBS 요금 (볼륨 타입별)
                ebs_pricing = {
                    'gp3': 0.08,    # $0.08/GB/월
                    'gp2': 0.10,    # $0.10/GB/월
                    'io1': 0.125,   # $0.125/GB/월
                    'io2': 0.125    # $0.125/GB/월
                }
                
                cost_per_gb = ebs_pricing.get(volume_type, 0.08)
                monthly_cost = size_gb * cost_per_gb
                
                project_costs[project]['storage_gb'] += size_gb
                project_costs[project]['monthly_cost'] += monthly_cost
                project_costs[project]['volumes'].append({
                    'volume_id': volume_id,
                    'instance_id': instance_id,
                    'type': volume_type,
                    'size_gb': size_gb,
                    'cost': round(monthly_cost, 2)
                })
                
                logging.info(f"EBS {volume_id}: {size_gb}GB {volume_type} → {project}")
            
            return project_costs
            
        except Exception as e:
            logging.error(f"EBS 비용 수집 실패: {e}")
            return {}
    
    def map_bucket_to_project(self, bucket_name):
        """버킷명으로 프로젝트 매핑"""
        bucket_lower = bucket_name.lower()
        
        for project, patterns in self.project_patterns.items():
            for pattern in patterns:
                if pattern.lower() in bucket_lower:
                    return project
        
        return 'unknown'
    
    def map_instance_to_project(self, instance_id):
        """인스턴스로 프로젝트 매핑"""
        if not instance_id:
            return 'unknown'
        
        # 인스턴스별 기본 프로젝트 (Enhanced Agent v2.0 데이터 기반)
        instance_mapping = {
            'i-0d53ba43b64510164': 'cds_bart_v2',      # P4DE
            'i-0dc3c13df82448939': 'UTR_diffusion',    # G5
            'i-0c30cae12f60d69d1': 'P240003_MGC_DEV',  # R7
            'i-074a73c3cf9656989': 'queue_management'   # HEAD
        }
        
        return instance_mapping.get(instance_id, 'unknown')
    
    def collect_and_upload(self):
        """수집 및 S3 업로드"""
        try:
            logging.info("S3/EBS 비용 수집 시작")
            
            # 데이터 수집
            s3_costs = self.get_s3_costs_by_project()
            ebs_costs = self.get_ebs_costs_by_project()
            
            # 통합 데이터 구성
            storage_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'collection_source': 'ans_instance_storage_tracker',
                'data_type': 'storage_costs',
                's3_costs': s3_costs,
                'ebs_costs': ebs_costs,
                'summary': {
                    'total_s3_cost': sum(p['monthly_cost'] for p in s3_costs.values()),
                    'total_ebs_cost': sum(p['monthly_cost'] for p in ebs_costs.values()),
                    'projects_tracked': len(set(list(s3_costs.keys()) + list(ebs_costs.keys())))
                }
            }
            
            # S3에 업로드 (Enhanced Agent v2.0과 같은 버킷)
            timestamp = datetime.utcnow()
            s3_key = f"metrics/storage_costs/{timestamp.strftime('%Y/%m/%d/%H')}/storage_costs_{int(time.time())}.json"
            
            self.s3.put_object(
                Bucket='mogam-or-cur-stg',
                Key=s3_key,
                Body=json.dumps(storage_metrics, indent=2),
                ContentType='application/json'
            )
            
            logging.info(f"스토리지 비용 데이터 업로드 완료: {s3_key}")
            logging.info(f"총 S3 비용: ${storage_metrics['summary']['total_s3_cost']:.2f}")
            logging.info(f"총 EBS 비용: ${storage_metrics['summary']['total_ebs_cost']:.2f}")
            
            return True
            
        except Exception as e:
            logging.error(f"수집/업로드 실패: {e}")
            return False

def main():
    """메인 실행 루프"""
    tracker = S3EBSCostTracker()
    
    logging.info("FinOps S3/EBS 비용 추적 시스템 시작")
    logging.info("30분 간격으로 실행됩니다")
    
    while True:
        try:
            success = tracker.collect_and_upload()
            if success:
                logging.info("수집 완료, 30분 대기 중...")
            else:
                logging.error("수집 실패, 30분 후 재시도...")
            
            # 30분 대기
            time.sleep(1800)
            
        except KeyboardInterrupt:
            logging.info("사용자에 의해 중단됨")
            break
        except Exception as e:
            logging.error(f"예상치 못한 오류: {e}")
            logging.info("30분 후 재시도...")
            time.sleep(1800)

if __name__ == "__main__":
    main()
