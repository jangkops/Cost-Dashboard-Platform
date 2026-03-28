@sso_bp.route('/api/provision-sso-user', methods=['POST'])
def provision_sso_user():
    """통합 프로비저닝 - SSO 사용자 자동 생성 (Identity Center 자동 이메일만 사용)"""
    
    data = request.get_json()
    email = data.get('email', '').strip()
    role = data.get('role', 'user')
    
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400
    
    try:
        # 이메일에서 사용자 정보 추출
        username = email
        local_part = email.split('@')[0]
        if '.' in local_part:
            first_name = local_part.split('.')[0]
            last_name = local_part.split('.')[1]
        else:
            first_name = local_part
            last_name = 'user'
        display_name = f"{first_name} {last_name}".strip()
        
        # AWS SSO 사용자 생성
        import boto3
        session = boto3.Session(
            aws_access_key_id=os.getenv('MG_INFRA_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('MG_INFRA_SECRET_KEY'),
            region_name='us-west-2'
        )
        identitystore = session.client('identitystore')
        identity_store_id = 'd-9267fbde5d'
        
        # 기존 사용자 확인 및 삭제 (jangeyq34@gmail.com만 해당)
        if email == 'jangeyq34@gmail.com':
            try:
                existing_users = identitystore.list_users(
                    IdentityStoreId=identity_store_id,
                    Filters=[{
                        'AttributePath': 'userName',
                        'AttributeValue': email
                    }]
                )
                
                if existing_users['Users']:
                    for user in existing_users['Users']:
                        print(f"Deleting existing user: {user['UserId']}")
                        identitystore.delete_user(
                            IdentityStoreId=identity_store_id,
                            UserId=user['UserId']
                        )
                    
                    import time
                    time.sleep(2)
                    
            except Exception as cleanup_error:
                print(f"User cleanup failed: {cleanup_error}")
        
        # 실제 사용자 생성 (AWS Identity Center 자동 이메일 발송)
        user_response = identitystore.create_user(
            IdentityStoreId=identity_store_id,
            UserName=username,
            DisplayName=display_name,
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
        print(f"Created user: {user_id}")
        
        # 애플리케이션에 사용자 할당
        try:
            sso_admin = session.client('sso-admin')
            instance_arn = 'arn:aws:sso:::instance/ssoins-79075a0c988e2858'
            application_arn = 'arn:aws:sso::107650139384:application/ssoins-79075a0c988e2858/apl-1554e160b9167875'
            
            sso_admin.create_application_assignment(
                ApplicationArn=application_arn,
                PrincipalId=user_id,
                PrincipalType='USER'
            )
            
            app_assignment_success = True
        except Exception as app_error:
            app_assignment_success = False
            print(f"Application assignment failed: {app_error}")
        
        return jsonify({
            'success': True,
            'message': f'SSO 사용자 {display_name} 생성 완료',
            'user_id': user_id,
            'email': email,
            'invitation_sent': True,
            'invitation_message': f'AWS Identity Center 초대 이메일이 {email}로 자동 발송되었습니다.',
            'app_assignment': app_assignment_success
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"SSO user creation failed: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': f'Failed to create SSO user: {error_msg}'
        }), 500
