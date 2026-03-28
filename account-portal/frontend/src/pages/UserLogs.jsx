import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ChevronRightIcon, ClockIcon, ArrowPathIcon, FunnelIcon, XMarkIcon } from "@heroicons/react/24/outline";

export default function UserLogs() {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  
  const [dateFilter, setDateFilter] = useState("");
  const [instanceFilter, setInstanceFilter] = useState("");
  const [regionFilter, setRegionFilter] = useState("");
  const [usernameFilter, setUsernameFilter] = useState("");
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/user-access-logs");
      const data = await res.json();
      const logsWithKST = (data.logs || []).map(log => ({
        ...log,
        kst: new Date(log.timestamp + "+00:00").toLocaleString("ko-KR", {
          timeZone: "Asia/Seoul",
          year: '2-digit',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        })
      }));
      setLogs(logsWithKST);
      setFilteredLogs(logsWithKST);
    } catch (error) {
      console.error("Failed to load logs:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  useEffect(() => {
    let filtered = [...logs];

    if (dateFilter) {
      filtered = filtered.filter(log => {
        const logDate = new Date(log.timestamp).toISOString().split('T')[0];
        return logDate === dateFilter;
      });
    }

    if (instanceFilter) {
      filtered = filtered.filter(log => log.instance_name === instanceFilter);
    }

    if (regionFilter) {
      filtered = filtered.filter(log => log.region === regionFilter);
    }

    if (usernameFilter) {
      filtered = filtered.filter(log => log.username === usernameFilter);
    }

    setFilteredLogs(filtered);
    setCurrentPage(1);
  }, [dateFilter, instanceFilter, regionFilter, usernameFilter, logs]);

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentLogs = filteredLogs.slice(startIndex, endIndex);

  const uniqueRegions = [...new Set(logs.map(log => log.region).filter(Boolean))];
  const uniqueInstances = [...new Set(logs.map(log => log.instance_name).filter(Boolean))];
  const uniqueUsernames = [...new Set(logs.map(log => log.username).filter(Boolean))];

  const resetFilters = () => {
    setDateFilter("");
    setInstanceFilter("");
    setRegionFilter("");
    setUsernameFilter("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-blue-600">모니터링</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>사용자 접속 로그</span>
      </motion.div>

      <div className="max-w-[1600px] mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <ClockIcon className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">사용자 접속 로그</h1>
                <p className="text-gray-500 mt-1">EC2 인스턴스 사용자 접속 기록</p>
              </div>
            </div>
            <button onClick={loadLogs} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
              <ArrowPathIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              새로고침
            </button>
          </div>

          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border-2 border-blue-200">
            <div className="flex items-center gap-2 mb-4">
              <FunnelIcon className="w-5 h-5 text-gray-600" />
              <span className="font-semibold text-gray-700">필터</span>
              {(dateFilter || instanceFilter || regionFilter || usernameFilter) && (
                <button onClick={resetFilters} className="ml-auto text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
                  <XMarkIcon className="w-4 h-4" />
                  초기화
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">날짜</label>
                <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">인스턴스</label>
                <select value={instanceFilter} onChange={(e) => setInstanceFilter(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">전체</option>
                  {uniqueInstances.map(i => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">리전</label>
                <select value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">전체</option>
                  {uniqueRegions.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">계정명</label>
                <select value={usernameFilter} onChange={(e) => setUsernameFilter(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">전체</option>
                  {uniqueUsernames.map(u => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-16">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
              <p className="mt-4 text-gray-500">로딩 중...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-16">
              <ClockIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">조회된 로그가 없습니다.</p>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="overflow-x-auto rounded-xl border-2 border-gray-200">
              <table className="w-full">
                <thead className="bg-gradient-to-r from-blue-50 to-cyan-50">
                  <tr>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">시간</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">인스턴스</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">리전</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">계정명</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">IP 주소</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">상세</th>
                  </tr>
                </thead>
                <tbody className="bg-white">
                  {currentLogs.map((log, idx) => (
                    <motion.tr key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.02 }} className="hover:bg-blue-50 transition-colors border-b border-gray-100">
                      <td className="px-4 py-3 text-xs text-gray-700 text-center">{log.kst}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs text-gray-900">
                          {log.instance_name || log.instance_id || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs text-gray-900">
                          {log.region || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-900 text-center">{log.username || '-'}</td>
                      <td className="px-4 py-3 text-xs text-gray-600 text-center">{log.source_ip || log.terminal || '-'}</td>
                      <td className="px-4 py-3 text-center">
                        <button onClick={() => setSelectedLog(log)} className="text-blue-600 hover:text-blue-800 font-medium text-xs underline">
                          보기
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          )}

          {!loading && filteredLogs.length > 0 && (
            <div className="mt-6 flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {startIndex + 1}-{Math.min(endIndex, filteredLogs.length)} / 총 {filteredLogs.length}개
              </span>
              <div className="flex items-center gap-2">
                <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1} className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                  처음
                </button>
                <button onClick={() => setCurrentPage(p => p - 1)} disabled={currentPage === 1} className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                  이전
                </button>
                <span className="px-4 py-1 text-sm font-medium text-blue-600">
                  {currentPage} / {totalPages}
                </span>
                <button onClick={() => setCurrentPage(p => p + 1)} disabled={currentPage === totalPages} className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                  다음
                </button>
                <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages} className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                  마지막
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedLog && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedLog(null)}>
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-white rounded-2xl p-8 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">로그 상세</h3>
              <button onClick={() => setSelectedLog(null)} className="text-gray-400 hover:text-gray-600 transition-colors">
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-sm">
                <span className="font-semibold text-gray-700">시간:</span>
                <span className="col-span-2 text-gray-900">{selectedLog.kst}</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <span className="font-semibold text-gray-700">인스턴스:</span>
                <span className="col-span-2 text-gray-900">{selectedLog.instance_name || selectedLog.instance_id || '-'}</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <span className="font-semibold text-gray-700">리전:</span>
                <span className="col-span-2 text-gray-900">{selectedLog.region || '-'}</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <span className="font-semibold text-gray-700">계정명:</span>
                <span className="col-span-2 text-gray-900">{selectedLog.username || '-'}</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <span className="font-semibold text-gray-700">IP 주소:</span>
                <span className="col-span-2 text-gray-900">{selectedLog.source_ip || selectedLog.terminal || '-'}</span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
