/**
 * 백테스트 전략 및 설정 통합 모듈
 * 
 * **역할**:
 * - 모든 constants 파일을 re-export하여 하위 호환성 유지
 * - 기존 import 경로 변경 없이 리팩터링 완료
 * 
 * **새 구조**:
 * - constants/strategies.ts - 전략 설정
 * - constants/stocks.ts - 종목 목록
 * - constants/assetTypes.ts - 자산 타입
 * - constants/dcaConfig.ts - DCA 설정
 * - constants/rebalancing.ts - 리밸런싱 설정
 * - constants/validation.ts - 검증 규칙 및 기본값
 */

export * from './constants';
