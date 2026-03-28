from flask import Blueprint, request, jsonify
from ansible_runner import run_playbook
from routes.logs import write_log
from datetime import datetime
import pytz
import boto3

delete_account_bp = Blueprint("delete_account", __name__)

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

@delete_account_bp.route("/api/delete-account", methods=["POST"])
def delete_account():
    data = request.json
    region_instances = data.get("regionInstances", {})
    usernames = data.get("usernames") if isinstance(data.get("usernames"), list) else [data.get("username")]
    
    results = []
    seoul_tz = pytz.timezone('Asia/Seoul')
    
    for username in usernames:
        for region, instances in region_instances.items():
            for instance in instances:
                try:
                    instance_name = get_instance_name(region, instance)
                    
                    output = run_playbook(
                        f"regions/{region}/playbooks/delete_account.yml",
                        {
                            "username": username,
                            "instance_ids": instance
                        }
                    )
                    
                    success = output.get("status") == "success"
                    
                    log_entry = {
                        "timestamp": datetime.now(seoul_tz).isoformat(),
                        "action": "계정 삭제",
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "instance_name": instance_name,
                        "status": "완료" if success else "실패",
                        "reason": output.get("error", "") if not success else "",
                        "details": output.get("stdout", "") + "\n" + output.get("stderr", "")
                    }
                    write_log(log_entry)
                    
                    results.append({
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "success": success,
                        "result": output
                    })
                    
                except Exception as e:
                    instance_name = get_instance_name(region, instance)
                    log_entry = {
                        "timestamp": datetime.now(seoul_tz).isoformat(),
                        "action": "계정 삭제",
                        "username": username,
                        "region": region,
                        "instance": instance,
                        "instance_name": instance_name,
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
                        "error": str(e)
                    })
    
    success_count = len([r for r in results if r.get("success")])
    fail_count = len([r for r in results if not r.get("success")])
    
    return jsonify({
        "success": fail_count == 0,
        "message": f"{success_count}개 성공, {fail_count}개 실패",
        "results": results
    })
