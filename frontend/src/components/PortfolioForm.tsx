import { Stock, PortfolioInputMode } from '../types/backtest-form';

export interface PortfolioFormProps {
  portfolio: Stock[];
  updateStock: (index: number, field: keyof Stock, value: string | number) => void;
  addStock: () => void;
  addCash: () => void;
  removeStock: (index: number) => void;
  getTotalAmount: () => number;
  portfolioInputMode: PortfolioInputMode;
  setPortfolioInputMode: (mode: PortfolioInputMode) => void;
  totalInvestment: number;
  setTotalInvestment: (amount: number) => void;
}

import React, { ChangeEvent } from 'react';
import { PREDEFINED_STOCKS, ASSET_TYPES } from '../constants/strategies';
import { Tooltip } from './common';
import StockAutocomplete from './common/StockAutocomplete';
import { Button } from './ui/button';
import { Input } from './ui/input';

const PortfolioForm: React.FC<PortfolioFormProps> = ({
  portfolio,
  updateStock,
  addStock,
  addCash,
  removeStock,
  getTotalAmount,
  portfolioInputMode,
  setPortfolioInputMode,
  totalInvestment,
  setTotalInvestment,
}) => {
  return (
    <div className="mb-8">
      <div className="flex flex-col md:flex-row md:items-center md:gap-6 mb-4">
        <h5 className="text-lg font-semibold mb-2 md:mb-0">포트폴리오 구성</h5>
                <div className="mb-6">
          <label className="font-medium text-foreground">입력 방식:</label>
          <div className="flex border border-primary rounded-md overflow-hidden">
            <Button
              type="button"
              onClick={() => setPortfolioInputMode('amount')}
              className={`rounded-none border-0 ${portfolioInputMode === 'amount' ? 'bg-primary text-primary-foreground' : 'bg-background text-foreground hover:bg-accent'}`}
              style={{
                border: 'none',
                boxShadow: 'none',
              }}
            >
              금액 기준
            </Button>
            <Button
              type="button"
              onClick={() => setPortfolioInputMode('weight')}
              className={`rounded-none border-0 border-l ${portfolioInputMode === 'weight' ? 'bg-primary text-primary-foreground' : 'bg-background text-foreground hover:bg-accent'}`}
              style={{
                border: 'none',
                boxShadow: 'none',
              }}
            >
              비중 기준
            </Button>
          </div>
        </div>
        {portfolioInputMode === 'weight' && (
          <div className="flex items-center gap-2 ml-0 md:ml-8 mt-2 md:mt-0">
            <label className="font-medium text-foreground">전체 투자금액($):</label>
            <Input
              type="number"
              min={1000}
              step={100}
              value={totalInvestment}
              onChange={e => setTotalInvestment(Number(e.target.value))}
              className="w-32"
            />
          </div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full table-fixed divide-y divide-border border border-border rounded-lg">
          <thead className="bg-muted/50">
            <tr>
              <th className="w-64 px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">종목/자산</th>
              <th className="w-32 px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">투자 금액 ($)</th>
              <th className="w-28 px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">투자 방식</th>
              <th className="w-24 px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">자산 타입</th>
              <th className="w-24 px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">비중 (%)</th>
              <th className="w-20 px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">작업</th>
            </tr>
          </thead>
          <tbody className="bg-background divide-y divide-border">
            {portfolio.map((stock, index) => (
              <tr key={index} className="hover:bg-muted/50">
                <td className="w-64 px-6 py-4 whitespace-nowrap">
                  <div className="space-y-2 max-w-full overflow-hidden">
                    {stock.assetType === ASSET_TYPES.CASH ? (
                      <Input
                        type="text"
                        value={stock.symbol || ''}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'symbol', e.target.value)}
                        placeholder="현금 자산 이름 입력 (예: USD, KRW)"
                        maxLength={20}
                        className="w-full bg-accent/50"
                      />
                    ) : (
                      <>
                        <select
                          value={stock.symbol === '' ? 'CUSTOM' : stock.symbol}
                          onChange={(e: ChangeEvent<HTMLSelectElement>) => {
                            if (e.target.value === 'CUSTOM') {
                              updateStock(index, 'symbol', '');
                            } else {
                              updateStock(index, 'symbol', e.target.value);
                            }
                          }}
                          className="w-full px-3 py-2 border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent bg-background text-foreground"
                        >
                          <option value="CUSTOM">직접 입력</option>
                          {PREDEFINED_STOCKS.slice(1).map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {(stock.symbol === '' || !PREDEFINED_STOCKS.some(opt => opt.value === stock.symbol)) && (
                          <StockAutocomplete
                            value={stock.symbol}
                            onChange={(value: string) => updateStock(index, 'symbol', value)}
                            placeholder="종목 심볼 입력 (예: AAPL)"
                            className=""
                          />
                        )}
                      </>
                    )}
                  </div>
                </td>
                                <td className="w-32 px-6 py-4 whitespace-nowrap">
                  <Input
                    type="number"
                    value={stock.amount}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'amount', e.target.value)}
                    min="100"
                    step="100"
                    disabled={portfolioInputMode === 'weight'}
                    className="w-full"
                  />
                </td>
                <td className="w-28 px-6 py-4 whitespace-nowrap">
                  <div className="space-y-2">
                    <select
                      value={stock.investmentType}
                      onChange={(e: ChangeEvent<HTMLSelectElement>) => updateStock(index, 'investmentType', e.target.value)}
                      className="w-full px-3 py-2 border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent bg-background text-foreground"
                    >
                      <option value="lump_sum">일시불 투자</option>
                      <option value="dca">분할 매수 (DCA)</option>
                    </select>
                    {stock.investmentType === 'dca' && (
                      <Input
                        type="number"
                        value={stock.dcaPeriods || 12}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'dcaPeriods', e.target.value)}
                        min="1"
                        max="60"
                        placeholder="개월 수"
                        className="w-full"
                      />
                    )}
                  </div>
                  {stock.investmentType === 'dca' && stock.dcaPeriods && (
                    <p className="text-xs text-muted-foreground mt-1">
                      월 ${Math.round(stock.amount / stock.dcaPeriods)}씩 {stock.dcaPeriods}개월
                    </p>
                  )}
                </td>
                <td className="w-24 px-6 py-4 whitespace-nowrap">
                  <div className="space-y-2">
                    <select
                      value={stock.assetType || ASSET_TYPES.STOCK}
                      onChange={(e: ChangeEvent<HTMLSelectElement>) => updateStock(index, 'assetType', e.target.value)}
                      className="w-full px-3 py-2 border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent bg-background text-foreground"
                    >
                      <option value={ASSET_TYPES.STOCK}>주식</option>
                      <option value={ASSET_TYPES.CASH}>현금</option>
                    </select>
                    {/* 자산 타입 배지(위험자산/무위험) 노출 제거 */}
                  </div>
                </td>
                <td className="w-24 px-6 py-4 whitespace-nowrap text-sm">
                  {/* 비중(%) 입력: weight 기반 모드면 직접 입력, 금액 기반 모드면 자동 계산 */}
                  {portfolioInputMode === 'weight' ? (
                    <Input
                      type="number"
                      value={typeof stock.weight === 'number' ? stock.weight : ''}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => updateStock(index, 'weight', Number(e.target.value))}
                      min="0"
                      max="100"
                      step="0.1"
                      className="w-20 px-2 py-1 text-sm"
                    />
                  ) : (
                    <span title="투자 금액 비율로 자동 계산됨. 비중을 직접 입력하려면 비중 기반 모드로 전환하세요.">
                      {((stock.amount / getTotalAmount()) * 100).toFixed(1)}%
                    </span>
                  )}
                </td>
                <td className="w-20 px-6 py-4 whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => removeStock(index)}
                    disabled={portfolio.length <= 1}
                    className="px-3 py-1 text-sm font-medium text-destructive bg-destructive/10 border border-destructive rounded-md hover:bg-destructive/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-accent/50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-foreground">합계</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-foreground">${getTotalAmount().toLocaleString()}</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-foreground">-</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-foreground">-</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-foreground">100.0%</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-foreground"></th>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="flex gap-3 mt-4">
        <button
          type="button"
          onClick={addStock}
          disabled={portfolio.length >= 10}
          className="px-4 py-2 text-sm font-medium text-primary bg-accent border border-primary rounded-md hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          + 종목 추가
        </button>
        <Tooltip content="현금을 포트폴리오에 추가 (무위험 자산)">
          <button
            type="button"
            onClick={addCash}
            disabled={portfolio.length >= 10}
            className="px-4 py-2 text-sm font-medium text-green-600 bg-green-50 border border-green-300 rounded-md hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            현금 추가
          </button>
        </Tooltip>
      </div>
    </div>
  );
};

export default PortfolioForm;
