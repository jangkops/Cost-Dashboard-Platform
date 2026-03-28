from flask import Blueprint, request, jsonify
from ansible_runner import run_playbook
from routes.logs import write_log
from datetime import datetime
import pytz
import boto3

create_account_bp = Blueprint("create_account", __name__)

def get_instance_name(region, instance_id):
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

@create_account_bp.route("/api/create-account", methods=["POST"])
def create_account():
    data = request.json
    region_instances = data.get("regionInstances", {})
    username = data.get("username")
    
    results = []
    has_duplicate = False
    first_error = None
    seoul_tz = pytz.timezone('Asia/Seoul')
    
    for region, instances in region_instances.items():
        for instance in instances:
            try:
                instance_name = get_instance_name(region, instance)
                
                result = run_playbook(
                    f"regions/{region}/playbooks/create_account.yml",
                    {
                        "username": username,
                        "role": data.get("role"),
                        "instance_ids": instance
                    }
                )
                
                success = result.get("status") == "success"
                error_msg = result.get("error", "")
                
                if not success and "already exists" in result.get("stdout", ""):
                    has_duplicate = True
                    error_msg = f"User 중복계정(이미 계정이 존재합니다.)"
                elif not success and not first_error:
                    first_error = error_msg if error_msg else "생성 실패"
                
                log_entry = {
                    "timestamp": datetime.now(seoul_tz).isoformat(),
                    "action": "계정 생성",
                    "username": username,
                    "region": region,
                    "instance": instance,
                    "instance_name": instance_name,
                    "role": data.get("role"),
                    "status": "완료" if success else "실패",
                    "reason": error_msg if not success else "",
                    "details": result.get("stdout", "") + "\n" + result.get("stderr", "")
                }
                write_log(log_entry)
                
                results.append({
                    "region": region,
                    "instance": instance,
                    "success": success,
                    "error": error_msg if not success else None
                })
                
            except Exception as e:
                instance_name = get_instance_name(region, instance)
                error_msg = str(e)
                if not first_error:
                    first_error = error_msg
                    
                log_entry = {
                    "timestamp": datetime.now(seoul_tz).isoformat(),
                    "action": "계정 생성",
                    "username": username,
                    "region": region,
                    "instance": instance,
                    "instance_name": instance_name,
                    "role": data.get("role"),
                    "status": "실패",
                    "reason": error_msg,
                    "details": error_msg
                }
                write_log(log_entry)
                results.append({
                    "region": region,
                    "instance": instance,
                    "success": False,
                    "error": error_msg
                })
    
    success_count = len([r for r in results if r.get("success")])
    fail_count = len([r for r in results if not r.get("success")])
    
    if has_duplicate:
        return jsonify({
            "success": False,
            "message": f"des : User 중복계정(이미 계정이 존재합니다.)"
        }), 400
    
    if fail_count > 0:
        error_detail = first_error if first_error else "생성 실패"
        message = f"des : {error_detail}"
        if len(results) > 1:
            message = f"{success_count}개 성공, {fail_count}개 실패 - {error_detail}"
        
        return jsonify({
            "success": False,
            "message": message
        }), 400
    
    return jsonify({
        "success": True,
        "message": "계정이 생성되었습니다."
    })
