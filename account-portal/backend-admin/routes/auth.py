from flask import Blueprint, request, jsonify
import boto3
from botocore.exceptions import ClientError
import jwt
import datetime
import json
import os
import hashlib

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mogam-portal-secret-key-2024")
SECRET_NAME = os.getenv("PORTAL_SECRET_NAME", "mogam-portal/admin-credentials")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)

def hash_password(password):
    """비밀번호를 SHA-256으로 해시"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_admin_credentials():
    """Secrets Manager에서 모든 관리자 자격증명 가져오기"""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        return secret.get('admins', [])
    except ClientError as e:
        print(f"Failed to get secret: {e}")
        return []

def find_admin_by_username(username):
    """사용자 이름으로 관리자 찾기"""
    admins = get_admin_credentials()
    for admin in admins:
        if admin.get('username') == username:
            return admin
    return None

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "사용자 이름과 비밀번호를 입력해주세요."}), 400

        admin = find_admin_by_username(username)
        
        if not admin:
            return jsonify({"error": "존재하지 않는 사용자입니다."}), 404

        # 비밀번호 검증 (해시 또는 평문 지원)
        stored_password = admin.get("password")
        if stored_password.startswith("sha256:"):
            # 해시된 비밀번호
            password_hash = hash_password(password)
            if f"sha256:{password_hash}" != stored_password:
                return jsonify({"error": "비밀번호가 올바르지 않습니다."}), 401
        else:
            # 평문 비밀번호 (하위 호환성)
            if password != stored_password:
                return jsonify({"error": "비밀번호가 올바르지 않습니다."}), 401

        # AWS 자격증명 검증
        try:
            session = boto3.Session(
                aws_access_key_id=admin.get("access_key"),
                aws_secret_access_key=admin.get("secret_key")
            )
            
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            
            token = jwt.encode({
                "username": username,
                "account_id": identity['Account'],
                "user_arn": identity['Arn'],
                "name": admin.get("name", username),
                "role": "admin",
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY, algorithm="HS256")

            return jsonify({
                "token": token,
                "accessToken": token,
                "refreshToken": token,
                "role": "admin",
                "username": username,
                "name": admin.get("name", username),
                "account_id": identity['Account']
            }), 200
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return jsonify({"error": f"AWS 자격증명 검증 실패: {error_code}"}), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": f"로그인 중 오류가 발생했습니다: {str(e)}"}), 500

@auth_bp.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json
        token = data.get("token")

        if not token:
            return jsonify({"error": "토큰이 필요합니다."}), 400

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        return jsonify({
            "valid": True, 
            "username": payload.get("username"), 
            "role": payload.get("role"),
            "account_id": payload.get("account_id")
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "토큰이 만료되었습니다."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "유효하지 않은 토큰입니다."}), 401
    except Exception as e:
        print(f"Verify error: {str(e)}")
        return jsonify({"error": "토큰 검증 실패"}), 401
