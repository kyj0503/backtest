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
    return `₩${value.toFixed(0)}`;
  };

  // Y축용 환율 포맷팅 함수 (더 간결하게)
  const formatRateAxis = (value: number) => {
    if (value >= 1000) {
      return `₩${(value/1000).toFixed(1)}K`;
    }
    return `₩${value.toFixed(0)}`;
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
            <h5 className="text-lg font-semibold text-gray-900 mb-1">원달러 환율 변동</h5>
            <p className="text-sm text-gray-600">백테스트 기간 동안의 USD/KRW 환율 추이</p>
          </div>
          <div className="text-right">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${rateChange >= 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
              {rateChange >= 0 ? '▲' : '▼'} {Math.abs(rateChange).toFixed(2)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">기간 변동률</div>
          </div>
        </div>
      </div>
      <div className="px-6 py-4">
        {/* 환율 차트 */}
        <div style={{ width: '100%', height: '400px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
              data={exchangeData}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="date" 
                tickFormatter={formatDate}
                interval="preserveStartEnd"
                tick={{ fontSize: 12 }}
                height={50}
              />
              <YAxis 
                tickFormatter={formatRateAxis}
                domain={[minRate * 0.998, maxRate * 1.002]}
                tick={{ fontSize: 12 }}
                width={70}
              />
              <Tooltip 
                labelFormatter={(label: any) => `날짜: ${label}`}
                formatter={(value: number) => [formatRate(value), 'USD/KRW']}
                contentStyle={{
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #dee2e6',
                  borderRadius: '6px',
                  fontSize: '13px'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="rate" 
                stroke="#fd7e14" 
                strokeWidth={3}
                dot={false}
                activeDot={{ 
                  r: 5, 
                  stroke: '#fd7e14', 
                  strokeWidth: 2, 
                  fill: '#fff' 
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 환율 요약 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-100">
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">시작 환율</div>
            <div className="text-sm font-semibold text-gray-800">{formatRate(exchangeData[0]?.rate)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">종료 환율</div>
            <div className="text-sm font-semibold text-gray-800">{formatRate(exchangeData[exchangeData.length - 1]?.rate)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">최고점</div>
            <div className="text-sm font-semibold text-red-600">{formatRate(maxRate)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">최저점</div>
            <div className="text-sm font-semibold text-green-600">{formatRate(minRate)}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExchangeRateChart;
