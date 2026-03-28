import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class GitHubService:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.default_org = 'mogam-ai'
    
    # ===== 1. 레포지토리 관리 =====
    
    def create_secure_repo(self, name: str, description: str = "") -> Dict:
        """보안 설정이 강제된 레포지토리 생성"""
        # 1단계: Private 레포 생성
        repo_data = {
            "name": name,
            "description": description,
            "private": True,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "auto_init": True
        }
        response = requests.post(
            f'{self.base_url}/orgs/{self.default_org}/repos',
            headers=self.headers,
            json=repo_data
        )
        response.raise_for_status()
        repo = response.json()
        
        # 2단계: Actions 비활성화
        requests.put(
            f'{self.base_url}/repos/{self.default_org}/{name}/actions/permissions',
            headers=self.headers,
            json={"enabled": False}
        )
        
        # 3단계: Branch Protection (main)
        protection_data = {
            "required_status_checks": None,
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "required_approving_review_count": 1
            },
            "restrictions": None
        }
        requests.put(
            f'{self.base_url}/repos/{self.default_org}/{name}/branches/main/protection',
            headers=self.headers,
            json=protection_data
        )
        
        return repo
    
    def convert_to_private(self, repo_name: str) -> Dict:
        """레포지토리를 Private으로 전환"""
        response = requests.patch(
            f'{self.base_url}/repos/{self.default_org}/{repo_name}',
            headers=self.headers,
            json={"private": True}
        )
        response.raise_for_status()
        return response.json()
    
    def archive_repo(self, repo_name: str) -> Dict:
        """레포지토리 아카이브 (Read-only)"""
        response = requests.patch(
            f'{self.base_url}/repos/{self.default_org}/{repo_name}',
            headers=self.headers,
            json={"archived": True}
        )
        response.raise_for_status()
        return response.json()
    
    def get_org_repos(self, org: str) -> List[Dict]:
        """조직 레포지토리 목록"""
        response = requests.get(
            f'{self.base_url}/orgs/{org}/repos?per_page=100',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== 2. 팀 및 권한 관리 =====
    
    def get_org_teams(self, org: str) -> List[Dict]:
        """조직 팀 목록"""
        response = requests.get(f'{self.base_url}/orgs/{org}/teams', headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_team_repos(self, org: str, team_slug: str) -> List[Dict]:
        """팀이 접근 가능한 레포지토리 목록"""
        response = requests.get(
            f'{self.base_url}/orgs/{org}/teams/{team_slug}/repos',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def set_team_repo_permission(self, org: str, team_slug: str, repo_name: str, permission: str) -> bool:
        """팀의 레포지토리 권한 설정 (pull, push, admin)"""
        response = requests.put(
            f'{self.base_url}/orgs/{org}/teams/{team_slug}/repos/{org}/{repo_name}',
            headers=self.headers,
            json={"permission": permission}
        )
        return response.status_code == 204
    
    def remove_team_repo_access(self, org: str, team_slug: str, repo_name: str) -> bool:
        """팀의 레포지토리 접근 제거"""
        response = requests.delete(
            f'{self.base_url}/orgs/{org}/teams/{team_slug}/repos/{org}/{repo_name}',
            headers=self.headers
        )
        return response.status_code == 204
    
    def get_team_members(self, org: str, team_slug: str) -> List[Dict]:
        """팀 멤버 목록"""
        response = requests.get(
            f'{self.base_url}/orgs/{org}/teams/{team_slug}/members',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== 3. 보안 및 정책 =====
    
    def disable_actions_org_wide(self, org: str) -> bool:
        """조직 전체 Actions 비활성화"""
        response = requests.put(
            f'{self.base_url}/orgs/{org}/actions/permissions',
            headers=self.headers,
            json={"enabled_repositories": "none"}
        )
        return response.status_code == 204
    
    def disable_repo_features(self, repo_name: str) -> Dict:
        """레포지토리의 외부 기능 비활성화"""
        updates = {
            "has_projects": False,
            "has_wiki": False
        }
        response = requests.patch(
            f'{self.base_url}/repos/{self.default_org}/{repo_name}',
            headers=self.headers,
            json=updates
        )
        response.raise_for_status()
        
        # Actions 비활성화
        requests.put(
            f'{self.base_url}/repos/{self.default_org}/{repo_name}/actions/permissions',
            headers=self.headers,
            json={"enabled": False}
        )
        
        return response.json()
    
    def get_org_ssh_keys(self, org: str) -> List[Dict]:
        """조직 멤버의 SSH 키 조회"""
        members = self.get_org_members(org)
        keys_data = []
        for member in members:
            try:
                response = requests.get(
                    f'{self.base_url}/users/{member["login"]}/keys',
                    headers=self.headers
                )
                if response.status_code == 200:
                    keys = response.json()
                    for key in keys:
                        keys_data.append({
                            "user": member["login"],
                            "key_id": key["id"],
                            "title": key.get("title", ""),
                            "created_at": key.get("created_at", "")
                        })
            except:
                continue
        return keys_data
    
    # ===== 4. 감사 및 로그 =====
    
    def get_repo_admins(self, org: str) -> List[Dict]:
        """Admin 권한을 가진 사용자 조회 (모든 저장소 표시)"""
        repos = self.get_org_repos(org)
        result = []
        
        for repo in repos:
            repo_data = {
                "repo": repo["name"],
                "admins": [],
                "count": 0
            }
            try:
                response = requests.get(
                    f'{self.base_url}/repos/{org}/{repo["name"]}/collaborators',
                    headers=self.headers,
                    params={"affiliation": "direct", "permission": "admin"}
                )
                if response.status_code == 200:
                    admins = response.json()
                    repo_data["admins"] = [admin["login"] for admin in admins]
                    repo_data["count"] = len(admins)
            except:
                pass
            
            result.append(repo_data)
        
        return result
    
    def get_audit_log(self, org: str, days: int = 1) -> List[Dict]:
        """조직 감사 로그 조회"""
        try:
            response = requests.get(
                f'{self.base_url}/orgs/{org}/audit-log',
                headers=self.headers,
                params={"per_page": 100}
            )
            if response.status_code == 200:
                logs = response.json()
                cutoff = datetime.now() - timedelta(days=days)
                
                filtered = []
                for log in logs:
                    log_time = datetime.fromisoformat(log.get("@timestamp", "").replace("Z", "+00:00"))
                    if log_time >= cutoff:
                        filtered.append({
                            "timestamp": log.get("@timestamp"),
                            "action": log.get("action"),
                            "actor": log.get("actor"),
                            "repo": log.get("repo"),
                            "user": log.get("user")
                        })
                
                return filtered
            return []
        except:
            return []
    
    def get_org_members(self, org: str) -> List[Dict]:
        """조직 멤버 목록"""
        response = requests.get(f'{self.base_url}/orgs/{org}/members', headers=self.headers)
        response.raise_for_status()
        return response.json()

    def add_repo_collaborator(self, org: str, repo: str, username: str, permission: str = 'admin') -> bool:
        """저장소에 협력자 추가"""
        response = requests.put(
            f'{self.base_url}/repos/{org}/{repo}/collaborators/{username}',
            headers=self.headers,
            json={'permission': permission}
        )
        return response.status_code in [201, 204]
    
    def remove_repo_collaborator(self, org: str, repo: str, username: str) -> bool:
        """저장소에서 협력자 제거"""
        response = requests.delete(
            f'{self.base_url}/repos/{org}/{repo}/collaborators/{username}',
            headers=self.headers
        )
        return response.status_code == 204

    def get_repo_events(self, owner: str, repo: str, days: int = 30) -> List[Dict]:
        """Get repository events (push, PR, etc)"""
        try:
            response = requests.get(
                f'{self.base_url}/repos/{owner}/{repo}/events',
                headers=self.headers,
                params={'per_page': 100}
            )
            response.raise_for_status()
            events = response.json()
            
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for event in events:
                event_time = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                if event_time >= cutoff:
                    filtered.append({
                        'type': event['type'],
                        'actor': event['actor']['login'],
                        'created_at': event['created_at'],
                        'payload': event.get('payload', {})
                    })
            return filtered
        except Exception as e:
            print(f'Error getting repo events: {e}')
            return []
