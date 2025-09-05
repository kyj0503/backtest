import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useExchangeRate } from "../hooks/useExchangeRate";

interface ExchangeRateChartProps {
  startDate: string;
  endDate: string;
  className?: string;
}

const ExchangeRateChart: React.FC<ExchangeRateChartProps> = ({ 
  startDate, 
  endDate, 
  className = "" 
}) => {
  const { exchangeData, loading, error } = useExchangeRate({ startDate, endDate });

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
  };

  // 환율 포맷팅 함수
  const formatRate = (value: number) => {
    return `₩${value.toLocaleString()}`;
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">원달러 환율 변동</h5>
        </div>
        <div className="px-6 py-4 text-center">
          <div className="inline-flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            <span>환율 데이터 로딩 중...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">원달러 환율 변동</h5>
        </div>
        <div className="px-6 py-4 text-center">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!exchangeData || exchangeData.length === 0) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="border-b border-gray-200 px-6 py-4">
          <h5 className="text-lg font-semibold text-gray-900 mb-0">원달러 환율 변동</h5>
        </div>
        <div className="px-6 py-4 text-center">
          <p className="text-gray-500">표시할 환율 데이터가 없습니다.</p>
        </div>
      </div>
    );
  }

  const minRate = Math.min(...exchangeData.map((d) => d.rate));
  const maxRate = Math.max(...exchangeData.map((d) => d.rate));
  const rateChange = ((exchangeData[exchangeData.length - 1]?.rate - exchangeData[0]?.rate) / exchangeData[0]?.rate * 100);

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h5 className="text-lg font-semibold text-gray-900 mb-0">원달러 환율 변동</h5>
          </div>
          <div>
            <small className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${rateChange >= 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
              {rateChange >= 0 ? '+' : ''}{rateChange.toFixed(2)}%
            </small>
          </div>
        </div>
      </div>
      <div className="px-6 py-4">
        {/* 환율 차트 */}
        <div style={{ width: '100%', height: '300px' }}>
          <ResponsiveContainer>
            <LineChart data={exchangeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={formatDate}
                interval="preserveStartEnd"
              />
              <YAxis 
                tickFormatter={formatRate}
                domain={[minRate * 0.995, maxRate * 1.005]}
              />
              <Tooltip 
                labelFormatter={(label: any) => `날짜: ${label}`}
                formatter={(value: number) => [formatRate(value), 'USD/KRW']}
              />
              <Line 
                type="monotone" 
                dataKey="rate" 
                stroke="#fd7e14" 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 환율 요약 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
          <div>
            <small className="text-gray-500 block">시작 환율</small>
            <strong>{formatRate(exchangeData[0]?.rate)}</strong>
          </div>
          <div>
            <small className="text-gray-500 block">종료 환율</small>
            <strong>{formatRate(exchangeData[exchangeData.length - 1]?.rate)}</strong>
          </div>
          <div>
            <small className="text-gray-500 block">기간 중 변동폭</small>
            <strong>{formatRate(maxRate - minRate)}</strong>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExchangeRateChart;
