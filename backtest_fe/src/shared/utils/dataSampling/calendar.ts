/**
 * 월간 경계 달력 계산 (dataSampling 내부 모듈)
 *
 * 가격 샘플링(priceSampling)과 수익률 집계(returnAggregation)가 공유하는
 * "N번째 요일" 기반 월 경계 계산이다. 백엔드 DCA/리밸런싱 스케줄러의
 * get_weekday_occurrence / get_nth_weekday_of_month 와 같은 규칙을 따른다.
 * 공개 API가 아니므로 index.ts에서 재export하지 않는다.
 */

/**
 * ISO 날짜 문자열을 로컬 타임존의 Date 객체로 파싱
 *
 * 주의:
 * - new Date("2024-01-15")는 UTC 자정으로 파싱되어 타임존에 따라 요일이 달라질 수 있음
 * - 이 함수는 날짜를 로컬 타임존으로 파싱하여 한국 시간대 사용자에게 일관된 결과 제공
 *
 * @param dateStr ISO 형식 날짜 문자열 (예: "2024-01-15")
 * @returns 로컬 타임존의 Date 객체
 * @throws Error 유효하지 않은 날짜 형식이나 값인 경우
 */
export function parseLocalDate(dateStr: string): Date {
  // YYYY-MM-DD 형식 검증
  const isoDateRegex = /^(\d{4})-(\d{2})-(\d{2})$/;
  const match = isoDateRegex.exec(dateStr);
  
  if (!match) {
    throw new Error(`유효하지 않은 날짜 형식: ${dateStr}. "YYYY-MM-DD" 형식이어야 합니다.`);
  }
  
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  
  // 값 범위 검증
  if (
    isNaN(year) || isNaN(month) || isNaN(day) ||
    month < 1 || month > 12 ||
    day < 1 || day > 31
  ) {
    throw new Error(`유효하지 않은 날짜 값: ${dateStr}`);
  }
  
  const date = new Date(year, month - 1, day); // month는 0-indexed
  
  // NaN timestamp 검증
  if (isNaN(date.getTime())) {
    throw new Error(`유효하지 않은 날짜: ${dateStr}`);
  }
  
  // 입력값과 실제 Date 객체의 값이 일치하는지 확인 (존재하지 않는 날짜 방지)
  // 예: "2024-02-30"은 자동으로 3월로 롤오버되는데, 이를 방지
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    throw new Error(`유효하지 않은 날짜: ${dateStr} (존재하지 않는 날짜)`);
  }
  
  return date;
}

/**
 * 날짜가 해당 월의 몇 번째 요일인지 계산
 * 백엔드의 get_weekday_occurrence 함수와 동일한 로직
 *
 * @param date 확인할 날짜
 * @returns 1-5: 몇 번째 해당 요일인지
 * 
 * @note Weekday 인덱싱 차이:
 * - JavaScript getDay(): 0=일요일, 1=월요일, ..., 6=토요일
 * - Python weekday(): 0=월요일, 1=화요일, ..., 6=일요일
 * - 두 시스템은 독립적으로 같은 날짜의 "N번째 발생"을 계산하므로 결과는 동일
 *   (예: "2024-01-08"은 JS/Python 모두 "1월의 2번째 월요일"로 계산)
 */
export function getWeekdayOccurrence(date: Date): number {
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
export function getNthWeekdayOfMonth(year: number, month: number, weekday: number, n: number): number {
  // 해당 월의 첫날
  const firstDay = new Date(year, month, 1);
  const firstWeekday = firstDay.getDay();

  // 첫 번째 해당 요일까지의 일수
  // (weekday - firstWeekday + 7) % 7 는 백엔드의 (weekday - first_weekday) % 7과 수학적으로 동일
  // +7은 음수 방지용 (JS 모듈로는 음수 결과 가능)
  const daysUntilTarget = (weekday - firstWeekday + 7) % 7;

  // N번째 해당 요일
  let targetDay = 1 + daysUntilTarget + (n - 1) * 7;

  // 월의 마지막 날 확인
  const lastDay = new Date(year, month + 1, 0).getDate();

  // N번째 요일이 월을 벗어나면 마지막 해당 요일 반환
  if (targetDay > lastDay) {
    targetDay = lastDay;
    while (targetDay > 0 && new Date(year, month, targetDay).getDay() !== weekday) {
      targetDay--;
    }
    // 안전장치: 요일을 찾지 못한 경우 (수학적으로 불가능하지만 방어적 프로그래밍)
    if (targetDay === 0) {
      throw new Error(`Unable to find weekday ${weekday} in month ${month + 1}/${year}`);
    }
  }

  return targetDay;
}

/**
 * 다음 Nth Weekday 날짜 계산 (달력 월 기준, 1개월 간격 고정)
 * 
 * @param currentDate 기준 날짜
 * @param originalNth 원본 "몇 번째 요일" 값 (1-5)
 * @returns 다음 달의 같은 N번째 요일 날짜
 * 
 * @note 백엔드 API와의 차이점 (의도된 설계):
 * **Frontend (이 함수):**
 * - 1개월 간격만 지원
 * - 용도: 월별 수익률 집계 (차트 표시용)
 * - 이유: 리밸런싱 주기와 무관하게 월간 집계는 항상 1개월 단위
 * 
 * **Backend (get_next_nth_weekday):**
 * - 가변 interval 지원 (monthly_1, monthly_2, monthly_3 등)
 * - 용도: 리밸런싱/DCA 스케줄링
 * - 시그니처: get_next_nth_weekday(current_date, period_type, interval, original_nth)
 * 
 * **예시:**
 * - 사용자가 monthly_3 (3개월) 리밸런싱 선택 시:
 *   - 백엔드: 3개월마다 리밸런싱 실행
 *   - 프론트엔드: 차트는 여전히 월간 집계로 표시 (더 세밀한 시각화)
 *   - 리밸런싱 마커는 3개월마다 표시됨
 */
export function getNextMonthNthWeekday(currentDate: Date, originalNth: number): Date {
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
