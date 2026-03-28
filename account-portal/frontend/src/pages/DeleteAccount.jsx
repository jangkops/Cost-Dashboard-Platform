import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRightIcon, TrashIcon, CheckCircleIcon, XCircleIcon, ChevronDownIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { getRegions, getInstances, deleteAccount, getAccounts } from "../api";

export default function DeleteAccount() {
  const [regions, setRegions] = useState([]);
  const [regionInstances, setRegionInstances] = useState({});
  const [selectedInstances, setSelectedInstances] = useState({});
  const [availableAccounts, setAvailableAccounts] = useState([]);
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [expandedRegions, setExpandedRegions] = useState({});
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    const init = async () => {
      const regionList = await getRegions();
      setRegions(regionList);
      regionList.forEach(async (region) => {
        try {
          const inst = await getInstances(region);
          setRegionInstances(prev => ({ ...prev, [region]: inst }));
        } catch (error) {
          console.error("Failed:", error);
        }
      });
    };
    init();
  }, []);

  const refreshAccounts = async () => {
    const accountsMap = new Map();
    for (const [region, instances] of Object.entries(selectedInstances)) {
      for (const instanceId of instances) {
        try {
          const accounts = await getAccounts(region, instanceId);
          const instanceInfo = regionInstances[region]?.find(i => i.instanceId === instanceId);
          const instanceName = instanceInfo?.name || instanceId;
          
          accounts.forEach(acc => {
            const key = acc.username;
            if (!accountsMap.has(key)) {
              accountsMap.set(key, { 
                username: acc.username, 
                role: acc.role,
                instances: []
              });
            }
            accountsMap.get(key).instances.push({ region, instanceId, instanceName });
          });
        } catch (error) {
          console.error("Failed:", error);
        }
      }
    }
    const accountsList = Array.from(accountsMap.values()).sort((a, b) => a.username.localeCompare(b.username));
    setAvailableAccounts(accountsList);
    setSelectedAccounts(prev => prev.filter(username => accountsList.some(a => a.username === username)));
  };

  useEffect(() => {
    if (Object.keys(selectedInstances).length > 0) {
      refreshAccounts();
    } else {
      setAvailableAccounts([]);
      setSelectedAccounts([]);
    }
  }, [selectedInstances]);

  const toggleRegion = (region) => {
    setExpandedRegions(prev => ({ ...prev, [region]: !prev[region] }));
  };

  const toggleInstance = (region, instanceId) => {
    setSelectedInstances(prev => {
      const regionSelected = prev[region] || [];
      const newRegionSelected = regionSelected.includes(instanceId)
        ? regionSelected.filter(id => id !== instanceId)
        : [...regionSelected, instanceId];
      if (newRegionSelected.length === 0) {
        const { [region]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [region]: newRegionSelected };
    });
  };

  const addAccount = (e) => {
    const username = e.target.value;
    if (username && !selectedAccounts.includes(username)) {
      setSelectedAccounts([...selectedAccounts, username]);
    }
    e.target.value = "";
  };

  const removeAccount = (username) => {
    setSelectedAccounts(selectedAccounts.filter(a => a !== username));
  };

  const getRoleLabel = (role) => {
    if (role === "admin") return "Admin";
    if (role === "ops") return "Ops";
    if (role === "user") return "User";
    return "None";
  };

  const onSubmit = async () => {
    const totalSelected = Object.values(selectedInstances).flat().length;
    
    if (totalSelected === 0 || selectedAccounts.length === 0) {
      setValidationError("모든 필드를 입력해주세요.");
      setTimeout(() => setValidationError(""), 3000);
      return;
    }

    setLoading(true);
    setResult(null);
    setValidationError("");
    
    try {
      const results = [];
      for (const username of selectedAccounts) {
        const acc = availableAccounts.find(a => a.username === username);
        if (!acc) continue;
        
        const accountRegionInstances = {};
        acc.instances.forEach(inst => {
          if (!accountRegionInstances[inst.region]) {
            accountRegionInstances[inst.region] = [];
          }
          accountRegionInstances[inst.region].push(inst.instanceId);
        });
        
        const result = await deleteAccount({ 
          regionInstances: accountRegionInstances, 
          usernames: [username]
        });
        results.push(result);
      }
      
      const allSuccess = results.every(r => r.success);
      let totalSuccess = 0, totalFail = 0;
      
      results.forEach(r => {
        const msg = r.message;
        const successMatch = msg.match(/(\d+)개 성공/);
        const failMatch = msg.match(/(\d+)개 실패/);
        
        if (successMatch) totalSuccess += parseInt(successMatch[1]);
        if (failMatch) totalFail += parseInt(failMatch[1]);
      });
      
      const deletedAccounts = selectedAccounts.map(username => {
        const acc = availableAccounts.find(a => a.username === username);
        return `${username} : ${getRoleLabel(acc?.role)} 삭제`;
      }).join(", ");
      
      const finalMessage = deletedAccounts;
      
      setResult({ 
        success: allSuccess, 
        message: finalMessage 
      });
      setTimeout(() => setResult(null), 3000);
      setSelectedAccounts([]);
      await refreshAccounts();
    } catch (error) {
      setResult({ success: false, message: error.message });
      setTimeout(() => setResult(null), 3000);
      setSelectedAccounts([]);
      await refreshAccounts();
    } finally {
      setLoading(false);
    }
  };

  const totalSelected = Object.values(selectedInstances).flat().length;
  const unselectedAccounts = availableAccounts.filter(acc => !selectedAccounts.includes(acc.username));

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-rose-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-red-600">서버 계정 관리</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>계정 삭제</span>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="max-w-5xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-red-100 rounded-xl">
              <TrashIcon className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">계정 삭제</h1>
              <p className="text-gray-500 mt-1">서버 계정을 삭제합니다</p>
            </div>
          </div>

          <div className="space-y-6">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">계정명 선택</label>
              {availableAccounts.length > 0 ? (
                <div>
                  <select onChange={addAccount} className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all">
                    <option value="">계정을 선택하세요</option>
                    {unselectedAccounts.map(acc => (
                      <option key={acc.username} value={acc.username}>
                        {acc.username} : {getRoleLabel(acc.role)} ({acc.instances?.map(i => i.instanceName).join(", ") || ""})
                      </option>
                    ))}
                  </select>
                  {selectedAccounts.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {selectedAccounts.map(username => {
                        const acc = availableAccounts.find(a => a.username === username);
                        return (
                          <span key={username} className="bg-red-100 text-red-800 px-3 py-2 rounded-full text-sm font-medium flex items-center gap-2">
                            {username} : {getRoleLabel(acc?.role)}
                            <button onClick={() => removeAccount(username)} className="hover:bg-red-200 rounded-full p-0.5">
                              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                            </button>
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <input type="text" value="" placeholder="인스턴스를 먼저 선택하세요" disabled className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl bg-gray-100" />
              )}
            </motion.div>

            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-3">대상 서버 선택</label>
              <div className="space-y-3">
                {regions.map((region, idx) => {
                  const regionSelected = selectedInstances[region] || [];
                  const isExpanded = expandedRegions[region];
                  return (
                    <motion.div key={region} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 + idx * 0.1 }} className="border-2 border-gray-200 rounded-xl overflow-hidden">
                      <button type="button" onClick={() => toggleRegion(region)} className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-gray-700">{region}</span>
                          {regionSelected.length > 0 && (
                            <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs">{regionSelected.length}</span>
                          )}
                        </div>
                        <ChevronDownIcon className={`w-5 h-5 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                      </button>
                      {isExpanded && regionInstances[region] && (
                        <div className="p-4 space-y-2">
                          <button
                            type="button"
                            onClick={() => {
                              const allIds = regionInstances[region].map(inst => inst.instanceId);
                              const allSelected = allIds.every(id => regionSelected.includes(id));
                              setSelectedInstances(prev => ({
                                ...prev,
                                [region]: allSelected ? [] : allIds
                              }));
                            }}
                            className="mb-2 px-3 py-1 text-xs bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                          >
                            {regionInstances[region].every(inst => regionSelected.includes(inst.instanceId)) ? "전체 해제" : "전체 선택"}
                          </button>
                          {regionInstances[region].map(inst => (
                            <label key={inst.instanceId} className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${regionSelected.includes(inst.instanceId) ? "bg-red-50 border-2 border-red-500" : "hover:bg-gray-50 border-2 border-transparent"}`}>
                              <input type="checkbox" checked={regionSelected.includes(inst.instanceId)} onChange={() => toggleInstance(region, inst.instanceId)} className="w-5 h-5 text-red-600 rounded focus:ring-2 focus:ring-red-500" />
                              <div className="flex-1">
                                <div className="font-medium text-gray-900">{inst.name}</div>
                                <div className="text-sm text-gray-500">{inst.instanceId}</div>
                              </div>
                            </label>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>

            {validationError && (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-4 bg-yellow-50 border-2 border-yellow-200 rounded-xl flex items-center gap-3">
                <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600 flex-shrink-0" />
                <p className="text-yellow-800 font-medium">{validationError}</p>
              </motion.div>
            )}

            <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={onSubmit} disabled={loading} className="w-full px-6 py-4 bg-gradient-to-r from-red-600 to-rose-600 text-white font-semibold rounded-xl hover:from-red-700 hover:to-rose-700 disabled:from-gray-400 disabled:to-gray-500 transition-all shadow-lg hover:shadow-xl">
              {loading ? "처리 중..." : `계정 삭제${selectedAccounts.length > 0 ? ` (${selectedAccounts.length}개 계정, ${totalSelected}개 인스턴스)` : ""}`}
            </motion.button>
          </div>

{result && (
            <AnimatePresence>
              <motion.div 
                key="result"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
              >
                <motion.div
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="pointer-events-auto max-w-lg w-full mx-4"
                >
                  <div className="p-6 rounded-xl border-2 shadow-2xl bg-red-50 border-red-200">
                    <div className="flex items-start gap-3">
                      <XCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h3 className="font-bold text-lg mb-2 text-red-800">계정 삭제 완료</h3>
                        <p className="text-sm">{result.message}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </motion.div>
    </div>
  );
}
