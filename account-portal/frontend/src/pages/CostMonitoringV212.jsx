import React, { useState, useEffect } from "react";

export default function CostMonitoringV212() {
  const [selectedDate, setSelectedDate] = useState('2026-01-13');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('projects');

  useEffect(() => { loadData(); }, [selectedDate]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/cost-monitoring-v212-test/v212-test?date=${selectedDate}`);
      const result = await res.json();
      setData(result);
    } catch (e) { 
      console.error('v2.12 데이터 로드 실패:', e); 
    }
    setLoading(false);
  };

  const colors = ['#6366f1','#8b5cf6','#ec4899','#f43f5e','#f97316','#eab308','#22c55e','#14b8a6','#06b6d4','#3b82f6'];
  const instColors = {
    'i-0dc3c13df82448939': '#6366f1', // g5
    'i-06a9b5df345d47eaa': '#f43f5e', // p4d  
    'i-0d53ba43b64510164': '#8b5cf6', // p4de
    'i-0c30cae12f60d69d1': '#22c55e', // r7
    'i-074a73c3cf9656989': '#06b6d4'  // HeadNode
  };

  // 프로젝트별 집계
  const projectSummary = {};
  if (data?.workspaces) {
    data.workspaces.forEach(ws => {
      const project = ws.mapped_project;
      if (!projectSummary[project]) {
        projectSummary[project] = {
          project: project,
          instances: new Set(),
          workspaces: [],
          last_active: ws.last_active
        };
      }
      projectSummary[project].instances.add(ws.instance_id);
      projectSummary[project].workspaces.push(ws.workspace_path);
    });
  }

  const projects = Object.values(projectSummary).map(p => ({
    ...p,
    instance_count: p.instances.size,
    instances: Array.from(p.instances)
  }));

  // 인스턴스별 집계
  const instanceSummary = {};
  if (data?.sample_metrics) {
    data.sample_metrics.forEach(metric => {
      const instanceId = metric.instance_id;
      if (instanceId && !instanceSummary[instanceId]) {
        instanceSummary[instanceId] = {
          instance_id: instanceId,
          agent_version: metric.agent_version,
          process_count: metric.process_count,
          has_vscode: metric.has_vscode,
          timestamp: metric.timestamp
        };
      }
    });
  }

  const instances = Object.values(instanceSummary);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Enhanced Agent v2.12 모니터링
        </h1>
        <p className="text-gray-600">
          실시간 VSCode 워크스페이스 추적 및 프로젝트 식별
        </p>
      </div>

      {/* 날짜 선택 */}
      <div className="mb-6 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">날짜:</label>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={loadData}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '로딩...' : '새로고침'}
        </button>
      </div>

      {/* 뷰 모드 선택 */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
          {['projects', 'instances', 'workspaces'].map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === mode
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {mode === 'projects' ? '프로젝트별' : 
               mode === 'instances' ? '인스턴스별' : 'VSCode 워크스페이스'}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">데이터 로딩 중...</p>
        </div>
      )}

      {data && !loading && (
        <>
          {/* 메타데이터 */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {data.metadata?.v212_files || 0}
              </div>
              <div className="text-sm text-blue-600">v2.12 메트릭 파일</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {projects.length}
              </div>
              <div className="text-sm text-green-600">활성 프로젝트</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {data.workspaces?.length || 0}
              </div>
              <div className="text-sm text-purple-600">VSCode 워크스페이스</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {instances.length}
              </div>
              <div className="text-sm text-orange-600">모니터링 인스턴스</div>
            </div>
          </div>

          {/* 프로젝트별 뷰 */}
          {viewMode === 'projects' && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  프로젝트별 리소스 사용 현황
                </h2>
              </div>
              <div className="p-6">
                {projects.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    활성 프로젝트가 없습니다.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {projects.map((project, idx) => (
                      <div key={project.project} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900">
                            {project.project}
                          </h3>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500">
                              {project.instance_count}개 인스턴스
                            </span>
                          </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600 mb-1">사용 인스턴스:</p>
                            <div className="flex flex-wrap gap-1">
                              {project.instances.map(instId => (
                                <span
                                  key={instId}
                                  className="px-2 py-1 text-xs rounded"
                                  style={{ 
                                    backgroundColor: instColors[instId] + '20',
                                    color: instColors[instId]
                                  }}
                                >
                                  {instId.slice(-8)}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600 mb-1">워크스페이스:</p>
                            <div className="text-xs text-gray-500 space-y-1">
                              {project.workspaces.slice(0, 3).map((ws, i) => (
                                <div key={i}>{ws}</div>
                              ))}
                              {project.workspaces.length > 3 && (
                                <div>... +{project.workspaces.length - 3}개 더</div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 인스턴스별 뷰 */}
          {viewMode === 'instances' && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  인스턴스별 모니터링 상태
                </h2>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {instances.map(instance => (
                    <div key={instance.instance_id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900">
                          {instance.instance_id?.slice(-8) || 'Unknown'}
                        </h3>
                        <span
                          className="px-2 py-1 text-xs rounded"
                          style={{ 
                            backgroundColor: instColors[instance.instance_id] + '20',
                            color: instColors[instance.instance_id]
                          }}
                        >
                          v{instance.agent_version}
                        </span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">프로세스:</span>
                          <span className="font-medium">{instance.process_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">VSCode:</span>
                          <span className={`font-medium ${instance.has_vscode ? 'text-green-600' : 'text-gray-400'}`}>
                            {instance.has_vscode ? '활성' : '비활성'}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(instance.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* VSCode 워크스페이스 뷰 */}
          {viewMode === 'workspaces' && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  VSCode 워크스페이스 추적 현황
                </h2>
              </div>
              <div className="p-6">
                {!data.workspaces || data.workspaces.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    활성 VSCode 워크스페이스가 없습니다.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            프로젝트
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            워크스페이스 경로
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            인스턴스
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            마지막 활성
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data.workspaces.map((ws, idx) => (
                          <tr key={idx}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {ws.mapped_project}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-900 font-mono">
                                {ws.workspace_path}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span
                                className="px-2 py-1 text-xs rounded"
                                style={{ 
                                  backgroundColor: instColors[ws.instance_id] + '20',
                                  color: instColors[ws.instance_id]
                                }}
                              >
                                {ws.instance_id?.slice(-8)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(ws.last_active).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
