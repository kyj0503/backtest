/**
 * 부가 데이터 수집 실패 안내 (A-08 supplemental_status)
 *
 * 부가 섹션(뉴스·벤치마크·환율 등)은 데이터가 없으면 블록째 숨긴다. 그래서
 * 수집이 시간 초과·오류로 실패한 경우와 원래 데이터가 없는 경우가 화면에서
 * 똑같아 보인다. timeout/error인 섹션만 골라 짧게 알린다. empty(정상적으로
 * 비어 있음)와 skipped(요청하지 않음)는 안내하지 않는다.
 */
import React from 'react';
import { Info } from 'lucide-react';
import type {
  SupplementalOutcome,
  SupplementalSection,
  SupplementalStatus,
} from '../../model/types/backtest-result-types';

const SECTION_LABELS: Record<SupplementalSection, string> = {
  ticker_info: '종목 정보',
  stock_data: '개별 종목 주가',
  volatility_events: '급등락 이벤트',
  exchange_rates: '환율',
  benchmarks: '벤치마크 지수',
  news: '최신 뉴스',
};

const FAILURE_LABELS: Partial<Record<SupplementalOutcome, string>> = {
  timeout: '시간 초과',
  error: '오류',
};

interface SupplementalStatusNoticeProps {
  status?: SupplementalStatus;
}

const SupplementalStatusNotice: React.FC<SupplementalStatusNoticeProps> = ({ status }) => {
  if (!status) return null;

  const failed = (Object.keys(SECTION_LABELS) as SupplementalSection[])
    .map((section) => {
      const outcome = status[section];
      const reason = outcome ? FAILURE_LABELS[outcome] : undefined;
      return reason ? `${SECTION_LABELS[section]}(${reason})` : null;
    })
    .filter((item): item is string => item !== null);

  if (failed.length === 0) return null;

  return (
    <div
      role="status"
      aria-label="부가 데이터 수집 상태"
      className="flex gap-2 rounded-lg border border-border bg-muted/40 p-3 text-sm text-muted-foreground"
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <p>
        일부 부가 데이터를 불러오지 못했습니다: {failed.join(', ')}. 해당 섹션이 비어 있다면
        데이터가 없어서가 아니라 수집에 실패했기 때문이며, 다시 실행하면 표시될 수 있습니다.
        백테스트 결과 자체에는 영향이 없습니다.
      </p>
    </div>
  );
};

export default SupplementalStatusNotice;
