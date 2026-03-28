-- CUR 테이블 파티션 자동 추가 | DB: cur_database | 실행: 매 요청 시 (캐시됨)
ALTER TABLE cur_database.mogam_hourly_cur
ADD IF NOT EXISTS PARTITION (year='2026', month='3')
