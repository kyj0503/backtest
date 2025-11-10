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
 * 
 * @param startDate 시작 날짜 (문자열 또는 Date 객체)
 * @param endDate 종료 날짜 (문자열 또는 Date 객체)
 * @returns 백테스트 기간 (년 단위)
 * @throws Error 유효하지 않은 날짜 또는 endDate가 startDate보다 작은 경우
 */
function calculateYearDuration(startDate: string | Date, endDate: string | Date): number {
  const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
  const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
  
  // 날짜 유효성 검증
  if (isNaN(start.getTime())) {
    throw new Error(`유효하지 않은 시작 날짜: ${startDate}`);
  }
  if (isNaN(end.getTime())) {
    throw new Error(`유효하지 않은 종료 날짜: ${endDate}`);
  }
  
  const diffMs = end.getTime() - start.getTime();
  
  // 종료 날짜가 시작 날짜보다 작은 경우
  if (diffMs < 0) {
    throw new Error(`종료 날짜가 시작 날짜보다 작을 수 없습니다: ${startDate} ~ ${endDate}`);
  }
  
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays / 365.25; // 윤년 고려
}

/**
 * 가격/가치 데이터를 주간 간격으로 샘플링합니다 (단순 샘플링)
 * 
 * ⚠️ 주의:
 * - 이 함수는 가격/가치/equity 데이터용으로, 매 7번째 항목을 선택합니다 (단순 샘플링)
 * - 수익률 데이터는 이 함수를 사용하지 않습니다 (aggregateReturns() 사용)
 * - 배열 인덱스 기반이므로 실제 달력 주(월~일)와 일치하지 않습니다
 * - 예: 데이터가 수요일에 시작하면 첫 "주간" 포인트는 다음 수요일 데이터입니다
 * 
 * @param data 원본 일간 데이터 (가격, equity, value 등)
 * @returns 매 7번째 데이터 포인트만 포함된 배열
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
 * ISO 날짜 문자열을 로컬 타임존의 Date 객체로 파싱
 *
 * 주의:
 * - new Date("2024-01-15")는 UTC 자정으로 파싱되어 타임존에 따라 요일이 달라질 수 있음
 * - 이 함수는 날짜를 로컬 타임존으로 파싱하여 한국 시간대 사용자에게 일관된 결과 제공
 *
 * @param dateStr ISO 형식 날짜 문자열 (예: "2024-01-15")
 * @returns 로컬 타임존의 Date 객체
 */
function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day); // month는 0-indexed
}

/**
 * 날짜가 해당 월의 몇 번째 요일인지 계산
 * 백엔드의 get_weekday_occurrence 함수와 동일한 로직
 *
 * @param date 확인할 날짜
 * @returns 1-5: 몇 번째 해당 요일인지
 */
function getWeekdayOccurrence(date: Date): number {
  const jsWeekday = date.getDay(); // JavaScript: 0=일요일, 6=토요일
  const year = date.getFullYear();
  const month = date.getMonth();

  let occurrence = 0;
  for (let day = 1; day <= date.getDate(); day++) {
    const checkDate = new Date(year, month, day);
    if (checkDate.getDay() === jsWeekday) {
      occurrence++;
    }
  }

  return occurrence;
}

/**
 * 월의 N번째 특정 요일 날짜 계산
 * 백엔드의 get_nth_weekday_of_month 함수와 동일한 로직
 *
 * @param year 연도
 * @param month 월 (0-11, JavaScript Date 기준)
 * @param weekday 요일 (0=일요일, 6=토요일)
 * @param n 몇 번째 주인지 (1-5)
 * @returns 해당 월의 N번째 요일 날짜 (day)
 */
function getNthWeekdayOfMonth(year: number, month: number, weekday: number, n: number): number {
  // 해당 월의 첫날
  const firstDay = new Date(year, month, 1);
  const firstWeekday = firstDay.getDay();

  // 첫 번째 해당 요일까지의 일수
  const daysUntilTarget = (weekday - firstWeekday + 7) % 7;

  // N번째 해당 요일
  let targetDay = 1 + daysUntilTarget + (n - 1) * 7;

  // 월의 마지막 날 확인
  const lastDay = new Date(year, month + 1, 0).getDate();

  // N번째 요일이 월을 벗어나면 마지막 해당 요일 반환
  if (targetDay > lastDay) {
    targetDay = lastDay;
    while (new Date(year, month, targetDay).getDay() !== weekday) {
      targetDay--;
    }
  }

  return targetDay;
}

/**
 * 다음 Nth Weekday 날짜 계산 (달력 월 기준)
 * 백엔드의 get_next_nth_weekday 함수와 동일한 로직
 *
 * @param currentDate 기준 날짜
 * @param originalNth 원본 "몇 번째 요일" 값 (1-5)
 * @returns 다음 달의 같은 N번째 요일 날짜
 */
function getNextMonthNthWeekday(currentDate: Date, originalNth: number): Date {
  const weekday = currentDate.getDay();

  // 다음 달 계산
  let targetYear = currentDate.getFullYear();
  let targetMonth = currentDate.getMonth() + 1;

  if (targetMonth > 11) {
    targetMonth = 0;
    targetYear++;
  }

  // 원본 N번째 요일 계산 (없으면 자동으로 마지막 해당 요일로 폴백)
  const targetDay = getNthWeekdayOfMonth(targetYear, targetMonth, weekday, originalNth);

  return new Date(targetYear, targetMonth, targetDay);
}

/**
 * 가격/가치 데이터를 월간 간격으로 샘플링합니다 (실제 달력 월 기준)
 *
 * ⚠️ 주의:
 * - 이 함수는 가격/가치/equity 데이터용으로, 실제 달력 월 기준으로 샘플링합니다
 * - 수익률 데이터는 이 함수를 사용하지 않습니다 (aggregateReturns() 사용)
 * - Nth Weekday 방식: 시작일이 1월 10일(2번째 수요일)이면, 다음은 2월의 2번째 수요일
 * - 백엔드의 DCA/리밸런싱 로직과 동일한 방식으로 월 경계를 계산합니다
 *
 * @param data 원본 일간 데이터 (가격, equity, value 등)
 * @returns 실제 달력 월 기준으로 샘플링된 배열
 */
function aggregateToMonthly<T extends { date: string; [key: string]: any }>(data: T[]): T[] {
  if (!data || data.length === 0) return [];

  const monthly: T[] = [];

  // 첫 데이터는 항상 포함
  monthly.push(data[0]);

  // 시작 날짜의 "몇 번째 요일" 계산 (로컬 타임존)
  const startDate = parseLocalDate(data[0].date);
  const originalNth = getWeekdayOccurrence(startDate);

  // 데이터를 Map으로 변환 (O(1) 조회를 위함)
  const dataByDate = new Map<string, T>();
  for (const item of data) {
    dataByDate.set(item.date, item);
  }

  // 다음 월 날짜 계산하며 샘플링
  let currentDate = startDate;
  const lastDateStr = data[data.length - 1].date;
  const lastDate = parseLocalDate(lastDateStr);

  // 무한 루프 방지: 최대 반복 횟수 설정
  const maxIterations = data.length;
  let iterations = 0;

  while (true) {
    // 안전장치: 무한 루프 방지
    if (++iterations > maxIterations) {
      console.error('[dataSampling] Monthly sampling exceeded max iterations');
      break;
    }

    // 다음 달의 Nth Weekday 계산
    const nextDate = getNextMonthNthWeekday(currentDate, originalNth);

    // Map을 사용한 O(1) 조회 (최대 7일 탐색)
    let found = false;
    let searchDate = nextDate;

    for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
      // 로컬 타임존 기준으로 날짜 문자열 생성 (parseLocalDate와 일관성 유지)
      const year = searchDate.getFullYear();
      const month = String(searchDate.getMonth() + 1).padStart(2, '0');
      const day = String(searchDate.getDate()).padStart(2, '0');
      const searchDateStr = `${year}-${month}-${day}`;
      const foundItem = dataByDate.get(searchDateStr);

      if (foundItem) {
        // 마지막 항목과 날짜로 비교하여 중복 방지
        const lastItem = monthly[monthly.length - 1];
        if (lastItem?.date !== foundItem.date) {
          monthly.push(foundItem);
        }
        found = true;
        currentDate = parseLocalDate(foundItem.date);
        break;
      }

      // 다음 날짜로 이동 (1일 증가)
      searchDate = new Date(searchDate.getTime() + 24 * 60 * 60 * 1000);
    }

    // 더 이상 데이터가 없으면 종료
    if (!found) break;

    // 마지막 데이터에 도달했으면 종료
    if (currentDate >= lastDate) break;
  }

  // 마지막 데이터가 포함되지 않았다면 추가
  const lastItem = data[data.length - 1];
  if (monthly[monthly.length - 1] !== lastItem) {
    monthly.push(lastItem);
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

  // 1일 미만: 원본 데이터 반환 (다운스트림 처리 안전성)
  if (yearDuration < (2 / 365.25)) {
    return {
      data,
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
 * @param aggregationType 'daily' | 'weekly' | 'monthly'
 * @returns 집계된 수익률 데이터
 */
export function aggregateReturns<T extends { date: string; return_pct: number; [key: string]: any }>(
  dailyReturns: T[],
  aggregationType: 'daily' | 'weekly' | 'monthly'
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  // 명시적으로 daily 처리 (타입 안정성 향상)
  if (aggregationType === 'daily') return dailyReturns;
  if (aggregationType === 'weekly') return aggregateWeeklyReturns(dailyReturns);
  if (aggregationType === 'monthly') return aggregateMonthlyReturns(dailyReturns);

  return dailyReturns;
}

/**
 * 주간 수익률 계산 (7일 단위, 복리 기반)
 * 
 * ⚠️ 주의: 배열 인덱스 기반 집계로, 실제 달력 주 경계와 일치하지 않을 수 있습니다.
 * - 데이터가 월요일이 아닌 날짜에 시작하면 첫 주는 7일 미만일 수 있습니다.
 * - 금융 백테스트에서 주간 리밸런싱 등의 경우 실제 주 경계(월~일)와 다를 수 있습니다.
 * - 매 7번째 항목마다 집계되므로 중간에 거래일이 없는 날이 있어도 카운트됩니다.
 * 
 * @param dailyReturns 일간 수익률 배열
 * @returns 7일 단위로 집계된 복리 수익률
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
 * 월간 수익률 계산 (실제 달력 월 기준, 복리 기반)
 *
 * ⚠️ 주의: 실제 달력 월 경계로 집계됩니다.
 * - Nth Weekday 방식: 시작일이 1월 10일(2번째 수요일)이면, 2월의 2번째 수요일까지가 한 달
 * - 백엔드의 DCA/리밸런싱 로직과 동일한 방식으로 월 경계를 계산합니다
 * - 복리 수익률: (1 + r1) * (1 + r2) * ... - 1
 *
 * @param dailyReturns 일간 수익률 배열
 * @returns 실제 달력 월 단위로 집계된 복리 수익률
 */
function aggregateMonthlyReturns<T extends { date: string; return_pct: number; [key: string]: any }>(
  dailyReturns: T[]
): T[] {
  if (!dailyReturns || dailyReturns.length === 0) return [];

  const monthly: T[] = [];

  // 시작 날짜의 "몇 번째 요일" 계산 (로컬 타임존)
  const startDate = parseLocalDate(dailyReturns[0].date);
  const originalNth = getWeekdayOccurrence(startDate);

  let currentMonthData: T[] = [];
  let currentMonthEndDate = getNextMonthNthWeekday(startDate, originalNth);

  for (let i = 0; i < dailyReturns.length; i++) {
    const item = dailyReturns[i];
    const itemDate = parseLocalDate(item.date);

    // 다음 달 경계를 넘었거나 마지막 데이터일 때
    const isLastItem = i === dailyReturns.length - 1;
    const crossedMonthBoundary = itemDate >= currentMonthEndDate;

    if (crossedMonthBoundary || isLastItem) {
      // 여러 달을 건너뛴 경우 처리
      while (itemDate >= currentMonthEndDate && !isLastItem) {
        if (currentMonthData.length > 0) {
          // 현재 달 데이터 마감
          const monthlyReturn = calculateCompoundReturn(currentMonthData);
          const lastDay = currentMonthData[currentMonthData.length - 1];
          monthly.push({
            ...lastDay,
            return_pct: monthlyReturn,
          });
          currentMonthData = [];
        }
        
        // 다음 달 경계로 이동
        currentMonthEndDate = getNextMonthNthWeekday(currentMonthEndDate, originalNth);
        
        // 현재 아이템이 새로운 경계 내에 있으면 추가하고 종료
        if (itemDate < currentMonthEndDate) {
          currentMonthData.push(item);
          break;
        }
      }
      
      // 마지막 아이템 처리
      if (isLastItem) {
        currentMonthData.push(item);
        if (currentMonthData.length > 0) {
          const monthlyReturn = calculateCompoundReturn(currentMonthData);
          const lastDay = currentMonthData[currentMonthData.length - 1];
          monthly.push({
            ...lastDay,
            return_pct: monthlyReturn,
          });
        }
      }
    } else {
      // 경계를 넘지 않은 경우 현재 달 데이터에 추가
      currentMonthData.push(item);
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

