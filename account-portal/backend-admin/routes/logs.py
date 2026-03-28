from flask import Blueprint, jsonify
import json
import os
from datetime import datetime

logs_bp = Blueprint("logs", __name__)

LOG_FILE = "/home/app/ansible/task_logs.json"

def read_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        return json.load(f)

def write_log(log_entry):
    logs = read_logs()
    logs.insert(0, log_entry)
    logs = logs[:200]  # 최근 100개만 유지
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

@logs_bp.route("/api/logs", methods=["GET"])
def get_logs():
    """작업 로그 조회"""
    try:
        logs = read_logs()
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/api/portal-logs", methods=["GET"])
def get_portal_logs():
    """포털 작업 로그 조회 (호환성)"""
    return get_logs()
