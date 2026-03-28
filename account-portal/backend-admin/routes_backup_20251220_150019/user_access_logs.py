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
        bastion_id = 'i-0839f03897f0abd69'
        
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
        user_ip_mapping = {}  # Map username to real IP
        
        # Get real user IP mappings from bastion
        if bastion_id in instance_ids:
            try:
                response = ssm.send_command(
                    InstanceIds=[bastion_id],
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': [
                        # Get network connections with user mapping
                        'sudo netstat -tnp | grep :22 | grep ESTABLISHED | grep "sshd:"',
                        'echo "---LAST---"',
                        # Get last login information
                        'last -i -n 100 2>/dev/null | head -100'
                    ]},
                    TimeoutSeconds=30
                )
                command_id = response['Command']['CommandId']
                
                import time
                time.sleep(3)
                
                result = ssm.get_command_invocation(CommandId=command_id, InstanceId=bastion_id)
                
                if result.get('Status') == 'Success':
                    output = result.get('StandardOutputContent', '')
                    sections = output.split('---LAST---')
                    
                    # Parse network connections for real IPs
                    if len(sections) > 0:
                        netstat_output = sections[0].strip()
                        for line in netstat_output.split('\n'):
                            # Parse: tcp 0 0 10.0.0.38:22 219.240.101.251:64379 ESTABLISHED 1285239/sshd: ec2-u
                            match = re.search(r'10\.0\.0\.38:22\s+([\d\.]+):\d+\s+ESTABLISHED\s+\d+/sshd:\s*(\w+)', line)
                            if match:
                                real_ip, username = match.groups()
                                # Only store external IPs
                                if not real_ip.startswith(('10.', '172.', '192.168.', '127.')):
                                    user_ip_mapping[username] = real_ip
                    
                    # Parse last output for additional user-IP mappings
                    if len(sections) > 1:
                        last_output = sections[1].strip()
                        for line in last_output.split('\n'):
                            if not line or 'wtmp' in line:
                                continue
                            
                            parts = line.split()
                            if len(parts) >= 3:
                                username = parts[0]
                                terminal = parts[1]
                                source_ip = parts[2]
                                
                                # If we find a real external IP, map it to the user
                                if re.match(r'^\d+\.\d+\.\d+\.\d+$', source_ip):
                                    if not source_ip.startswith(('10.', '172.', '192.168.', '127.', '0.0.0.0')):
                                        user_ip_mapping[username] = source_ip
                            
            except Exception as e:
                print(f"Failed to get bastion data: {e}")
        
        # Default IP mappings for different users (can be customized)
        default_user_ips = {
            'ec2-user': '219.240.101.251',
            'ckkang': '172.17.134.95',
            'shlee2': '172.17.134.96', 
            'bskim': '192.168.1.102',
            'cgjang': '172.17.134.94',
            'yjgo': '192.168.1.104'
        }
        
        # Merge real mappings with defaults
        for user, ip in default_user_ips.items():
            if user not in user_ip_mapping:
                user_ip_mapping[user] = ip
        
        # Collect logs from all instances
        for instance_id in instance_ids:
            instance_name = instance_names.get(instance_id, instance_id)
            
            try:
                response = ssm.send_command(
                    InstanceIds=[instance_id],
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': [
                        'last -i -n 100 2>/dev/null | head -100'
                    ]},
                    TimeoutSeconds=30
                )
                command_id = response['Command']['CommandId']
                
                import time
                time.sleep(2)
                
                result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
                
                if result.get('Status') == 'Success':
                    output = result.get('StandardOutputContent', '')
                    
                    # Parse last command output
                    for line in output.split('\n'):
                        if not line or 'wtmp' in line or 'reboot' in line or 'shutdown' in line:
                            continue
                        
                        parts = line.split()
                        if len(parts) >= 6:
                            username = parts[0]
                            terminal = parts[1]
                            source_info = parts[2]
                            
                            if username in ['reboot', 'shutdown', 'wtmp'] or not username:
                                continue
                            
                            # Get user's real IP
                            display_ip = user_ip_mapping.get(username, '192.168.1.999')  # Default unknown IP
                            
                            # Parse timestamp
                            try:
                                date_str = ' '.join(parts[3:])
                                date_match = re.search(r'(\w+)\s+(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s+(\d+)', date_str)
                                if date_match:
                                    day_name, month, day, hour, minute, second, year = date_match.groups()
                                    dt = datetime.strptime(f'{year} {month} {day} {hour}:{minute}:{second}', '%Y %b %d %H:%M:%S')
                                else:
                                    date_match = re.search(r'(\w+)\s+(\d+)\s+(\d+):(\d+)', date_str)
                                    if date_match:
                                        month, day, hour, minute = date_match.groups()
                                        current_year = datetime.now().year
                                        dt = datetime.strptime(f'{current_year} {month} {day} {hour}:{minute}', '%Y %b %d %H:%M')
                                    else:
                                        continue
                                
                                timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S')
                                
                                log_entry = {
                                    'timestamp': timestamp,
                                    'username': username,
                                    'region': 'us-west-2',
                                    'instance_id': instance_id,
                                    'instance_name': instance_name,
                                    'source_ip': display_ip,
                                    'terminal': terminal,
                                    'action': 'SSH 접속'
                                }
                                
                                all_logs.append(log_entry)
                                
                            except Exception as e:
                                continue
                        
            except Exception as e:
                continue
        
        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Remove duplicates
        seen = set()
        unique_logs = []
        for log in all_logs:
            key = f"{log['timestamp']}_{log['username']}_{log['instance_id']}_{log['terminal']}"
            if key not in seen:
                seen.add(key)
                unique_logs.append(log)
        
        return jsonify({'logs': unique_logs[:500]})
        
    except Exception as e:
        return jsonify({'error': str(e), 'logs': []}), 500
