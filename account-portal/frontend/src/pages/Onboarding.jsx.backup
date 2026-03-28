import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronRightIcon, UserPlusIcon, CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";

export default function Onboarding() {
  const [emailPrefix, setEmailPrefix] = useState("");
  const [department, setDepartment] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [emailError, setEmailError] = useState("");

  const departments = ["RNA AI팀", "Small molecule AI팀", "Computational biology팀", "Machine learning research팀"];
  const EMAIL_DOMAIN = "@mogam.re.kr";

  const validateEmailPrefix = (value) => {
    if (!value) return "";
    
    const koreanRegex = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/;
    if (koreanRegex.test(value)) {
      return "이메일에 한글을 사용할 수 없습니다.";
    }
    
    if (/^\d/.test(value)) {
      return "이메일은 숫자로 시작할 수 없습니다.";
    }
    
    const validPrefixRegex = /^[a-zA-Z][a-zA-Z0-9._-]*$/;
    if (!validPrefixRegex.test(value)) {
      return "올바른 이메일 형식이 아닙니다.";
    }
    
    return "";
  };

  const handleEmailPrefixChange = (e) => {
    const value = e.target.value;
    setEmailPrefix(value);
    const error = validateEmailPrefix(value);
    setEmailError(error);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const error = validateEmailPrefix(emailPrefix);
    if (error) {
      setEmailError(error);
      return;
    }
    
    const fullEmail = emailPrefix + EMAIL_DOMAIN;
    
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("/api/provisioning/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: fullEmail, department })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setResult({ success: true, data });
      } else {
        setResult({ success: false, error: data.error || "작업 실행 중 오류가 발생했습니다." });
      }
    } catch (error) {
      setResult({ success: false, error: "서버 연결 실패" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <span className="font-medium text-blue-600">통합 프로비저닝</span>
        <ChevronRightIcon className="w-4 h-4" />
        <span>사용자 등록</span>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-blue-100 rounded-xl">
              <UserPlusIcon className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">사용자 등록</h1>
              <p className="text-gray-500 mt-1">이메일과 부서를 입력하면 SSO 및 서버 접근 권한이 자동으로 부여됩니다</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                이메일 주소
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={emailPrefix}
                  onChange={handleEmailPrefixChange}
                  placeholder="username"
                  required
                  className={`flex-1 px-4 py-3 border-2 rounded-xl transition-all ${
                    emailError 
                      ? "border-red-300 focus:ring-2 focus:ring-red-500 focus:border-red-500" 
                      : "border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  }`}
                />
                <span className="text-gray-600 font-medium">{EMAIL_DOMAIN}</span>
              </div>
              {emailError && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-2 p-3 bg-yellow-50 border-2 border-yellow-200 rounded-lg flex items-center gap-2">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                  <p className="text-sm text-yellow-800 font-medium">{emailError}</p>
                </motion.div>
              )}
            </motion.div>

            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                소속 부서
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all appearance-none bg-white"
              >
                <option value="">부서를 선택하세요</option>
                {departments.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </motion.div>

            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading || !!emailError}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 transition-all shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  처리 중...
                </span>
              ) : (
                "사용자 등록"
              )}
            </motion.button>
          </form>

          {result && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className={`mt-6 p-6 rounded-xl border-2 ${result.success ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
              <div className="flex items-start gap-3">
                {result.success ? (
                  <CheckCircleIcon className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <h3 className={`font-bold text-lg mb-2 ${result.success ? "text-green-800" : "text-red-800"}`}>
                    {result.success ? "작업 완료" : "작업 실패"}
                  </h3>
                  <pre className="text-sm whitespace-pre-wrap font-mono bg-white bg-opacity-50 p-4 rounded-lg overflow-auto max-h-96">
                    {result.success ? JSON.stringify(result.data, null, 2) : result.error}
                  </pre>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
