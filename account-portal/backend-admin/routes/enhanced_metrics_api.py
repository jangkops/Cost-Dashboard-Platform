from flask import Blueprint, jsonify
import boto3
import json
from datetime import datetime, timedelta

enhanced_api = Blueprint('enhanced_api', __name__)

@enhanced_api.route('/api/enhanced/dashboard', methods=['GET'])
def get_enhanced_dashboard():
    try:
        # S3에서 실제 enhanced_daily_dashboard.json 읽기
        s3 = boto3.client('s3')
        response = s3.get_object(
            Bucket='mogam-or-cur-stg',
            Key='metrics/enhanced_daily_dashboard.json'
        )
        data = json.loads(response['Body'].read())
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_api.route('/api/enhanced/realtime', methods=['GET'])
def get_realtime_metrics():
    try:
        s3 = boto3.client('s3')
        # 최신 메트릭 파일 조회
        response = s3.list_objects_v2(
            Bucket='mogam-or-cur-stg',
            Prefix='metrics/enhanced_v2/',
            MaxKeys=10
        )
        files = sorted(response.get('Contents', []), key=lambda x: x['LastModified'], reverse=True)
        if files:
            latest = s3.get_object(Bucket='mogam-or-cur-stg', Key=files[0]['Key'])
            data = json.loads(latest['Body'].read())
            return jsonify(data)
        return jsonify({'error': 'No data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
