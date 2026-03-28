from flask import Blueprint, jsonify
import json
import os
from datetime import datetime

audit_logs_bp = Blueprint("audit_logs", __name__)

AUDIT_LOG_FILE = "/home/app/ansible/audit_logs.json"

def read_audit_logs():
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    with open(AUDIT_LOG_FILE, 'r') as f:
        return json.load(f)

def write_audit_log(log_entry):
    logs = read_audit_logs()
    logs.insert(0, log_entry)
    logs = logs[:500]  # 최근 500개만 유지
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    with open(AUDIT_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

@audit_logs_bp.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():
    """감사 로그 조회"""
    try:
        logs = read_audit_logs()
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
