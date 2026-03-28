from flask import Blueprint, jsonify, request
from services.github_service import GitHubService

github_bp = Blueprint('github', __name__)
github_service = GitHubService()

@github_bp.route('/user', methods=['GET'])
def get_user():
    try:
        user = github_service.get_authenticated_user()
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations', methods=['GET'])
def get_organizations():
    try:
        orgs = github_service.get_organizations()
        return jsonify(orgs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/members', methods=['GET'])
def get_org_members(org):
    try:
        members = github_service.get_org_members(org)
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/teams', methods=['GET'])
def get_org_teams(org):
    try:
        teams = github_service.get_org_teams(org)
        return jsonify(teams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/repositories', methods=['GET'])
def get_org_repos(org):
    try:
        repos = github_service.get_org_repos(org)
        return jsonify(repos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/teams/<team_slug>/members', methods=['GET'])
def get_team_members(org, team_slug):
    try:
        members = github_service.get_team_members(org, team_slug)
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/teams/<team_slug>/repositories', methods=['GET'])
def get_team_repos(org, team_slug):
    try:
        repos = github_service.get_team_repos(org, team_slug)
        return jsonify(repos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<owner>/<repo>/collaborators', methods=['GET'])
def get_repo_collaborators(owner, repo):
    try:
        collaborators = github_service.get_repo_collaborators(owner, repo)
        return jsonify(collaborators)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<owner>/<repo>/permissions', methods=['GET'])
def get_repo_permissions(owner, repo):
    try:
        permissions = github_service.get_repo_permissions(owner, repo)
        return jsonify(permissions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<owner>/<repo>/events', methods=['GET'])
def get_repo_events(owner, repo):
    try:
        days = request.args.get('days', 7, type=int)
        events = github_service.get_repo_events(owner, repo, days)
        return jsonify(events)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/audit-log', methods=['GET'])
def get_audit_log(org):
    try:
        days = request.args.get('days', 7, type=int)
        logs = github_service.get_audit_log(org, days)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/organizations/<org>/teams/<team_slug>/members/<username>', methods=['PUT'])
def add_team_member(org, team_slug, username):
    role = request.json.get('role', 'member')
    result = github_service.add_team_member(org, team_slug, username, role)
    return jsonify(result)

@github_bp.route('/organizations/<org>/teams/<team_slug>/members/<username>', methods=['DELETE'])
def remove_team_member(org, team_slug, username):
    success = github_service.remove_team_member(org, team_slug, username)
    return jsonify({'success': success})

@github_bp.route('/organizations/<org>/teams/<team_slug>/repositories/<owner>/<repo>', methods=['PUT'])
def add_repo_to_team(org, team_slug, owner, repo):
    permission = request.json.get('permission', 'pull')
    success = github_service.add_repo_to_team(org, team_slug, owner, repo, permission)
    return jsonify({'success': success})

@github_bp.route('/organizations/<org>/teams/<team_slug>/repositories/<owner>/<repo>', methods=['DELETE'])
def remove_repo_from_team(org, team_slug, owner, repo):
    success = github_service.remove_repo_from_team(org, team_slug, owner, repo)
    return jsonify({'success': success})

@github_bp.route('/logs', methods=['GET'])
def get_github_logs():
    """GitHub 로그 조회 (호환성)"""
    try:
        days = request.args.get('days', 7, type=int)
        logs = github_service.get_audit_log('mogam-ai', days)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
