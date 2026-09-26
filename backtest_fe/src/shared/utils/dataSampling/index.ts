/**
 * 데이터 샘플링 유틸리티 공개 API
 *
 * 책임별 모듈:
 * - periodSampling: 백테스트 기간 판정 + 기간에 맞는 샘플링 선택 (smartSampleByPeriod)
 * - priceSampling: 가격/가치 시계열의 주간(인덱스)·월간(달력) 포인트 선택
 * - returnAggregation: 일간 수익률의 주간/월간 복리 집계 (aggregateReturns)
 * - calendar: 두 경로가 공유하는 "N번째 요일" 월 경계 계산
 * - pointLimitSampling: 최대 포인트 수 기반 샘플러와 리밸런싱 마커 제한
 */

export { smartSampleByPeriod } from './periodSampling';
export type { AggregationType } from './periodSampling';
export { aggregateReturns } from './returnAggregation';
export { sampleData, adaptiveSampleData, filterRebalanceMarkers } from './pointLimitSampling';
