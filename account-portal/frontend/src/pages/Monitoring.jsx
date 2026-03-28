import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ChevronRightIcon, ClockIcon, ArrowPathIcon, FunnelIcon } from "@heroicons/react/24/outline";
import { getLogs } from "../api";

export default function Monitoring() {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  
  const [dateFilter, setDateFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [regionFilter, setRegionFilter] = useState("");
  const [usernameFilter, setUsernameFilter] = useState("");
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await getLogs();
      setLogs(data);
      setFilteredLogs(data);
    } catch (error) {
      console.error(error);
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

    if (actionFilter) {
      filtered = filtered.filter(log => log.action === actionFilter);
    }

    if (regionFilter) {
      filtered = filtered.filter(log => log.region === regionFilter);
    }

    if (usernameFilter) {
      filtered = filtered.filter(log => log.username.includes(usernameFilter));
    }

    setFilteredLogs(filtered);
    setCurrentPage(1);
  }, [dateFilter, actionFilter, regionFilter, usernameFilter, logs]);

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentLogs = filteredLogs.slice(startIndex, endIndex);

  const uniqueActions = [...new Set(logs.map(log => log.action))];
  const uniqueRegions = [...new Set(logs.map(log => log.region))];

  const resetFilters = () => {
    setDateFilter("");
    setActionFilter("");
    setRegionFilter("");
    setUsernameFilter("");
  };

  const getStatusBadge = (status) => {
    if (status === "완료") return "bg-green-100 text-green-800";
    if (status === "유지") return "bg-blue-100 text-blue-800";
    return "bg-red-100 text-red-800";
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-purple-600">모니터링</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>포털 작업 로그</span>
      </motion.div>

      <div className="max-w-[1600px] mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-xl">
                <ClockIcon className="w-8 h-8 text-purple-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">포털 작업 로그</h1>
                <p className="text-gray-500 mt-1">포털 작업 이력</p>
              </div>
            </div>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={loadLogs} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:bg-gray-400 transition-all shadow-md">
              <ArrowPathIcon className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
              새로고침
            </motion.button>
          </div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mb-6 p-4 bg-purple-50 rounded-xl border border-purple-200">
            <div className="flex items-center gap-2 mb-3">
              <FunnelIcon className="w-5 h-5 text-purple-600" />
              <h3 className="font-semibold text-gray-800">필터</h3>
              {(dateFilter || actionFilter || regionFilter || usernameFilter) && (
                <button onClick={resetFilters} className="ml-auto text-xs text-purple-600 hover:text-purple-800 underline">
                  필터 초기화
                </button>
              )}
            </div>
            <div className="grid grid-cols-4 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">날짜</label>
                <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">작업</label>
                <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                  <option value="">전체</option>
                  {uniqueActions.map(action => (
                    <option key={action} value={action}>{action}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">리전</label>
                <select value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                  <option value="">전체</option>
                  {uniqueRegions.map(region => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">계정명</label>
                <input type="text" value={usernameFilter} onChange={(e) => setUsernameFilter(e.target.value)} placeholder="검색..." className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              총 {logs.length}개 중 {filteredLogs.length}개 표시
            </div>
          </motion.div>

          {loading ? (
            <div className="text-center py-16">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-200 border-t-purple-600"></div>
              <p className="mt-4 text-gray-500">로딩 중...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-16">
              <ClockIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">조회된 로그가 없습니다.</p>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="overflow-x-auto rounded-xl border-2 border-gray-200">
              <table className="w-full table-fixed">
                <thead className="bg-gradient-to-r from-purple-50 to-indigo-50">
                  <tr>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-32">시간</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-32">작업명</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-20">계정명</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-24">리전</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-40">인스턴스</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-16">상태</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 w-14">상세</th>
                  </tr>
                </thead>
                <tbody className="bg-white">
                  {currentLogs.map((log, idx) => (
                    <motion.tr key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.02 }} className="hover:bg-purple-50 transition-colors border-b border-gray-100">
                      <td className="px-2 py-3 text-xs text-gray-700 text-center truncate">
                        {formatSeoulTime(log.timestamp)}
                      </td>
                      <td className="px-2 py-3 text-xs text-gray-900 text-center truncate">{log.action}</td>
                      <td className="px-2 py-3 text-xs text-gray-700 text-center truncate">{log.username}</td>
                      <td className="px-2 py-3 text-xs text-gray-700 text-center truncate">{log.region}</td>
                      <td className="px-2 py-3 text-xs text-gray-600 text-center truncate" title={log.instance_name || log.instance}>
                        {log.instance_name || log.instance}
                      </td>
                      <td className="px-2 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${getStatusBadge(log.status)}`}>
                          {log.status}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-center">
                        <button onClick={() => setSelectedLog(log)} className="text-purple-600 hover:text-purple-800 font-medium text-xs underline">
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
                <span className="px-4 py-1 text-sm font-medium text-purple-600">
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
              <h2 className="text-2xl font-bold text-gray-900">로그 상세 정보</h2>
              <button onClick={() => setSelectedLog(null)} className="text-gray-400 hover:text-gray-600 text-3xl leading-none">
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-xl">
                <span className="font-semibold text-gray-700">시간:</span>
                <span className="ml-2 text-gray-900">{formatSeoulTime(selectedLog.timestamp)}</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <span className="font-semibold text-gray-700">작업:</span>
                <span className="ml-2 text-gray-900">{selectedLog.action}</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <span className="font-semibold text-gray-700">계정명:</span>
                <span className="ml-2 text-gray-900">{selectedLog.username}</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <span className="font-semibold text-gray-700">리전:</span>
                <span className="ml-2 text-gray-900">{selectedLog.region}</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="mb-2">
                  <span className="font-semibold text-gray-700">인스턴스 이름:</span>
                  <span className="ml-2 text-gray-900">{selectedLog.instance_name || selectedLog.instance}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">인스턴스 ID:</span>
                  <span className="ml-2 text-gray-600 font-mono text-sm">{selectedLog.instance}</span>
                </div>
              </div>
              {selectedLog.role && (
                <div className="p-4 bg-gray-50 rounded-xl">
                  <span className="font-semibold text-gray-700">권한:</span>
                  <span className="ml-2 text-gray-900">{selectedLog.role}</span>
                </div>
              )}
              <div className="p-4 bg-gray-50 rounded-xl">
                <span className="font-semibold text-gray-700">상태:</span>
                <span className={`ml-2 px-3 py-1 rounded-full text-sm font-semibold ${getStatusBadge(selectedLog.status)}`}>
                  {selectedLog.status}
                </span>
              </div>
              {selectedLog.reason && (
                <div className="p-4 bg-red-50 rounded-xl border-2 border-red-200">
                  <div className="font-semibold text-red-800 mb-2">실패 사유:</div>
                  <div className="text-sm text-red-700 whitespace-pre-wrap break-words">{selectedLog.reason}</div>
                </div>
              )}
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="font-semibold text-gray-700 mb-2">상세 로그:</div>
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono bg-white p-4 rounded-lg border border-gray-200 overflow-x-auto">
                  {selectedLog.details}
                </pre>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
