import React, { useState } from 'react';
import { Loader2, TrendingUp } from 'lucide-react';
import { BacktestRequest } from '../model/api-types';
import { PREDEFINED_STOCKS } from '../model/strategyConfig';
import DateRangeForm from './DateRangeForm';
import StrategyForm from './StrategyForm';
import { FormSection } from '@/shared/components';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Alert, AlertDescription } from '@/shared/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface SingleStockFormProps {
  onSubmit: (request: BacktestRequest) => Promise<any>;
  loading?: boolean;
}

const SingleStockForm: React.FC<SingleStockFormProps> = ({ onSubmit, loading = false }) => {
  // State
  const [ticker, setTicker] = useState<string>('AAPL');
  const [initialCash, setInitialCash] = useState<number>(10000);
  const [startDate, setStartDate] = useState<string>('2023-01-01');
  const [endDate, setEndDate] = useState<string>('2024-01-01');
  const [selectedStrategy, setSelectedStrategy] = useState<string>('buy_and_hold');
  const [strategyParams, setStrategyParams] = useState<Record<string, any>>({});
  const [commission, setCommission] = useState<number>(0.2); // 0.2%
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateStrategyParam = (key: string, value: any) => {
    setStrategyParams(prev => ({ ...prev, [key]: value }));
  };

  const validateForm = () => {
    const newErrors: string[] = [];

    if (!ticker || ticker.trim() === '') {
      newErrors.push('티커 심볼을 입력해주세요.');
    }

    if (initialCash < 100) {
      newErrors.push('초기 투자금액은 최소 $100 이상이어야 합니다.');
    }

    if (!startDate || !endDate) {
      newErrors.push('백테스트 기간을 설정해주세요.');
    } else if (new Date(startDate) >= new Date(endDate)) {
      newErrors.push('종료일은 시작일보다 이후여야 합니다.');
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors([]);

    try {
      // 전략 파라미터 타입 변환
      const params: Record<string, any> = {};
      Object.entries(strategyParams).forEach(([key, value]) => {
        params[key] = typeof value === 'string' ? parseInt(value) || value : value;
      });

      // 단일 종목 백테스트 요청 생성
      const request: BacktestRequest = {
        portfolio: [{
          symbol: ticker.toUpperCase(),
          amount: initialCash,
          asset_type: 'stock',
          investment_type: 'lump_sum'
        }],
        start_date: startDate,
        end_date: endDate,
        strategy: selectedStrategy,
        strategy_params: params,
        commission: commission / 100, // 퍼센트를 소수점으로 변환
        rebalance_frequency: 'monthly'
      };

      await onSubmit(request);
    } catch (error) {
      console.error('백테스트 실행 중 오류:', error);
      const errorMessage = error instanceof Error ? error.message : '백테스트 실행 중 오류가 발생했습니다.';
      setErrors([errorMessage]);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-6">
      {errors.length > 0 && (
        <Alert variant="destructive" className="mb-2">
          <AlertDescription>
            <h3 className="text-sm font-semibold">입력 오류</h3>
            <ul className="mt-2 space-y-1 text-sm">
              {errors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* 종목 선택 */}
        <FormSection
          title="종목 선택"
          description="백테스트할 종목의 티커 심볼과 투자금액을 입력하세요."
        >
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="ticker">티커 심볼</Label>
              <div className="flex gap-2">
                <Input
                  id="ticker"
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="예: AAPL, GOOGL"
                  className="flex-1"
                />
                <Select value={ticker} onValueChange={setTicker}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="빠른 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    {PREDEFINED_STOCKS.filter(stock => stock.value !== 'CUSTOM').map((stock) => (
                      <SelectItem key={stock.value} value={stock.value}>
                        {stock.value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <p className="text-xs text-muted-foreground">
                미국 주식 티커 심볼을 입력하세요 (예: AAPL, TSLA)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="initialCash">초기 투자금액 ($)</Label>
              <Input
                id="initialCash"
                type="number"
                min={100}
                step={100}
                value={initialCash}
                onChange={(e) => setInitialCash(Number(e.target.value))}
                placeholder="10000"
              />
              <p className="text-xs text-muted-foreground">
                최소 $100 이상 투자 가능
              </p>
            </div>
          </div>
        </FormSection>

        {/* 백테스트 기간 */}
        <FormSection
          title="백테스트 기간"
          description="백테스트를 실행할 기간을 지정하세요."
        >
          <DateRangeForm
            startDate={startDate}
            setStartDate={setStartDate}
            endDate={endDate}
            setEndDate={setEndDate}
          />
        </FormSection>

        {/* 전략 및 수수료 */}
        <div className="grid gap-6 md:grid-cols-2">
          <FormSection
            title="전략 선택"
            description="적용할 투자 전략과 파라미터를 설정하세요."
          >
            <StrategyForm
              selectedStrategy={selectedStrategy}
              setSelectedStrategy={setSelectedStrategy}
              strategyParams={strategyParams}
              updateStrategyParam={updateStrategyParam}
            />
          </FormSection>

          <FormSection
            title="거래 수수료"
            description="거래 시 발생하는 수수료 비율을 입력하세요."
          >
            <div className="space-y-2">
              <Label htmlFor="commission">수수료 (%)</Label>
              <Input
                id="commission"
                type="number"
                min={0}
                max={5}
                step={0.01}
                value={commission}
                onChange={(e) => setCommission(Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground">
                일반적으로 0.1% ~ 0.5% 사이입니다
              </p>
            </div>
          </FormSection>
        </div>

        {/* 제출 버튼 */}
        <div className="flex justify-end pt-4">
          <Button
            type="submit"
            disabled={loading || isSubmitting}
            size="lg"
            className="min-w-[200px]"
          >
            {(loading || isSubmitting) ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                백테스트 실행 중...
              </>
            ) : (
              <>
                <TrendingUp className="mr-2 h-4 w-4" />
                백테스트 실행
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default SingleStockForm;
