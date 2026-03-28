from flask import Blueprint, jsonify
import boto3
from functools import lru_cache
from datetime import datetime, timedelta

regions_bp = Blueprint("regions", __name__)

# 캐시: 5분간 유효
_cache = {"data": None, "timestamp": None}

@regions_bp.route("/api/regions", methods=["GET"])
def get_regions():
    """EC2 인스턴스가 있는 리전만 반환 (캐싱)"""
    try:
        now = datetime.now()
        
        # 캐시가 유효하면 반환
        if _cache["data"] and _cache["timestamp"]:
            if (now - _cache["timestamp"]) < timedelta(minutes=5):
                return jsonify({"regions": _cache["data"]})
        
        # 빠른 응답을 위해 주요 리전만 확인
        common_regions = ['us-east-1', 'us-west-2', 'ap-northeast-2', 'ap-northeast-1', 'eu-west-1']
        regions_with_instances = []
        
        for region in common_regions:
            try:
                ec2 = boto3.client('ec2', region_name=region)
                response = ec2.describe_instances(
                    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}],
                    MaxResults=5
                )
                
                if response.get('Reservations'):
                    regions_with_instances.append(region)
            except:
                continue
        
        # 캐시 업데이트
        _cache["data"] = sorted(regions_with_instances)
        _cache["timestamp"] = now
        
        return jsonify({"regions": _cache["data"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
