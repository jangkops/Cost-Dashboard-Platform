# Cost Monitoring System

## 아키텍처

```
[EC2 6대] --agent(60s)--> S3 metrics/enhanced_v2/ (JSONL)
                                    |
                              Glue DDL 테이블
                                    |
                                 Athena
                               /   |   \
               enhanced_metrics  CUR  s3_inventory
                               \   |   /
                            backend-cost (Flask)
                                    |
                                  nginx
                                    |
                              React 대시보드

[mogam-or 버킷] --S3 Inventory(Weekly)--> s3_inventory_mogam_or
[AWS CUR] --hourly--> cur/mogam-hourly-cur/ (Parquet)
[BOK ECOS] --환율 API--> backend-cost
```

## 인스턴스 구성

| Instance ID | 타입 | 이름 | 일비용 (USD/KRW) | 용도 |
|---|---|---|---|---|
| i-004e23df368dcb30e | p5.48xlarge | mogam-or-p5 | $104/약 150,000 | GPU LLM 학습 |
| i-06a9b5df345d47eaa | p4d.24xlarge | mogam-or-p4d | $285/약 410,000 | GPU 연구 |
| i-0d53ba43b64510164 | p4de.24xlarge | mogam-or-p4de | $356/약 510,000 | GPU 연구 |
| i-0dc3c13df82448939 | g5.12xlarge | mogam-or-g5 | $81/약 115,000 | GPU 연구 |
| i-0c30cae12f60d69d1 | r7i.4xlarge | mogam-or-zonea-r7 | $16/약 23,000 | CPU 전용 |
| i-074a73c3cf9656989 | g4dn.xlarge | HeadNode (G4DN) | $7.5/약 10,000 | ParallelCluster 헤드노드 |

## S3 버킷: mogam-or-cur-stg

| 경로 | 용도 | 형식 |
|---|---|---|
| `metrics/enhanced_v2/` | 에이전트 수집 데이터 | JSONL (year/month/day/hour 파티션) |
| `cur/mogam-hourly-cur/` | AWS Cost & Usage Report | Parquet (year/month 파티션) |
| `inventory/mogam-or/project-weekly-inventory/` | S3 인벤토리 (mogam-or 버킷) | Parquet |
| `inventory-snapshots/` | 월말 인벤토리 스냅샷 (비용 확정용) | JSON (`YYYY-MM.json`) |
| `athena-results/` | Athena 쿼리 결과 | CSV |

## AWS Glue / Athena

### Database: cost_monitoring

| 테이블 | 설명 | 파티션 | 형식 | S3 위치 |
|---|---|---|---|---|
| enhanced_metrics_v2 | 에이전트 프로세스 메트릭 | year/month/day/hour | JSON | `metrics/enhanced_v2/` |
| s3_inventory_mogam_or | S3 인벤토리 (프로젝트별 용량) | 없음 | Parquet | `inventory/mogam-or/project-weekly-inventory/data/` |

### Database: cur_database

| 테이블 | 설명 | 파티션 | 형식 | S3 위치 |
|---|---|---|---|---|
| mogam_hourly_cur | AWS CUR (시간별 비용) | year/month | Parquet | `cur/mogam-hourly-cur/` |

### 주요 쿼리

```sql
-- 일별 EC2 비용 (SP/RI 할인 반영)
SELECT resource_id, SUM(CASE
  WHEN line_item_type='SavingsPlanCoveredUsage' THEN savings_plan_effective_cost
  WHEN line_item_type='DiscountedUsage' THEN reservation_effective_cost
  WHEN line_item_type='SavingsPlanNegation' THEN 0
  ELSE unblended_cost END) as cost
FROM cur_database.mogam_hourly_cur
WHERE year='2026' AND month='3' AND day(line_item_usage_start_date)=7
GROUP BY resource_id

-- 에이전트 데이터 (인스턴스별 프로젝트별 사용량)
SELECT instance_id, p.project, p.username, COUNT(*), SUM(p.gpu_count), AVG(p.cpu_percent)
FROM cost_monitoring.enhanced_metrics_v2
CROSS JOIN UNNEST(processes) AS t(p)
WHERE year='2026' AND month='03' AND day='07'
GROUP BY instance_id, p.project, p.username
```

## S3 인벤토리 설정

- 소스 버킷: mogam-or
- 대상: mogam-or-cur-stg/inventory/
- ID: project-weekly-inventory
- 주기: Weekly (AWS 자체 스케줄, 특정 요일 지정 불가)
- 필터: `project/` prefix
- 형식: Parquet
- 필드: Size, LastModifiedDate, StorageClass

## 에이전트

### 배포 위치
- 소스: `backend-cost/agent/`
- 각 인스턴스: Docker 컨테이너 `cost-monitoring-agent`

### 동작
- 60초 주기로 프로세스 수집
- GPU 인스턴스: nvidia-smi로 GPU 프로세스 + /proc에서 CPU 프로세스
- CPU 인스턴스: /proc에서 python, python3, java 프로세스만
- 프로젝트 추출: cwd 경로 기반 (`/fsx/home/`, `/fsx/s3/`, `/fsx/tmp/`, `/home/`, `/opt/`, `/local_nvme/`, `/workspace/`)
- S3 업로드: `s3://mogam-or-cur-stg/metrics/enhanced_v2/{year}/{month}/{day}/{hour}/`

### 배포
```bash
cd /home/app/ansible/cost_monitoring
chmod +x deploy.sh
./deploy.sh
```

## 백엔드 (backend-cost)

### 파일 구조
```
backend-cost/
  app.py                          # Flask 앱
  routes/
    cost_monitoring.py            # 비용 계산 로직
    finops_routes.py              # FinOps API
  utils/
    exchange_rate.py              # BOK ECOS 환율 API
  data/
    mappings.json                 # 프로젝트/사용자/인스턴스 매핑
```

### API

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/cost-monitoring/daily-costs/{date}` | 일별 비용 (48시간 지연) |
| `GET /api/cost-monitoring/monthly-costs/{year}/{month}` | 월별 비용 |
| `GET /api/cost-monitoring/storage-costs/{year}/{month}` | 스토리지 비용 (S3/FSx) |
| `POST /api/cost-monitoring/clear-cache` | 캐시 초기화 |
| `GET /api/cost-monitoring/mappings` | 매핑 데이터 조회 |
| `PUT /api/cost-monitoring/mappings/<category>` | 매핑 데이터 수정 (category별) |

### 비용 배분 로직 (EC2 4단계)

1. **CUR 데이터 조회**: 인스턴스별 일 비용 조회 (SP/RI 할인 반영)
2. **GPU/CPU 비용 분리**: 인스턴스 타입별 GPU/CPU 비율로 일비용을 GPU 풀과 CPU 풀로 분리
3. **에이전트 데이터 기반 weight 계산 → 프로젝트별 배분**
   - GPU weight: `samples × max(cpu, 10%) × (1 + gpu_count)`
   - CPU weight: `samples × max(cpu, 1%) / 100`
   - cpu=0이어도 프로세스가 존재하면 최소 weight 부여
   - GPU 풀은 GPU weight 비율로, CPU 풀은 CPU weight 비율로 각 프로젝트에 배분
4. **미배분 처리**: GPU 프로세스가 없는 인스턴스의 GPU 비용은 미배분(Unallocated)으로 처리

### GPU/CPU 비율

GPU 비율 = (GPU 인스턴스 시간당 가격 - 동일 vCPU 범용 인스턴스 시간당 가격) ÷ GPU 인스턴스 시간당 가격

기준: AWS EC2 On-Demand Pricing (us-west-2), 범용 인스턴스 m5 vCPU당 $0.048/hr

| 인스턴스 | 타입 | GPU 비율 | CPU 비율 | 산정 근거 |
|---|---|---|---|---|
| P5 | p5.48xlarge | 83.3% | 16.7% | ($55.040-$9.216)/$55.040 |
| P4D | p4d.24xlarge | 79.0% | 21.0% | ($21.958-$4.608)/$21.958 |
| P4DE | p4de.24xlarge | 83.2% | 16.8% | ($27.447-$4.608)/$27.447 |
| G5 | g5.12xlarge | 59.4% | 40.6% | ($5.672-$2.304)/$5.672 |
| R7i | r7i.4xlarge | 0% | 100% | CPU 전용 |
| G4DN | g4dn.xlarge | 63.5% | 36.5% | ($0.526-$0.192)/$0.526 |

참고:
- [AWS EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [AWS EC2 Accelerated Computing Instances](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
- [AWS EC2 General Purpose Instances](https://docs.aws.amazon.com/ec2/latest/instancetypes/gp.html)
- [AWS EC2 Instance Type Specifications](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-type-specifications.html)

### 스토리지 비용 배분

- S3: 인벤토리 용량 비율로 프로젝트별 배분
- FSx: EC2 비용 비율로 프로젝트별 배분
- 월말 확정: 과거 월은 인벤토리 스냅샷 고정 (`inventory-snapshots/YYYY-MM.json`)
- 현재 월: 라이브 인벤토리 사용 (주간 갱신 반영)
- 전달의 완전한 스토리지 데이터 확인: 익월 3일 00:00 이후 (CUR 48시간 지연)

### 캐시 정책

| 대상 | TTL | 비고 |
|---|---|---|
| 일별 비용 | 1시간 | 모든 날짜 동일 |
| 월별 비용 (과거 월) | 24시간 | 확정된 데이터 |
| 월별 비용 (현재 월) | 1시간 | 데이터 갱신 반영 |
| 매핑 설정 변경 시 | 즉시 초기화 | `_daily_cache.clear()`, `_monthly_cache.clear()` |

### 유효하지 않은 프로젝트 필터링

에이전트가 수집한 프로젝트명 중 아래 패턴은 weight 집계에서 제외:
- `tmp*` (임시 디렉토리)
- `pip-install-*`
- 숫자만으로 구성된 이름
- 8자리 랜덤 해시
- 시스템 디렉토리 (.vscode-server, miniconda3, ms-* 등)
- `_홈` 접미사, `_unknown_*` 접두사
- 타임스탬프 패턴 (dd-dd-dd)

## 프론트엔드

### 파일
- 소스: `frontend/src/pages/CostMonitoring.jsx`
- 빌드: `frontend/dist/assets/index-*.js`
- 서빙: nginx 컨테이너 (`userportal-nginx`)

### 화면 구성

- 일별/월별 전환
- 달력에서 날짜 선택 (48시간 지연 적용)
- USD/KRW 통화 전환
- 뷰 모드: 프로젝트별 / 사용자별 / 인스턴스별
- 원형 차트 (프로젝트별, 사용자별, 인스턴스별)
- 검색 필터 (프로젝트/사용자/인스턴스)

### 엑셀 다운로드

ExcelJS 라이브러리로 클라이언트에서 생성.

| 시트 | 일별 | 월별 |
|---|---|---|
| 요약 | EC2 비용만 | EC2 + 스토리지 비용 |
| 프로젝트별 | 7열 (EC2) | 11열 (EC2 + S3/FSx/소계/총합) |
| 사용자별 | O | O |
| 인스턴스별 | O | O |
| 프로젝트상세 | O | O |
| 스토리지비용배분 | X | O |

### 설정 UI

대시보드 내 설정 탭에서 매핑 데이터 직접 편집 가능:
- 프로젝트 코드 매핑 (코드 -> 설명)
- 프로젝트명 -> 코드 매핑 (별칭)
- UID -> 사용자명 매핑
- 인스턴스 ID -> 이름 매핑

주의: 매핑 설정의 동시 수정은 권장하지 않음 (이전 변경안이 사라질 수 있음)

## mappings.json 구조

| 키 | 설명 | 예시 |
|---|---|---|
| project_name_to_code | 에이전트 프로젝트명 -> 프로젝트 코드 | `"MI25003_LNP": "MI25003"` |
| project_code_mapping | 프로젝트 코드 -> 설명 | `"MI25003": "LNP 최적화"` |
| uid_to_username | Linux UID -> 사용자명 | `"1001": "cgjang"` |
| instance_names | 인스턴스 ID -> 표시 이름 | `"i-06a9b5df345d47eaa": "P4D"` |

대시보드 설정 UI 또는 파일 직접 수정으로 변경 가능. 변경 후 캐시 자동 초기화.

## 미배분 비용

GPU 프로세스가 없는 인스턴스의 GPU 비용은 배분 대상이 없어 미배분으로 남는다. 정상 동작이다.

## 비용 정합성 검증 (2026년 2월)

| 검증 항목 | 결과 |
|---|---|
| 검증 기간 | 2/1 ~ 2/28 (28일) |
| CUR 총비용 합계 | $24,918.85 |
| 배분 + 미배분 합계 | $24,918.85 |
| 일별 차이 최대값 | $0.01 (부동소수점 반올림) |
| 누수·중복 | $0 |

## 트러블슈팅

에이전트 상태 확인 (SSM):
```bash
aws ssm send-command --instance-ids <INSTANCE_ID> --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker ps | grep cost"]' --region us-west-2
```

Athena에서 에이전트 데이터 직접 조회:
```sql
SELECT instance_id, COUNT(DISTINCT p.project), COUNT(*)
FROM cost_monitoring.enhanced_metrics_v2
CROSS JOIN UNNEST(processes) AS t(p)
WHERE year='2026' AND month='03' AND day='09'
GROUP BY instance_id
```

특정 날짜에 에이전트 데이터가 없으면 해당 인스턴스의 컨테이너 상태를 확인한다.

## 빌드 및 배포

```bash
# 백엔드
cd /home/app/account-portal
docker compose -f docker-compose-fixed.yml up -d --build backend-cost

# 프론트엔드
cd /home/app/account-portal/frontend
node node_modules/.bin/vite build
docker restart userportal-nginx

# 캐시 초기화
curl -s -X POST "http://52.40.59.142/api/cost-monitoring/clear-cache"
```
