/**
 * UnifiedBacktestResponse 최상위 계약 (A-23)
 *
 * BE(POST /api/v1/backtest)의 성공 응답 최상위는 `{ status, data }`뿐이다.
 * 경고는 `data.warnings`에만 실린다. 최상위에 warnings/message/backtest_type을
 * 선언해 두면 `response.warnings`처럼 항상 undefined인 값을 읽는 코드가
 * 타입 검사를 통과한다. 이 파일은 type-check:test가 그런 접근을 막는지 고정한다.
 */
import { describe, it, expect } from 'vitest'
import type { UnifiedBacktestResponse } from '../api-types'
import { makePortfolioResponse } from '@/test/fixtures/backtestResults'

describe('UnifiedBacktestResponse 최상위 필드', () => {
  it('BE가 보내지 않는 최상위 필드는 타입에 없다', () => {
    const response: UnifiedBacktestResponse = makePortfolioResponse({ warnings: ['경고'] })

    // @ts-expect-error — 경고는 data.warnings에만 온다
    void response.warnings
    // @ts-expect-error — BE는 최상위 message를 보내지 않는다(오류는 HTTP 상태와 detail)
    void response.message
    // @ts-expect-error — BE는 backtest_type을 보내지 않는다
    void response.backtest_type

    expect(Object.keys(response).sort()).toEqual(['data', 'status'])
  })

  it('경고는 data.warnings로 읽는다', () => {
    const response: UnifiedBacktestResponse = makePortfolioResponse({ warnings: ['경고'] })
    const data = response.data
    expect('warnings' in data ? data.warnings : undefined).toEqual(['경고'])
  })
})
