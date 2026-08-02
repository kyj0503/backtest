/**
 * extractErrorMessage 회귀 테스트 (P1-09 / P2-29)
 *
 * 백엔드(FastAPI)는 에러를 `detail` 필드로 응답한다:
 *   - 문자열 형태: { "detail": "메시지" }
 *   - Pydantic 검증 에러 배열 형태: { "detail": [{ loc, msg, type }, ...] }
 *
 * 과거의 extractErrorMessage는 FastAPI가 절대 보내지 않는 `data.message` /
 * `data.error` 키를 확인하는 죽은 코드였고, 항상 axios의 일반 메시지
 * ("Request failed with status code 422" 등)로 폴백했다. 이 테스트는 실제
 * axios 요청을 MSW로 가로채 진짜 AxiosError를 만들어, 백엔드가 실제로 보내는
 * `detail` 형태를 올바르게 추출하는지 검증한다.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'
import { apiClient, extractErrorMessage } from '../client'

describe('extractErrorMessage', () => {
  const TEST_BASE_URL = 'http://localhost:3000'

  beforeAll(() => {
    apiClient.defaults.baseURL = TEST_BASE_URL
  })

  afterAll(() => {
    apiClient.defaults.baseURL = ''
  })

  afterEach(() => {
    server.resetHandlers()
  })

  const triggerAxiosError = async (
    body: Record<string, unknown>,
    status: number
  ): Promise<unknown> => {
    server.use(
      http.post(`${TEST_BASE_URL}/api/v1/backtest`, () => HttpResponse.json(body, { status }))
    )
    try {
      await apiClient.post('/api/v1/backtest', {})
    } catch (err) {
      return err
    }
    throw new Error('요청이 실패했어야 하는데 성공함 (테스트 설정 오류)')
  }

  it('FastAPI 문자열 detail을 그대로 반환한다', async () => {
    const err = await triggerAxiosError(
      { detail: '포트폴리오 구성이 올바르지 않습니다.' },
      422
    )

    expect(extractErrorMessage(err)).toBe('포트폴리오 구성이 올바르지 않습니다.')
  })

  it('Pydantic 검증 에러 배열([{loc,msg,type}])에서 msg를 추출한다', async () => {
    const err = await triggerAxiosError(
      {
        detail: [
          { loc: ['body', 'start_date'], msg: '날짜 형식이 올바르지 않습니다.', type: 'value_error' },
          { loc: ['body', 'end_date'], msg: '종료일은 시작일 이후여야 합니다.', type: 'value_error' },
        ],
      },
      422
    )

    const message = extractErrorMessage(err)
    expect(message).toContain('날짜 형식이 올바르지 않습니다.')
    expect(message).toContain('종료일은 시작일 이후여야 합니다.')
  })

  it('data.message/data.error 같은 FastAPI가 보내지 않는 키에는 의존하지 않는다', async () => {
    // 회귀 방지: 예전 구현은 이 키들을 확인했다. detail이 없을 때
    // message/error로 우연히 통과하지 않는지 확인한다 (axios 기본 메시지로
    // 폴백해야 한다).
    const err = await triggerAxiosError(
      { message: '이 키는 FastAPI가 보내지 않음', error: '이것도 아님' },
      500
    )

    const message = extractErrorMessage(err)
    expect(message).not.toBe('이 키는 FastAPI가 보내지 않음')
    expect(message).not.toBe('이것도 아님')
  })

  it('axios 에러가 아닌 일반 Error는 message를 반환한다', () => {
    expect(extractErrorMessage(new Error('네트워크 오류'))).toBe('네트워크 오류')
  })

  it('알 수 없는 값이면 기본 메시지를 반환한다', () => {
    expect(extractErrorMessage('그냥 문자열')).toBe(
      '요청 처리 중 알 수 없는 오류가 발생했습니다.'
    )
  })
})
