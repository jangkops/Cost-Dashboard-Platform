from flask import Blueprint, request, jsonify, g
import boto3
import json
import os
from datetime import datetime

project_groups_bp = Blueprint("project_groups", __name__)

LOG_FILE = "/home/app/ansible/task_logs.json"

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

@project_groups_bp.route("/api/project-groups", methods=["POST"])
def get_project_groups():
    """프로젝트 그룹 목록 조회"""
    data = request.json
    region = data.get("region")
    instance_id = data.get("instanceId")
    
    try:
        ssm = boto3.client("ssm", region_name=region)
        
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "getent group | grep -E '^P[0-9]|^MI[0-9]|^Candidate|^MG[0-9]|^Intern' | sort"
                ]
            }
        )
        
        command_id = response["Command"]["CommandId"]
        
        import time
        time.sleep(2)
        
        result = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        output = result.get("StandardOutputContent", "")
        
        groups = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 4:
                group_name = parts[0]
                gid = parts[2]
                members = parts[3].split(",") if parts[3] else []
                groups.append({
                    "name": group_name,
                    "gid": gid,
                    "members": members,
                    "memberCount": len(members)
                })
        
        return jsonify({"groups": groups})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@project_groups_bp.route("/api/project-groups/members", methods=["POST"])
def manage_project_members():
    """프로젝트 그룹 멤버 추가/제거"""
    data = request.json
    region = data.get("region")
    instance_id = data.get("instanceId")
    group_name = data.get("groupName")
    username = data.get("username")
    action = data.get("action")
    
    user_email = getattr(g, 'user_email', 'unknown')
    
    try:
        ssm = boto3.client("ssm", region_name=region)
        ec2 = boto3.client("ec2", region_name=region)
        
        instances = ec2.describe_instances(InstanceIds=[instance_id])
        instance_name = "unknown"
        for reservation in instances["Reservations"]:
            for instance in reservation["Instances"]:
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        instance_name = tag["Value"]
        
        if action == "add":
            command = f"gpasswd -a {username} {group_name}"
            action_text = "추가"
        elif action == "remove":
            command = f"gpasswd -d {username} {group_name}"
            action_text = "제거"
        else:
            return jsonify({"error": "Invalid action"}), 400
        
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [command]
            }
        )
        
        command_id = response["Command"]["CommandId"]
        
        import time
        time.sleep(2)
        
        result = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        success = result.get("Status") == "Success"
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": user_email,
            "action": f"프로젝트 권한 멤버 {action_text}",
            "target": f"{instance_name} ({instance_id})",
            "details": f"{group_name} 그룹에 {username} {action_text}",
            "status": "성공" if success else "실패"
        }
        write_log(log_entry)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"{action_text} 완료"
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get("StandardErrorContent", "실패")
            }), 500
            
    except Exception as e:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": user_email,
            "action": f"프로젝트 권한 멤버 {action_text if 'action_text' in locals() else action}",
            "target": f"{instance_id}",
            "details": f"{group_name} 그룹에 {username} {action_text if 'action_text' in locals() else action}",
            "status": "실패"
        }
        write_log(log_entry)
        return jsonify({"error": str(e)}), 500
