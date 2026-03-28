from flask import Blueprint, request, jsonify
import boto3
import secrets
import string

sso_bp = Blueprint('sso', __name__)

def generate_temp_password(length=16):
    """임시 비밀번호 생성"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(chars) for _ in range(length))

def send_ses_email(to_email, subject, body):
    """AWS SES로 이메일 발송"""
    try:
        ses = boto3.client('ses', region_name='us-east-1')
        
        response = ses.send_email(
            Source='noreply@mogam.re.kr',
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
            }
        )
        
        print(f"SES email sent to {to_email}, MessageId: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"SES error: {e}")
        return False

@sso_bp.route('/api/provision-sso-user', methods=['POST'])
def provision_sso_user():
    """IAM Identity Center 사용자 생성 및 초대 이메일 발송"""
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        role = data.get('role', 'user')
        username = email.split('@')[0].replace('.', '_')
        first_name = username.capitalize()
        last_name = 'User'
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Valid email required'}), 400
        
        # AWS 세션 생성
        session = boto3.Session()
        
        # Identity Store 클라이언트 (버지니아)
        identitystore = session.client('identitystore', region_name='us-east-1')
        identity_store_id = 'd-90679e0e0f'
        
        # 1. 사용자 생성
        print(f"Creating user: {username} with email {email}")
        
        user_response = identitystore.create_user(
            IdentityStoreId=identity_store_id,
            UserName=username,
            DisplayName=f"{first_name} {last_name}",
            Name={
                'GivenName': first_name,
                'FamilyName': last_name
            },
            Emails=[{
                'Value': email,
                'Type': 'work',
                'Primary': True
            }]
        )
        
        user_id = user_response['UserId']
        print(f"User created: {user_id}")
        
        # 2. 비밀번호 재설정 URL
        reset_url = "https://d-90679e0e0f.awsapps.com/start"
        
        # 3. 이메일 발송
        subject = "Welcome to Mogam Identity Center"
        body = f"""Hello {first_name},

Your account has been created in Mogam Identity Center.

Username: {username}
Email: {email}
Role: {role}

Please set your password by visiting:
{reset_url}

After setting your password, you can access the portal.

If you have any questions, please contact the administrator.

Best regards,
Mogam Team
"""
        
        email_sent = send_ses_email(email, subject, body)
        
        if not email_sent:
            print("Warning: User created but email failed to send")
        
        return jsonify({
            'success': True,
            'message': f'User {username} created successfully',
            'username': username,
            'display_name': f"{first_name} {last_name}",
            'role': role,
            'application': 'Mogam Identity Center',
            'userId': user_id,
            'email': email,
            'emailSent': email_sent,
            'real_creation': True
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error creating user: {error_msg}")
        
        # 사용자 이미 존재하는 경우
        if 'ConflictException' in error_msg or 'already exists' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'User already exists in Identity Center'
            }), 409
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
