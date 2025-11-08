/**
 * 백테스트 경고 메시지 배너 컴포넌트
 * 
 * **역할**:
 * - 상장일 등의 경고 메시지를 사용자에게 표시
 * - 백테스트 결과 상단에 눈에 띄게 배치
 */
import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { CARD_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';

interface WarningBannerProps {
  warnings: string[];
}

const WarningBanner: React.FC<WarningBannerProps> = ({ warnings }) => {
  if (!warnings || warnings.length === 0) {
    return null;
  }

  return (
    <div className={`${CARD_STYLES.base} bg-yellow-50 border-l-4 border-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-600`}>
      <div className={`flex ${SPACING.contentGap}`}>
        <div className="flex-shrink-0">
          <AlertTriangle className="h-5 w-5 text-yellow-400 dark:text-yellow-500" />
        </div>
        <div className="flex-1">
          <h3 className={`${TEXT_STYLES.body} font-semibold text-yellow-800 dark:text-yellow-300 mb-2`}>
            주의사항
          </h3>
          <div className="space-y-1">
            {warnings.map((warning, index) => (
              <p key={index} className={`${TEXT_STYLES.caption} text-yellow-700 dark:text-yellow-400`}>
                • {warning}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WarningBanner;
