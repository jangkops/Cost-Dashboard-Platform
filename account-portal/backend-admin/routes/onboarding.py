from flask import Blueprint, request, jsonify
import json
import os
import sys

sys.path.append("/home/app/ansible")
from ansible_runner import run_playbook

onboarding_bp = Blueprint("onboarding", __name__)

POLICIES_FILE = "/home/app/user-portal/backend/policies.json"

def load_policies():
    with open(POLICIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@onboarding_bp.route("/api/provisioning/onboarding", methods=["POST"])
def onboarding():
    data = request.json
    email = data.get("email")
    department = data.get("department")
    
    if not email or not department:
        return jsonify({"error": "email과 department는 필수입니다."}), 400
    
    username = email.split("@")[0].replace(".", "_")
    
    policies = load_policies()
    role_config = policies["role_mappings"].get(department)
    
    if not role_config:
        return jsonify({"error": f"부서 {department}에 대한 정책이 없습니다."}), 400
    
    results = []
    for group_name in role_config["server_groups"]:
        group_config = policies["server_groups"].get(group_name)
        if not group_config:
            continue
        
        region = group_config["region"]
        
        playbook_path = f"regions/{region}/playbooks/create_account.yml"
        extra_vars = {
            "username": username,
            "shell": role_config["shell"],
            "sudo_access": role_config["sudo"],
            "target_group": group_name
        }
        
        result = run_playbook(playbook_path, extra_vars)
        results.append({
            "group": group_name,
            "region": region,
            "success": result.get("success", False),
            "output": result.get("output", "")
        })
    
    return jsonify({
        "email": email,
        "username": username,
        "department": department,
        "sso_created": False,
        "server_results": results
    })
