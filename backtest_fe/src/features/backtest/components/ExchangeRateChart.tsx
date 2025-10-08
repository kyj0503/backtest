import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useExchangeRate } from "../hooks/useExchangeRate";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

interface ExchangeRateChartProps {
  startDate: string;
  endDate: string;
  className?: string;
  showCard?: boolean;
}

const ExchangeRateChart: React.FC<ExchangeRateChartProps> = ({ 
  startDate, 
  endDate, 
  className = "",
  showCard = true
}) => {
  const { exchangeData, loading, error } = useExchangeRate({ startDate, endDate });

  // 환율 포맷팅 함수
  const formatRate = (value: number) => {
    return `₩${value.toFixed(0)}`;
  };

  if (loading) {
    const loadingContent = (
      <div className="text-center">
        <div className="inline-flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
          <span>환율 데이터 로딩 중...</span>
        </div>
      </div>
    );
    return showCard ? (
      <Card className={className}>
        <CardHeader>
          <CardTitle>원달러 환율 변동</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingContent}
        </CardContent>
      </Card>
    ) : loadingContent;
  }

  if (error) {
    const errorContent = (
      <div className="text-center">
        <p className="text-destructive">{error}</p>
      </div>
    );
    return showCard ? (
      <Card className={className}>
        <CardHeader>
          <CardTitle>원달러 환율 변동</CardTitle>
        </CardHeader>
        <CardContent>
          {errorContent}
        </CardContent>
      </Card>
    ) : errorContent;
  }

  if (!exchangeData || exchangeData.length === 0) {
    const emptyContent = (
      <div className="text-center">
        <p className="text-muted-foreground">표시할 환율 데이터가 없습니다.</p>
      </div>
    );
    return showCard ? (
      <Card className={className}>
        <CardHeader>
          <CardTitle>원달러 환율 변동</CardTitle>
        </CardHeader>
        <CardContent>
          {emptyContent}
        </CardContent>
      </Card>
    ) : emptyContent;
  }

  const minRate = Math.min(...exchangeData.map((d) => d.rate));
  const maxRate = Math.max(...exchangeData.map((d) => d.rate));
  const rateChange = ((exchangeData[exchangeData.length - 1]?.rate - exchangeData[0]?.rate) / exchangeData[0]?.rate * 100);

  const chartContent = (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={exchangeData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            tickFormatter={(value: any) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            tickFormatter={(value: number) => `₩${value.toFixed(0)}`}
          />
          <Tooltip 
            formatter={(value: number) => [`₩${value.toFixed(2)}`, '환율']}
            labelFormatter={(label: any) => `날짜: ${label}`}
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

      {/* 환율 요약 정보 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-border">
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">시작 환율</div>
          <div className="text-sm font-semibold text-foreground">{formatRate(exchangeData[0]?.rate)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">종료 환율</div>
          <div className="text-sm font-semibold text-foreground">{formatRate(exchangeData[exchangeData.length - 1]?.rate)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">최고점</div>
          <div className="text-sm font-semibold text-destructive">{formatRate(maxRate)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">최저점</div>
          <div className="text-sm font-semibold text-green-600">{formatRate(minRate)}</div>
        </div>
      </div>
    </>
  );

  if (showCard) {
    return (
      <Card className={className}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="mb-1">원/달러 환율</CardTitle>
              <p className="text-sm text-muted-foreground">백테스트 기간 동안의 원달러 환율 변화</p>
            </div>
            <div className="text-right">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${rateChange >= 0 ? 'bg-destructive/10 text-destructive' : 'bg-green-100 text-green-800'}`}>
                {rateChange >= 0 ? '▲' : '▼'} {Math.abs(rateChange).toFixed(2)}%
              </div>
              <div className="text-xs text-muted-foreground mt-1">기간 변동률</div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          {chartContent}
        </CardContent>
      </Card>
    );
  }

  return <div className={className}>{chartContent}</div>;
};

export default ExchangeRateChart;
