import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRightIcon,
  ArrowPathIcon,
  CpuChipIcon,
  UserIcon,
  ShieldExclamationIcon,
  XMarkIcon,
  SignalIcon,
  SignalSlashIcon,
} from "@heroicons/react/24/outline";

const API_BASE = "/api/gateway";
const POLL_INTERVAL_MS = 5000;
const BAND_THRESHOLDS = [500000, 1000000, 1500000, 2000000];
const HARD_CAP = 2000000;

function getAuthHeaders() {
  const token = localStorage.getItem("authToken");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchGateway(path) {
  const res = await fetch(`${API_BASE}${path}`, { headers: getAuthHeaders() });
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem("authToken");
      localStorage.removeItem("userRole");
      localStorage.removeItem("username");
      window.location.href = "/login";
      throw new Error("AUTH_EXPIRED");
    }
    if (res.status === 403) {
      throw new Error("AUTH_FORBIDDEN");
    }
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return res.json();
}

function formatKRW(val) {
  if (val == null) return "—";
  return `₩${Number(val).toLocaleString("ko-KR", { maximumFractionDigits: 2 })}`;
}

function formatTokens(val) {
  if (val == null || val === 0) return "0";
  if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
  if (val >= 1000) return `${(val / 1000).toFixed(1)}K`;
  return val.toLocaleString();
}

function extractUsername(principalId) {
  if (!principalId) return "—";
  const match = principalId.match(/BedrockUser-(.+)$/);
  return match ? match[1] : principalId;
}

function formatTime(date) {
  return date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatCWTimestamp(ts) {
  if (!ts) return "—";
  // CW Logs format: "2026-03-23 15:13:19.000"
  const d = new Date(ts.replace(" ", "T") + "Z");
  if (isNaN(d.getTime())) return ts;
  return d.toLocaleString("ko-KR", { timeZone: "Asia/Seoul", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

/* ── Usage progress bar with band markers ── */
function UsageBar({ cost, limit }) {
  if (!limit) return <span className="text-xs text-gray-400">—</span>;
  const pct = Math.min((cost / limit) * 100, 100);
  const globalPct = Math.min((cost / HARD_CAP) * 100, 100);
  let barColor = "bg-green-500";
  if (pct >= 80) barColor = "bg-red-500";
  else if (pct >= 50) barColor = "bg-yellow-500";

  return (
    <div className="w-full min-w-[140px]">
      <div className="flex items-center gap-2 mb-0.5">
        <span className={`text-xs font-semibold ${pct >= 80 ? "text-red-700" : pct >= 50 ? "text-yellow-700" : "text-green-700"}`}>
          {pct.toFixed(1)}%
        </span>
        <span className="text-[10px] text-gray-400">{formatKRW(cost)} / {formatKRW(limit)}</span>
      </div>
      <div className="relative h-2.5 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          className={`absolute left-0 top-0 h-full rounded-full ${barColor}`}
          initial={false}
          animate={{ width: `${globalPct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
        {BAND_THRESHOLDS.map((threshold) => {
          const markerPct = (threshold / HARD_CAP) * 100;
          return (
            <div key={threshold} className="absolute top-0 h-full w-px bg-gray-400 opacity-50" style={{ left: `${markerPct}%` }} title={`₩${(threshold / 10000).toFixed(0)}만`} />
          );
        })}
        {limit < HARD_CAP && (
          <div className="absolute top-0 h-full w-0.5 bg-purple-600" style={{ left: `${(limit / HARD_CAP) * 100}%` }} title={`유효 한도: ${formatKRW(limit)}`} />
        )}
      </div>
      <div className="flex justify-between mt-0.5">
        <span className="text-[9px] text-gray-400">₩0</span>
        <span className="text-[9px] text-gray-400">₩200만</span>
      </div>
    </div>
  );
}

function PendingBadge({ pending }) {
  if (!pending) return <span className="text-xs text-gray-400">—</span>;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-yellow-500" />
      </span>
      대기중
    </span>
  );
}

function BandBadge({ band }) {
  const colors = ["bg-gray-100 text-gray-600", "bg-blue-100 text-blue-700", "bg-indigo-100 text-indigo-700", "bg-purple-100 text-purple-700"];
  const labels = ["기본", "+1단계", "+2단계", "+3단계"];
  const idx = Math.min(band, 3);
  return <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${colors[idx]}`}>{labels[idx]}</span>;
}

function PollingIndicator({ active, lastUpdated }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      {active ? (
        <><SignalIcon className="w-4 h-4 text-green-500" /><span className="text-green-600">자동 갱신 중</span></>
      ) : (
        <><SignalSlashIcon className="w-4 h-4 text-gray-400" /><span className="text-gray-400">일시 정지</span></>
      )}
      {lastUpdated && <span className="text-gray-400 ml-1">· 마지막 갱신: {formatTime(lastUpdated)}</span>}
    </div>
  );
}

export default function BedrockGateway() {
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);
  const [managedUsers, setManagedUsers] = useState([]);
  const [exceptionUsers, setExceptionUsers] = useState([]);
  const [exceptionUsage, setExceptionUsage] = useState([]);
  const [pricing, setPricing] = useState([]);
  const [month, setMonth] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedExceptionUser, setSelectedExceptionUser] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [pollActive, setPollActive] = useState(true);

  const intervalRef = useRef(null);
  const modalOpenRef = useRef(false);
  const authFailedRef = useRef(false);

  const loadData = useCallback(async (silent = false) => {
    if (authFailedRef.current) return;
    if (!silent) { setInitialLoading(true); setError(null); }
    try {
      const [usersRes, pricingRes, exceptionRes] = await Promise.all([
        fetchGateway("/users"),
        fetchGateway("/pricing"),
        fetchGateway("/exception-usage").catch(() => ({ exception_users: [] })),
      ]);
      setManagedUsers(usersRes.managed_users || []);
      setExceptionUsers(usersRes.exception_users || []);
      setExceptionUsage(exceptionRes.exception_users || []);
      setMonth(usersRes.month || "");
      setPricing(pricingRes.models || []);
      setLastUpdated(new Date());
      if (!silent) setError(null);
    } catch (e) {
      if (e.message === "AUTH_EXPIRED" || e.message === "AUTH_FORBIDDEN") {
        authFailedRef.current = true;
        setPollActive(false);
        if (e.message === "AUTH_FORBIDDEN") setError("관리자 권한이 필요합니다.");
        return;
      }
      if (!silent) setError(e.message);
    } finally {
      if (!silent) setInitialLoading(false);
    }
  }, []);

  useEffect(() => { loadData(false); }, [loadData]);

  useEffect(() => {
    if (!pollActive || authFailedRef.current) {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      return;
    }
    intervalRef.current = setInterval(() => {
      if (!modalOpenRef.current && !authFailedRef.current) loadData(true);
    }, POLL_INTERVAL_MS);
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [pollActive, loadData]);

  const openDetail = async (user) => {
    setSelectedUser(user);
    setSelectedExceptionUser(null);
    setDetailLoading(true);
    setDetailData(null);
    modalOpenRef.current = true;
    const encodedPid = encodeURIComponent(user.principal_id).replace(/%23/g, "%23");
    try {
      const [usage, policy] = await Promise.all([
        fetchGateway(`/users/${encodedPid}/usage`),
        fetchGateway(`/users/${encodedPid}/policy`),
      ]);
      setDetailData({ usage, policy });
    } catch (e) {
      if (e.message !== "AUTH_EXPIRED") {
        setDetailData({ error: e.message === "AUTH_FORBIDDEN" ? "관리자 권한이 필요합니다." : e.message });
      }
    } finally { setDetailLoading(false); }
  };

  const openExceptionDetail = (eu) => {
    setSelectedExceptionUser(eu);
    setSelectedUser(null);
    setDetailData(null);
    setDetailLoading(false);
    modalOpenRef.current = true;
  };

  const closeDetail = () => {
    setSelectedUser(null);
    setSelectedExceptionUser(null);
    setDetailData(null);
    modalOpenRef.current = false;
  };

  const handleManualRefresh = () => loadData(false);
  const togglePolling = () => setPollActive((prev) => !prev);

  // Merge exception user static info with live usage data
  const enrichedExceptionUsers = exceptionUsers.map((eu) => {
    const usage = exceptionUsage.find((u) => u.principal_id === eu.principal_id);
    return { ...eu, usage: usage || null };
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-purple-600">Bedrock 게이트웨이</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>사용량 모니터링</span>
      </motion.div>

      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-xl"><CpuChipIcon className="w-8 h-8 text-purple-600" /></div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Bedrock 게이트웨이 사용량</h1>
                <p className="text-gray-500 mt-1">{month ? `${month} 기준` : "로딩 중..."} · 관리자 전용</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <PollingIndicator active={pollActive} lastUpdated={lastUpdated} />
              <button onClick={togglePolling} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${pollActive ? "bg-green-100 text-green-700 hover:bg-green-200" : "bg-gray-100 text-gray-500 hover:bg-gray-200"}`}>
                {pollActive ? "자동 갱신 ON" : "자동 갱신 OFF"}
              </button>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleManualRefresh} disabled={initialLoading} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:bg-gray-400 transition-all shadow-md">
                <ArrowPathIcon className={`w-5 h-5 ${initialLoading ? "animate-spin" : ""}`} />
                새로고침
              </motion.button>
            </div>
          </div>
        </div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm flex items-center justify-between">
            <span>오류: {error}</span>
            {error.includes("권한") ? (
              <a href="/login" className="ml-4 px-3 py-1 bg-red-600 text-white rounded-lg text-xs hover:bg-red-700 transition-colors">로그인</a>
            ) : (
              <button onClick={handleManualRefresh} className="ml-4 px-3 py-1 bg-red-600 text-white rounded-lg text-xs hover:bg-red-700 transition-colors">재시도</button>
            )}
          </motion.div>
        )}

        {initialLoading && (
          <div className="text-center py-16">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-200 border-t-purple-600"></div>
            <p className="mt-4 text-gray-500">데이터 로딩 중...</p>
          </div>
        )}

        {/* ── Gateway-Managed Users ── */}
        {!initialLoading && !error && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <UserIcon className="w-6 h-6 text-purple-600" />
              <h2 className="text-xl font-bold text-gray-900">게이트웨이 관리 사용자</h2>
              <span className="text-sm text-gray-500">({managedUsers.length}명)</span>
              <span className="ml-auto px-2 py-0.5 rounded text-[10px] font-medium bg-purple-100 text-purple-600">데이터 소스: Gateway DynamoDB</span>
            </div>
            {managedUsers.length === 0 ? (
              <div className="text-center py-12"><UserIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" /><p className="text-gray-500">등록된 관리 사용자가 없습니다.</p></div>
            ) : (
              <div className="overflow-x-auto rounded-xl border-2 border-gray-200">
                <table className="w-full">
                  <thead className="bg-gradient-to-r from-purple-50 to-indigo-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 border-b-2 border-gray-200">사용자</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 border-b-2 border-gray-200 min-w-[200px]">사용량 / 한도</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">승인 밴드</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">승인 대기</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200">상세</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white">
                    {managedUsers.map((user, idx) => (
                      <motion.tr key={user.principal_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.03 }} className="hover:bg-purple-50 transition-colors border-b border-gray-100">
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">{extractUsername(user.principal_id)}</div>
                          <div className="text-xs text-gray-400 font-mono truncate max-w-[200px]" title={user.principal_id}>{user.principal_id}</div>
                        </td>
                        <td className="px-4 py-3"><UsageBar cost={user.current_month_cost_krw} limit={user.effective_limit_krw} /></td>
                        <td className="px-4 py-3 text-center"><BandBadge band={user.approval_band} /></td>
                        <td className="px-4 py-3 text-center"><PendingBadge pending={user.has_pending_approval} /></td>
                        <td className="px-4 py-3 text-center">
                          <button onClick={() => openDetail(user)} className="text-purple-600 hover:text-purple-800 font-medium text-xs underline">보기</button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>
        )}

        {/* ── Exception / Direct-Use Users ── */}
        {!initialLoading && !error && enrichedExceptionUsers.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-4">
              <ShieldExclamationIcon className="w-6 h-6 text-amber-500" />
              <h2 className="text-xl font-bold text-gray-900">직접 사용 예외 사용자</h2>
              <span className="text-sm text-gray-500">({enrichedExceptionUsers.length}명)</span>
              <span className="ml-auto px-2 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-700">데이터 소스: CloudWatch Logs</span>
            </div>
            <p className="text-sm text-gray-500 mb-4">게이트웨이를 통하지 않고 Bedrock을 직접 사용하는 사용자입니다. 사용량은 CloudWatch Logs (<code className="text-xs bg-gray-100 px-1 rounded">/aws/bedrock/modelinvocations</code>)에서 집계됩니다. 게이트웨이 한도/승인 밴드는 적용되지 않습니다.</p>
            <div className="overflow-x-auto rounded-xl border border-amber-200">
              <table className="w-full">
                <thead className="bg-amber-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 border-b border-amber-200">사용자</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 border-b border-amber-200">호출 수</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 border-b border-amber-200">입력 토큰</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 border-b border-amber-200">출력 토큰</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 border-b border-amber-200">추정 비용</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 border-b border-amber-200">마지막 활동</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 border-b border-amber-200">상세</th>
                  </tr>
                </thead>
                <tbody>
                  {enrichedExceptionUsers.map((eu) => {
                    const u = eu.usage;
                    return (
                      <tr key={eu.principal_id} className="border-b border-amber-100 hover:bg-amber-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">{extractUsername(eu.principal_id)}</div>
                          <div className="text-xs text-gray-400 font-mono">{eu.principal_id}</div>
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 mt-1 inline-block">{eu.status}</span>
                        </td>
                        <td className="px-4 py-3 text-right text-sm font-medium text-gray-900">
                          {u ? (u.total_invocations || 0).toLocaleString() : "—"}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-gray-700">
                          {u ? formatTokens(u.total_input_tokens) : "—"}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-gray-700">
                          {u ? formatTokens(u.total_output_tokens) : "—"}
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          {u ? (
                            u.estimated_cost_krw != null ? (
                              <span className="font-medium text-gray-900">{formatKRW(u.estimated_cost_krw)}</span>
                            ) : u.partial_cost_krw != null ? (
                              <span className="text-amber-700" title="일부 모델의 가격 정보가 없어 부분 추정치입니다">
                                ~{formatKRW(u.partial_cost_krw)}
                                <span className="text-[10px] ml-1">⚠️ 부분</span>
                              </span>
                            ) : <span className="text-gray-400">산정 불가</span>
                          ) : "—"}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {u?.last_activity ? formatCWTimestamp(u.last_activity) : "—"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {u && u.models?.length > 0 ? (
                            <button onClick={() => openExceptionDetail(eu)} className="text-amber-600 hover:text-amber-800 font-medium text-xs underline">보기</button>
                          ) : <span className="text-xs text-gray-400">—</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {/* Pricing reference */}
        {!initialLoading && !error && pricing.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-4">
              <CpuChipIcon className="w-6 h-6 text-indigo-500" />
              <h2 className="text-xl font-bold text-gray-900">모델 가격 참조</h2>
            </div>
            <div className="overflow-x-auto rounded-xl border border-gray-200">
              <table className="w-full">
                <thead className="bg-gradient-to-r from-indigo-50 to-purple-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 border-b-2 border-gray-200">모델 ID</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 border-b-2 border-gray-200">입력 (₩/1K 토큰)</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 border-b-2 border-gray-200">출력 (₩/1K 토큰)</th>
                  </tr>
                </thead>
                <tbody>
                  {pricing.map((m) => (
                    <tr key={m.model_id} className="border-b border-gray-100 hover:bg-indigo-50 transition-colors">
                      <td className="px-4 py-3 text-sm font-mono text-gray-800">{m.model_id}</td>
                      <td className="px-4 py-3 text-right text-sm text-gray-700">{formatKRW(m.input_price_per_1k)}</td>
                      <td className="px-4 py-3 text-right text-sm text-gray-700">{formatKRW(m.output_price_per_1k)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </div>

      {/* ── Gateway-Managed User Detail Modal ── */}
      <AnimatePresence>
        {selectedUser && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={closeDetail}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="bg-white rounded-2xl p-8 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{extractUsername(selectedUser.principal_id)}</h2>
                  <p className="text-xs text-gray-400 font-mono mt-1">{selectedUser.principal_id}</p>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-100 text-purple-600 mt-1 inline-block">게이트웨이 관리 · Gateway DynamoDB</span>
                </div>
                <button onClick={closeDetail} className="p-2 hover:bg-gray-100 rounded-lg transition-colors"><XMarkIcon className="w-6 h-6 text-gray-500" /></button>
              </div>

              {detailLoading && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-purple-200 border-t-purple-600"></div>
                  <p className="mt-3 text-gray-500 text-sm">상세 정보 로딩 중...</p>
                </div>
              )}

              {detailData?.error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">오류: {detailData.error}</div>}

              {detailData && !detailData.error && (
                <div className="space-y-6">
                  {detailData.policy && (
                    <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
                      <h3 className="font-semibold text-gray-800 mb-3">정책 정보</h3>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div><span className="text-gray-500">기본 한도:</span><span className="ml-2 font-medium">{formatKRW(detailData.policy.monthly_cost_limit_krw)}</span></div>
                        <div><span className="text-gray-500">최대 한도:</span><span className="ml-2 font-medium">{formatKRW(detailData.policy.max_monthly_cost_limit_krw)}</span></div>
                        <div><span className="text-gray-500">유효 한도:</span><span className="ml-2 font-medium text-purple-700">{formatKRW(detailData.policy.effective_limit_krw)}</span></div>
                        <div><span className="text-gray-500">승인 밴드:</span><span className="ml-2"><BandBadge band={detailData.policy.approval_band} /></span></div>
                        <div><span className="text-gray-500">승인 대기:</span><span className="ml-2"><PendingBadge pending={detailData.policy.has_pending_approval} /></span></div>
                        <div className="col-span-2">
                          <span className="text-gray-500">허용 모델:</span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {(detailData.policy.allowed_models || []).map((m) => (
                              <span key={m} className="px-2 py-0.5 bg-white rounded text-xs font-mono text-gray-600 border border-gray-200">{m}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                      {detailData.policy.active_boosts?.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-purple-200"><span className="text-sm text-gray-500">활성 부스트: {detailData.policy.active_boosts.length}건</span></div>
                      )}
                    </div>
                  )}
                  {detailData.usage && (
                    <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-200">
                      <h3 className="font-semibold text-gray-800 mb-3">{detailData.usage.month} 사용량</h3>
                      <div className="mb-4"><UsageBar cost={detailData.usage.total_cost_krw} limit={detailData.usage.effective_limit_krw || selectedUser.effective_limit_krw} /></div>
                      <div className="grid grid-cols-3 gap-3 text-sm mb-4">
                        <div><span className="text-gray-500">총 비용:</span><span className="ml-2 font-medium text-indigo-700">{formatKRW(detailData.usage.total_cost_krw)}</span></div>
                        <div><span className="text-gray-500">입력 토큰:</span><span className="ml-2 font-medium">{(detailData.usage.total_input_tokens || 0).toLocaleString()}</span></div>
                        <div><span className="text-gray-500">출력 토큰:</span><span className="ml-2 font-medium">{(detailData.usage.total_output_tokens || 0).toLocaleString()}</span></div>
                      </div>
                      {detailData.usage.models?.length > 0 && (
                        <div className="overflow-x-auto rounded-lg border border-indigo-200">
                          <table className="w-full text-sm">
                            <thead className="bg-indigo-100">
                              <tr>
                                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">모델</th>
                                <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">비용 (₩)</th>
                                <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">입력</th>
                                <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">출력</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailData.usage.models.map((m) => (
                                <tr key={m.model_id} className="border-b border-indigo-100">
                                  <td className="px-3 py-2 font-mono text-xs text-gray-700">{m.model_id}</td>
                                  <td className="px-3 py-2 text-right">{formatKRW(m.cost_krw)}</td>
                                  <td className="px-3 py-2 text-right text-gray-600">{(m.input_tokens || 0).toLocaleString()}</td>
                                  <td className="px-3 py-2 text-right text-gray-600">{(m.output_tokens || 0).toLocaleString()}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Exception User Detail Modal ── */}
      <AnimatePresence>
        {selectedExceptionUser && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={closeDetail}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="bg-white rounded-2xl p-8 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{extractUsername(selectedExceptionUser.principal_id)}</h2>
                  <p className="text-xs text-gray-400 font-mono mt-1">{selectedExceptionUser.principal_id}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800">{selectedExceptionUser.status || "direct-use-exception"}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-600">데이터 소스: CloudWatch Logs</span>
                  </div>
                </div>
                <button onClick={closeDetail} className="p-2 hover:bg-gray-100 rounded-lg transition-colors"><XMarkIcon className="w-6 h-6 text-gray-500" /></button>
              </div>

              {selectedExceptionUser.usage ? (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                    <h3 className="font-semibold text-gray-800 mb-3">월간 사용량 요약</h3>
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div><span className="text-gray-500">총 호출:</span><span className="ml-2 font-medium text-gray-900">{(selectedExceptionUser.usage.total_invocations || 0).toLocaleString()}</span></div>
                      <div><span className="text-gray-500">입력 토큰:</span><span className="ml-2 font-medium">{formatTokens(selectedExceptionUser.usage.total_input_tokens)}</span></div>
                      <div><span className="text-gray-500">출력 토큰:</span><span className="ml-2 font-medium">{formatTokens(selectedExceptionUser.usage.total_output_tokens)}</span></div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-amber-200 text-sm">
                      <span className="text-gray-500">추정 비용:</span>
                      {selectedExceptionUser.usage.estimated_cost_krw != null ? (
                        <span className="ml-2 font-semibold text-amber-800">{formatKRW(selectedExceptionUser.usage.estimated_cost_krw)}</span>
                      ) : selectedExceptionUser.usage.partial_cost_krw != null ? (
                        <span className="ml-2 font-semibold text-amber-700">~{formatKRW(selectedExceptionUser.usage.partial_cost_krw)} <span className="text-xs font-normal">(부분 추정)</span></span>
                      ) : (
                        <span className="ml-2 text-gray-400">산정 불가</span>
                      )}
                    </div>
                    {selectedExceptionUser.usage.has_unpriced_models && (
                      <div className="mt-2 p-2 bg-yellow-100 rounded-lg text-xs text-yellow-800">
                        ⚠️ 일부 모델의 가격 정보가 등록되지 않아 비용이 부분 추정치입니다. 가격 미등록 모델의 사용량은 비용에 포함되지 않습니다.
                      </div>
                    )}
                    {selectedExceptionUser.usage.last_activity && (
                      <div className="mt-2 text-xs text-gray-500">마지막 활동: {formatCWTimestamp(selectedExceptionUser.usage.last_activity)}</div>
                    )}
                  </div>

                  {/* Per-model breakdown */}
                  {selectedExceptionUser.usage.models?.length > 0 && (
                    <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                      <h3 className="font-semibold text-gray-800 mb-3">모델별 사용량</h3>
                      <div className="overflow-x-auto rounded-lg border border-amber-200">
                        <table className="w-full text-sm">
                          <thead className="bg-amber-100">
                            <tr>
                              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">모델</th>
                              <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">호출 수</th>
                              <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">입력 토큰</th>
                              <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">출력 토큰</th>
                              <th className="px-3 py-2 text-right text-xs font-semibold text-gray-700">추정 비용</th>
                              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">마지막 활동</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedExceptionUser.usage.models.map((m) => (
                              <tr key={m.model_id} className="border-b border-amber-100">
                                <td className="px-3 py-2 font-mono text-xs text-gray-700">{m.model_id}</td>
                                <td className="px-3 py-2 text-right">{(m.invocation_count || 0).toLocaleString()}</td>
                                <td className="px-3 py-2 text-right text-gray-600">{formatTokens(m.input_tokens)}</td>
                                <td className="px-3 py-2 text-right text-gray-600">{formatTokens(m.output_tokens)}</td>
                                <td className="px-3 py-2 text-right">
                                  {m.estimated_cost_krw != null ? (
                                    <span>{formatKRW(m.estimated_cost_krw)}</span>
                                  ) : (
                                    <span className="text-gray-400 text-xs" title={`cost_source: ${m.cost_source || "unknown"}`}>미등록</span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-xs text-gray-600">{formatCWTimestamp(m.last_activity)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400 text-sm">사용량 데이터가 없습니다.</div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
