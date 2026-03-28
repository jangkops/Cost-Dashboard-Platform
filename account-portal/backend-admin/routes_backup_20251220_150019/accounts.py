from flask import Blueprint, request, jsonify
import boto3
import time
import traceback

accounts_bp = Blueprint("accounts", __name__)

SYSTEM_ACCOUNTS = ['nobody', 'ec2-user', 'ssm-user', 'ubuntu', 'admin', 'centos']

@accounts_bp.route("/api/accounts", methods=["POST"])
def get_accounts():
    data = request.json
    region = data.get("region")
    instance_id = data.get("instanceId")

    if not region or not instance_id:
        return jsonify({"error": "region and instanceId are required"}), 400

    try:
        ssm = boto3.client('ssm', region_name=region)
        
        cmd = r'''
for user in $(grep -E "^[^:]+:x:[0-9]{4,}:" /etc/passwd | cut -d: -f1); do
  role="none"
  if id -nG "$user" 2>/dev/null | grep -qw mogam-admin; then
    role="admin"
  elif id -nG "$user" 2>/dev/null | grep -qw mogam-ops; then
    role="ops"
  elif id -nG "$user" 2>/dev/null | grep -qw mogam-user; then
    role="user"
  fi
  echo "$user:$role"
done
'''
        
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [cmd]}
        )
        
        command_id = response['Command']['CommandId']
        time.sleep(3)
        
        result = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        accounts = []
        for line in result.get('StandardOutputContent', '').split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            username, role = line.split(':', 1)
            if username not in SYSTEM_ACCOUNTS:
                accounts.append({"username": username, "role": role})
        
        return jsonify({"accounts": accounts})
    except Exception as e:
        print(f"Error in get_accounts: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
