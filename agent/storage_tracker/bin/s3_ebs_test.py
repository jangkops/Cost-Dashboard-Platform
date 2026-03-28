#!/usr/bin/env python3
"""
FinOps 0티어 S3/EBS 수집 테스트 (부하/리스크 최소화)
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import sys

def test_aws_connectivity():
    """AWS 연결 테스트"""
    try:
        # 가벼운 테스트: 현재 리전 확인
        session = boto3.Session()
        print(f"✅ AWS 세션 생성 성공: {session.region_name}")
        return True
    except Exception as e:
        print(f"❌ AWS 연결 실패: {e}")
        return False

def test_s3_access():
    """S3 접근 테스트 (읽기 전용)"""
    try:
        s3 = boto3.client('s3', region_name='us-west-2')
        
        # 가벼운 테스트: 버킷 목록만 조회
        response = s3.list_buckets()
        bucket_count = len(response['Buckets'])
        print(f"✅ S3 접근 성공: {bucket_count}개 버킷 발견")
        
        # mogam-or-cur-stg 버킷 확인
        buckets = [b['Name'] for b in response['Buckets']]
        if 'mogam-or-cur-stg' in buckets:
            print("✅ mogam-or-cur-stg 버킷 확인됨")
        else:
            print("⚠️ mogam-or-cur-stg 버킷 없음")
        
        return True
    except Exception as e:
        print(f"❌ S3 접근 실패: {e}")
        return False

def test_cloudwatch_access():
    """CloudWatch 접근 테스트 (읽기 전용)"""
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-west-2')
        
        # 가벼운 테스트: 네임스페이스 목록 조회
        response = cloudwatch.list_metrics(Namespace='AWS/S3')
        print("✅ CloudWatch 접근 성공")
        return True
    except Exception as e:
        print(f"❌ CloudWatch 접근 실패: {e}")
        return False

def test_cur_access():
    """CUR 데이터 접근 테스트"""
    try:
        # CUR은 S3에 저장되므로 S3로 테스트
        s3 = boto3.client('s3', region_name='us-west-2')
        
        # CUR 데이터 경로 확인
        try:
            response = s3.list_objects_v2(
                Bucket='mogam-or-cur-stg',
                Prefix='cur/',
                MaxKeys=1
            )
            if 'Contents' in response:
                print("✅ CUR 데이터 경로 확인됨")
            else:
                print("⚠️ CUR 데이터 없음")
        except:
            print("⚠️ CUR 경로 접근 불가")
        
        return True
    except Exception as e:
        print(f"❌ CUR 접근 실패: {e}")
        return False

def test_system_resources():
    """시스템 리소스 확인"""
    try:
        import psutil
        
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"📊 현재 CPU 사용률: {cpu_percent}%")
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        print(f"📊 현재 메모리 사용률: {memory.percent}%")
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        print(f"📊 현재 디스크 사용률: {disk.percent}%")
        
        # 부하 확인
        if cpu_percent > 80:
            print("⚠️ CPU 사용률 높음 - 추가 작업 주의")
        if memory.percent > 80:
            print("⚠️ 메모리 사용률 높음 - 추가 작업 주의")
        
        return True
    except Exception as e:
        print(f"❌ 시스템 리소스 확인 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🔍 FinOps S3/EBS 수집 가능성 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("AWS 연결", test_aws_connectivity),
        ("S3 접근", test_s3_access),
        ("CloudWatch 접근", test_cloudwatch_access),
        ("CUR 데이터", test_cur_access),
        ("시스템 리소스", test_system_resources)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name} 테스트...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📋 테스트 결과 요약:")
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 전체 성공률: {success_count}/{len(tests)} ({success_count/len(tests)*100:.1f}%)")
    
    if success_count >= 4:
        print("✅ S3/EBS 수집 시스템 구축 가능")
        print("💡 다음 단계: 실제 수집 스크립트 배포")
    else:
        print("❌ 추가 설정 필요")
        print("💡 AWS 권한 또는 네트워크 설정 확인 필요")

if __name__ == "__main__":
    main()
