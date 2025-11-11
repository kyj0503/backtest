/**
 * 디자인 시스템 토큰
 *
 * 전체 애플리케이션에서 일관된 디자인을 유지하기 위한 스타일 상수
 * Tailwind CSS 클래스 기반
 */

// ============================================
// 카드 및 컨테이너 스타일
// ============================================

/** 표준 카드 (주요 섹션) */
export const CARD_STYLES = {
  base: 'rounded-xl border border-border/40 bg-card p-2 sm:p-6 shadow-sm',
  compact: 'rounded-lg border border-border/40 bg-card p-2 sm:p-4 shadow-sm',
  nested: 'rounded-lg border border-border/30 bg-card/50 p-2 sm:p-4',
} as const;

/** 섹션 컨테이너 */
export const SECTION_STYLES = {
  base: 'space-y-6',
  compact: 'space-y-4',
  grid: 'grid gap-6',
  gridCompact: 'grid gap-4',
} as const;

// ============================================
// 타이포그래피
// ============================================

/** 제목 스타일 */
export const HEADING_STYLES = {
  h1: 'text-2xl font-bold text-foreground',
  h2: 'text-xl font-semibold text-foreground',
  h3: 'text-lg font-semibold text-foreground',
  h4: 'text-base font-semibold text-foreground',
} as const;

/** 본문 텍스트 */
export const TEXT_STYLES = {
  body: 'text-base text-foreground',
  bodySmall: 'text-sm text-foreground',
  caption: 'text-sm text-muted-foreground',
  captionSmall: 'text-xs text-muted-foreground',
  label: 'text-sm font-medium text-foreground',
} as const;

// ============================================
// 간격
// ============================================

/** 섹션 간 간격 */
export const SPACING = {
  section: 'space-y-3 sm:space-y-6',
  sectionCompact: 'space-y-2 sm:space-y-4',
  item: 'space-y-2 sm:space-y-3',
  itemCompact: 'space-y-1 sm:space-y-2',
  gap: 'gap-3 sm:gap-6',
  gapCompact: 'gap-2 sm:gap-4',
  gapSmall: 'gap-1 sm:gap-2',
  /** 버튼/제목과 컨텐츠 사이 간격 */
  contentGap: 'mb-3 sm:mb-6',
  contentGapCompact: 'mb-2 sm:mb-4',
} as const;

// ============================================
// 인터랙티브 요소
// ============================================

/** 버튼 그룹 */
export const BUTTON_GROUP_STYLES = {
  base: 'flex flex-wrap gap-2',
  compact: 'flex flex-wrap gap-1.5',
} as const;

/** 호버 효과 */
export const HOVER_STYLES = {
  card: 'hover:border-border hover:shadow-md transition-all duration-200',
  subtle: 'hover:bg-muted/50 transition-colors',
} as const;

// ============================================
// 차트 컨테이너
// ============================================

/** 차트 래퍼 */
export const CHART_STYLES = {
  container: 'w-full h-[400px]',
  containerTall: 'w-full h-[500px]',
  containerCompact: 'w-full h-[300px]',
} as const;

// ============================================
// 유틸리티 함수
// ============================================

/**
 * 여러 스타일 클래스를 조합
 */
export const combineStyles = (...styles: string[]): string => {
  return styles.filter(Boolean).join(' ');
};

/**
 * 조건부 스타일 적용
 */
export const conditionalStyle = (condition: boolean, trueStyle: string, falseStyle?: string): string => {
  return condition ? trueStyle : (falseStyle || '');
};
