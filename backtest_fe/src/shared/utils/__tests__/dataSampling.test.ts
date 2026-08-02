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
import { describe, it, expect } from 'vitest';
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
