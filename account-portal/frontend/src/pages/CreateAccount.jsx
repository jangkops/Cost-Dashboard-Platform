import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRightIcon, UserPlusIcon, CheckCircleIcon, XCircleIcon, ChevronDownIcon, ExclamationTriangleIcon, InformationCircleIcon } from "@heroicons/react/24/outline";
import { getRegions, getInstances, createAccount } from "../api";

const ROLE_DETAILS = {
  user: {
    label: "User - 일반 사용자",
    sudoers: "# sudo 권한 없음\n# 기본 Linux 명령어만 실행 가능\n# 프로젝트 디렉토리 접근은 그룹 권한으로 관리"
  },
  ops: {
    label: "Ops - 운영 권한",
    sudoers: `# 시스템 모니터링 (NOPASSWD)
systemctl status, journalctl, ps, top, htop, df, free, lsof

# Docker 관리 (NOPASSWD)
docker ps, docker run, docker logs, docker exec, docker build, docker images

# Slurm 관리 (NOPASSWD)
sinfo, squeue, systemctl reload/restart slurmctld

# 파일 편집 (NOPASSWD)
vim /etc/slurm/slurm.conf, vim /etc/hosts

# 사용자 그룹 관리 (NOPASSWD)
gpasswd -a, gpasswd -d

# 패키지 관리 (비밀번호 필요)
yum, apt, apt-get, snap

# 명시적 제한
sudo -i, su -, systemctl stop/disable/poweroff/reboot, passwd root, visudo 금지`
  },
  admin: {
    label: "Admin - 전체 권한",
    sudoers: "%mogam-admin ALL=(ALL) NOPASSWD: ALL"
  }
};

export default function CreateAccount() {
  const [regions, setRegions] = useState([]);
  const [regionInstances, setRegionInstances] = useState({});
  const [selectedInstances, setSelectedInstances] = useState({});
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("user");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [expandedRegions, setExpandedRegions] = useState({});
  const [showRoleDetails, setShowRoleDetails] = useState(false);
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

  const validateUsername = (name) => {
    if (!name) return "계정명을 입력해주세요.";
    if (name.length < 3) return "계정명은 3자 이상이어야 합니다.";
    if (!/^[a-z][a-z0-9_-]*$/.test(name)) return "계정명은 소문자로 시작하고 소문자, 숫자, -, _만 사용 가능합니다.";
    return "";
  };

  const onSubmit = async () => {
    const totalSelected = Object.values(selectedInstances).flat().length;
    const usernameError = validateUsername(username);
    
    if (usernameError) {
      setValidationError(usernameError);
      setTimeout(() => setValidationError(""), 3000);
      return;
    }
    
    if (totalSelected === 0 || !role) {
      setValidationError("모든 필드를 입력해주세요.");
      setTimeout(() => setValidationError(""), 3000);
      return;
    }

    setLoading(true);
    setResult(null);
    setValidationError("");
    
    try {
      const result = await createAccount({ 
        regionInstances: selectedInstances, 
        username, 
        role 
      });
      
      setResult({ 
        success: result.success, 
        message: result.success 
          ? `${username} 계정이 ${totalSelected}개 인스턴스에 생성되었습니다`
          : result.message || "계정 생성에 실패했습니다"
      });
      
      setTimeout(() => {
        setResult(null);
      }, 3000);
      
      if (result.success) {
        setUsername("");
      }
    } catch (error) {
      setResult({ success: false, message: error.message || "계정 생성에 실패했습니다" });
      setTimeout(() => {
        setResult(null);
      }, 3000);
    } finally {
      setLoading(false);
    }
  };

  const totalSelected = Object.values(selectedInstances).flat().length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-blue-600">서버 계정 관리</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>계정 생성</span>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="max-w-5xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-blue-100 rounded-xl">
              <UserPlusIcon className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">계정 생성</h1>
              <p className="text-gray-500 mt-1">새로운 서버 계정을 생성합니다</p>
            </div>
          </div>

          <div className="space-y-6">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">계정명 입력</label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="계정명을 입력하세요 (예: cgjang)"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
            </motion.div>

            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-semibold text-gray-700">권한(Role)</label>
                <button 
                  type="button"
                  onClick={() => setShowRoleDetails(!showRoleDetails)} 
                  className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
                >
                  <InformationCircleIcon className="w-4 h-4" />
                  {showRoleDetails ? "권한 상세 닫기" : "권한 상세 보기"}
                </button>
              </div>
              <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all">
                <option value="user">User - 읽기 권한</option>
                <option value="ops">Ops - 운영 권한</option>
                <option value="admin">Admin - 전체 권한</option>
              </select>
            </motion.div>

            <AnimatePresence>
              {showRoleDetails && (
                <motion.div 
                  initial={{opacity:0,height:0}} 
                  animate={{opacity:1,height:"auto"}} 
                  exit={{opacity:0,height:0}}
                  transition={{duration:0.3}}
                  className="mt-4 p-4 bg-blue-50 rounded-lg border-2 border-blue-200"
                >
                  <h4 className="font-semibold text-blue-900 mb-3">권한 상세 정보</h4>
                  <div className="space-y-3">
                    {Object.entries(ROLE_DETAILS).map(([key, detail]) => (
                      <div key={key} className={`p-3 rounded-lg ${role === key ? "bg-blue-100 border-2 border-blue-400" : "bg-white"}`}>
                        <div className="font-semibold text-gray-900">{detail.label}</div>
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono mt-2">{detail.sudoers}</pre>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-3">대상 서버 선택</label>
              <div className="space-y-3">
                {regions.map((region, idx) => {
                  const regionSelected = selectedInstances[region] || [];
                  const isExpanded = expandedRegions[region];
                  return (
                    <motion.div key={region} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 + idx * 0.1 }} className="border-2 border-gray-200 rounded-xl overflow-hidden">
                      <button type="button" onClick={() => toggleRegion(region)} className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-gray-700">{region}</span>
                          {regionSelected.length > 0 && (
                            <span className="bg-blue-500 text-white px-2 py-1 rounded-full text-xs">{regionSelected.length}</span>
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
                            className="mb-2 px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                          >
                            {regionInstances[region].every(inst => regionSelected.includes(inst.instanceId)) ? "전체 해제" : "전체 선택"}
                          </button>
                          {regionInstances[region].map(inst => (
                            <label key={inst.instanceId} className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${regionSelected.includes(inst.instanceId) ? "bg-blue-50 border-2 border-blue-500" : "hover:bg-gray-50 border-2 border-transparent"}`}>
                              <input type="checkbox" checked={regionSelected.includes(inst.instanceId)} onChange={() => toggleInstance(region, inst.instanceId)} className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500" />
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

            <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={onSubmit} disabled={loading} className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 transition-all shadow-lg hover:shadow-xl">
              {loading ? "처리 중..." : `계정 생성${totalSelected > 0 ? ` (${totalSelected}개 인스턴스)` : ""}`}
            </motion.button>
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
                  <div className={`p-6 rounded-xl border-2 shadow-2xl ${result.success ? 'bg-blue-50 border-blue-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-start gap-3">
                      {result.success ? (
                        <CheckCircleIcon className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
                      ) : (
                        <XCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <h3 className={`font-bold text-lg mb-2 ${result.success ? 'text-blue-800' : 'text-red-800'}`}>
                          {result.success ? '계정 생성 완료' : '계정 생성 실패'}
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
      </motion.div>
    </div>
  );
}
