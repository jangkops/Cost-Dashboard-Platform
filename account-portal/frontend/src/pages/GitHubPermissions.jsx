import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRightIcon, ShieldCheckIcon, MagnifyingGlassIcon, CheckCircleIcon, XCircleIcon, InformationCircleIcon, MinusCircleIcon } from "@heroicons/react/24/outline";

const PERMISSION_DETAILS = {
  read: {
    label: "Read (읽기)",
    description: "저장소 읽기 전용",
    details: "• 코드 읽기 및 클론\n• 이슈 및 PR 조회\n• 다운로드 가능"
  },
  write: {
    label: "Write (쓰기)",
    description: "읽기 + 푸시 권한",
    details: "• Read 권한 포함\n• 코드 푸시 및 커밋\n• 이슈 및 PR 생성/수정\n• 브랜치 관리"
  },
  maintain: {
    label: "Maintain (유지)",
    description: "저장소 유지 관리",
    details: "• Write 권한 포함\n• 저장소 설정 관리\n• Webhook 관리\n• 브랜치 보호 규칙 관리"
  },
  admin: {
    label: "Admin (관리)",
    description: "전체 관리 권한",
    details: "• Maintain 권한 포함\n• 팀 및 협업자 관리\n• 저장소 삭제 가능\n• 모든 설정 변경 가능"
  }
};

export default function GitHubPermissions() {
  const [teams, setTeams] = useState([]);
  const [repos, setRepos] = useState([]);
  const [selectedTeams, setSelectedTeams] = useState([]);
  const [selectedRepos, setSelectedRepos] = useState([]);
  const [permission, setPermission] = useState("write");
  const [teamSearch, setTeamSearch] = useState("");
  const [repoSearch, setRepoSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showPermissionDetails, setShowPermissionDetails] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [teamsRes, reposRes] = await Promise.all([
        fetch("/api/github/organizations/mogam-ai/teams"),
        fetch("/api/github/organizations/mogam-ai/repositories")
      ]);
      const teamsData = await teamsRes.json();
      const reposData = await reposRes.json();
      setTeams(teamsData || []);
      setRepos(reposData || []);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredTeams = teams.filter(t =>
    t.name.toLowerCase().includes(teamSearch.toLowerCase())
  );

  const filteredRepos = repos.filter(r =>
    r.name.toLowerCase().includes(repoSearch.toLowerCase())
  );

  const toggleTeam = (teamId) => {
    setSelectedTeams(prev =>
      prev.includes(teamId) ? prev.filter(id => id !== teamId) : [...prev, teamId]
    );
  };

  const toggleRepo = (repoId) => {
    setSelectedRepos(prev =>
      prev.includes(repoId) ? prev.filter(id => id !== repoId) : [...prev, repoId]
    );
  };

  const selectAllTeams = () => {
    setSelectedTeams(filteredTeams.map(t => t.id));
  };

  const deselectAllTeams = () => {
    setSelectedTeams([]);
  };

  const selectAllRepos = () => {
    setSelectedRepos(filteredRepos.map(r => r.id));
  };

  const deselectAllRepos = () => {
    setSelectedRepos([]);
  };

  const handleSubmit = async () => {
    if (selectedTeams.length === 0 || selectedRepos.length === 0) {
      setResult({
        type: "error",
        message: "프로젝트 팀과 저장소를 선택해주세요"
      });
      setTimeout(() => setResult(null), 3000);
      return;
    }

    setSubmitting(true);
    setResult(null);

    try {
      const selectedTeamsList = teams.filter(t => selectedTeams.includes(t.id));
      const selectedReposList = repos.filter(r => selectedRepos.includes(r.id));
      
      let totalSuccess = 0;
      let totalFail = 0;
      let totalMaintained = 0;

      // GitHub API는 pull/push/maintain/admin 사용
      const apiPermission = permission === "read" ? "pull" : permission === "write" ? "push" : permission;

      for (const team of selectedTeamsList) {
        const results = await Promise.all(
          selectedReposList.map(async repo => {
            try {
              const res = await fetch(
                `/api/github/organizations/mogam-ai/teams/${team.slug}/repositories/${repo.owner.login}/${repo.name}`,
                {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ permission: apiPermission })
                }
              );
              const data = await res.json();
              if (data.status === "maintained") {
                return { status: "maintained" };
              }
              return { status: res.ok ? "success" : "fail" };
            } catch (err) {
              return { status: "fail" };
            }
          })
        );
        
        totalSuccess += results.filter(r => r.status === "success").length;
        totalFail += results.filter(r => r.status === "fail").length;
        totalMaintained += results.filter(r => r.status === "maintained").length;
      }

      if (totalMaintained > 0 && totalSuccess === 0 && totalFail === 0) {
        setResult({
          type: "maintained",
          message: `${totalMaintained}개 저장소 권한이 이미 설정되어 있습니다 (유지)`
        });
      } else if (totalSuccess > 0) {
        setResult({
          type: "success",
          message: `${selectedTeams.length}개 팀에 ${totalSuccess}개 권한 부여 성공${totalMaintained > 0 ? `, ${totalMaintained}개 유지` : ""}${totalFail > 0 ? `, ${totalFail}개 실패` : ""}`
        });
      } else {
        setResult({
          type: "error",
          message: `권한 부여 실패 (${totalFail}개)`
        });
      }

      if (totalSuccess > 0 || totalMaintained > 0) {
        setSelectedTeams([]);
        setSelectedRepos([]);
      }
    } catch (err) {
      setResult({
        type: "error",
        message: "권한 부여 실패: " + err.message
      });
    } finally {
      setSubmitting(false);
      setTimeout(() => setResult(null), 5000);
    }
  };

  const getResultStyle = (type) => {
    switch(type) {
      case "success":
        return { bg: "#f0fdf4", border: "#86efac", color: "#166534" };
      case "maintained":
        return { bg: "#fef3c7", border: "#fbbf24", color: "#92400e" };
      case "error":
        return { bg: "#fef2f2", border: "#fca5a5", color: "#991b1b" };
      default:
        return { bg: "#f3f4f6", border: "#d1d5db", color: "#374151" };
    }
  };

  const getResultIcon = (type) => {
    switch(type) {
      case "success":
        return <CheckCircleIcon className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />;
      case "maintained":
        return <MinusCircleIcon className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />;
      case "error":
        return <XCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />;
      default:
        return null;
    }
  };

  const getResultTitle = (type) => {
    switch(type) {
      case "success":
        return "권한 부여 완료";
      case "maintained":
        return "권한 유지";
      case "error":
        return "권한 부여 실패";
      default:
        return "";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-8">
      <motion.div initial={{opacity:0,y:-20}} animate={{opacity:1,y:0}} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-indigo-600">GitHub</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>저장소 프로젝트 권한</span>
      </motion.div>

      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-indigo-100 rounded-xl">
              <ShieldCheckIcon className="w-8 h-8 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">저장소 프로젝트 권한</h1>
              <p className="text-gray-500 mt-1">프로젝트 팀에 저장소 접근 권한 부여</p>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                {/* Team Selection */}
                <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.1}}>
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-semibold text-gray-700">프로젝트 팀 선택</label>
                    <div className="flex items-center gap-2">
                      <button onClick={selectAllTeams} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-xs font-medium">
                        전체 선택
                      </button>
                      <button onClick={deselectAllTeams} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-xs font-medium">
                        해제
                      </button>
                      <span className="text-xs text-gray-600">{selectedTeams.length}개</span>
                    </div>
                  </div>
                  <div className="relative mb-2">
                    <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={teamSearch}
                      onChange={(e) => setTeamSearch(e.target.value)}
                      placeholder="팀 검색..."
                      className="w-full pl-9 pr-3 py-2 text-sm border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                  <div className="border-2 border-gray-200 rounded-lg max-h-80 overflow-y-auto">
                    {filteredTeams.map(team => (
                      <label
                        key={team.id}
                        className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50 border-b last:border-b-0 ${
                          selectedTeams.includes(team.id) ? "bg-indigo-50" : ""
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedTeams.includes(team.id)}
                          onChange={() => toggleTeam(team.id)}
                          className="w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">{team.name}</div>
                          <div className="text-xs text-gray-600 truncate">{team.description || "No description"}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </motion.div>

                {/* Repository Selection */}
                <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.2}}>
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-semibold text-gray-700">대상 저장소 선택</label>
                    <div className="flex items-center gap-2">
                      <button onClick={selectAllRepos} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-xs font-medium">
                        전체 선택
                      </button>
                      <button onClick={deselectAllRepos} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-xs font-medium">
                        해제
                      </button>
                      <span className="text-xs text-gray-600">{selectedRepos.length}개</span>
                    </div>
                  </div>
                  <div className="relative mb-2">
                    <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={repoSearch}
                      onChange={(e) => setRepoSearch(e.target.value)}
                      placeholder="저장소 검색..."
                      className="w-full pl-9 pr-3 py-2 text-sm border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                  <div className="border-2 border-gray-200 rounded-lg max-h-80 overflow-y-auto">
                    {filteredRepos.map(repo => (
                      <label
                        key={repo.id}
                        className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50 border-b last:border-b-0 ${
                          selectedRepos.includes(repo.id) ? "bg-indigo-50" : ""
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedRepos.includes(repo.id)}
                          onChange={() => toggleRepo(repo.id)}
                          className="w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">{repo.name}</div>
                          <div className="text-xs text-gray-600 truncate">{repo.description || "No description"}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </motion.div>
              </div>

              {/* Permission Level */}
              <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.3}}>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-semibold text-gray-700">권한 레벨</label>
                  <button
                    onClick={() => setShowPermissionDetails(!showPermissionDetails)}
                    className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
                  >
                    <InformationCircleIcon className="w-4 h-4" />
                    {showPermissionDetails ? "권한 상세 닫기" : "권한 상세 보기"}
                  </button>
                </div>
                <select
                  value={permission}
                  onChange={(e) => setPermission(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none text-gray-900 font-medium"
                >
                  <option value="read">Read (읽기) - 저장소 읽기 전용</option>
                  <option value="write">Write (쓰기) - 읽기 + 푸시 권한</option>
                  <option value="maintain">Maintain (유지) - 저장소 유지 관리</option>
                  <option value="admin">Admin (관리) - 전체 관리 권한</option>
                </select>

                <AnimatePresence>
                  {showPermissionDetails && (
                    <motion.div
                      initial={{opacity:0,height:0}}
                      animate={{opacity:1,height:"auto"}}
                      exit={{opacity:0,height:0}}
                      className="mt-4 p-4 bg-indigo-50 rounded-lg border-2 border-indigo-200"
                    >
                      <h4 className="font-semibold text-indigo-900 mb-3">권한 상세 정보</h4>
                      <div className="space-y-3">
                        {Object.entries(PERMISSION_DETAILS).map(([key, detail]) => (
                          <div key={key} className={`p-3 rounded-lg ${permission === key ? "bg-indigo-100 border-2 border-indigo-400" : "bg-white"}`}>
                            <div className="font-semibold text-gray-900">{detail.label}</div>
                            <div className="text-sm text-gray-600 mt-1">{detail.description}</div>
                            <div className="text-xs text-gray-500 mt-2 whitespace-pre-line">{detail.details}</div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

              {/* Submit Button */}
              <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.4}}>
                <button
                  onClick={handleSubmit}
                  disabled={selectedTeams.length === 0 || selectedRepos.length === 0 || submitting}
                  className="w-full px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 transition-all shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
                >
                  {submitting ? "처리 중..." : `권한 부여 (${selectedTeams.length}개 팀 × ${selectedRepos.length}개 저장소)`}
                </button>
              </motion.div>
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{opacity:0}}
            animate={{opacity:1}}
            exit={{opacity:0}}
            className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
          >
            <motion.div
              initial={{scale:0.9,opacity:0}}
              animate={{scale:1,opacity:1}}
              exit={{scale:0.9,opacity:0}}
              className="pointer-events-auto max-w-lg w-full mx-4"
            >
              <div
                className="p-6 rounded-xl border-2 shadow-2xl"
                style={{
                  backgroundColor: getResultStyle(result.type).bg,
                  borderColor: getResultStyle(result.type).border
                }}
              >
                <div className="flex items-start gap-3">
                  {getResultIcon(result.type)}
                  <div className="flex-1">
                    <h3
                      className="font-bold text-lg mb-2"
                      style={{color: getResultStyle(result.type).color}}
                    >
                      {getResultTitle(result.type)}
                    </h3>
                    <p className="text-sm" style={{color: getResultStyle(result.type).color}}>
                      {result.message}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
