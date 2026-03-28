const API_BASE = "/api";

export async function getRegions() {
  const res = await fetch(`${API_BASE}/regions`);
  const data = await res.json();
  return data.regions || [];
}

export async function getInstances(region) {
  const res = await fetch(`${API_BASE}/instances`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ region }),
  });
  const data = await res.json();
  return data.instances || [];
}

export async function createAccount(payload) {
  const res = await fetch(`${API_BASE}/create-account`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok || !data.success) {
    throw new Error(data.message || "계정 생성 실패");
  }
  return data;
}

export async function updateRole(payload) {
  const res = await fetch(`${API_BASE}/update-role`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function deleteAccount(payload) {
  const res = await fetch(`${API_BASE}/delete-account`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function getLogs() {
  const res = await fetch(`${API_BASE}/logs`);
  const data = await res.json();
  return data.logs || [];
}

export async function getAccounts(region, instanceId) {
  const res = await fetch(`${API_BASE}/accounts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ region, instanceId }),
  });
  const data = await res.json();
  return data.accounts || [];
}

export async function getProjectGroups(region, instanceId) {
  const res = await fetch(`${API_BASE}/project-groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ region, instanceId }),
  });
  const data = await res.json();
  return data.groups || [];
}

export async function manageProjectMember(region, instanceId, groupName, username, action) {
  const res = await fetch(`${API_BASE}/project-groups/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ region, instanceId, groupName, username, action }),
  });
  return await res.json();
}

export async function getGitHubUser() {
  const res = await fetch(`${API_BASE}/github/user`);
  return await res.json();
}

export async function getGitHubOrganizations() {
  const res = await fetch(`${API_BASE}/github/organizations`);
  return await res.json();
}

export async function getGitHubOrgMembers(org) {
  const res = await fetch(`${API_BASE}/github/organizations/${org}/members`);
  return await res.json();
}

export async function getGitHubOrgTeams(org) {
  const res = await fetch(`${API_BASE}/github/organizations/${org}/teams`);
  return await res.json();
}

export async function getGitHubOrgRepos(org) {
  const res = await fetch(`${API_BASE}/github/organizations/${org}/repositories`);
  return await res.json();
}

export async function getGitHubUserRepos() {
  const res = await fetch(`${API_BASE}/github/user/repositories`);
  return await res.json();
}

export async function collectUserAccessLogs(region, instanceIds) {
  const res = await fetch(`${API_BASE}/user-access-logs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ region, instance_ids: instanceIds })
  });
  return await res.json();
}

export async function getUserAccessLogs() {
  const res = await fetch(`${API_BASE}/user-access-logs`);
  const data = await res.json();
  return data.logs || [];
}
