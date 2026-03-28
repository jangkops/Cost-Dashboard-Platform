import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRightIcon, UserGroupIcon, PlusIcon, MinusIcon, MagnifyingGlassIcon, CheckCircleIcon, XCircleIcon, UserIcon } from "@heroicons/react/24/outline";
import { getRegions, getInstances, getProjectGroups, manageProjectMember, getAccounts } from "../api";

export default function ProjectGroups() {
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [instances, setInstances] = useState([]);
  const [selectedInstance, setSelectedInstance] = useState("");
  const [projectGroups, setProjectGroups] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [accountSearch, setAccountSearch] = useState("");

  useEffect(() => {
    const init = async () => {
      const regionList = await getRegions();
      setRegions(regionList);
    };
    init();
  }, []);

  useEffect(() => {
    if (selectedRegion) {
      loadInstances();
    }
  }, [selectedRegion]);

  useEffect(() => {
    if (selectedRegion && selectedInstance) {
      loadProjectGroups();
      loadAvailableUsers();
    }
  }, [selectedRegion, selectedInstance]);

  const loadInstances = async () => {
    try {
      const inst = await getInstances(selectedRegion);
      setInstances(inst);
    } catch (error) {
      console.error("Failed:", error);
    }
  };

  const loadProjectGroups = async () => {
    setLoading(true);
    try {
      const groups = await getProjectGroups(selectedRegion, selectedInstance);
      setProjectGroups(groups);
    } catch (error) {
      console.error("Failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableUsers = async () => {
    try {
      const accounts = await getAccounts(selectedRegion, selectedInstance);
      setAvailableUsers(accounts.map(acc => acc.username));
    } catch (error) {
      console.error("Failed:", error);
    }
  };

  const handleAddMember = async (groupName, username) => {
    setLoading(true);
    try {
      const res = await manageProjectMember(selectedRegion, selectedInstance, groupName, username, "add");
      if (res.success) {
        setResult({ type: "success", action: "add", message: `${username}을(를) ${groupName}에 추가했습니다` });
        await loadProjectGroups();
      } else {
        setResult({ type: "error", action: "add", message: res.message });
      }
    } catch (error) {
      setResult({ type: "error", action: "add", message: error.message });
    } finally {
      setLoading(false);
      setTimeout(() => setResult(null), 3000);
    }
  };

  const handleRemoveMember = async (groupName, username) => {
    setLoading(true);
    try {
      const res = await manageProjectMember(selectedRegion, selectedInstance, groupName, username, "remove");
      if (res.success) {
        setResult({ type: "success", action: "remove", message: `${username}을(를) ${groupName}에서 제거했습니다` });
        await loadProjectGroups();
      } else {
        setResult({ type: "error", action: "remove", message: res.message });
      }
    } catch (error) {
      setResult({ type: "error", action: "remove", message: error.message });
    } finally {
      setLoading(false);
      setTimeout(() => setResult(null), 3000);
    }
  };

  const filteredGroups = projectGroups.filter(group => {
    const matchesGroupName = group.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesAccount = accountSearch === "" || group.members.some(member => 
      member.toLowerCase().includes(accountSearch.toLowerCase())
    );
    return matchesGroupName && matchesAccount;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-indigo-600">서버 계정 관리</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>계정 프로젝트 권한</span>
      </motion.div>

      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-indigo-100 rounded-xl">
              <UserGroupIcon className="w-8 h-8 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">계정 프로젝트 권한</h1>
              <p className="text-gray-500 mt-1">계정 프로젝트 권한 관리</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">리전</label>
                <select value={selectedRegion} onChange={(e) => setSelectedRegion(e.target.value)} className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                  <option value="">리전 선택</option>
                  {regions.map(region => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">인스턴스</label>
                <select value={selectedInstance} onChange={(e) => setSelectedInstance(e.target.value)} disabled={!selectedRegion} className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100">
                  <option value="">인스턴스 선택</option>
                  {instances.map(inst => (
                    <option key={inst.instanceId} value={inst.instanceId}>{inst.name}</option>
                  ))}
                </select>
              </div>
            </div>

            {selectedInstance && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="relative">
                    <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="프로젝트 그룹 검색..." className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" />
                  </div>
                  <div className="relative">
                    <UserIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input type="text" value={accountSearch} onChange={(e) => setAccountSearch(e.target.value)} placeholder="계정명 검색..." className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500" />
                  </div>
                </div>

                <div className="text-sm text-gray-600 text-right">
                  총 {filteredGroups.length}개 그룹
                </div>

                {loading ? (
                  <div className="text-center py-16">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
                    <p className="mt-4 text-gray-500">로딩 중...</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredGroups.map((group, idx) => (
                      <motion.div key={group.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="border-2 border-gray-200 rounded-xl p-4 hover:border-indigo-300 transition-colors">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-bold text-gray-900">{group.name}</h3>
                          <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm font-semibold">
                            {group.memberCount}명
                          </span>
                        </div>
                        
                        <div className="space-y-2">
                          {group.members.length > 0 ? (
                            group.members.map(member => (
                              <div key={member} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg">
                                <span className="text-sm text-gray-700">{member}</span>
                                <button onClick={() => handleRemoveMember(group.name, member)} className="text-red-600 hover:text-red-800 p-1">
                                  <MinusIcon className="w-4 h-4" />
                                </button>
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-gray-400 text-center py-2">계정 없음</p>
                          )}
                        </div>

                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="relative">
                            <PlusIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                            <select onChange={(e) => { if (e.target.value) handleAddMember(group.name, e.target.value); e.target.value = ""; }} className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                              <option value="">계정 추가...</option>
                              {availableUsers.filter(u => !group.members.includes(u)).map(user => (
                                <option key={user} value={user}>{user}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          <AnimatePresence>
            {result && (
              <motion.div 
                key="result"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="pointer-events-auto max-w-lg w-full mx-4"
                >
                  <div className={`p-6 rounded-xl border-2 shadow-2xl ${
                    result.action === 'remove' 
                      ? 'bg-red-50 border-red-200' 
                      : result.type === 'success' 
                        ? 'bg-blue-50 border-blue-200' 
                        : 'bg-red-50 border-red-200'
                  }`}>
                    <div className="flex items-start gap-3">
                      {result.type === "success" ? (
                        <CheckCircleIcon className={`w-6 h-6 flex-shrink-0 mt-0.5 ${result.action === 'remove' ? 'text-red-600' : 'text-blue-600'}`} />
                      ) : (
                        <XCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <h3 className={`font-bold text-lg mb-2 ${
                          result.action === 'remove'
                            ? 'text-red-800'
                            : result.type === 'success'
                              ? 'text-blue-800'
                              : 'text-red-800'
                        }`}>
                          {result.type === "success" 
                            ? result.action === 'add' ? '계정 추가' : '계정 제거'
                            : '작업 실패'}
                        </h3>
                        <p className="text-sm">{result.message}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
