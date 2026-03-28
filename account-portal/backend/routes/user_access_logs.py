from flask import Blueprint, jsonify
import boto3
import re
from datetime import datetime

user_access_logs_bp = Blueprint('user_access_logs', __name__)

@user_access_logs_bp.route('/api/user-access-logs', methods=['GET'])
def get_user_access_logs():
    try:
        ssm = boto3.client('ssm', region_name='us-west-2')
        ec2 = boto3.client('ec2', region_name='us-west-2')
        
        instances_info = ssm.describe_instance_information(
            Filters=[{'Key': 'PingStatus', 'Values': ['Online']}]
        )
        
        instance_ids = [inst['InstanceId'] for inst in instances_info['InstanceInformationList']]
        
        if not instance_ids:
            return jsonify({'logs': []})
        
        ec2_response = ec2.describe_instances(InstanceIds=instance_ids)
        instance_names = {}
        for reservation in ec2_response['Reservations']:
            for instance in reservation['Instances']:
                inst_id = instance['InstanceId']
                name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), inst_id)
                instance_names[inst_id] = name
        
        all_logs = []
        
        for instance_id in instance_ids:
            instance_name = instance_names.get(instance_id, instance_id)
            
            try:
                response = ssm.send_command(
                    InstanceIds=[instance_id],
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': ['last -n 200 -F 2>/dev/null']},
                    TimeoutSeconds=30
                )
                command_id = response['Command']['CommandId']
                
                import time
                time.sleep(1.5)
                
                result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
                
                if result.get('Status') == 'Success':
                    output = result.get('StandardOutputContent', '')
                    for line in output.strip().split('\n'):
                        if not line or 'wtmp' in line or 'still logged in' in line or 'reboot' in line:
                            continue
                        
                        match = re.search(r'^(\S+)\s+(\S+)\s+(\S+)\s+\w+\s+(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s+(\d+)', line)
                        if match:
                            username = match.group(1)
                            terminal = match.group(2)
                            source = match.group(3)
                            month = match.group(4)
                            day = match.group(5)
                            hour = match.group(6)
                            minute = match.group(7)
                            second = match.group(8)
                            year = match.group(9)
                            
                            if not username or username == '':
                                continue
                            
                            try:
                                dt = datetime.strptime(f'{year} {month} {day} {hour}:{minute}:{second}', '%Y %b %d %H:%M:%S')
                                timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S')
                                
                                all_logs.append({
                                    'timestamp': timestamp,
                                    'username': username,
                                    'region': 'us-west-2',
                                    'instance_id': instance_id,
                                    'instance_name': instance_name,
                                    'source_ip': source if ':' not in source else terminal,
                                    'terminal': terminal,
                                    'action': 'SSH 접속'
                                })
                            except:
                                pass
            except:
                pass
        
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'logs': all_logs[:500]})
        
    except Exception as e:
        return jsonify({'error': str(e), 'logs': []}), 500
