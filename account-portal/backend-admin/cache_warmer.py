#!/usr/bin/env python3
"""
비용 데이터 캐시 워밍 스크립트
매일 새벽 실행하여 최근 60일 데이터를 Redis에 미리 저장
"""
import sys
sys.path.insert(0, '/app')

from routes.cost_monitoring import get_cost_data
from datetime import datetime, timedelta

def warm_cache(days=60):
    """최근 N일 데이터를 캐시에 저장"""
    today = datetime.now()
    
    for i in range(days):
        date = (today - timedelta(days=i+2)).strftime('%Y-%m-%d')  # 48시간 전부터
        try:
            print(f"Caching {date}...", end=' ')
            data = get_cost_data(date)
            print(f"OK (${data['total_cost']:.2f})")
        except Exception as e:
            print(f"FAIL: {e}")

if __name__ == '__main__':
    print("Starting cache warming...")
    warm_cache(60)
    print("Cache warming completed!")
