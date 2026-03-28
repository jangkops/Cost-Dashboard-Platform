import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { UserGroupIcon, CheckCircleIcon, XCircleIcon } from "@heroicons/react/24/outline";

export default function GitHubTeams() {
  const [teams, setTeams] = useState([]);
  const [repos, setRepos] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState("");
  const [selectedRepo, setSelectedRepo] = useState("");
  const [permission, setPermission] = useState("pull");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadTeams();
    loadRepos();
  }, []);

  const loadTeams = async () => {
    try {
      const res = await fetch("/api/github/organizations/mogam-ai/teams");
      const data = await res.json();
      setTeams(data || []);
    } catch (err) {
      console.error("Failed to load teams:", err);
    }
  };

  const loadRepos = async () => {
    try {
      const res = await fetch("/api/github/repositories");
      const data = await res.json();
      setRepos(data || []);
    } catch (err) {
      console.error("Failed to load repos:", err);
    }
  };

  const handleAddRepo = async () => {
    if (!selectedTeam || !selectedRepo) return;
    setLoading(true);
    setResult(null);
    try {
      await fetch(`/api/github/teams/${selectedTeam}/repos/${selectedRepo}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ permission })
      });
      setResult({ success: true, message: "저장소 권한이 추가되었습니다." });
    } catch (err) {
      setResult({ success: false, message: "권한 추가 실패" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">팀 관리</h1>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">팀에 저장소 권한 부여</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">팀 선택</label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">팀을 선택하세요</option>
              {teams.map((team) => (
                <option key={team.id} value={team.slug}>{team.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">저장소 선택</label>
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">저장소를 선택하세요</option>
              {repos.map((repo) => (
                <option key={repo.id} value={repo.name}>{repo.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">권한</label>
            <select
              value={permission}
              onChange={(e) => setPermission(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="pull">Read (pull)</option>
              <option value="push">Write (push)</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button
            onClick={handleAddRepo}
            disabled={loading || !selectedTeam || !selectedRepo}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "추가 중..." : "권한 부여"}
          </button>
        </div>
      </div>

      {result && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded mb-6 flex items-center gap-2 ${result.success ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}
        >
          {result.success ? <CheckCircleIcon className="w-5 h-5" /> : <XCircleIcon className="w-5 h-5" />}
          {result.message}
        </motion.div>
      )}

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">팀 목록</h2>
        <div className="space-y-2">
          {teams.map((team) => (
            <div key={team.id} className="flex items-center gap-3 p-3 border rounded hover:bg-gray-50">
              <UserGroupIcon className="w-5 h-5 text-gray-500" />
              <div>
                <div className="font-medium">{team.name}</div>
                <div className="text-sm text-gray-500">{team.description || "설명 없음"}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
