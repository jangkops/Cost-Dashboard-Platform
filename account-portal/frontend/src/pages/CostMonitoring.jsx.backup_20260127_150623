import React, { useState, useEffect } from 'react';

const CostMonitoringDashboard = () => {
  const [selectedDate, setSelectedDate] = useState('2026-01-26'); // 12월 24일 이후 기본값
  const [projectData, setProjectData] = useState([]);
  const [userData, setUserData] = useState([]);
  const [calendarData, setCalendarData] = useState({});
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState('KRW');

  useEffect(() => {
    fetchDailyData(selectedDate);
    fetchCalendarData();
  }, []);

  const fetchCalendarData = async () => {
    try {
      const response = await fetch('/api/cost-monitoring/finops/calendar-data?year=2026&month=1');
      const data = await response.json();
      setCalendarData(data.calendar_data || {});
    } catch (error) {
      console.error('달력 데이터 로딩 실패:', error);
    }
  };

  const fetchDailyData = async (date) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/cost-monitoring/finops/daily-cost-allocation/${date}`);
      const data = await response.json();
      
      if (data.error) {
        console.error('날짜 오류:', data.error);
        alert(data.message || '12월 24일 이후 데이터만 사용 가능합니다.');
        setLoading(false);
        return;
      }
      
      setProjectData(data.projects || []);
      setUserData(data.users || []);
      setSummary(data.summary || {});
      setLoading(false);
    } catch (error) {
      console.error('일별 데이터 로딩 실패:', error);
      setLoading(false);
    }
  };

  const handleDateClick = (date) => {
    // 12월 24일 이전 데이터 차단
    if (date < '2025-12-24') {
      alert('12월 24일 이후 데이터만 정확합니다. 이전 데이터는 사용할 수 없습니다.');
      return;
    }
    
    setSelectedDate(date);
    fetchDailyData(date);
  };

  const formatCurrency = (amount, curr = currency) => {
    if (curr === 'KRW') {
      return `₩${amount.toLocaleString()}`;
    }
    return `$${amount.toLocaleString()}`;
  };

  const getMaxCost = (data) => {
    return Math.max(...data.map(item => 
      currency === 'KRW' ? item.cost_krw : item.cost_usd
    ));
  };

  // 현대적인 막대그래프 컴포넌트
  const ModernBarChart = ({ data, title, maxItems = 8 }) => {
    const displayData = data.slice(0, maxItems);
    const maxCost = getMaxCost(displayData);

    return (
      <div className="modern-chart-container">
        <h3 className="chart-title">{title}</h3>
        <div className="modern-bar-chart">
          {displayData.map((item, index) => {
            const cost = currency === 'KRW' ? item.cost_krw : item.cost_usd;
            const percentage = (cost / maxCost) * 100;
            const label = item.project_code || item.username;
            
            return (
              <div key={index} className="modern-bar-item">
                <div className="bar-header">
                  <span className="bar-label">{label}</span>
                  <span className="bar-value">{formatCurrency(cost)}</span>
                </div>
                <div className="bar-track">
                  <div 
                    className="bar-progress"
                    style={{ 
                      width: `${percentage}%`,
                      background: `linear-gradient(90deg, hsl(${(index * 40) % 360}, 70%, 60%), hsl(${(index * 40 + 20) % 360}, 70%, 70%))`
                    }}
                  />
                </div>
                <div className="bar-stats">
                  <span>GPU: {item.avg_gpu_utilization}%</span>
                  <span>CPU: {item.avg_cpu_utilization}%</span>
                  <span>{item.usage_count || item.total_usage_hours}h</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // 현대적인 도넛 차트 컴포넌트
  const ModernDonutChart = ({ data, title, maxItems = 6 }) => {
    const displayData = data.slice(0, maxItems);
    const totalCost = displayData.reduce((sum, item) => 
      sum + (currency === 'KRW' ? item.cost_krw : item.cost_usd), 0
    );

    let currentAngle = 0;
    const radius = 70;
    const innerRadius = 45;
    const centerX = 100;
    const centerY = 100;

    return (
      <div className="modern-chart-container">
        <h3 className="chart-title">{title}</h3>
        <div className="donut-chart-wrapper">
          <div className="donut-chart">
            <svg width="200" height="200" viewBox="0 0 200 200">
              {displayData.map((item, index) => {
                const cost = currency === 'KRW' ? item.cost_krw : item.cost_usd;
                const percentage = (cost / totalCost) * 100;
                const angle = (cost / totalCost) * 360;
                
                const startAngle = currentAngle;
                const endAngle = currentAngle + angle;
                currentAngle += angle;

                const startX = centerX + radius * Math.cos((startAngle - 90) * Math.PI / 180);
                const startY = centerY + radius * Math.sin((startAngle - 90) * Math.PI / 180);
                const endX = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180);
                const endY = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180);

                const innerStartX = centerX + innerRadius * Math.cos((startAngle - 90) * Math.PI / 180);
                const innerStartY = centerY + innerRadius * Math.sin((startAngle - 90) * Math.PI / 180);
                const innerEndX = centerX + innerRadius * Math.cos((endAngle - 90) * Math.PI / 180);
                const innerEndY = centerY + innerRadius * Math.sin((endAngle - 90) * Math.PI / 180);

                const largeArcFlag = angle > 180 ? 1 : 0;
                const pathData = [
                  `M ${startX} ${startY}`,
                  `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`,
                  `L ${innerEndX} ${innerEndY}`,
                  `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerStartX} ${innerStartY}`,
                  'Z'
                ].join(' ');

                return (
                  <path
                    key={index}
                    d={pathData}
                    fill={`hsl(${(index * 50) % 360}, 70%, 65%)`}
                    stroke="white"
                    strokeWidth="2"
                  />
                );
              })}
              
              {/* 중앙 텍스트 */}
              <text x={centerX} y={centerY - 5} textAnchor="middle" className="donut-center-text">
                총 비용
              </text>
              <text x={centerX} y={centerY + 10} textAnchor="middle" className="donut-center-value">
                {formatCurrency(totalCost)}
              </text>
            </svg>
          </div>
          
          <div className="donut-legend">
            {displayData.map((item, index) => {
              const cost = currency === 'KRW' ? item.cost_krw : item.cost_usd;
              const percentage = ((cost / totalCost) * 100).toFixed(1);
              const label = item.project_code || item.username;
              
              return (
                <div key={index} className="legend-item">
                  <div 
                    className="legend-dot"
                    style={{ backgroundColor: `hsl(${(index * 50) % 360}, 70%, 65%)` }}
                  />
                  <span className="legend-label">
                    {label} ({percentage}%)
                  </span>
                  <span className="legend-value">
                    {formatCurrency(cost)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  // 달력 컴포넌트
  const Calendar = () => {
    const daysInMonth = 31;
    const startDay = 6; // 2025년 12월 1일은 일요일

    return (
      <div className="calendar-container">
        <h3 className="calendar-title">2025년 12월 비용 달력</h3>
        <div className="calendar-grid">
          <div className="calendar-header">
            {['일', '월', '화', '수', '목', '금', '토'].map(day => (
              <div key={day} className="calendar-day-header">{day}</div>
            ))}
          </div>
          <div className="calendar-body">
            {Array.from({ length: startDay }, (_, i) => (
              <div key={`empty-${i}`} className="calendar-day empty"></div>
            ))}
            {Array.from({ length: daysInMonth }, (_, i) => {
              const day = i + 1;
              const dateStr = `2025-12-${day.toString().padStart(2, '0')}`;
              const dayData = calendarData[dateStr];
              const isSelected = selectedDate === dateStr;
              const hasData = dayData && dayData.has_data && dateStr >= '2025-12-24'; // 12월 24일 이후만
              const isBlocked = dateStr < '2025-12-24'; // 12월 24일 이전 차단
              
              return (
                <div 
                  key={day}
                  className={`calendar-day ${isSelected ? 'selected' : ''} ${hasData ? 'has-data' : ''} ${isBlocked ? 'blocked' : ''}`}
                  onClick={() => hasData && !isBlocked && handleDateClick(dateStr)}
                >
                  <div className="day-number">{day}</div>
                  {hasData && !isBlocked && (
                    <div className="day-cost">
                      {formatCurrency(currency === 'KRW' ? dayData.cost_krw : dayData.cost_usd)}
                    </div>
                  )}
                  {isBlocked && (
                    <div className="day-cost" style={{color: '#9ca3af', fontSize: '9px'}}>
                      차단됨
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="cost-dashboard">
      <style jsx>{`
        .cost-dashboard {
          padding: 24px;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          min-height: 100vh;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .dashboard-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 32px;
          border-radius: 16px;
          margin-bottom: 32px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }

        .header-title {
          font-size: 32px;
          font-weight: 700;
          margin-bottom: 8px;
          letter-spacing: -0.5px;
        }

        .header-subtitle {
          font-size: 16px;
          opacity: 0.9;
          font-weight: 400;
        }

        .controls-section {
          display: flex;
          gap: 16px;
          margin-bottom: 32px;
          align-items: center;
        }

        .currency-selector {
          display: flex;
          background: white;
          border-radius: 12px;
          padding: 4px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .currency-btn {
          padding: 8px 16px;
          border: none;
          background: transparent;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .currency-btn.active {
          background: #667eea;
          color: white;
          box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
        }

        .selected-date {
          background: white;
          padding: 16px 24px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          font-weight: 600;
          color: #333;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 24px;
          margin-bottom: 32px;
        }

        .summary-card {
          background: white;
          padding: 24px;
          border-radius: 16px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
          border: 1px solid rgba(255,255,255,0.2);
          backdrop-filter: blur(10px);
        }

        .card-title {
          font-size: 14px;
          color: #6b7280;
          margin-bottom: 8px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .card-value {
          font-size: 28px;
          font-weight: 700;
          color: #1f2937;
          margin-bottom: 4px;
        }

        .card-subtitle {
          font-size: 12px;
          color: #9ca3af;
        }

        .main-content {
          display: grid;
          grid-template-columns: 1fr 400px;
          gap: 32px;
          margin-bottom: 32px;
        }

        .charts-section {
          display: grid;
          gap: 24px;
        }

        .modern-chart-container {
          background: white;
          padding: 24px;
          border-radius: 16px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }

        .chart-title {
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
          margin: 0 0 20px 0;
        }

        .modern-bar-chart {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .modern-bar-item {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .bar-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .bar-label {
          font-weight: 600;
          color: #374151;
          font-size: 14px;
        }

        .bar-value {
          font-weight: 700;
          color: #667eea;
          font-size: 14px;
        }

        .bar-track {
          height: 8px;
          background: #f3f4f6;
          border-radius: 4px;
          overflow: hidden;
        }

        .bar-progress {
          height: 100%;
          border-radius: 4px;
          transition: width 0.8s ease;
        }

        .bar-stats {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #6b7280;
        }

        .donut-chart-wrapper {
          display: flex;
          gap: 24px;
          align-items: center;
        }

        .donut-center-text {
          font-size: 12px;
          fill: #6b7280;
          font-weight: 500;
        }

        .donut-center-value {
          font-size: 14px;
          fill: #1f2937;
          font-weight: 700;
        }

        .donut-legend {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
        }

        .legend-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .legend-label {
          flex: 1;
          font-size: 14px;
          color: #374151;
          font-weight: 500;
        }

        .legend-value {
          font-size: 14px;
          color: #667eea;
          font-weight: 600;
        }

        .calendar-container {
          background: white;
          padding: 24px;
          border-radius: 16px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }

        .calendar-title {
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
          margin: 0 0 20px 0;
        }

        .calendar-grid {
          display: flex;
          flex-direction: column;
        }

        .calendar-header {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 1px;
          margin-bottom: 8px;
        }

        .calendar-day-header {
          padding: 12px 8px;
          text-align: center;
          font-weight: 600;
          color: #6b7280;
          font-size: 12px;
        }

        .calendar-body {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 1px;
        }

        .calendar-day {
          aspect-ratio: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 8px 4px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          background: #f9fafb;
        }

        .calendar-day.has-data {
          background: #e0e7ff;
          border: 1px solid #c7d2fe;
        }

        .calendar-day.has-data:hover {
          background: #c7d2fe;
          transform: translateY(-1px);
        }

        .calendar-day.selected {
          background: #667eea;
          color: white;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .calendar-day.blocked {
          background: #f3f4f6;
          color: #9ca3af;
          cursor: not-allowed;
          opacity: 0.5;
        }

        .calendar-day.blocked:hover {
          background: #f3f4f6;
          transform: none;
        }

        .day-number {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 2px;
        }

        .day-cost {
          font-size: 10px;
          font-weight: 500;
          text-align: center;
          line-height: 1.2;
        }

        .loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
          font-size: 16px;
          color: #6b7280;
        }

        @media (max-width: 1200px) {
          .main-content {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .cost-dashboard {
            padding: 16px;
          }
          
          .summary-grid {
            grid-template-columns: 1fr;
          }
          
          .donut-chart-wrapper {
            flex-direction: column;
          }
        }
      `}</style>

      <div className="dashboard-header">
        <div className="header-title">FinOps 비용 모니터링 대시보드</div>
        <div className="header-subtitle">
          S3 mogam-or-cur-stg Enhanced 메트릭 + AWS CUR 데이터 기반 정확한 비용정산<br/>
          5개 인스턴스 (g5, r7, p4d, p4de, head) + AWS 공식 가중치 + 12월 24일 이후 정확한 데이터만
        </div>
      </div>

      <div className="controls-section">
        <div className="currency-selector">
          <button 
            className={`currency-btn ${currency === 'USD' ? 'active' : ''}`}
            onClick={() => setCurrency('USD')}
          >
            USD ($)
          </button>
          <button 
            className={`currency-btn ${currency === 'KRW' ? 'active' : ''}`}
            onClick={() => setCurrency('KRW')}
          >
            KRW (₩)
          </button>
        </div>
        <div className="selected-date">
          선택된 날짜: {selectedDate}
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <div className="card-title">총 프로젝트</div>
          <div className="card-value">{summary.total_projects || 0}개</div>
          <div className="card-subtitle">상세불명 프로젝트 자동 배분</div>
        </div>
        <div className="summary-card">
          <div className="card-title">총 사용자</div>
          <div className="card-value">{summary.total_users || 0}명</div>
          <div className="card-subtitle">실제 메트릭 기반</div>
        </div>
        <div className="summary-card">
          <div className="card-title">일일 비용</div>
          <div className="card-value">
            {calendarData[selectedDate] ? 
              formatCurrency(currency === 'KRW' ? calendarData[selectedDate].cost_krw : calendarData[selectedDate].cost_usd) 
              : '$0'}
          </div>
          <div className="card-subtitle">AWS CUR 실제 데이터</div>
        </div>
        <div className="summary-card">
          <div className="card-title">5개 인스턴스 타입</div>
          <div className="card-value">g5, r7, p4d, p4de, head</div>
          <div className="card-subtitle">AWS 공식 가중치 적용</div>
        </div>
      </div>

      <div className="main-content">
        <div className="charts-section">
          {loading ? (
            <div className="loading">비용 데이터 로딩 중...</div>
          ) : (
            <>
              <ModernBarChart 
                data={projectData} 
                title="프로젝트별 비용 분석 (실시간 업데이트)"
              />
              <ModernDonutChart 
                data={projectData} 
                title="프로젝트별 비용 비율"
              />
              <ModernBarChart 
                data={userData} 
                title="사용자별 비용 분석"
              />
            </>
          )}
        </div>
        
        <Calendar />
      </div>
    </div>
  );
};

export default CostMonitoringDashboard;
