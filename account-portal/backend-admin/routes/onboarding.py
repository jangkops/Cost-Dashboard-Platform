from flask import Blueprint, request, jsonify, g
import json
import os
import sys
from datetime import datetime

sys.path.append("/home/app/account-portal/backend-admin")
from ansible_runner import run_playbook

onboarding_bp = Blueprint("onboarding", __name__)

LOG_FILE = "/home/app/ansible/task_logs.json"

ALLOWED_INSTANCES = [
    'mogam-or-p4d',
    'mogam-or-p4de',
    'mogam-or-g5',
    'mogam-or-zonea-r7',
    'mogam-or-p5',
    'headnod'
]

def is_instance_allowed(instance_name):
    """허용된 인스턴스인지 확인"""
    return any(allowed.lower() in instance_name.lower() for allowed in ALLOWED_INSTANCES)

def read_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        return json.load(f)

def write_log(log_entry):
    logs = read_logs()
    logs.insert(0, log_entry)
    logs = logs[:100]
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def get_instance_name(region, instance_id):
    import boto3
    try:
        ec2 = boto3.client("ec2", region_name=region)
        res = ec2.describe_instances(InstanceIds=[instance_id])
        for reservation in res.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                name = next(
                    (tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"),
                    instance_id
                )
                return name
    except:
        pass
    return instance_id

@onboarding_bp.route("/api/sso/groups", methods=["GET"])
def get_sso_groups():
    """IAM Identity Center Groups 조회 (Permission Sets 포함)"""
    import boto3
    try:
        sso = boto3.client('sso-admin', region_name='us-east-1')
        identitystore = boto3.client('identitystore', region_name='us-east-1')
        
        instances = sso.list_instances()
        if not instances.get('Instances'):
            return jsonify({"error": "IAM Identity Center 인스턴스를 찾을 수 없습니다"}), 404
        
        instance_arn = instances['Instances'][0]['InstanceArn']
        identity_store_id = instances['Instances'][0]['IdentityStoreId']
        
        # 그룹 조회
        groups_response = identitystore.list_groups(IdentityStoreId=identity_store_id)
        
        # 모든 Permission Sets 조회
        permission_sets_response = sso.list_permission_sets(InstanceArn=instance_arn)
        
        # 모든 계정 조회
        orgs = boto3.client('organizations', region_name='us-east-1')
        accounts = []
        try:
            paginator = orgs.get_paginator('list_accounts')
            for page in paginator.paginate():
                accounts.extend([acc for acc in page['Accounts'] if acc['Status'] == 'ACTIVE'])
        except:
            pass
        
        groups = []
        for group in groups_response.get('Groups', []):
            group_id = group['GroupId']
            permission_sets = set()
            
            # 각 Permission Set과 계정에 대해 할당 조회
            for ps_arn in permission_sets_response.get('PermissionSets', []):
                for account in accounts:
                    try:
                        assignments = sso.list_account_assignments(
                            InstanceArn=instance_arn,
                            AccountId=account['Id'],
                            PermissionSetArn=ps_arn
                        )
                        
                        for assignment in assignments.get('AccountAssignments', []):
                            if assignment['PrincipalType'] == 'GROUP' and assignment['PrincipalId'] == group_id:
                                # Permission Set 이름 조회
                                ps_detail = sso.describe_permission_set(
                                    InstanceArn=instance_arn,
                                    PermissionSetArn=ps_arn
                                )
                                permission_sets.add(ps_detail['PermissionSet']['Name'])
                    except Exception as ex:
                        continue
            
            groups.append({
                "GroupId": group_id,
                "DisplayName": group['DisplayName'],
                "Description": group.get('Description', ''),
                "PermissionSets": sorted(list(permission_sets))
            })
        
        return jsonify({"groups": groups})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@onboarding_bp.route("/api/sso/permission-sets", methods=["GET"])
def get_permission_sets():
    """IAM Identity Center Permission Sets 조회"""
    import boto3
    try:
        sso = boto3.client('sso-admin', region_name='us-east-1')
        
        instances = sso.list_instances()
        if not instances.get('Instances'):
            return jsonify({"error": "IAM Identity Center 인스턴스를 찾을 수 없습니다"}), 404
        
        instance_arn = instances['Instances'][0]['InstanceArn']
        identity_store_id = instances['Instances'][0]['IdentityStoreId']
        
        permission_sets_response = sso.list_permission_sets(InstanceArn=instance_arn)
        
        permission_sets = []
        for ps_arn in permission_sets_response.get('PermissionSets', []):
            ps_detail = sso.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=ps_arn
            )
            permission_sets.append({
                "arn": ps_arn,
                "name": ps_detail['PermissionSet']['Name'],
                "description": ps_detail['PermissionSet'].get('Description', '')
            })
        
        return jsonify({
            "instance_arn": instance_arn,
            "identity_store_id": identity_store_id,
            "permission_sets": permission_sets
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@onboarding_bp.route("/api/provisioning/check-email", methods=["POST"])
def check_email():
    """이메일 중복 체크 (IAM Identity Center)"""
    data = request.json
    email = data.get("email", "")
    
    if not email:
        return jsonify({"exists": False})
    
    try:
        import boto3
        client = boto3.client("identitystore", region_name="us-east-1")
        identity_store_id = "d-906617189d"
        
        response = client.list_users(
            IdentityStoreId=identity_store_id,
            Filters=[
                {
                    "AttributePath": "UserName",
                    "AttributeValue": email
                }
            ]
        )
        
        exists = len(response.get("Users", [])) > 0
        return jsonify({"exists": exists})
    except Exception as e:
        print(f"Error checking email: {e}")
        return jsonify({"exists": False, "error": str(e)})

CHECK_INSTANCES = {
    "us-west-2": {
        "p4d": "i-06a9b5df345d47eaa",
        "g5": "i-0dc3c13df82448939"
    }
}

def _get_max_uid_from_instance(ssm, instance_id):
    """SSM으로 서버의 최대 UID 조회"""
    import time
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $3}' | sort -n | tail -1"]}
    )
    command_id = response["Command"]["CommandId"]
    time.sleep(2)
    result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    output = result.get("StandardOutputContent", "").strip()
    return int(output) if output and output.isdigit() else 0

def _get_all_uids_from_instance(ssm, instance_id):
    """SSM으로 서버의 모든 UID 목록 조회"""
    import time
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $3}' | sort -n"]}
    )
    command_id = response["Command"]["CommandId"]
    time.sleep(2)
    result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    output = result.get("StandardOutputContent", "").strip()
    return set(int(x) for x in output.split("\n") if x.strip().isdigit()) if output else set()

@onboarding_bp.route("/api/provisioning/predict-uid", methods=["POST"])
def predict_uid():
    """p4d, g5 교차확인으로 다음 사용 가능한 UID/GID 조회"""
    import boto3
    ssm = boto3.client("ssm", region_name="us-west-2")
    all_uids = set()
    
    for name, iid in CHECK_INSTANCES["us-west-2"].items():
        try:
            uids = _get_all_uids_from_instance(ssm, iid)
            all_uids.update(uids)
        except Exception as e:
            print(f"Error predict UID from {name}: {e}")
    
    # 1026부터 시작하여 빈 UID 찾기
    next_uid = 1026
    while next_uid in all_uids:
        next_uid += 1
    
    return jsonify({"predicted_uid": next_uid})

@onboarding_bp.route("/api/provisioning/check-uid", methods=["POST"])
def check_uid():
    """UID/GID 중복 체크 (p4d, g5 교차확인)"""
    data = request.json
    check_uid_val = data.get("uid")
    
    if not check_uid_val:
        return jsonify({"exists": False})
    
    check_uid_val = int(check_uid_val)
    import boto3
    ssm = boto3.client("ssm", region_name="us-west-2")
    exists_on = []
    
    for name, iid in CHECK_INSTANCES["us-west-2"].items():
        try:
            uids = _get_all_uids_from_instance(ssm, iid)
            if check_uid_val in uids:
                exists_on.append(name)
        except Exception as e:
            print(f"Error checking UID on {name}: {e}")
    
    return jsonify({"exists": len(exists_on) > 0, "exists_on": exists_on})

@onboarding_bp.route("/api/provisioning/check-user", methods=["POST"])
def check_user():
    """사용자명 중복 체크 (Ansible) - 서버 미선택 시 p4d/g5 기본 체크"""
    data = request.json
    username = data.get("username")
    region_instances = data.get("regionInstances", {})
    
    if not username:
        return jsonify({"exists": False})
    
    # 서버 미선택 시 p4d, g5 기본 체크
    if not region_instances:
        region_instances = {"us-west-2": list(CHECK_INSTANCES["us-west-2"].values())}
    
    exists_on = []
    
    for region, instances in region_instances.items():
        for instance_id in instances:
            try:
                result = run_playbook(
                    "check_user.yml",
                    {
                        "region": region,
                        "instance_id": instance_id,
                        "username": username
                    }
                )
                
                if result.get("status") == "success":
                    stdout = result.get("stdout", "")
                    if '"exists": true' in stdout or "'exists': True" in stdout:
                        instance_name = get_instance_name(region, instance_id)
                        exists_on.append({
                            "region": region,
                            "instance": instance_name,
                            "instance_id": instance_id
                        })
                    
            except Exception as e:
                print(f"Error checking user on {instance_id}: {e}")
                continue
    
    return jsonify({
        "exists": len(exists_on) > 0,
        "exists_on": exists_on
    })

@onboarding_bp.route("/api/provisioning/onboarding", methods=["POST"])
def onboarding():
    """통합 프로비저닝 (Ansible + SSO + SES)"""
    data = request.json
    email = data.get("email")
    username = data.get("username")
    uid = data.get("uid")
    gid = data.get("gid")
    role = data.get("role", "user")
    groups = data.get("groups", [])
    sso_group_ids = data.get("ssoGroups", [])
    region_instances = data.get("regionInstances", {})
    dry_run = data.get("dryRun", False)
    
    user_email = getattr(g, 'user_email', 'unknown')
    
    if not email or not username:
        return jsonify({"error": "email, username은 필수입니다."}), 400
    
    if not region_instances or len(region_instances) == 0:
        return jsonify({"error": "최소 1개 이상의 서버를 선택해주세요."}), 400
    
    # 그룹은 선택사항
    
    # UID/GID 자동 할당 - p4d, g5 교차확인으로 빈 UID 찾기
    if not uid or not gid:
        import boto3
        ssm = boto3.client("ssm", region_name="us-west-2")
        all_uids = set()
        for name, iid in CHECK_INSTANCES["us-west-2"].items():
            try:
                uids = _get_all_uids_from_instance(ssm, iid)
                all_uids.update(uids)
            except Exception as e:
                print(f"Error getting UIDs from {name}: {e}")
        next_uid = 1026
        while next_uid in all_uids:
            next_uid += 1
        uid = next_uid
        gid = next_uid
    
    # SSO 사용자 생성 및 이메일 발송 (Ansible)
    sso_result = None
    if sso_group_ids and len(sso_group_ids) > 0:
        if dry_run:
            sso_result = {"success": True, "message": "DRY RUN - SSO 사용자 생성 및 이메일 발송 건너뜀", "dry_run": True}
        else:
            try:
                result = run_playbook(
                    "create_sso_user.yml",
                    {
                        "email": email,
                        "permission_set_arns": [],
                        "sso_group_ids": sso_group_ids
                    }
                )
                
                if result.get("status") == "success":
                    stdout = result.get("stdout", "")
                    for line in stdout.split('\n'):
                        if line.strip().startswith('{') and 'user_id' in line:
                            try:
                                sso_result = json.loads(line.strip())
                            except:
                                pass
                    
                    if not sso_result:
                        sso_result = {
                            "success": True,
                            "message": "SSO user created and email sent"
                        }
                else:
                    sso_result = {
                        "success": False,
                        "error": result.get("error", "SSO user creation failed")
                    }
            except Exception as e:
                sso_result = {
                    "success": False,
                    "error": str(e)
                }
    
    results = []
    
    for region, instances in region_instances.items():
        for instance_id in instances:
            try:
                instance_name = get_instance_name(region, instance_id)
                
                # 허용된 인스턴스인지 확인
                if not is_instance_allowed(instance_name):
                    results.append({
                        "region": region,
                        "instance": instance_name,
                        "instance_id": instance_id,
                        "success": False,
                        "error": "선택 불가능한 서버입니다",
                        "stdout": "",
                        "stderr": ""
                    })
                    continue
                
                result = run_playbook(
                    "onboarding_provisioning.yml",
                    {
                        "region": region,
                        "instance_id": instance_id,
                        "username": username,
                        "uid": uid,
                        "gid": gid,
                        "role": role,
                        "user_groups": groups,
                        "dry_run": dry_run
                    }
                )
                
                success = result.get("status") == "success"
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                error_msg = result.get("error", "")
                
                if "already exists" in stdout.lower() or "already exists" in error_msg.lower():
                    success = False
                    error_msg = "사용자가 이미 존재합니다"
                
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "user": user_email,
                    "action": "통합 프로비저닝 (Ansible)",
                    "target": f"{instance_name} ({instance_id})",
                    "details": f"사용자: {username}, 권한: {role}, 그룹: {', '.join(groups) if groups else '없음'}",
                    "status": "성공" if success else "실패"
                }
                write_log(log_entry)
                
                results.append({
                    "region": region,
                    "instance": instance_name,
                    "instance_id": instance_id,
                    "success": success,
                    "error": error_msg if not success else None,
                    "stdout": stdout,
                    "stderr": stderr
                })
                
            except Exception as e:
                instance_name = get_instance_name(region, instance_id)
                error_msg = str(e)
                
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "user": user_email,
                    "action": "통합 프로비저닝 (Ansible)",
                    "target": f"{instance_name} ({instance_id})",
                    "details": f"사용자: {username}, 권한: {role}",
                    "status": "실패"
                }
                write_log(log_entry)
                
                results.append({
                    "region": region,
                    "instance": instance_name,
                    "instance_id": instance_id,
                    "success": False,
                    "error": error_msg
                })
    
    success_count = len([r for r in results if r.get("success")])
    fail_count = len([r for r in results if not r.get("success")])
    
    return jsonify({
        "email": email,
        "username": username,
        "uid": uid,
        "gid": gid,
        "role": role,
        "user_groups": groups,
        "sso_result": sso_result,
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results
    })
