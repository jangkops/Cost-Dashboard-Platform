import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ChevronRightIcon, ClockIcon, ArrowPathIcon, FunnelIcon } from "@heroicons/react/24/outline";

export default function GitHubAuditLogs() {
  const [activeTab, setActiveTab] = useState("activity");
  const [events, setEvents] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  
  const [dateFilter, setDateFilter] = useState("");
  const [repoFilter, setRepoFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterData();
  }, [activeTab, events, auditLogs, dateFilter, repoFilter, typeFilter, userFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [reposRes, auditRes] = await Promise.all([
        fetch("/api/github/organizations/mogam-ai/repositories"),
        fetch("/api/audit-logs")
      ]);
      const repos = await reposRes.json();
      const audit = await auditRes.json();
      
      let allEvents = [];
      for (const repo of repos || []) {
        try {
          const eventsRes = await fetch(`/api/github/repositories/${repo.owner.login}/${repo.name}/events?days=30`);
          const repoEvents = await eventsRes.json();
          allEvents = [...allEvents, ...(repoEvents || []).map(e => ({...e, repo: repo.name}))];
        } catch (err) {
          console.error(`Failed to load events for ${repo.name}:`, err);
        }
      }
      
      setEvents(allEvents);
      setAuditLogs(audit.logs || []);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const filterData = () => {
    const data = activeTab === "activity" ? events : auditLogs;
    let filtered = [...data];

    if (dateFilter) {
      filtered = filtered.filter(item => {
        const itemDate = new Date(item.created_at || item.timestamp).toISOString().split('T')[0];
        return itemDate === dateFilter;
      });
    }

    if (repoFilter) {
      filtered = filtered.filter(item => 
        (item.repo || item.instance) === repoFilter
      );
    }

    if (typeFilter) {
      filtered = filtered.filter(item => 
        (item.type || item.action || "").includes(typeFilter)
      );
    }

    if (userFilter) {
      filtered = filtered.filter(item => 
        (item.actor || item.username || "").toLowerCase().includes(userFilter.toLowerCase())
      );
    }

    setFilteredData(filtered);
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setDateFilter("");
    setRepoFilter("");
    setTypeFilter("");
    setUserFilter("");
  };

  const formatSeoulTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('ko-KR', {
      year: '2-digit',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'Asia/Seoul',
      hour12: false
    });
  };

  const getStatusBadge = (status) => {
    if (status === "성공" || status === "완료") return "bg-green-100 text-green-800";
    if (status === "유지") return "bg-blue-100 text-blue-800";
    return "bg-red-100 text-red-800";
  };

  const getEventDescription = (event) => {
    const payload = event.payload || {};
    switch(event.type) {
      case 'PushEvent':
        const commits = payload.commits?.length || 0;
        return commits > 0 ? `${commits}개 Commit 푸시` : 'Commit 푸시';
      case 'PullRequestEvent':
        return `PR ${payload.action || ''}`;
      case 'IssuesEvent':
        return `이슈 ${payload.action || ''}`;
      case 'CreateEvent':
        return `${payload.ref_type || 'branch'} 생성`;
      case 'DeleteEvent':
        return `${payload.ref_type || 'branch'} 삭제`;
      case 'WatchEvent':
        return 'Star 추가';
      case 'ForkEvent':
        return 'Fork';
      default:
        return event.type?.replace('Event', '') || '-';
    }
  };

  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentData = filteredData.slice(startIndex, startIndex + itemsPerPage);

  const uniqueTypes = [...new Set((activeTab === "activity" ? events : auditLogs).map(item => item.type || item.action))];
  const uniqueRepos = [...new Set((activeTab === "activity" ? events : auditLogs).map(item => item.repo || item.instance).filter(Boolean))];

  const totalCount = activeTab === "activity" ? events.length : auditLogs.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-teal-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-green-600">모니터링</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>GitHub 로그</span>
      </motion.div>

      <div className="max-w-[1600px] mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-xl">
                <ClockIcon className="w-8 h-8 text-green-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">GitHub 로그</h1>
                <p className="text-gray-500 mt-1">GitHub 활동 및 프로젝트 권한 이력</p>
              </div>
            </div>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={loadData} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:bg-gray-400 transition-all shadow-md">
              <ArrowPathIcon className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
              새로고침
            </motion.button>
          </div>

          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveTab("activity")}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === "activity"
                  ? "bg-green-600 text-white shadow-md"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              활동 로그
            </button>
            <button
              onClick={() => setActiveTab("permission")}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === "permission"
                  ? "bg-green-600 text-white shadow-md"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              프로젝트 권한 로그
            </button>
          </div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mb-6 p-4 bg-green-50 rounded-xl border border-green-200">
            <div className="flex items-center gap-2 mb-3">
              <FunnelIcon className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-gray-800">필터</h3>
              {(dateFilter || repoFilter || typeFilter || userFilter) && (
                <button onClick={resetFilters} className="ml-auto text-xs text-green-600 hover:text-green-800 underline">
                  필터 초기화
                </button>
              )}
            </div>
            <div className="grid grid-cols-4 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">날짜</label>
                <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">저장소</label>
                <select value={repoFilter} onChange={(e) => setRepoFilter(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500">
                  <option value="">전체</option>
                  {uniqueRepos.map(repo => (
                    <option key={repo} value={repo}>{repo}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">유형</label>
                <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500">
                  <option value="">전체</option>
                  {uniqueTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">{activeTab === "activity" ? "사용자" : "프로젝트"}</label>
                <input type="text" value={userFilter} onChange={(e) => setUserFilter(e.target.value)} placeholder="검색..." className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500" />
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              총 {totalCount}개 중 {filteredData.length}개 표시
            </div>
          </motion.div>

          {loading ? (
            <div className="text-center py-16">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-200 border-t-green-600"></div>
              <p className="mt-4 text-gray-500">로딩 중...</p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-16">
              <ClockIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">조회된 로그가 없습니다.</p>
            </div>
          ) : (
            <>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="overflow-x-auto rounded-xl border-2 border-gray-200">
                <table className="w-full table-fixed">
                  <thead className="bg-gradient-to-r from-green-50 to-teal-50">
                    <tr>
                      <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-32">시간</th>
                      <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-56">저장소</th>
                      <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-24">유형</th>
                      <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-32">
                        {activeTab === "activity" ? "사용자" : "프로젝트"}
                      </th>
                      {activeTab === "permission" && (
                        <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-16">상태</th>
                      )}
                      <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-14">
                        {activeTab === "activity" ? "설명" : "상세"}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white">
                    {currentData.map((item, idx) => (
                      <motion.tr key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.02 }} className="hover:bg-green-50 transition-colors border-b border-gray-100">
                        <td className="px-2 py-3 text-xs text-gray-700 text-center truncate">
                          {formatSeoulTime(item.created_at || item.timestamp)}
                        </td>
                        <td className="px-2 py-3 text-xs text-gray-700 text-center truncate">
                          {item.repo || item.instance || '-'}
                        </td>
                        <td className="px-2 py-3 text-xs text-center truncate">
                          {activeTab === "activity" ? (
                            item.type?.replace('Event', '') || '-'
                          ) : (
                            item.action || '-'
                          )}
                        </td>
                        <td className="px-2 py-3 text-xs text-gray-900 text-center truncate">
                          {item.actor || item.username || '-'}
                        </td>
                        {activeTab === "permission" && (
                          <td className="px-2 py-3 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${getStatusBadge(item.status)}`}>
                              {item.status || '-'}
                            </span>
                          </td>
                        )}
                        <td className="px-2 py-3 text-center">
                          {activeTab === "activity" ? (
                            <span className="text-xs text-gray-600">{getEventDescription(item)}</span>
                          ) : (
                            <button onClick={() => setSelectedLog(item)} className="text-green-600 hover:text-green-800 font-medium text-xs underline">
                              보기
                            </button>
                          )}
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </motion.div>

              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-6">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    이전
                  </button>
                  <span className="text-sm text-gray-600">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    다음
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {selectedLog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedLog(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4">프로젝트 권한 상세</h3>
            <div className="space-y-3 text-sm">
              <div className="flex gap-2">
                <span className="font-semibold text-gray-700 w-24">시간:</span>
                <span className="text-gray-600">{formatSeoulTime(selectedLog.timestamp)}</span>
              </div>
              <div className="flex gap-2">
                <span className="font-semibold text-gray-700 w-24">프로젝트:</span>
                <span className="text-gray-600">{selectedLog.username || '-'}</span>
              </div>
              <div className="flex gap-2">
                <span className="font-semibold text-gray-700 w-24">작업:</span>
                <span className="text-gray-600">{selectedLog.action || '-'}</span>
              </div>
              <div className="flex gap-2">
                <span className="font-semibold text-gray-700 w-24">저장소:</span>
                <span className="text-gray-600">{selectedLog.instance || '-'}</span>
              </div>
              <div className="flex gap-2">
                <span className="font-semibold text-gray-700 w-24">상세:</span>
                <span className="text-gray-600">{(selectedLog.details || '-').replace(/팀/g, '프로젝트')}</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <span className="font-semibold text-gray-700">상태:</span>
                <span className={`ml-2 px-3 py-1 rounded-full text-sm font-semibold ${getStatusBadge(selectedLog.status)}`}>
                  {selectedLog.status || '-'}
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedLog(null)}
              className="mt-6 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              닫기
            </button>
          </motion.div>
        </div>
      )}
    </div>
  );
}
