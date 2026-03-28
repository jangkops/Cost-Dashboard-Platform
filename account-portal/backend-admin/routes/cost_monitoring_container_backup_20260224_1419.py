from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import boto3
import time
from collections import defaultdict
import re

cost_monitoring_bp = Blueprint('cost_monitoring', __name__)

UID_TO_USERNAME = {
    1002: 'aychoi', 1003: 'jykim', 1004: 'shlee', 1005: 'jhhong', 1006: 'enhuh',
    1007: 'hermee', 1008: 'srpark', 1009: 'bskim', 1010: 'hslee', 1011: 'hklee',
    1012: 'ymbaek', 1013: 'hblee', 1014: 'shlee2', 1015: 'ybkim', 1016: 'jykim2',
    1017: 'jwlee', 1018: 'yjgo', 1019: 'ckkang', 1020: 'sbkim', 1021: 'intern',
    1022: 'cgjang', 1023: 'yokim', 1024: 'sjchoe', 1025: 'syseo'
}


PROJECT_CODE_MAPPING = {
    "MG9121A": "공개 유전자 스크리닝과 약물 스크리닝의 통합 데이터에 대한 머신러닝 분석을 통한 신규 약물 타겟 발굴",
    "MI25001": "mRNA UTR diffusion 서열 생성 소프트웨어 개발",
    "MI25002": "AI를 활용한 항체 개발 가속화 모델 구축",
    "P240014": "연합학습 기반 ADMET 예측을 위한 K-Melloddy 언어-그래프 앙상블 모델 개발",
    "P240010": "치매 예측 프로젝트",
    "P240017": "mRNA_LLM",
    "INTERNAL": "내부 프로젝트",
    "MI25003": "효과성 있는 신규 이온화 지질 발굴을 위한 생성 AI LNP Generation모델 구축",
    "MI25004": "mRNA 서열 최적화 mRNA opt AI model 개발",
    "MI25005": "K-AI 중개·융합 데이터 기반 효능·독성 예측 및 용량-반응 최적화 임상이행 지원 AI소프트웨어 개발",
    "P250001": "mRNA_LLM2 모델 개발",
    "P230023": "희귀질환 LLM 모델 개발",
    "P230005": "AI 기반 LNP 약물전달 효능 예측 및 신규 ionizable lipid 도출",
    "P230006": "전사체 정보 분석 기반의 근감소 치료 표적 및 후보 약물 발굴",
    "P230020": "MetS 데이터기반 디지털 바이오 선도사업_대사질환",
    "P240003": "Codon optimization 서비스를 위한 mRNA SW 개발",
    "P240020": "mRNA 서열 최적화 서비스 자문 서비스 시행의 건"
}


INSTANCE_NAMES = {
    'i-004e23df368dcb30e': 'mogam-or-p5',
    'i-06a9b5df345d47eaa': 'mogam-or-p4d',
    'i-0d53ba43b64510164': 'mogam-or-p4de',
    'i-0dc3c13df82448939': 'mogam-or-g5',
    'i-0c30cae12f60d69d1': 'mogam-or-zonea-r7',
    'i-074a73c3cf9656989': 'HeadNode'
}

INSTANCE_TYPES = {
    'i-004e23df368dcb30e': 'P5.4xlarge',
    'i-06a9b5df345d47eaa': 'P4D.24xlarge',
    'i-0d53ba43b64510164': 'P4DE.24xlarge',
    'i-0dc3c13df82448939': 'G5.12xlarge',
    'i-0c30cae12f60d69d1': 'R7i.4xlarge',
    'i-074a73c3cf9656989': 'G4DN.xlarge'
}

INSTANCE_ORDER = [
    'i-004e23df368dcb30e',  # P5
    'i-06a9b5df345d47eaa',  # P4D
    'i-0d53ba43b64510164',  # P4DE
    'i-0dc3c13df82448939',  # G5
    'i-0c30cae12f60d69d1',  # R7i
    'i-074a73c3cf9656989'   # HeadNode
]

PROJECT_NAME_TO_CODE = {
    "MI25001_UTR_diffusion": "MI25001",
    "UTR_diffusion": "MI25001",
    "MI25002_AbDev": "MI25002",
    "MI25003_LNP": "MI25003",
    "P230023_Rare_LLM": "P230023",
    "P240014_K_MELLODDY": "P240014",
    "k_melloddy": "P240014",
    "Conformal_Regression": "P240014",
    "MI25005_KAI": "MI25005",
    "AbDev": "MI25002",
    "antibody": "MI25002",
    "ADMET-UC-MultiModal": "P240014",
    "LNP_pu": "MI25003",
    "LNP_pu2": "MI25003",
    "LNP_pu2": "MI25003",
    "pu-learning": "MI25003",
    "P240010_Dementia": "P240010",
    "cds_bart_v2": "MI25001",
    "DuET": "MI25001",
    "Genotype_VAE": "P240020",
    "agent": "MI25001",
    "0_ai_agent": "INTERNAL",
    "mle-star": "MI25004",
    "projects": "INTERNAL",
    "MI25004_RNA_AI": "MI25004",
    "P230020_MetS": "P230020",
    "Mets": "P230020",
    "MetS": "P230020",
    "P230005_LNP": "P230005",
    "P230006_Sarcopenia": "P230006",
    "P240003_Codon": "P240003",
    "P240020_mRNA": "P240020",
    "P250001_mRNA_LLM2": "P250001",
    "mRNA_LLM2": "P250001"
}

def get_project_info(project_name):
    if project_name in PROJECT_NAME_TO_CODE:
        code = PROJECT_NAME_TO_CODE[project_name]
        return {"code": code, "description": PROJECT_CODE_MAPPING.get(code, "")}
    match = re.match(r"^([A-Z]\d{6})_", project_name)
    if match:
        code = match.group(1)
        return {"code": code, "description": PROJECT_CODE_MAPPING.get(code, "")}
    return {"code": project_name, "description": ""}
def resolve_username(uid_str):
    if uid_str.startswith("uid_"):
        try:
            uid = int(uid_str.split("_")[1])
            return UID_TO_USERNAME.get(uid, uid_str)
        except:
            return uid_str
    try:
        uid = int(uid_str)
        return UID_TO_USERNAME.get(uid, uid_str)
    except:
        return uid_str

def get_cost_data(date):
    # AWS 온디맨드 가격 기반 GPU:CPU 비율
    INSTANCE_GPU_RATIO = {
        'i-004e23df368dcb30e': 0.852,   # p5.4xlarge
        'i-06a9b5df345d47eaa': 0.852,  # p4d.24xlarge
        'i-0d53ba43b64510164': 0.852,  # p4de.24xlarge
        'i-0dc3c13df82448939': 0.822,  # g5.12xlarge
        'i-0c30cae12f60d69d1': 0.0,    # r7i.4xlarge
        'i-074a73c3cf9656989': 0.635  # g4dn.xlarge
    }
    
    dt = datetime.strptime(date, '%Y-%m-%d')
    athena_client = boto3.client('athena', region_name='us-west-2')
    
    # 1. CUR - 인스턴스별 실제 비용 (RI 포함)
    query_cur = f"""
    SELECT line_item_resource_id, 
           SUM(CASE 
               WHEN line_item_line_item_type = 'Usage' THEN line_item_unblended_cost
               WHEN line_item_line_item_type = 'DiscountedUsage' THEN reservation_effective_cost
               ELSE 0 END) as cost
    FROM cur_database.mogam_hourly_cur
    WHERE DATE(line_item_usage_start_date) = DATE('{date}')
      AND line_item_product_code = 'AmazonEC2'
      AND line_item_resource_id LIKE 'i-%'
    GROUP BY line_item_resource_id
    """
    
    r_cur = athena_client.start_query_execution(
        QueryString=query_cur,
        QueryExecutionContext={'Database': 'cur_database'},
        ResultConfiguration={'OutputLocation': 's3://mogam-or-cur-stg/athena-results/'}
    )
    
    for _ in range(60):
        status = athena_client.get_query_execution(QueryExecutionId=r_cur['QueryExecutionId'])
        if status['QueryExecution']['Status']['State'] == 'SUCCEEDED':
            break
        time.sleep(1)
    
    res_cur = athena_client.get_query_results(QueryExecutionId=r_cur['QueryExecutionId'])
    instance_costs = {}
    total_cost = 0
    
    for row in res_cur['ResultSet']['Rows'][1:]:
        vals = [col.get('VarCharValue', '') for col in row['Data']]
        cost = float(vals[1])
        instance_costs[vals[0]] = cost
        total_cost += cost
    
    # 2. Enhanced Agent - 프로젝트별 사용 비율
    query_agent = f"""
    SELECT instance_id, p.project, p.username, 
           COUNT(*) as samples, 
           SUM(p.gpu_count) as gpu_count,
           AVG(p.cpu_percent) as avg_cpu_percent
    FROM cost_monitoring.enhanced_metrics_v2
    CROSS JOIN UNNEST(processes) AS t(p)
    WHERE year='{dt.year}' AND month='{dt.month:02d}' AND day='{dt.day:02d}'
      AND instance_id != ''
      AND p.project IS NOT NULL AND p.project != 'unknown'
    GROUP BY instance_id, p.project, p.username
    """
    
    r_agent = athena_client.start_query_execution(
        QueryString=query_agent,
        QueryExecutionContext={'Database': 'cost_monitoring'},
        ResultConfiguration={'OutputLocation': 's3://mogam-or-cur-stg/athena-results/'}
    )
    
    for _ in range(60):
        status = athena_client.get_query_execution(QueryExecutionId=r_agent['QueryExecutionId'])
        if status['QueryExecution']['Status']['State'] == 'SUCCEEDED':
            break
        time.sleep(1)
    
    res_agent = athena_client.get_query_results(QueryExecutionId=r_agent['QueryExecutionId'])
    
    # 인스턴스별 프로젝트별 데이터 집계 (가중치 기반)
    instance_project_data = defaultdict(lambda: defaultdict(lambda: {
        'weight': 0.0,
        'samples': 0,
        'users': defaultdict(lambda: {'samples': 0, 'weight': 0.0, 'gpu_count': 0})
    }))
    instance_total_weight = defaultdict(float)
    instance_allocated = defaultdict(float)
    
    for row in res_agent['ResultSet']['Rows'][1:]:
        vals = [col.get('VarCharValue', '') for col in row['Data']]
        instance_id = vals[0]
        project = vals[1]
        username = resolve_username(vals[2])
        samples = int(vals[3])
        gpu_count = int(vals[4] or 0)
        avg_cpu_percent = float(vals[5] or 0)
        
        # 가중치 = samples * (cpu_percent/100) * (1 + gpu_count)
        # GPU 사용 시 CPU 0%여도 최소 가중치 부여
        if gpu_count > 0:
            # GPU 사용 시: 최소 CPU 10% 가정
            effective_cpu = max(avg_cpu_percent, 10.0)
            weight = samples * (effective_cpu / 100.0) * (1.0 + gpu_count)
        else:
            weight = samples * (avg_cpu_percent / 100.0) * (1.0 + gpu_count)
        
        # 집계
        instance_total_weight[instance_id] += weight
        instance_project_data[instance_id][project]['weight'] += weight
        instance_project_data[instance_id][project]['samples'] += samples
        instance_project_data[instance_id][project]['users'][username]['samples'] += samples
        instance_project_data[instance_id][project]['users'][username]['weight'] += weight
        instance_project_data[instance_id][project]['users'][username]['gpu_count'] += gpu_count
    
    # 전체 GPU:CPU 비율 계산 (모든 재배분에 사용)
    total_gpu_cost = sum(instance_costs.get(iid, 0) * INSTANCE_GPU_RATIO.get(iid, 0) for iid in instance_costs)
    global_gpu_ratio = total_gpu_cost / total_cost if total_cost > 0 else 0
    
    # 3. 프로젝트별 비용 배분 (1차) - 가중치 기반
    proj_costs = defaultdict(lambda: {'total_cost': 0, 'gpu_cost': 0, 'cpu_cost': 0, 'users': set(), 'samples': 0})
    user_costs = defaultdict(lambda: {'total_cost': 0, 'gpu_cost': 0, 'cpu_cost': 0, 'projects': set()})
    
    
    # 1차 배분: 인스턴스별 → 프로젝트별 → 유저별 (가중치 기반)
    for instance_id, projects in instance_project_data.items():
        instance_cost = instance_costs.get(instance_id, 0)
        if instance_cost == 0:
            continue
            
        total_weight = instance_total_weight[instance_id]
        if total_weight == 0:
            continue
        
        
        for project, proj_data in projects.items():
            # 프로젝트 비용 배분
            project_allocated = instance_cost * (proj_data['weight'] / total_weight)
            instance_allocated[instance_id] += project_allocated
            
            proj_costs[project]['total_cost'] += project_allocated
            proj_costs[project]['samples'] += proj_data['samples']
            
            # GPU:CPU 비율 적용
            if global_gpu_ratio > 0:
                gpu_portion = project_allocated * global_gpu_ratio
                cpu_portion = project_allocated * (1 - global_gpu_ratio)
                proj_costs[project]['gpu_cost'] += gpu_portion
                proj_costs[project]['cpu_cost'] += cpu_portion
            else:
                proj_costs[project]['cpu_cost'] += project_allocated
            
            # 유저별 비용 배분
            project_total_weight = proj_data['weight']
            if project_total_weight > 0:
                for username, user_data in proj_data['users'].items():
                    proj_costs[project]['users'].add(username)
                    
                    user_allocated = project_allocated * (user_data['weight'] / project_total_weight)
                    user_costs[username]['total_cost'] += user_allocated
                    user_costs[username]['projects'].add(project)
                    
                    # GPU:CPU 비율 적용
                    if global_gpu_ratio > 0:
                        user_costs[username]['gpu_cost'] += user_allocated * global_gpu_ratio
                        user_costs[username]['cpu_cost'] += user_allocated * (1 - global_gpu_ratio)
                    else:
                        user_costs[username]['cpu_cost'] += user_allocated
    
    # 4. 인스턴스별 미배분 비용 재배분
    for instance_id, instance_cost in instance_costs.items():
        unallocated = instance_cost - instance_allocated.get(instance_id, 0)
        
        if unallocated <= 0.01:  # 1센트 미만 무시
            continue
        
        # 해당 인스턴스를 사용한 프로젝트만 필터링
        if instance_id not in instance_project_data:
            continue
        
        projects = instance_project_data[instance_id]
        total_weight = sum(p['weight'] for p in projects.values())
        
        if total_weight == 0:
            continue
        
        
        # 가중치 비율로 재배분
        for project, proj_data in projects.items():
            project_additional = unallocated * (proj_data['weight'] / total_weight)
            proj_costs[project]['total_cost'] += project_additional
            
            # GPU:CPU 비율 적용
            if global_gpu_ratio > 0:
                proj_costs[project]['gpu_cost'] += project_additional * global_gpu_ratio
                proj_costs[project]['cpu_cost'] += project_additional * (1 - global_gpu_ratio)
            else:
                proj_costs[project]['cpu_cost'] += project_additional
            
            # 유저별 재배분
            project_total_weight = proj_data['weight']
            if project_total_weight > 0:
                for username, user_data in proj_data['users'].items():
                    user_additional = project_additional * (user_data['weight'] / project_total_weight)
                    user_costs[username]['total_cost'] += user_additional
                    user_costs[username]['projects'].add(project)
                    
                    # GPU:CPU 비율 적용
                    if global_gpu_ratio > 0:
                        user_costs[username]['gpu_cost'] += user_additional * global_gpu_ratio
                        user_costs[username]['cpu_cost'] += user_additional * (1 - global_gpu_ratio)
                    else:
                        user_costs[username]['cpu_cost'] += user_additional
    

    # 5. 전체 미배분 비용 최종 재배분
    allocated_total = sum(p['total_cost'] for p in proj_costs.values())
    final_unallocated = total_cost - allocated_total
    
    if final_unallocated > 0.01 and instance_total_weight:
        total_weight = sum(instance_total_weight.values())
        if total_weight > 0:
            project_weights = defaultdict(float)
            for instance_id, projects in instance_project_data.items():
                for project, proj_data in projects.items():
                    project_weights[project] += proj_data['weight']
            for project, weight in project_weights.items():
                additional = final_unallocated * (weight / total_weight)
                proj_costs[project]['total_cost'] += additional
                proj_costs[project]['gpu_cost'] += additional * global_gpu_ratio
                proj_costs[project]['cpu_cost'] += additional * (1 - global_gpu_ratio)
    return {
        'date': date,
        'total_cost': total_cost,
        'proj_costs': proj_costs,
        'user_costs': user_costs,
        'instance_costs': instance_costs,
        'instance_project_data': instance_project_data,
        'validation': {
            'cur_total': total_cost,
            'allocated_before': sum(instance_allocated.values()),
            'project_sum': sum(d['total_cost'] for d in proj_costs.values()),
            'unallocated': total_cost - sum(d['total_cost'] for d in proj_costs.values()),
            'allocated_percentage': (sum(d['total_cost'] for d in proj_costs.values()) / total_cost * 100) if total_cost > 0 else 0
        }
    }

@cost_monitoring_bp.route('/daily-costs/<date>', methods=['GET'])
def get_daily_costs(date):
    try:
        data = get_cost_data(date)
        
        # 프로젝트 코드별로 합치기
        code_aggregated = defaultdict(lambda: {
            'total_cost': 0, 'gpu_cost': 0, 'cpu_cost': 0, 
            'users': set(), 'description': '', 'names': set()
        })
        
        for p, d in data["proj_costs"].items():
            info = get_project_info(p)
            code = info["code"]
            code_aggregated[code]['total_cost'] += d["total_cost"]
            code_aggregated[code]['gpu_cost'] += d["gpu_cost"]
            code_aggregated[code]['cpu_cost'] += d["cpu_cost"]
            code_aggregated[code]['users'].update(d["users"])
            code_aggregated[code]['description'] = info["description"]
            code_aggregated[code]['names'].add(p)
        
        projects = []
        for code, d in code_aggregated.items():
            projects.append({
                "code": code,
                "name": code,
                "description": d["description"],
                "total_cost": round(d["total_cost"], 2),
                "gpu_cost": round(d["gpu_cost"], 2),
                "cpu_cost": round(d["cpu_cost"], 2),
                "users": sorted([resolve_username(u) for u in d["users"]])
            })
        projects.sort(key=lambda x: x["total_cost"], reverse=True)
        users = [{'username': resolve_username(u), 'total_cost': round(d['total_cost'], 2), 'gpu_cost': round(d['gpu_cost'], 2),
                  'cpu_cost': round(d['cpu_cost'], 2), 'projects': sorted([get_project_info(p)["code"] for p in d['projects']])} 
                 for u, d in data['user_costs'].items()]
        users.sort(key=lambda x: x['total_cost'], reverse=True)
        
        # 인스턴스별 데이터 생성
        instances = {}
        for instance_id, cost in data.get('instance_costs', {}).items():
            gpu_ratio = {
                'i-004e23df368dcb30e': 0.852,
                'i-06a9b5df345d47eaa': 0.852,
                'i-0d53ba43b64510164': 0.852,
                'i-0dc3c13df82448939': 0.822,
                'i-0c30cae12f60d69d1': 0.0,
                'i-074a73c3cf9656989': 0.635
            }.get(instance_id, 0)
            
            # 인스턴스에서 실행된 프로젝트 수집
            inst_projects = set()
            if instance_id in data.get('instance_project_data', {}):
                for proj in data['instance_project_data'][instance_id].keys():
                    info = get_project_info(proj)
                    code = info['code']
                    # code_aggregated에서 비용 $0.01 이상인 프로젝트만 포함
                    if code in code_aggregated and code_aggregated[code]['total_cost'] > 0.01:
                        inst_projects.add(code)
            
            # 주요 6개 인스턴스만 포함
            if instance_id in INSTANCE_ORDER:
                instances[instance_id] = {
                    'name': INSTANCE_NAMES.get(instance_id, instance_id),
                    'type': INSTANCE_TYPES.get(instance_id, instance_id),
                    'instance_id': instance_id,
                    'total_cost_usd': round(cost, 2),
                    'total_cost_krw': round(cost * 1380, 2),
                    'gpu_cost': round(cost * gpu_ratio, 2),
                    'cpu_cost': round(cost * (1 - gpu_ratio), 2),
                    'projects': sorted(list(inst_projects))
                }

        
        return jsonify({
            'date': date,
            'total_cost': round(data['total_cost'], 2),
            'data_source': 'CUR reservation_effective_cost (100% allocated)',
            'projects': projects,
            'users': users,
            'instances': {k: instances[k] for k in INSTANCE_ORDER if k in instances},
            'validation': {
                'cur_total': round(data['validation']['cur_total'], 2),
                'allocated_before': round(data['validation']['allocated_before'], 2),
                'unallocated': round(data['validation']['unallocated'], 2),
                'project_sum': round(data['validation']['project_sum'], 2),
                'allocated_percentage': round(data['validation']['allocated_percentage'], 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'date': date}), 500

@cost_monitoring_bp.route('/finops/daily/<date>', methods=['GET'])
def get_finops_daily(date):
    try:
        data = get_cost_data(date)
        
        projects = []
        for p, d in data["proj_costs"].items():
            info = get_project_info(p)
            projects.append({
                "project": info["code"],
                "description": info["description"],
                "total_cost": round(d["total_cost"], 2),
                "gpu_cost": round(d["gpu_cost"], 2),
                "cpu_cost": round(d["cpu_cost"], 2),
                "users": sorted([resolve_username(u) for u in d["users"]])
            })
        projects.sort(key=lambda x: x['total_cost'], reverse=True)
        
        users = [{'username': resolve_username(u), 'total_cost': round(d['total_cost'], 2), 'gpu_cost': round(d['gpu_cost'], 2),
                  'cpu_cost': round(d['cpu_cost'], 2), 'projects': sorted([get_project_info(p)["code"] for p in d['projects']])} 
                 for u, d in data['user_costs'].items()]
        users.sort(key=lambda x: x['total_cost'], reverse=True)
        
        # 인스턴스별 데이터 생성
        instances = {}
        for instance_id, cost in data.get('instance_costs', {}).items():
            gpu_ratio = {
                'i-004e23df368dcb30e': 0.852,
                'i-06a9b5df345d47eaa': 0.852,
                'i-0d53ba43b64510164': 0.852,
                'i-0dc3c13df82448939': 0.822,
                'i-0c30cae12f60d69d1': 0.0,
                'i-074a73c3cf9656989': 0.635
            }.get(instance_id, 0)
            
            # 인스턴스에서 실행된 프로젝트 수집
            inst_projects = set()
            if instance_id in data.get('instance_project_data', {}):
                for proj in data['instance_project_data'][instance_id].keys():
                    info = get_project_info(proj)
                    code = info['code']
                    # code_aggregated에서 비용 $0.01 이상인 프로젝트만 포함
                    if code in code_aggregated and code_aggregated[code]['total_cost'] > 0.01:
                        inst_projects.add(code)
            
            # 주요 6개 인스턴스만 포함
            if instance_id in INSTANCE_ORDER:
                instances[instance_id] = {
                    'name': INSTANCE_NAMES.get(instance_id, instance_id),
                    'type': INSTANCE_TYPES.get(instance_id, instance_id),
                    'instance_id': instance_id,
                    'total_cost_usd': round(cost, 2),
                    'total_cost_krw': round(cost * 1380, 2),
                    'gpu_cost': round(cost * gpu_ratio, 2),
                    'cpu_cost': round(cost * (1 - gpu_ratio), 2),
                    'projects': sorted(list(inst_projects))
                }

        
        return jsonify({
            'success': True,
            'date': date,
            'total_cost': round(data['total_cost'], 2),
            'projects': projects,
            'users': users,
            'instances': {k: instances[k] for k in INSTANCE_ORDER if k in instances},
            'validation': data['validation']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cost_monitoring_bp.route('/finops/daily-cost-allocation/<date>', methods=['GET'])
def get_finops_daily_cost_allocation(date):
    try:
        data = get_cost_data(date)
        
        projects = []
        for p, d in data["proj_costs"].items():
            info = get_project_info(p)
            projects.append({
                "project": info["code"],
                "description": info["description"],
                "total_cost": round(d["total_cost"], 2),
                "gpu_cost": round(d["gpu_cost"], 2),
                "cpu_cost": round(d["cpu_cost"], 2),
                "users": sorted([resolve_username(u) for u in d["users"]])
            })
        projects.sort(key=lambda x: x['total_cost'], reverse=True)
        
        return jsonify({
            'date': date,
            'summary': {
                'total_cost': round(data['total_cost'], 2),
                'allocated_percentage': 100.0
            },
            'projects': projects
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_monthly_cost_data(year, month):
    """월별 비용 데이터 집계"""
    import time
    
    athena_client = boto3.client('athena', region_name='us-west-2')
    
    # 1. CUR - 월별 인스턴스 비용
    query_cur = f"""
    SELECT line_item_resource_id, 
           SUM(CASE 
               WHEN line_item_line_item_type = 'Usage' THEN line_item_unblended_cost
               WHEN line_item_line_item_type = 'DiscountedUsage' THEN reservation_effective_cost
               ELSE 0 END) as cost
    FROM cur_database.mogam_hourly_cur
    WHERE year='{year}' AND month='{int(month)}'
      AND line_item_product_code = 'AmazonEC2'
      AND line_item_resource_id LIKE 'i-%'
    GROUP BY line_item_resource_id
    """
    
    r_cur = athena_client.start_query_execution(
        QueryString=query_cur,
        QueryExecutionContext={'Database': 'cur_database'},
        ResultConfiguration={'OutputLocation': 's3://mogam-or-cur-stg/athena-results/'}
    )
    
    for _ in range(60):
        status = athena_client.get_query_execution(QueryExecutionId=r_cur['QueryExecutionId'])
        if status['QueryExecution']['Status']['State'] == 'SUCCEEDED':
            break
        time.sleep(1)
    
    res_cur = athena_client.get_query_results(QueryExecutionId=r_cur['QueryExecutionId'])
    instance_costs = {}
    total_cost = 0
    
    for row in res_cur['ResultSet']['Rows'][1:]:
        vals = [col.get('VarCharValue', '') for col in row['Data']]
        cost = float(vals[1])
        instance_costs[vals[0]] = cost
        total_cost += cost
    
    # 2. Enhanced Agent - 손상 파일 제외 (2026-01의 21일만)
    exclude_clause = ""
    if year == '2026' and int(month) == 1:
        exclude_clause = "AND day NOT IN ('12', '13', '14', '19', '21')"
    
    query_agent = f"""
    SELECT instance_id, p.project, p.username, 
           COUNT(*) as samples, 
           SUM(p.gpu_count) as gpu_count,
           AVG(p.cpu_percent) as avg_cpu_percent
    FROM cost_monitoring.enhanced_metrics_v2
    CROSS JOIN UNNEST(processes) AS t(p)
    WHERE year='{year}' AND month='{int(month):02d}'
      {exclude_clause}
      AND instance_id != ''
      AND p.project IS NOT NULL AND p.project != 'unknown'
    GROUP BY instance_id, p.project, p.username
    """
    
    r_agent = athena_client.start_query_execution(
        QueryString=query_agent,
        QueryExecutionContext={'Database': 'cost_monitoring'},
        ResultConfiguration={'OutputLocation': 's3://mogam-or-cur-stg/athena-results/'}
    )
    
    for _ in range(60):
        status = athena_client.get_query_execution(QueryExecutionId=r_agent['QueryExecutionId'])
        if status['QueryExecution']['Status']['State'] == 'SUCCEEDED':
            break
        time.sleep(1)
    
    res_agent = athena_client.get_query_results(QueryExecutionId=r_agent['QueryExecutionId'])
    
    instance_project_data = defaultdict(lambda: defaultdict(lambda: {
        'weight': 0.0, 'samples': 0,
        'users': defaultdict(lambda: {'samples': 0, 'weight': 0.0, 'gpu_count': 0})
    }))
    
    for row in res_agent['ResultSet']['Rows'][1:]:
        vals = [col.get('VarCharValue', '') for col in row['Data']]
        instance_id, project, username = vals[0], vals[1], vals[2]
        samples, gpu_count, avg_cpu = int(vals[3]), float(vals[4] or 0), float(vals[5] or 0)
        
        weight = gpu_count if gpu_count > 0 else (avg_cpu / 100.0)
        instance_project_data[instance_id][project]['weight'] += weight
        instance_project_data[instance_id][project]['samples'] += samples
        instance_project_data[instance_id][project]['users'][username]['samples'] += samples
        instance_project_data[instance_id][project]['users'][username]['weight'] += weight
        instance_project_data[instance_id][project]['users'][username]['gpu_count'] += gpu_count
    
    # 3. 비용 배분
    INSTANCE_GPU_RATIO = {
        'i-004e23df368dcb30e': 0.852, 'i-06a9b5df345d47eaa': 0.852,
        'i-0d53ba43b64510164': 0.852, 'i-0dc3c13df82448939': 0.822,
        'i-0c30cae12f60d69d1': 0.0, 'i-074a73c3cf9656989': 0.635
    }
    
    total_gpu_cost = sum(instance_costs.get(iid, 0) * INSTANCE_GPU_RATIO.get(iid, 0) for iid in instance_costs)
    global_gpu_ratio = total_gpu_cost / total_cost if total_cost > 0 else 0
    
    proj_costs = defaultdict(lambda: {'total_cost': 0, 'gpu_cost': 0, 'cpu_cost': 0, 'users': set(), 'samples': 0})
    user_costs = defaultdict(lambda: {'total_cost': 0, 'gpu_cost': 0, 'cpu_cost': 0, 'projects': set()})
    instance_allocated = defaultdict(float)
    
    for instance_id, instance_cost in instance_costs.items():
        if instance_id not in instance_project_data:
            continue
        
        projects = instance_project_data[instance_id]
        total_weight = sum(p['weight'] for p in projects.values())
        
        if total_weight == 0:
            continue
        
        for project, proj_data in projects.items():
            project_allocated = instance_cost * (proj_data['weight'] / total_weight)
            instance_allocated[instance_id] += project_allocated
            
            proj_costs[project]['total_cost'] += project_allocated
            proj_costs[project]['samples'] += proj_data['samples']
            
            if global_gpu_ratio > 0:
                proj_costs[project]['gpu_cost'] += project_allocated * global_gpu_ratio
                proj_costs[project]['cpu_cost'] += project_allocated * (1 - global_gpu_ratio)
            else:
                proj_costs[project]['cpu_cost'] += project_allocated
            
            project_total_weight = proj_data['weight']
            if project_total_weight > 0:
                for username, user_data in proj_data['users'].items():
                    proj_costs[project]['users'].add(username)
                    
                    user_allocated = project_allocated * (user_data['weight'] / project_total_weight)
                    user_costs[username]['total_cost'] += user_allocated
                    user_costs[username]['projects'].add(project)
                    
                    if global_gpu_ratio > 0:
                        user_costs[username]['gpu_cost'] += user_allocated * global_gpu_ratio
                        user_costs[username]['cpu_cost'] += user_allocated * (1 - global_gpu_ratio)
                    else:
                        user_costs[username]['cpu_cost'] += user_allocated
    
    return {
        'total_cost': total_cost,
        'instance_costs': instance_costs,
        'proj_costs': proj_costs,
        'user_costs': user_costs,
        'instance_project_data': instance_project_data,
        'validation': {
            'cur_total': total_cost,
            'allocated_before': sum(instance_allocated.values()),
            'project_sum': sum(p['total_cost'] for p in proj_costs.values())
        }
    }


@cost_monitoring_bp.route('/monthly-costs/<year>/<month>', methods=['GET'])
def get_monthly_costs(year, month):
    """월별 비용 집계 API"""
    try:
        data = get_monthly_cost_data(year, month)
        
        code_aggregated = defaultdict(lambda: {
            'total_cost': 0, 'gpu_cost': 0, 'cpu_cost': 0, 
            'users': set(), 'description': '', 'names': set()
        })
        
        for p, d in data["proj_costs"].items():
            info = get_project_info(p)
            code = info["code"]
            code_aggregated[code]['total_cost'] += d["total_cost"]
            code_aggregated[code]['gpu_cost'] += d["gpu_cost"]
            code_aggregated[code]['cpu_cost'] += d["cpu_cost"]
            code_aggregated[code]['users'].update(d["users"])
            code_aggregated[code]['description'] = info["description"]
            code_aggregated[code]['names'].add(p)
        
        projects = []
        for code, d in code_aggregated.items():
            projects.append({
                "code": code,
                "name": code,
                "description": d["description"],
                "total_cost": round(d["total_cost"], 2),
                "gpu_cost": round(d["gpu_cost"], 2),
                "cpu_cost": round(d["cpu_cost"], 2),
                "users": sorted([resolve_username(u) for u in d["users"]])
            })
        projects.sort(key=lambda x: x["total_cost"], reverse=True)
        
        users = [{'username': resolve_username(u), 'total_cost': round(d['total_cost'], 2), 
                  'gpu_cost': round(d['gpu_cost'], 2), 'cpu_cost': round(d['cpu_cost'], 2),
                  'projects': sorted([get_project_info(p)["code"] for p in d['projects']])} 
                 for u, d in data['user_costs'].items()]
        users.sort(key=lambda x: x['total_cost'], reverse=True)
        
        INSTANCE_GPU_RATIO = {
            'i-004e23df368dcb30e': 0.852, 'i-06a9b5df345d47eaa': 0.852,
            'i-0d53ba43b64510164': 0.852, 'i-0dc3c13df82448939': 0.822,
            'i-0c30cae12f60d69d1': 0.0, 'i-074a73c3cf9656989': 0.635
        }
        
        instances = {}
        for instance_id, cost in data.get('instance_costs', {}).items():
            gpu_ratio = INSTANCE_GPU_RATIO.get(instance_id, 0)
            
            inst_projects = set()
            if instance_id in data.get('instance_project_data', {}):
                for proj in data['instance_project_data'][instance_id].keys():
                    info = get_project_info(proj)
                    code = info['code']
                    if code in code_aggregated and code_aggregated[code]['total_cost'] > 0.01:
                        inst_projects.add(code)
            
            if instance_id in INSTANCE_ORDER:
                instances[instance_id] = {
                    'name': INSTANCE_NAMES.get(instance_id, instance_id),
                    'type': INSTANCE_TYPES.get(instance_id, instance_id),
                    'instance_id': instance_id,
                    'total_cost_usd': round(cost, 2),
                    'total_cost_krw': round(cost * 1380, 2),
                    'gpu_cost': round(cost * gpu_ratio, 2),
                    'cpu_cost': round(cost * (1 - gpu_ratio), 2),
                    'projects': sorted(list(inst_projects))
                }
        
        return jsonify({
            'year': year,
            'month': month,
            'total_cost': round(data['total_cost'], 2),
            'data_source': 'CUR + Enhanced Agent (Monthly)',
            'projects': projects,
            'users': users,
            'instances': {k: instances[k] for k in INSTANCE_ORDER if k in instances},
            'validation': {
                'cur_total': round(data['validation']['cur_total'], 2),
                'allocated_before': round(data['validation']['allocated_before'], 2),
                'project_sum': round(data['validation']['project_sum'], 2)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'year': year, 'month': month}), 500
