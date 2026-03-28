# Cost Dashboard Platform

AWS Athena, Glue, CUR, S3 기반 프로젝트별 GPU/CPU 리소스 비용 산출 대시보드

## 아키텍처

```
[Frontend (React+Vite)] → [Nginx (80/443)]
                              ├── /api/cost-monitoring → [backend-cost :5000]
                              └── /api/*               → [backend-admin :5000]
                          [Redis 7 (캐시)]
```

## 구동 서비스 (Docker Compose)

| 컨테이너 | 이미지 | 역할 |
|----------|--------|------|
| userportal-nginx | nginx:alpine | 리버스 프록시 (HTTP/HTTPS) |
| userportal-backend-admin | account-portal-backend-admin | 계정/SSO/GitHub/온보딩 API |
| userportal-backend-cost | account-portal-backend-cost | 비용 모니터링/FinOps API |
| userportal-redis | redis:7-alpine | 캐시 (256MB, allkeys-lru) |

## 디렉토리 구조

```
account-portal/
├── backend-admin/          # Flask - 계정 관리 API
│   ├── routes/             # accounts, auth, sso, onboarding, github, instances 등
│   ├── services/           # github_service
│   ├── data/               # mappings, 스크립트
│   └── Dockerfile
├── backend-cost/           # Flask - 비용 모니터링 API
│   ├── routes/             # cost_monitoring, finops_routes
│   ├── utils/              # exchange_rate
│   ├── agent/              # GPU/CPU 메트릭 수집 에이전트
│   └── Dockerfile
├── frontend/               # React + Vite + Tailwind
│   ├── src/pages/          # CostMonitoring, CreateAccount, Login 등
│   ├── src/components/     # Layout, Sidebar
│   ├── .env                # Cognito 설정
│   └── package.json
├── nginx/                  # nginx 설정 + SSL 인증서
└── docker-compose-fixed.yml

ansible/cost_monitoring/    # 에이전트 배포 (Ansible)
├── files/agent/            # 에이전트 Docker 파일
├── infrastructure/         # Athena DDL, Terraform, IAM 정책
├── lambda/                 # cost_monitoring_lambda
└── deploy.sh / deploy_agent.yml

aws-infrastructure/         # 실제 AWS 리소스 설정
├── athena/                 # 워크그룹, 저장 쿼리, 실행 쿼리 패턴 5종
├── glue/                   # cost_monitoring (4 tables), cur_database DDL
├── s3/                     # mogam-or-cur-stg 버킷 설정, CUR 리포트 정의
└── lambda/                 # finops_cost_tracking.py + 설정
```

## 환경변수

### backend-admin
| 변수 | 값 |
|------|-----|
| AWS_DEFAULT_REGION | us-west-2 |
| SES_SENDER_EMAIL | mogam.infra.admin-noreply@mogam.re.kr |
| SES_APPROVER_EMAIL | changgeun.jang@mogam.re.kr |
| SES_REGION | us-east-1 |

### backend-cost
| 변수 | 값 |
|------|-----|
| AWS_DEFAULT_REGION | us-west-2 |

### frontend (.env)
| 변수 | 설명 |
|------|------|
| VITE_COGNITO_DOMAIN | Cognito 도메인 |
| VITE_COGNITO_CLIENT_ID | Cognito 클라이언트 ID |
| VITE_COGNITO_REDIRECT | 인증 콜백 URL |

## AWS 인프라

- **S3**: `mogam-or-cur-stg` (metrics, CUR, athena-results, inventory)
- **Athena**: `cost-monitoring` 워크그룹 → `s3://mogam-or-cur-stg/athena-results/`
- **Glue**: `cost_monitoring` DB (enhanced_metrics_v2, mogam_hourly_cur, cur_temp, s3_inventory)
- **Glue**: `cur_database` DB (mogam_hourly_cur)
- **CUR**: `mogam-hourly-cur` (Hourly, Parquet, ATHENA artifact)
- **Lambda**: `cost-monitoring-query` (python3.9, 256MB)

## 실행

```bash
cd account-portal
docker compose -f docker-compose-fixed.yml up -d --build
```
