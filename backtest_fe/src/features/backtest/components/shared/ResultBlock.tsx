/**
 * ResultBlock 컴포넌트
 * 차트 결과를 감싸는 공통 카드 레이아웃
 */

import React from 'react';
import { CARD_STYLES, HEADING_STYLES, TEXT_STYLES, SPACING } from '@/shared/styles/design-tokens';

export interface ResultBlockProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

export const ResultBlock: React.FC<ResultBlockProps> = ({
  title,
  description,
  actions,
  children
}) => (
  <div className={CARD_STYLES.base}>
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div className={SPACING.itemCompact}>
        <h3 className={HEADING_STYLES.h3}>{title}</h3>
        {description ? <p className={TEXT_STYLES.caption}>{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
    <div className="mt-4">{children}</div>
  </div>
);
