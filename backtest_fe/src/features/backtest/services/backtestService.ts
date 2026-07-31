/**
 * 백테스트 서비스
 *
 * 백엔드는 통합 엔드포인트 POST /api/v1/backtest 하나만 제공한다.
 * 주가/환율/뉴스/벤치마크 데이터는 모두 이 응답에 포함되어 오므로
 * 별도 조회 메서드를 두지 않는다.
 */

import { apiClient } from '@/shared/api/client';
import {
  BacktestRequest,
  UnifiedBacktestResponse,
} from '../model/types/api-types';

export class BacktestService {
  /**
   * 백테스트 실행 (단일 종목 또는 포트폴리오)
   */
  static async executeBacktest(request: BacktestRequest): Promise<UnifiedBacktestResponse> {
    const response = await apiClient.post<UnifiedBacktestResponse>('/api/v1/backtest', request);
    return response.data;
  }
}

export default BacktestService;
