import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import * as XLSX from 'xlsx';

const API_ENDPOINT = 'https://your-api-gateway-url/cost-allocation';

const Container = styled.div`
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
`;

const Controls = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const Select = styled.select`
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  &:focus {
    outline: none;
    border-color: #6366f1;
  }
`;

const Button = styled.button`
  padding: 8px 16px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  &:hover {
    background: #4f46e5;
  }
  &:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
`;

const Th = styled.th`
  background: #f9fafb;
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  border-bottom: 1px solid #e5e7eb;
`;

const Td = styled.td`
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  color: #374151;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 48px;
  font-size: 16px;
  color: #6b7280;
`;

const ErrorBanner = styled.div`
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
`;

const Summary = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
`;

const SummaryCard = styled.div`
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
`;

const SummaryLabel = styled.div`
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
`;

const SummaryValue = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
`;

export default function CostTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [month, setMonth] = useState((new Date().getMonth() + 1).toString().padStart(2, '0'));

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINT}?year=${year}&month=${month}`);
      const result = await response.json();
      
      if (result.success) {
        setData(result.data);
      } else {
        setError(result.error || 'Failed to fetch data');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [year, month]);

  const downloadExcel = () => {
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Cost Report');
    XLSX.writeFile(wb, `Cost_Report_${year}-${month}.xlsx`);
  };

  const totalCost = data.reduce((sum, row) => sum + parseFloat(row.total_cost || 0), 0);
  const uniqueProjects = new Set(data.map(row => row.project)).size;
  const uniqueInstances = new Set(data.map(row => row.instance_id)).size;

  return (
    <Container>
      <Header>
        <Title>월간 비용 정산표</Title>
        <Controls>
          <Select value={year} onChange={(e) => setYear(e.target.value)}>
            {[2024, 2025, 2026].map(y => (
              <option key={y} value={y}>{y}년</option>
            ))}
          </Select>
          <Select value={month} onChange={(e) => setMonth(e.target.value)}>
            {Array.from({length: 12}, (_, i) => i + 1).map(m => (
              <option key={m} value={m.toString().padStart(2, '0')}>
                {m}월
              </option>
            ))}
          </Select>
          <Button onClick={fetchData} disabled={loading}>
            조회
          </Button>
          <Button onClick={downloadExcel} disabled={!data.length}>
            엑셀 다운로드
          </Button>
        </Controls>
      </Header>

      {error && <ErrorBanner>오류: {error}</ErrorBanner>}

      <Summary>
        <SummaryCard>
          <SummaryLabel>총 비용</SummaryLabel>
          <SummaryValue>${totalCost.toFixed(2)}</SummaryValue>
        </SummaryCard>
        <SummaryCard>
          <SummaryLabel>프로젝트 수</SummaryLabel>
          <SummaryValue>{uniqueProjects}</SummaryValue>
        </SummaryCard>
        <SummaryCard>
          <SummaryLabel>인스턴스 수</SummaryLabel>
          <SummaryValue>{uniqueInstances}</SummaryValue>
        </SummaryCard>
      </Summary>

      {loading ? (
        <LoadingSpinner>데이터를 불러오는 중...</LoadingSpinner>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>프로젝트</Th>
              <Th>인스턴스 ID</Th>
              <Th>기간</Th>
              <Th>활동 일수</Th>
              <Th>비용 (USD)</Th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                <Td>{row.project}</Td>
                <Td>{row.instance_id}</Td>
                <Td>{row.month}</Td>
                <Td>{row.active_days}</Td>
                <Td>${parseFloat(row.total_cost).toFixed(2)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
}
