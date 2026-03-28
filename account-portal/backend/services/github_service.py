import os
import requests
from typing import List, Dict, Optional

class GitHubService:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.default_org = 'mogam-ai'
    
    def get_authenticated_user(self) -> Dict:
        response = requests.get(f'{self.base_url}/user', headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_organizations(self) -> List[Dict]:
        # Return mogam-ai as default organization
        try:
            response = requests.get(f'{self.base_url}/orgs/{self.default_org}', headers=self.headers)
            response.raise_for_status()
            return [response.json()]
        except:
            return []
    
    def get_org_members(self, org: str) -> List[Dict]:
        response = requests.get(f'{self.base_url}/orgs/{org}/members', headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_org_teams(self, org: str) -> List[Dict]:
        response = requests.get(f'{self.base_url}/orgs/{org}/teams', headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_org_repos(self, org: str) -> List[Dict]:
        response = requests.get(f'{self.base_url}/orgs/{org}/repos', headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_team_members(self, org: str, team_slug: str) -> List[Dict]:
        response = requests.get(f'{self.base_url}/orgs/{org}/teams/{team_slug}/members', headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_repo_collaborators(self, owner: str, repo: str) -> List[Dict]:
        response = requests.get(f'{self.base_url}/repos/{owner}/{repo}/collaborators', headers=self.headers)
        response.raise_for_status()
        return response.json()
