from flask import Blueprint, request, jsonify
from ansible_runner import run_playbook
from routes.logs import write_log
from datetime import datetime
import pytz
import boto3

update_role_bp = Blueprint("update_role", __name__)

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

@update_role_bp.route("/api/update-role", methods=["POST"])
def update_role():
    data = request.json
    region_instances = data.get("regionInstances", {})
    usernames = data.get("usernames") if isinstance(data.get("usernames"), list) else [data.get("username")]
    role = data.get("role")
    
    results = []
    seoul_tz = pytz.timezone('Asia/Seoul')
    
    for username in usernames:
        for region, instances in region_instances.items():
            for instance in instances:
                try:
                    instance_name = get_instance_name(region, instance)
                    
                    output = run_playbook(
                        f"regions/{region}/playbooks/update_role.yml",
                        {
                            "username": username,
                            "role": role,
                            "instance_ids": instance
                        }
                    )
                    
                    status = output.get("status")
                    success = status == "success"
                    skipped = status == "skipped"
                    
                    if skipped:
                        log_status = "유지"
                    elif success:
                        log_status = "완료"
                    else:
                        log_status = "실패"
                    
                    log_entry = {
                        "timestamp": datetime.now(seoul_tz).isoformat(),
                        "action": "계정 권한 변경",
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "instance_name": instance_name,
                        "role": role,
                        "status": log_status,
                        "reason": output.get("error", "") if not success and not skipped else "",
                        "details": output.get("stdout", "") + "\n" + output.get("stderr", "")
                    }
                    write_log(log_entry)
                    
                    results.append({
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "success": success,
                        "skipped": skipped,
                        "result": output
                    })
                    
                except Exception as e:
                    instance_name = get_instance_name(region, instance)
                    log_entry = {
                        "timestamp": datetime.now(seoul_tz).isoformat(),
                        "action": "계정 권한 변경",
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "instance_name": instance_name,
                        "role": role,
                        "status": "실패",
                        "reason": str(e),
                        "details": str(e)
                    }
                    write_log(log_entry)
                    results.append({
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "success": False,
                        "skipped": False,
                        "error": str(e)
                    })
    
    success_count = len([r for r in results if r.get("success")])
    fail_count = len([r for r in results if not r.get("success") and not r.get("skipped")])
    skip_count = len([r for r in results if r.get("skipped")])
    
    message_parts = []
    if success_count > 0:
        message_parts.append(f"{success_count}개 변경")
    if skip_count > 0:
        message_parts.append(f"{skip_count}개 유지")
    if fail_count > 0:
        message_parts.append(f"{fail_count}개 실패")
    
    return jsonify({
        "success": fail_count == 0,
        "unchanged": skip_count > 0 and success_count == 0 and fail_count == 0,
        "message": ", ".join(message_parts) if message_parts else "처리 완료",
        "results": results
    })
