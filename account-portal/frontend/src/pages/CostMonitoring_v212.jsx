import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const CostMonitoring = () => {
  const [projectCosts, setProjectCosts] = useState([]);
  const [userCosts, setUserCosts] = useState([]);
  const [instanceUsage, setInstanceUsage] = useState([]);
  const [vscodeWorkspaces, setVscodeWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  // 색상 팔레트
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658'];

  useEffect(() => {
    fetchCostData();
  }, [selectedDate]);

  const fetchCostData = async () => {
    setLoading(true);
    try {
      // v2.12 메트릭과 CUR 데이터 연동 API 호출
      const response = await fetch(`/api/cost-monitoring/v212-integration?date=${selectedDate}`);
      const data = await response.json();
      
      // 프로젝트별 비용 데이터 처리
      const projectData = data.projects.map(project => ({
        name: project.project_name || project.project,
        username: project.username,
        cost: parseFloat(project.total_weighted_cost || 0).toFixed(2),
        allocatedCost: parseFloat(project.total_allocated_cost || 0).toFixed(2),
        instances: project.instances_used,
        activeHours: project.total_active_hours,
        avgProcesses: parseFloat(project.avg_processes_per_hour || 0).toFixed(1),
        instanceTypes: project.instance_types,
        vscodeWorkspaces: project.vscode_workspaces
      }));

      // 사용자별 비용 집계
      const userMap = {};
      projectData.forEach(project => {
        if (!userMap[project.username]) {
          userMap[project.username] = {
            username: project.username,
            totalCost: 0,
            projects: 0,
            instances: new Set()
          };
        }
        userMap[project.username].totalCost += parseFloat(project.cost);
        userMap[project.username].projects += 1;
        project.instanceTypes.forEach(type => userMap[project.username].instances.add(type));
      });

      const userData = Object.values(userMap).map(user => ({
        ...user,
        totalCost: user.totalCost.toFixed(2),
        instances: Array.from(user.instances).join(', ')
      }));

      // 인스턴스 사용 현황
      const instanceData = data.instances.map(instance => ({
        instanceId: instance.instance_id,
        instanceType: instance.product_instance_type,
        dailyCost: parseFloat(instance.daily_cost).toFixed(2),
        usageHours: instance.usage_hours,
        projects: instance.projects.length,
        activeProjects: instance.projects.join(', ')
      }));

      // VSCode 워크스페이스 현황
      const workspaceData = data.workspaces.map(workspace => ({
        user: workspace.username,
        workspace: workspace.workspace_path,
        project: workspace.mapped_project,
        lastActive: workspace.last_active
      }));

      setProjectCosts(projectData);
      setUserCosts(userData);
      setInstanceUsage(instanceData);
      setVscodeWorkspaces(workspaceData);
    } catch (error) {
      console.error('비용 데이터 로딩 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">v2.12 메트릭 기반 비용 데이터 로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">프로젝트별 비용 모니터링 (v2.12)</h1>
        <div className="flex items-center space-x-4">
          <label>날짜 선택:</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="border rounded px-3 py-1"
          />
          <div className="text-sm text-gray-500">
            * CUR 데이터 24시간 딜레이 반영
          </div>
        </div>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>총 프로젝트</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{projectCosts.length}</div>
            <div className="text-sm text-gray-500">활성 프로젝트</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>총 사용자</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userCosts.length}</div>
            <div className="text-sm text-gray-500">활성 사용자</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>일간 총 비용</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${projectCosts.reduce((sum, p) => sum + parseFloat(p.cost), 0).toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">EC2 인스턴스 기준</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>VSCode 워크스페이스</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{vscodeWorkspaces.length}</div>
            <div className="text-sm text-gray-500">실시간 추적</div>
          </CardContent>
        </Card>
      </div>

      {/* 프로젝트별 비용 차트 */}
      <Card>
        <CardHeader>
          <CardTitle>프로젝트별 일간 비용 (가중치 적용)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={projectCosts}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [`$${value}`, name]}
                labelFormatter={(label) => `프로젝트: ${label}`}
              />
              <Legend />
              <Bar dataKey="cost" fill="#8884d8" name="가중치 적용 비용" />
              <Bar dataKey="allocatedCost" fill="#82ca9d" name="균등 분할 비용" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 사용자별 비용 파이 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>사용자별 비용 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={userCosts}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({username, totalCost}) => `${username}: $${totalCost}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="totalCost"
                >
                  {userCosts.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`$${value}`, '비용']} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* VSCode 워크스페이스 현황 */}
        <Card>
          <CardHeader>
            <CardTitle>VSCode 워크스페이스 추적 (lsof 기반)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {vscodeWorkspaces.map((workspace, index) => (
                <div key={index} className="border rounded p-2 text-sm">
                  <div className="font-semibold">{workspace.user}</div>
                  <div className="text-gray-600">{workspace.project}</div>
                  <div className="text-xs text-gray-500">{workspace.workspace}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 상세 테이블 */}
      <Card>
        <CardHeader>
          <CardTitle>프로젝트별 상세 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-300 px-4 py-2">프로젝트</th>
                  <th className="border border-gray-300 px-4 py-2">사용자</th>
                  <th className="border border-gray-300 px-4 py-2">가중치 비용</th>
                  <th className="border border-gray-300 px-4 py-2">활성 시간</th>
                  <th className="border border-gray-300 px-4 py-2">평균 프로세스</th>
                  <th className="border border-gray-300 px-4 py-2">인스턴스 타입</th>
                  <th className="border border-gray-300 px-4 py-2">VSCode 워크스페이스</th>
                </tr>
              </thead>
              <tbody>
                {projectCosts.map((project, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-300 px-4 py-2 font-semibold">{project.name}</td>
                    <td className="border border-gray-300 px-4 py-2">{project.username}</td>
                    <td className="border border-gray-300 px-4 py-2">${project.cost}</td>
                    <td className="border border-gray-300 px-4 py-2">{project.activeHours}h</td>
                    <td className="border border-gray-300 px-4 py-2">{project.avgProcesses}</td>
                    <td className="border border-gray-300 px-4 py-2">{project.instanceTypes.join(', ')}</td>
                    <td className="border border-gray-300 px-4 py-2 text-xs">
                      {project.vscodeWorkspaces.filter(w => w).join(', ') || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 데이터 검증 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>데이터 검증 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-semibold">v2.12 메트릭</div>
              <div>• lsof 기반 VSCode 워크스페이스 추적</div>
              <div>• 실시간 프로세스 모니터링</div>
              <div>• 60초 주기 데이터 수집</div>
            </div>
            <div>
              <div className="font-semibold">CUR 데이터</div>
              <div>• 24시간 딜레이 반영</div>
              <div>• EC2 인스턴스 실제 비용</div>
              <div>• 시간당 사용량 기준</div>
            </div>
            <div>
              <div className="font-semibold">비용 할당 로직</div>
              <div>• 동시 사용 프로젝트 수로 분할</div>
              <div>• 활동 시간 비율 가중치</div>
              <div>• VSCode 워크스페이스 매핑</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CostMonitoring;
