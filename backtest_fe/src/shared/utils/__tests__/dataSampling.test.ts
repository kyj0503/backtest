/**
 * dataSampling 단위 테스트 (P2-35).
 *
 * src에서 가장 큰 파일(736줄)이자 차트 데이터 파이프라인의 핵심이지만
 * 지금까지 커버리지가 0%였다. useChartData.ts가 실제로 쓰는 두 함수
 * (smartSampleByPeriod, aggregateReturns)를 중심으로 검증하고, 나머지
 * export(sampleData, adaptiveSampleData, filterRebalanceMarkers)도
 * 기본 계약을 확인한다.
 *
 * 가장 날카로운 테스트는 aggregateReturns의 월간 집계다: 한 달의 수익률
 * 버킷에 심어둔 "튀는 값"이 인접한 달의 버킷으로 새어 들어가지 않는지
 * (날짜 경계 계산이 정확한지) 직접 확인한다 -- 이런 종류의 날짜 경계
 * 오류가 바로 이번 감사가 찾아낸 "잘못된 날짜에 값이 새는" 버그 계열이다.
 */
import { describe, it, expect, vi } from 'vitest';
import {
  smartSampleByPeriod,
  sampleData,
  adaptiveSampleData,
  filterRebalanceMarkers,
  aggregateReturns,
} from '../dataSampling';

type DatedPoint = { date: string; value: number };
type ReturnPoint = { date: string; return_pct: number };

/** start부터 n일치 연속된 날짜 문자열(YYYY-MM-DD)을 만든다 (로컬 자정 기준). */
function sequentialDates(start: string, n: number): string[] {
  const parts = start.split('-').map(Number);
  const y = parts[0]!, m = parts[1]!, d = parts[2]!;
  const base = new Date(y, m - 1, d);
  return Array.from({ length: n }, (_, i) => {
    const dt = new Date(base.getFullYear(), base.getMonth(), base.getDate() + i);
    return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
  });
}

describe('smartSampleByPeriod', () => {
  it('returns an empty daily result for empty input', () => {
    expect(smartSampleByPeriod([], '2024-01-01', '2024-01-05')).toEqual({
      data: [], aggregationType: 'daily',
    });
  });

  it('returns data unchanged when startDate/endDate are omitted', () => {
    const data: DatedPoint[] = [{ date: '2024-01-01', value: 1 }];
    expect(smartSampleByPeriod(data)).toEqual({ data, aggregationType: 'daily' });
  });

  it('warns and returns raw data for a span under 2 days', () => {
    const data: DatedPoint[] = [{ date: '2024-01-01', value: 1 }];
    const result = smartSampleByPeriod(data, '2024-01-01', '2024-01-01');

    expect(result.aggregationType).toBe('daily');
    expect(result.data).toBe(data);
    expect(result.warning).toMatch(/2일 이상/);
  });

  it('does not warn for a span of exactly 2 days', () => {
    const data: DatedPoint[] = [{ date: '2024-01-01', value: 1 }];
    const result = smartSampleByPeriod(data, '2024-01-01', '2024-01-03');

    expect(result.aggregationType).toBe('daily');
    expect(result.warning).toBeUndefined();
  });

  it('throws for an invalid date string', () => {
    expect(() => smartSampleByPeriod([{ date: '2024-01-01', value: 1 }], 'not-a-date', '2024-01-05'))
      .toThrow();
  });

  it('throws when endDate precedes startDate', () => {
    expect(() => smartSampleByPeriod([{ date: '2024-01-01', value: 1 }], '2024-01-05', '2024-01-01'))
      .toThrow();
  });

  it('samples every 7th index for a multi-year span (weekly bucket), keeping first/last', () => {
    // yearDuration은 오직 startDate/endDate로만 결정되므로(계산 함수가 data를
    // 참조하지 않음), data 자체는 10개짜리 작은 배열로도 정확한 버킷 분기를
    // 확정적으로 트리거할 수 있다.
    const dates = sequentialDates('2024-01-01', 10);
    const data: DatedPoint[] = dates.map((date, i) => ({ date, value: i }));

    const result = smartSampleByPeriod(data, '2020-01-01', '2023-06-01'); // ~3.4년 -> weekly

    expect(result.aggregationType).toBe('weekly');
    // 손으로 계산: index 0(첫 항목 고정) -> 7(7 간격) -> 마지막 항목(9)이
    // 7의 배수 위치가 아니므로 별도로 추가됨.
    expect(result.data.map((d) => d.date)).toEqual([dates[0], dates[7], dates[9]]);
  });

  it('samples on real calendar-month Nth-weekday boundaries for a 5-10 year span (monthly bucket)', () => {
    // 2024-01-01(월요일, 1월의 첫 번째 월요일)부터 2024-04-10까지 매일
    // 데이터가 존재한다. 각 달의 "첫 번째 월요일"은 파이썬 datetime으로
    // 사전에 확인한 값: 2/5, 3/4, 4/1.
    const dates = sequentialDates('2024-01-01', 101); // 2024-01-01 ~ 2024-04-10
    const data: DatedPoint[] = dates.map((date, i) => ({ date, value: i }));

    const result = smartSampleByPeriod(data, '2018-01-01', '2024-04-10'); // ~6.3년 -> monthly

    expect(result.aggregationType).toBe('monthly');
    expect(result.data.map((d) => d.date)).toEqual([
      '2024-01-01', '2024-02-05', '2024-03-04', '2024-04-01', '2024-04-10',
    ]);
  });

  it('warns for spans over 10 years but still aggregates monthly', () => {
    const dates = sequentialDates('2024-01-01', 5);
    const data: DatedPoint[] = dates.map((date, i) => ({ date, value: i }));

    const result = smartSampleByPeriod(data, '2010-01-01', '2024-01-01'); // 14년

    expect(result.aggregationType).toBe('monthly');
    expect(result.warning).toMatch(/10년 초과/);
  });

  it('reduces point count while preserving first/last on a genuinely large series', () => {
    const dates = sequentialDates('2015-01-01', 1500); // ~4.1년치 일간 데이터
    const data: DatedPoint[] = dates.map((date, i) => ({ date, value: i }));

    const result = smartSampleByPeriod(data, dates[0]!, dates[dates.length - 1]!); // weekly bucket

    expect(result.aggregationType).toBe('weekly');
    expect(result.data.length).toBeLessThan(data.length);
    expect(result.data[0]?.date).toBe(dates[0]);
    expect(result.data[result.data.length - 1]?.date).toBe(dates[dates.length - 1]);
  });

  it('treats "first"/"last" as array position, not chronological order, for unsorted input', () => {
    // 인덱스 기반 샘플링이므로, 정렬되지 않은 입력을 주면 "첫/마지막 보존"은
    // 배열상의 위치를 의미하지 -- 실제 날짜순 최초/최후를 의미하지 않는다.
    // 아래 예시에서는 실제로 가장 이른 날짜(1월)가 중간에 있고 결과에서
    // 통째로 빠진다.
    const data: DatedPoint[] = [
      { date: '2024-06-01', value: 1 }, // 배열상 첫 항목이지만 날짜순으로는 아님
      { date: '2024-01-01', value: 2 }, // 실제로 가장 이른 날짜, 배열 중간
      { date: '2024-03-01', value: 3 },
    ];

    const result = smartSampleByPeriod(data, '2020-01-01', '2023-06-01'); // weekly bucket

    expect(result.data.map((d) => d.date)).toEqual(['2024-06-01', '2024-03-01']);
    expect(result.data.map((d) => d.date)).not.toContain('2024-01-01');
  });
});

describe('aggregateReturns', () => {
  it('returns an empty array for empty input', () => {
    expect(aggregateReturns([], 'weekly')).toEqual([]);
  });

  it('passes daily input through unchanged', () => {
    const data: ReturnPoint[] = [{ date: '2024-01-01', return_pct: 1.5 }];
    expect(aggregateReturns(data, 'daily')).toBe(data);
  });

  it('compounds a short (<7 day) series into a single weekly bucket, hand-derived', () => {
    // (1.10) * (0.95) * (1.02) - 1 = 0.065899999999999985 -> *100
    const data: ReturnPoint[] = [
      { date: '2024-01-01', return_pct: 10 },
      { date: '2024-01-02', return_pct: -5 },
      { date: '2024-01-03', return_pct: 2 },
    ];

    const result = aggregateReturns(data, 'weekly');

    expect(result).toHaveLength(1);
    expect(result[0]?.date).toBe('2024-01-03'); // 마지막 항목의 날짜로 태그됨
    expect(result[0]?.return_pct).toBeCloseTo(6.59, 9);
  });

  it('splits a 10-day series into two weekly buckets (7 + 3) with correct date tags', () => {
    const dates = sequentialDates('2024-01-01', 10);
    const data: ReturnPoint[] = dates.map((date) => ({ date, return_pct: 0 }));

    const result = aggregateReturns(data, 'weekly');

    expect(result.map((r) => r.date)).toEqual([dates[6], dates[9]]);
  });

  it('closes each monthly bucket the day before the next Nth-weekday boundary, hand-derived dates', () => {
    // 월간 경계(각 달의 "첫 번째 월요일"): 2/5, 3/4, 4/1, (다음 경계는 데이터
    // 범위를 벗어나는 5/6). 수익률 집계 버킷은 "경계 하루 전"에 마감되므로
    // (가격 샘플링과 달리) 날짜 태그가 2/4, 3/3, 3/31이 되고, 마지막
    // 버킷은 데이터의 마지막 날(4/10)에 마감된다.
    const dates = sequentialDates('2024-01-01', 101); // 2024-01-01 ~ 2024-04-10
    const data: ReturnPoint[] = dates.map((date) => ({ date, return_pct: 0 }));

    const result = aggregateReturns(data, 'monthly');

    expect(result.map((r) => r.date)).toEqual(['2024-02-04', '2024-03-03', '2024-03-31', '2024-04-10']);
    expect(result.every((r) => r.return_pct === 0)).toBe(true);
  });

  it('does not leak a single-day spike into the adjacent month bucket', () => {
    // 1/15(첫 번째 버킷, 1/1~2/4 구간 내부)에만 +10%를 심고 나머지는 전부
    // 0%로 둔다. 올바른 날짜 경계 계산이라면 그 +10%는 오직 1/1~2/4를
    // 대표하는 첫 버킷(2/4로 태그됨)에만 복리로 반영되고, 이후 버킷들은
    // 정확히 0%를 유지해야 한다 (잘못된 경계라면 인접 달로 "샌다").
    const dates = sequentialDates('2024-01-01', 101);
    const data: ReturnPoint[] = dates.map((date) => ({
      date, return_pct: date === '2024-01-15' ? 10 : 0,
    }));

    const result = aggregateReturns(data, 'monthly');

    expect(result.map((r) => r.date)).toEqual(['2024-02-04', '2024-03-03', '2024-03-31', '2024-04-10']);
    expect(result[0]?.return_pct).toBeCloseTo(10, 9); // 1.10 * 1^34 - 1 = 10%
    expect(result[1]?.return_pct).toBe(0); // 인접 버킷으로 새지 않음
    expect(result[2]?.return_pct).toBe(0);
    expect(result[3]?.return_pct).toBe(0);
  });
});

describe('sampleData (deprecated equal-interval sampler)', () => {
  it('returns data unchanged when already within maxPoints', () => {
    const data = [1, 2, 3];
    expect(sampleData(data, 10)).toEqual(data);
  });

  it('reduces a large series while preserving the first and last element', () => {
    // 값은 의도적으로 1부터 시작한다 (0이 아님): sampleData의 `if (firstItem)`은
    // truthy 체크라서 data[0]가 falsy 값(0, '', false 등)이면 "항상 첫
    // 포인트 포함"이 조용히 깨진다 -- 발견했지만 sampleData/adaptiveSampleData는
    // 현재 어디서도 호출되지 않는 사실상 죽은 코드(smartSampleByPeriod로
    // 대체된 @deprecated 함수)라 프로덕션 코드는 수정하지 않았다. 여기서는
    // 그 함정을 피해 이 함수의 핵심 계약(개수 축소 + 양끝 보존)만 검증한다.
    const data = Array.from({ length: 1000 }, (_, i) => i + 1);
    const result = sampleData(data, 50);

    expect(result.length).toBeLessThan(data.length);
    expect(result[0]).toBe(1);
    expect(result[result.length - 1]).toBe(1000);
  });
});

describe('adaptiveSampleData', () => {
  it('returns data unchanged when already within maxPoints', () => {
    const data = [{ value: 1 }, { value: 2 }];
    expect(adaptiveSampleData(data, 10)).toEqual(data);
  });

  it('reduces point count while preserving a large mid-series spike and the endpoints', () => {
    // 대부분 평탄(100)하다가 중앙에서 한 번 크게 튀는(10000) 시계열.
    const n = 500;
    const data = Array.from({ length: n }, (_, i) => ({
      value: i === Math.floor(n / 2) ? 10000 : 100,
    }));

    const result = adaptiveSampleData(data, 100, 'value');

    expect(result.length).toBeLessThan(data.length);
    expect(result[0]).toEqual(data[0]);
    expect(result[result.length - 1]).toEqual(data[data.length - 1]);
    expect(result.some((d) => d.value === 10000)).toBe(true);
  });
});

describe('filterRebalanceMarkers', () => {
  it('returns markers unchanged when within maxMarkers', () => {
    const markers = [{ date: '2024-01-01' }, { date: '2024-02-01' }];
    expect(filterRebalanceMarkers(markers, 5)).toBe(markers);
  });

  it('keeps only the most recent maxMarkers entries when over the limit', () => {
    const markers = [
      { date: '2024-01-01' }, { date: '2024-02-01' }, { date: '2024-03-01' },
      { date: '2024-04-01' }, { date: '2024-05-01' },
    ];

    const result = filterRebalanceMarkers(markers, 2);

    expect(result.map((m) => m.date)).toEqual(['2024-04-01', '2024-05-01']);
  });
});

/**
 * 특성화 테스트 (A-16).
 *
 * dataSampling.ts를 책임 단위 모듈로 쪼개기 전에, 기존 테스트가 닿지 않던
 * 분기(월간 샘플링의 N번째 요일 폴백/연도 경계/휴장일 탐색, 입력 날짜 검증,
 * 기간 경계값, 월간 수익률 집계의 공백 구간 처리, 적응형 샘플링의 비폴백
 * 경로)의 "현재" 동작을 그대로 고정한다. 일부는 명세라기보다 현재 구현의
 * 부산물이며(예: 휴장일로 밀린 뒤 요일이 바뀌는 현상, 60개월 넘는 공백에서
 * 포인트가 빠지는 현상) 그런 경우 테스트 이름과 주석에 그렇게 적었다.
 * 분리 작업은 이 동작을 바꾸지 않아야 한다.
 */
describe('characterization: monthly price sampling calendar edge cases', () => {
  const MONTHLY_START = '2015-01-01';
  const MONTHLY_END = '2021-01-01'; // ~6년 -> monthly 버킷

  function monthlyDates(dates: string[]): string[] {
    return smartSampleByPeriod(dates.map((date) => ({ date })), MONTHLY_START, MONTHLY_END)
      .data.map((d) => d.date);
  }

  it('falls back to the last matching weekday when the Nth weekday does not exist in the next month', () => {
    // 2024-01-29는 1월의 5번째 월요일. 2월·3월에는 5번째 월요일이 없으므로
    // 각 달의 마지막 월요일(2/26, 3/25)로 폴백하고, 4월은 5번째 월요일(4/29)이 있다.
    const dates = sequentialDates('2024-01-29', 93); // ~ 2024-04-30

    expect(monthlyDates(dates)).toEqual([
      '2024-01-29', '2024-02-26', '2024-03-25', '2024-04-29', '2024-04-30',
    ]);
  });

  it('rolls over December into January of the next year', () => {
    // 2023-11-01은 11월의 첫 번째 수요일 -> 12/6, 1/3, 2/7(각 달 첫 번째 수요일).
    const dates = sequentialDates('2023-11-01', 107); // ~ 2024-02-15

    expect(monthlyDates(dates)).toEqual([
      '2023-11-01', '2023-12-06', '2024-01-03', '2024-02-07', '2024-02-15',
    ]);
  });

  it('skips weekends while still landing on each month\'s Nth weekday', () => {
    const weekdaysOnly = sequentialDates('2024-01-01', 100).filter((d) => {
      const [y, m, day] = d.split('-').map(Number) as [number, number, number];
      const w = new Date(y, m - 1, day).getDay();
      return w !== 0 && w !== 6;
    });

    expect(monthlyDates(weekdaysOnly)).toEqual([
      '2024-01-01', '2024-02-05', '2024-03-04', '2024-04-01', '2024-04-09',
    ]);
  });

  it('moves forward to the next available day when the target is missing (current behavior: the weekday then drifts)', () => {
    // 2/5(첫 번째 월요일)를 빼면 다음 날 2/6(화)을 쓴다. 이후 경계 계산은
    // "현재 날짜의 요일"을 기준으로 하므로 3월부터는 첫 번째 화요일(3/5, 4/2)이 된다.
    // 명세라기보다 현재 구현의 부산물이지만, 분리 과정에서 바뀌면 안 된다.
    const dates = sequentialDates('2024-01-01', 100).filter((d) => d !== '2024-02-05');

    expect(monthlyDates(dates)).toEqual([
      '2024-01-01', '2024-02-06', '2024-03-05', '2024-04-02', '2024-04-09',
    ]);
  });

  it('stops sampling at a data gap longer than a week and only appends the last point', () => {
    const dates = [...sequentialDates('2024-01-01', 10), ...sequentialDates('2024-05-15', 6)];

    expect(monthlyDates(dates)).toEqual(['2024-01-01', '2024-05-20']);
  });

  it.each([
    ['2024/01/01', /형식/],
    ['2024-13-01', /날짜 값/],
    ['2024-02-30', /존재하지 않는 날짜/],
  ])('rejects the malformed date %s on the monthly path', (bad, message) => {
    expect(() => smartSampleByPeriod([{ date: bad }], MONTHLY_START, MONTHLY_END)).toThrow(message);
  });

  it('does not validate data dates on the daily/weekly paths', () => {
    const data = [{ date: '2024/01/01' }];
    expect(smartSampleByPeriod(data, '2020-01-01', '2023-01-01').data).toEqual(data);
  });
});

describe('characterization: smartSampleByPeriod range inputs', () => {
  it('accepts Date objects for the range', () => {
    const data = sequentialDates('2024-01-01', 10).map((date) => ({ date }));
    const result = smartSampleByPeriod(data, new Date(2020, 0, 1), new Date(2023, 0, 1));

    expect(result.aggregationType).toBe('weekly');
  });

  it('throws for an invalid end date', () => {
    expect(() => smartSampleByPeriod([{ date: '2024-01-01' }], '2024-01-01', 'nope'))
      .toThrow(/종료 날짜/);
  });

  it('treats exactly 2 and 5 years as inclusive upper bounds of the daily/weekly buckets', () => {
    const data = [{ date: '2024-01-01' }];
    // 2년 = 730.5일, 5년 = 1826.25일 (1년 = 365.25일 기준)
    const bucket = (end: string) => smartSampleByPeriod(data, '2020-01-01T00:00:00Z', end).aggregationType;

    expect(bucket('2021-12-31T12:00:00Z')).toBe('daily');
    expect(bucket('2021-12-31T12:00:01Z')).toBe('weekly');
    expect(bucket('2024-12-31T06:00:00Z')).toBe('weekly');
    expect(bucket('2024-12-31T06:00:01Z')).toBe('monthly');
  });
});

describe('characterization: monthly return aggregation gaps', () => {
  const round = (rows: ReturnPoint[]) => rows.map((r) => [r.date, Number(r.return_pct.toFixed(10))]);
  const ones = (dates: string[]): ReturnPoint[] => dates.map((date) => ({ date, return_pct: 1 }));

  it('skips empty months across a multi-month gap', () => {
    const dates = [...sequentialDates('2024-01-01', 10), ...sequentialDates('2024-05-15', 6)];

    expect(round(aggregateReturns(ones(dates), 'monthly'))).toEqual([
      ['2024-01-10', 10.4622125411], // 1.01^10 - 1
      ['2024-05-20', 6.1520150601], // 1.01^6 - 1
    ]);
  });

  it('opens a new single-day bucket when the last item lands exactly on a boundary', () => {
    const dates = sequentialDates('2024-01-01', 36); // 마지막 2/5 = 2월 첫 번째 월요일

    expect(round(aggregateReturns(ones(dates), 'monthly'))).toEqual([
      ['2024-02-04', 41.6602756031], // 1.01^35 - 1
      ['2024-02-05', 1],
    ]);
  });

  it('logs and drops the crossing point when a gap exceeds the 60-month safety limit (current behavior)', () => {
    // 60개월 넘는 공백을 만나면 while 루프가 안전장치로 중단되고, 그 시점의
    // 항목(2010-01-04)은 어느 버킷에도 들어가지 않는다. 다음 항목에서 경계
    // 이동이 이어져 2010-01-05는 단독 버킷이 된다.
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    try {
      const data = ones(['2000-01-03', '2000-01-04', '2010-01-04', '2010-01-05']);

      expect(round(aggregateReturns(data, 'monthly'))).toEqual([['2000-01-04', 2.01], ['2010-01-05', 1]]);
      expect(errorSpy).toHaveBeenCalledWith('[dataSampling] Monthly aggregation exceeded safety limit');
    } finally {
      errorSpy.mockRestore();
    }
  });

  it('returns the input unchanged for an unknown aggregation type', () => {
    const data = ones(['2024-01-01']);
    expect(aggregateReturns(data, 'yearly' as never)).toBe(data);
  });

  it('keeps extra fields of the bucket\'s last day and only overwrites return_pct', () => {
    const data = sequentialDates('2024-01-01', 3).map((date, i) => ({ date, return_pct: 0, tag: `t${i}` }));

    expect(aggregateReturns(data, 'weekly')).toEqual([{ date: '2024-01-03', return_pct: 0, tag: 't2' }]);
  });
});

describe('characterization: adaptiveSampleData branches', () => {
  it('keeps the adaptive result (no fallback) when enough points change beyond the threshold', () => {
    const data = Array.from({ length: 20 }, (_, i) => ({ value: i % 2 ? 100 : 0 }));
    const result = adaptiveSampleData(data, 10, 'value');

    // 모든 변화(100)가 임계값(0.5 표준편차 = 25)을 넘으므로 maxPoints-1개에서
    // 멈추고 마지막 점을 더해 정확히 maxPoints개가 된다.
    expect(result).toHaveLength(10);
    expect(result.slice(0, 9)).toEqual(data.slice(0, 9));
    expect(result[9]).toBe(data[19]);
  });

  it('falls back to equal-interval sampling when the values are all NaN', () => {
    const data = Array.from({ length: 20 }, (_, i) => ({ value: NaN, i }));
    const result = adaptiveSampleData(data, 10, 'value');

    expect(result).toEqual(sampleData(data, 10));
    expect(result.map((d) => d.i)).toEqual([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 19]);
  });
});
