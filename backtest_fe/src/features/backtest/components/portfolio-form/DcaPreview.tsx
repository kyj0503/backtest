import React from 'react';
import { Stock } from '../../model/types/backtest-form-types';
import { DCA_FREQUENCY_OPTIONS } from '../../model/strategyConfig';
import { TEXT_STYLES } from '@/shared/styles/design-tokens';
import { calculateDcaPeriods } from '../../utils/calculateDcaPeriods';

interface DcaPreviewProps {
  stock: Stock;
  startDate?: string;
  endDate?: string;
}

export const DcaPreview: React.FC<DcaPreviewProps> = ({ stock, startDate, endDate }) => {
  const periodAmount = stock.amount || 0;
  const frequencyLabel = DCA_FREQUENCY_OPTIONS.find(opt => opt.value === stock.dcaFrequency)?.label || '';

  let dcaPeriods = 1;
  let totalAmount = periodAmount;

  if (startDate && endDate) {
    dcaPeriods = calculateDcaPeriods(startDate, endDate, stock.dcaFrequency || 'monthly_1');
    totalAmount = periodAmount * dcaPeriods;
  }

  return (
    <p className={`${TEXT_STYLES.captionSmall} mt-1`}>
      {frequencyLabel}: 총 {dcaPeriods}회, 회당 ${periodAmount.toLocaleString()} (총 ${totalAmount.toLocaleString()})
    </p>
  );
};
