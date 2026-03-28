import { useState } from "react";
import { motion } from "framer-motion";

export default function SSOTest() {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('user');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/provision-sso-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, role })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: error.message });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">SSO 프로비저닝 테스트</h1>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">이메일</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="이메일 입력"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">권한</label>
              <select 
                value={role} 
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button 
                onClick={() => setEmail('jangeyq34@gmail.com')}
                className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors"
              >
                테스트 계정
              </button>
              <button 
                onClick={() => setEmail('test.user@mogam.re.kr')}
                className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
              >
                일반 계정
              </button>
            </div>

            <button 
              onClick={handleTest}
              disabled={loading || !email}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'SSO 계정 생성 중...' : 'SSO 계정 생성'}
            </button>
          </div>

          {result && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }}
              className={`mt-6 p-4 rounded-xl ${result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}
            >
              {result.success ? (
                <div className="text-green-800">
                  <h3 className="font-semibold mb-2">✅ SSO 계정 생성 완료</h3>
                  <div className="text-sm space-y-1">
                    <p><strong>사용자명:</strong> {result.username}</p>
                    <p><strong>표시명:</strong> {result.display_name}</p>
                    <p><strong>권한:</strong> {result.role}</p>
                    <p><strong>애플리케이션:</strong> {result.application}</p>
                    {result.real_creation && <p className="text-green-600">🎯 실제 AWS SSO 계정 생성됨</p>}
                  </div>
                </div>
              ) : (
                <div className="text-red-800">
                  <h3 className="font-semibold mb-2">❌ 오류 발생</h3>
                  <p className="text-sm">{result.error}</p>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
