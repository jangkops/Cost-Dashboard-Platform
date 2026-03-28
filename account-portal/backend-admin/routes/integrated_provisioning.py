from flask import Blueprint, request, jsonify
import boto3
import sys

sys.path.append("/home/app/ansible")
from ansible_runner import run_playbook

integrated_provisioning_bp = Blueprint('integrated_provisioning', __name__)

def send_ses_email_mock(to_email, subject, body):
    print("[MOCK] Would send email to: {}".format(to_email))
    print("[MOCK] Subject: {}".format(subject))
    return True

@integrated_provisioning_bp.route('/api/integrated-provisioning', methods=['POST'])
def integrated_provisioning():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        region = data.get('region', 'us-east-1')
        username = data.get('username', '').strip()
        project_group = data.get('project_group', '').strip()
        target_account_id = data.get('target_account_id', '').strip()
        instance_ids = data.get('instance_ids', [])
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Valid email required'}), 400
        if not username:
            username = email.split('@')[0].replace('.', '_')
        if not project_group:
            return jsonify({'success': False, 'error': 'Project group required'}), 400
        if not target_account_id:
            return jsonify({'success': False, 'error': 'Target AWS account ID required'}), 400
        if not instance_ids:
            return jsonify({'success': False, 'error': 'At least one instance ID required'}), 400
        
        identitystore = boto3.client('identitystore', region_name='us-east-1')
        identity_store_id = 'd-90679e0e0f'
        first_name = username.split('_')[0].capitalize()
        last_name = username.split('_')[-1].capitalize() if '_' in username else 'User'
        
        print("Creating SSO user: {} ({})".format(username, email))
        
        user_response = identitystore.create_user(
            IdentityStoreId=identity_store_id,
            UserName=username,
            DisplayName="{} {}".format(first_name, last_name),
            Name={'GivenName': first_name, 'FamilyName': last_name},
            Emails=[{'Value': email, 'Type': 'work', 'Primary': True}]
        )
        
        user_id = user_response['UserId']
        print("SSO user created: {}".format(user_id))
        
        reset_url = "https://d-90679e0e0f.awsapps.com/start"
        subject = "Welcome to Mogam Identity Center"
        body = """Hello {},

Your account has been created in Mogam Identity Center.

Username: {}
Email: {}
Project Group: {}

Please set your password and configure MFA by visiting:
{}

Best regards,
Mogam Team
""".format(first_name, username, email, project_group, reset_url)
        
        email_sent = send_ses_email_mock(email, subject, body)
        
        playbook_path = "integrated_provisioning.yml"
        extra_vars = {
            "user_id": user_id,
            "username": username,
            "project_group": project_group,
            "target_account_id": target_account_id,
            "instance_ids": instance_ids,
            "region": region
        }
        
        print("Running Ansible playbook: {}".format(playbook_path))
        ansible_result = run_playbook(playbook_path, extra_vars)
        
        return jsonify({
            'success': True,
            'message': 'User {} provisioned successfully'.format(username),
            'sso': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'email_sent': email_sent
            },
            'ansible': {
                'status': ansible_result.get('status'),
                'output': ansible_result.get('stdout', '')[:500]
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        print("Error in integrated provisioning: {}".format(error_msg))
        
        if 'ConflictException' in error_msg or 'already exists' in error_msg.lower():
            return jsonify({'success': False, 'error': 'User already exists in Identity Center'}), 409
        
        return jsonify({'success': False, 'error': error_msg}), 500
