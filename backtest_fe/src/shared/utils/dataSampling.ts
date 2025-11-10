/**
 * 데이터 샘플링 유틸리티
 * 
 * **역할**:
 * - 대량의 차트 데이터 포인트를 성능 최적화를 위해 샘플링
 * - 백테스트 기간에 따라 적절한 시간 단위로 집계
 * - 시각적 품질을 유지하면서 렌더링 부하 감소
 * 
 * **전략**:
 * - 1일: 오류 (최소 2일 이상 필요)
 * - 2일 ~ 2년: 일간 데이터 (원본 그대로)
 * - 2년 초과 ~ 5년: 주간 데이터
 * - 5년 초과 ~ 10년: 월간 데이터
 * - 10년 초과: 월간 데이터 + 경고
 */

/**
 * 백테스트 기간 계산 (년 단위)
 */
function calculateYearDuration(startDate: string | Date, endDate: string | Date): number {
  const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
  const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
  const diffMs = end.getTime() - start.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays / 365.25; // 윤년 고려
}

/**
 * 주간 데이터로 집계 (7일 = 1주 단위)
 * 
 * @param data 원본 일간 데이터
 * @returns 주간으로 집계된 데이터 (매 7일째 데이터 포인트)
 */
function aggregateToWeekly<T extends { date: string; [key: string]: any }>(data: T[]): T[] {
  if (!data || data.length === 0) return [];

  const weekly: T[] = [];
  const DAYS_PER_WEEK = 7;
  
  // 첫 데이터는 항상 포함
  weekly.push(data[0]);
  
  // 7일 간격으로 데이터 추출
  for (let i = DAYS_PER_WEEK; i < data.length; i += DAYS_PER_WEEK) {
    weekly.push(data[i]);
  }
  
  // 마지막 데이터가 7일 간격에 포함되지 않았다면 추가
  const lastIndex = data.length - 1;
  if (lastIndex > 0 && data[lastIndex] !== weekly[weekly.length - 1]) {
    weekly.push(data[lastIndex]);
  }

  return weekly;
}

/**
 * 월간 데이터로 집계 (28일 = 4주 단위)
 * 
 * @param data 원본 일간 데이터
 * @returns 월간으로 집계된 데이터 (매 28일째 데이터 포인트)
 */
function aggregateToMonthly<T extends { date: string; [key: string]: any }>(data: T[]): T[] {
  if (!data || data.length === 0) return [];

  const monthly: T[] = [];
  const DAYS_PER_MONTH = 28; // 4주 = 28일
  
  // 첫 데이터는 항상 포함
  monthly.push(data[0]);
  
  // 28일 간격으로 데이터 추출
  for (let i = DAYS_PER_MONTH; i < data.length; i += DAYS_PER_MONTH) {
    monthly.push(data[i]);
  }
  
  // 마지막 데이터가 28일 간격에 포함되지 않았다면 추가
  const lastIndex = data.length - 1;
  if (lastIndex > 0 && data[lastIndex] !== monthly[monthly.length - 1]) {
    monthly.push(data[lastIndex]);
  }

  return monthly;
}

/**
 * 백테스트 기간에 따른 스마트 샘플링
 * 
 * @param data 원본 데이터 (date 필드 필수)
 * @param startDate 백테스트 시작일
 * @param endDate 백테스트 종료일
 * @returns 집계된 데이터 및 메타 정보
 */
export function smartSampleByPeriod<T extends { date: string; [key: string]: any }>(
  data: T[],
  startDate?: string | Date,
  endDate?: string | Date
): {
  data: T[];
  aggregationType: 'daily' | 'weekly' | 'monthly';
  warning?: string;
} {
  if (!data || data.length === 0) {
    return { data: [], aggregationType: 'daily' };
  }

  // 날짜 정보가 없으면 원본 반환
  if (!startDate || !endDate) {
    return { data, aggregationType: 'daily' };
  }

  const yearDuration = calculateYearDuration(startDate, endDate);

  // 1일 미만: 오류 (호출자가 처리해야 함)
  if (yearDuration < (2 / 365.25)) {
    return {
      data: [],
      aggregationType: 'daily',
      warning: '백테스트 기간은 최소 2일 이상이어야 합니다.',
    };
  }

  // 2일 ~ 2년: 일간 데이터 (원본 그대로)
  if (yearDuration <= 2) {
    return { data, aggregationType: 'daily' };
  }

  // 2년 초과 ~ 5년: 주간 데이터
  if (yearDuration <= 5) {
    return {
      data: aggregateToWeekly(data),
      aggregationType: 'weekly',
    };
  }

  // 5년 초과: 월간 데이터
  const warning = yearDuration > 10 ? '10년 초과 백테스트는 월간 데이터로 표시됩니다.' : undefined;
  
  return {
    data: aggregateToMonthly(data),
    aggregationType: 'monthly',
    warning,
  };
}

/**
 * 균등 샘플링 - 일정 간격으로 데이터 포인트 추출
 * 
 * @deprecated 대신 smartSampleByPeriod 사용 권장
 * 
 * @param data 원본 데이터 배열
 * @param maxPoints 최대 포인트 수 (기본: 500)
 * @returns 샘플링된 데이터 배열
 */
export function sampleData<T>(data: T[], maxPoints: number = 500): T[] {
  if (!data || data.length === 0) {
    return [];
  }

  // 데이터가 이미 충분히 작으면 그대로 반환
  if (data.length <= maxPoints) {
    return data;
  }

  const step = Math.ceil(data.length / maxPoints);
  const sampled: T[] = [];

  // 첫 번째 포인트는 항상 포함
  sampled.push(data[0]);

  // 균등 간격으로 샘플링
  for (let i = step; i < data.length - 1; i += step) {
    sampled.push(data[i]);
  }

  // 마지막 포인트는 항상 포함 (종료 값 보존)
  if (data.length > 1) {
    sampled.push(data[data.length - 1]);
  }

  return sampled;
}

/**
 * 적응형 샘플링 - 변화가 큰 구간은 더 많은 포인트 유지
 * 
 * @param data 원본 데이터 배열
 * @param maxPoints 최대 포인트 수 (기본: 500)
 * @param valueKey 비교할 값의 키 (예: 'value', 'close')
 * @returns 샘플링된 데이터 배열
 */
export function adaptiveSampleData<T>(
  data: T[],
  maxPoints: number = 500,
  valueKey: keyof T = 'value' as keyof T
): T[] {
  if (!data || data.length === 0) {
    return [];
  }

  if (data.length <= maxPoints) {
    return data;
  }

  const sampled: T[] = [data[0]]; // 첫 포인트
  const threshold = calculateThreshold(data, valueKey);

  let lastAddedIndex = 0;

  for (let i = 1; i < data.length - 1; i++) {
    const currentValue = data[i][valueKey] as number;
    const lastValue = data[lastAddedIndex][valueKey] as number;

    // 변화가 임계값보다 크면 포인트 추가
    if (Math.abs(currentValue - lastValue) > threshold) {
      sampled.push(data[i]);
      lastAddedIndex = i;
    }

    // 최대 포인트 수에 도달하면 중단
    if (sampled.length >= maxPoints - 1) {
      break;
    }
  }

  // 마지막 포인트 추가
  sampled.push(data[data.length - 1]);

  // 여전히 포인트가 부족하면 균등 샘플링으로 보완
  if (sampled.length < maxPoints * 0.5) {
    return sampleData(data, maxPoints);
  }

  return sampled;
}

/**
 * 변화 임계값 계산 (표준편차 기반)
 */
function calculateThreshold<T>(data: T[], valueKey: keyof T): number {
  const values = data.map((d) => d[valueKey] as number).filter((v) => !isNaN(v));

  if (values.length === 0) return 0;

  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);

  return stdDev * 0.5; // 0.5 표준편차를 임계값으로 사용
}

/**
 * 리밸런싱 마커 필터링 - 화면에 보이는 마커만 유지
 * 
 * @param markers 리밸런싱 마커 배열
 * @param maxMarkers 최대 마커 수 (기본: 20)
 * @returns 필터링된 마커 배열
 */
export function filterRebalanceMarkers<T extends { date?: string; timestamp?: string }>(
  markers: T[],
  maxMarkers: number = 20
): T[] {
  if (!markers || markers.length <= maxMarkers) {
    return markers;
  }

  // 최신 마커를 우선적으로 유지
  return markers.slice(-maxMarkers);
}

/**
 * 일간 수익률을 주간/월간 수익률로 변환
 * 
 * @param dailyReturns 일간 수익률 데이터 { date: string, return_pct: number }
 * @param aggregationType 'weekly' | 'monthly'
 * @returns 집계된 수익률 데이터
 */
export function aggregateReturns<T extends { date: string; return_pct: number; [key: string]: any }>(
  dailyReturns: T[],
  aggregationType: 'weekly' | 'monthly'
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];
  if (aggregationType === 'weekly') return aggregateWeeklyReturns(dailyReturns);
  if (aggregationType === 'monthly') return aggregateMonthlyReturns(dailyReturns);
  return dailyReturns;
}

/**
 * 주간 수익률 계산 (7일 단위, 복리 기반)
 */
function aggregateWeeklyReturns<T extends { date: string; return_pct: number; [key: string]: any }>(
  dailyReturns: T[]
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  const weekly: T[] = [];
  const DAYS_PER_WEEK = 7;
  let currentWeekData: T[] = [];

  for (let i = 0; i < dailyReturns.length; i++) {
    currentWeekData.push(dailyReturns[i]);

    // 7일마다 또는 마지막 데이터일 때 주간 수익률 계산
    if ((i + 1) % DAYS_PER_WEEK === 0 || i === dailyReturns.length - 1) {
      if (currentWeekData.length > 0) {
        const weeklyReturn = calculateCompoundReturn(currentWeekData);
        const lastDay = currentWeekData[currentWeekData.length - 1];
        weekly.push({
          ...lastDay,
          return_pct: weeklyReturn,
        });
        currentWeekData = [];
      }
    }
  }

  return weekly;
}

/**
 * 월간 수익률 계산 (28일 = 4주 단위, 복리 기반)
 */
function aggregateMonthlyReturns<T extends { date: string; return_pct: number; [key: string]: any }>(
  dailyReturns: T[]
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  const monthly: T[] = [];
  const DAYS_PER_MONTH = 28; // 4주
  let currentMonthData: T[] = [];

  for (let i = 0; i < dailyReturns.length; i++) {
    currentMonthData.push(dailyReturns[i]);

    // 28일마다 또는 마지막 데이터일 때 월간 수익률 계산
    if ((i + 1) % DAYS_PER_MONTH === 0 || i === dailyReturns.length - 1) {
      if (currentMonthData.length > 0) {
        const monthlyReturn = calculateCompoundReturn(currentMonthData);
        const lastDay = currentMonthData[currentMonthData.length - 1];
        monthly.push({
          ...lastDay,
          return_pct: monthlyReturn,
        });
        currentMonthData = [];
      }
    }
  }

  return monthly;
}

/**
 * 복리 수익률 계산
 * 
 * @param returns 일간 수익률 배열
 * @returns 누적 복리 수익률 (백분율)
 */
function calculateCompoundReturn<T extends { return_pct: number }>(returns: T[]): number {
  if (returns.length === 0) return 0;

  // 복리 공식: (1 + r1) * (1 + r2) * ... - 1
  let compoundedValue = 1;
  for (const item of returns) {
    const dailyReturn = item.return_pct / 100; // 백분율 → 소수
    compoundedValue *= (1 + dailyReturn);
  }

  return (compoundedValue - 1) * 100; // 소수 → 백분율
}

