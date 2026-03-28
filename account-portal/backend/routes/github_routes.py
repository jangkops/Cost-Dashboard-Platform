from flask import Blueprint, jsonify, request
from services.github_service import GitHubService

github_bp = Blueprint('github', __name__)
github_service = GitHubService()

# ===== 1. 레포지토리 관리 (/github/repositories) =====

@github_bp.route('/repositories', methods=['GET'])
def list_repositories():
    """레포지토리 목록 조회"""
    try:
        repos = github_service.get_org_repos('mogam-ai')
        return jsonify(repos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories', methods=['POST'])
def create_repository():
    """보안 설정이 강제된 레포지토리 생성"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Repository name is required'}), 400
        
        repo = github_service.create_secure_repo(name, description)
        return jsonify({
            'success': True,
            'repo': repo,
            'message': f'Repository {name} created with security settings'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<repo_name>/private', methods=['PUT'])
def convert_to_private(repo_name):
    """레포지토리를 Private으로 전환"""
    try:
        repo = github_service.convert_to_private(repo_name)
        return jsonify({
            'success': True,
            'repo': repo,
            'message': f'Repository {repo_name} converted to private'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<repo_name>/archive', methods=['PUT'])
def archive_repository(repo_name):
    """레포지토리 아카이브 (Read-only)"""
    try:
        repo = github_service.archive_repo(repo_name)
        return jsonify({
            'success': True,
            'repo': repo,
            'message': f'Repository {repo_name} archived'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 2. 팀 및 권한 관리 (/github/teams) =====

@github_bp.route('/teams', methods=['GET'])
def list_teams():
    """팀 목록 조회"""
    try:
        teams = github_service.get_org_teams('mogam-ai')
        return jsonify(teams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/teams/<team_slug>/repos', methods=['GET'])
def get_team_repositories(team_slug):
    """팀이 접근 가능한 레포지토리 목록"""
    try:
        repos = github_service.get_team_repos('mogam-ai', team_slug)
        return jsonify(repos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route("/organizations/<org>/teams/<team_slug>/repositories/<owner>/<repo_name>", methods=["PUT"])
def set_team_repo_permission_full(org, team_slug, owner, repo_name):
    """팀의 레포지토리 권한 설정 (full path)"""
    from routes.audit_logs import write_audit_log
    from datetime import datetime
    import pytz
    
    try:
        data = request.json
        permission = data.get("permission", "pull")
        if permission not in ["pull", "push", "admin"]:
            return jsonify({"error": "Invalid permission"}), 400
        
        # 현재 권한 확인
        current_repos = github_service.get_team_repos(org, team_slug)
        current_repo = next((r for r in current_repos if r['name'] == repo_name), None)
        
        seoul_tz = pytz.timezone('Asia/Seoul')
        
        if current_repo:
            current_permission = current_repo.get('permissions', {})
            if current_permission.get('admin'):
                existing_perm = 'admin'
            elif current_permission.get('push'):
                existing_perm = 'push'
            elif current_permission.get('pull'):
                existing_perm = 'pull'
            else:
                existing_perm = None
            
            if existing_perm == permission:
                log_entry = {
                    "timestamp": datetime.now(seoul_tz).isoformat(),
                    "action": "GitHub 권한 관리",
                    "username": team_slug,
                    "region": org,
                    "instance": repo_name,
                    "instance_name": f"{permission} 권한",
                    "status": "유지",
                    "details": f"팀 {team_slug}의 {repo_name} 저장소 {permission} 권한이 이미 설정되어 있습니다"
                }
                write_audit_log(log_entry)
                return jsonify({"success": True, "message": f"권한이 이미 {permission}으로 설정되어 있습니다 (유지)", "status": "maintained"})
        
        # 권한 설정
        success = github_service.set_team_repo_permission(org, team_slug, repo_name, permission)
        
        if success:
            log_entry = {
                "timestamp": datetime.now(seoul_tz).isoformat(),
                "action": "GitHub 권한 관리",
                "username": team_slug,
                "region": org,
                "instance": repo_name,
                "instance_name": f"{permission} 권한",
                "status": "완료",
                "details": f"팀 {team_slug}에 {repo_name} 저장소 {permission} 권한 부여 완료"
            }
            write_audit_log(log_entry)
            return jsonify({"success": True, "message": f"Team {team_slug} granted {permission} access to {repo_name}"})
        else:
            log_entry = {
                "timestamp": datetime.now(seoul_tz).isoformat(),
                "action": "GitHub 권한 관리",
                "username": team_slug,
                "region": org,
                "instance": repo_name,
                "instance_name": f"{permission} 권한",
                "status": "실패",
                "reason": "GitHub API 호출 실패",
                "details": f"팀 {team_slug}에 {repo_name} 저장소 권한 부여 실패"
            }
            write_audit_log(log_entry)
            return jsonify({"error": "Failed to set permission"}), 500
    except Exception as e:
        seoul_tz = pytz.timezone('Asia/Seoul')
        log_entry = {
            "timestamp": datetime.now(seoul_tz).isoformat(),
            "action": "GitHub 권한 관리",
            "username": team_slug if 'team_slug' in locals() else "Unknown",
            "region": org if 'org' in locals() else "Unknown",
            "instance": repo_name if 'repo_name' in locals() else "Unknown",
            "status": "실패",
            "reason": str(e),
            "details": f"오류 발생: {str(e)}"
        }
        write_audit_log(log_entry)
        return jsonify({"error": str(e)}), 500



@github_bp.route('/teams/<team_slug>/repos/<repo_name>', methods=['PUT'])
def set_team_permission(team_slug, repo_name):
    """팀의 레포지토리 권한 설정"""
    try:
        data = request.json
        permission = data.get('permission', 'pull')  # pull, push, admin
        
        if permission not in ['pull', 'push', 'admin']:
            return jsonify({'error': 'Invalid permission'}), 400
        
        success = github_service.set_team_repo_permission('mogam-ai', team_slug, repo_name, permission)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Team {team_slug} granted {permission} access to {repo_name}'
            })
        else:
            return jsonify({'error': 'Failed to set permission'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/teams/<team_slug>/repos/<repo_name>', methods=['DELETE'])
def remove_team_access(team_slug, repo_name):
    """팀의 레포지토리 접근 제거"""
    try:
        success = github_service.remove_team_repo_access('mogam-ai', team_slug, repo_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Team {team_slug} access removed from {repo_name}'
            })
        else:
            return jsonify({'error': 'Failed to remove access'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/teams/<team_slug>/members', methods=['GET'])
def get_team_members(team_slug):
    """팀 멤버 목록"""
    try:
        members = github_service.get_team_members('mogam-ai', team_slug)
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 3. 보안 및 정책 (/github/policies) =====

@github_bp.route('/policies/actions/disable', methods=['POST'])
def disable_actions():
    """조직 전체 Actions 비활성화"""
    try:
        success = github_service.disable_actions_org_wide('mogam-ai')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'GitHub Actions disabled organization-wide'
            })
        else:
            return jsonify({'error': 'Failed to disable actions'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/policies/repos/<repo_name>/features/disable', methods=['POST'])
def disable_repo_features(repo_name):
    """레포지토리 외부 기능 비활성화"""
    try:
        repo = github_service.disable_repo_features(repo_name)
        return jsonify({
            'success': True,
            'repo': repo,
            'message': f'External features disabled for {repo_name}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/policies/ssh-keys', methods=['GET'])
def list_ssh_keys():
    """조직 멤버의 SSH 키 조회"""
    try:
        keys = github_service.get_org_ssh_keys('mogam-ai')
        return jsonify(keys)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 4. 감사 및 로그 (/github/audit) =====

@github_bp.route('/audit/admins', methods=['GET'])
def get_repository_admins():
    """Admin 권한을 가진 사용자 조회"""
    try:
        admins = github_service.get_repo_admins('mogam-ai')
        return jsonify(admins)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/audit/logs', methods=['GET'])
def get_audit_logs():
    """감사 로그 조회 (최근 24시간)"""
    try:
        days = request.args.get('days', 1, type=int)
        logs = github_service.get_audit_log('mogam-ai', days)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 기존 호환성 유지 =====

@github_bp.route('/organizations/<org>/members', methods=['GET'])
def get_org_members(org):
    """조직 멤버 목록 (기존 호환)"""
    try:
        members = github_service.get_org_members(org)
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/repositories', methods=['GET'])
def get_org_repos(org):
    """조직 레포지토리 목록 (기존 호환)"""
    try:
        repos = github_service.get_org_repos(org)
        return jsonify(repos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/teams', methods=['GET'])
def get_org_teams(org):
    """조직 팀 목록 (기존 호환)"""
    try:
        teams = github_service.get_org_teams(org)
        return jsonify(teams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 5. 권한 일괄 부여 (/github/permissions) =====

@github_bp.route('/permissions', methods=['POST'])
def grant_permissions():
    """팀에 여러 저장소 권한 일괄 부여"""
    try:
        data = request.json
        team_slug = data.get('teamSlug')
        repositories = data.get('repositories', [])
        permission = data.get('permission', 'push')
        
        if not team_slug or not repositories:
            return jsonify({'error': 'teamSlug and repositories are required'}), 400
        
        if permission not in ['pull', 'push', 'admin']:
            return jsonify({'error': 'Invalid permission'}), 400
        
        results = []
        for repo_name in repositories:
            try:
                success = github_service.set_team_repo_permission('mogam-ai', team_slug, repo_name, permission)
                results.append({'repo': repo_name, 'success': success})
            except Exception as e:
                results.append({'repo': repo_name, 'success': False, 'error': str(e)})
        
        all_success = all(r['success'] for r in results)
        
        return jsonify({
            'success': all_success,
            'results': results,
            'message': f'Granted {permission} permission to {len([r for r in results if r["success"]])} repositories'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 저장소 관리자 관리 =====

@github_bp.route('/repositories/<repo>/collaborators/<username>', methods=['PUT'])
def add_collaborator(repo, username):
    """저장소에 관리자 추가"""
    try:
        github_service.add_repo_collaborator('mogam-ai', repo, username, 'admin')
        return jsonify({'message': f'{username}을(를) {repo}의 관리자로 추가했습니다.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<repo>/collaborators/<username>', methods=['DELETE'])
def remove_collaborator(repo, username):
    """저장소에서 관리자 제거"""
    try:
        github_service.remove_repo_collaborator('mogam-ai', repo, username)
        return jsonify({'message': f'{username}을(를) {repo}에서 제거했습니다.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<owner>/<repo>/events', methods=['GET'])
def get_repo_events(owner, repo):
    try:
        days = request.args.get('days', 30, type=int)
        events = github_service.get_repo_events(owner, repo, days)
        return jsonify(events)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
