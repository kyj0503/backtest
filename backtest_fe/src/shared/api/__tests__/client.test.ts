/**
 * apiClient 경로 합성 회귀 테스트
 *
 * 서비스 레이어(backtestService.ts)는 axios에 전체 경로
 * (`/api/v1/...`)를 그대로 넘긴다. 이때 VITE_API_BASE_URL이 `/api`로 설정되어
 * 있으면 baseURL과 경로가 겹쳐 `/api/api/v1/backtest`가 만들어지고,
 * vite 프록시(`/api/v1/backtest`)에 매칭되지 않아 404가 난다.
 *
 * 실제로 dev 환경에서 이 이유로 백테스트 실행이 404가 났었다.
 * 설정 값과 무관하게 최종 요청 URL이 올바르게 합성되는지 고정한다.
 *
 * getUri()는 요청 인터셉터를 거치지 않으므로, 실제로 어댑터까지 전달되는
 * 설정을 캡처해 baseURL + url 조합을 검증한다.
 */

import { describe, it, expect, afterEach, vi } from 'vitest'

const ORIGINAL_ENV = { ...import.meta.env }

/** 지정한 VITE_API_BASE_URL로 클라이언트를 새로 로드해 최종 요청 URL을 얻는다. */
const resolveUrl = async (baseUrl: string | undefined, requestUrl: string) => {
  vi.resetModules()
  const env = import.meta.env as unknown as Record<string, unknown>
  if (baseUrl === undefined) {
    delete env.VITE_API_BASE_URL
  } else {
    env.VITE_API_BASE_URL = baseUrl
  }

  const { apiClient } = await import('../client')

  let resolved = ''
  apiClient.defaults.adapter = async (config) => {
    resolved = `${config.baseURL ?? ''}${config.url ?? ''}`
    return {
      data: null,
      status: 200,
      statusText: 'OK',
      headers: {},
      config,
    }
  }

  await apiClient.get(requestUrl)
  return resolved
}

describe('apiClient URL 합성', () => {
  afterEach(() => {
    Object.assign(import.meta.env, ORIGINAL_ENV)
    vi.resetModules()
  })

  it('VITE_API_BASE_URL이 비어 있으면 전체 경로를 그대로 사용한다', async () => {
    expect(await resolveUrl('', '/api/v1/backtest')).toBe('/api/v1/backtest')
  })

  it('VITE_API_BASE_URL이 미설정이면 전체 경로를 그대로 사용한다', async () => {
    expect(await resolveUrl(undefined, '/api/v1/backtest')).toBe('/api/v1/backtest')
  })

  it('VITE_API_BASE_URL=/api 여도 경로가 이중으로 붙지 않는다', async () => {
    expect(await resolveUrl('/api', '/api/v1/backtest')).toBe('/api/v1/backtest')
  })

  it('VITE_API_BASE_URL=/api 이고 경로에 접두사가 없으면 baseURL을 적용한다', async () => {
    expect(await resolveUrl('/api', '/v1/backtest')).toBe('/api/v1/backtest')
  })

  it('절대 URL 베이스에서도 경로가 이중으로 붙지 않는다', async () => {
    expect(await resolveUrl('https://backtest-be.example.com/api', '/api/v1/backtest')).toBe(
      'https://backtest-be.example.com/api/v1/backtest'
    )
  })

  it('접두사가 유사하기만 한 경로는 잘라내지 않는다', async () => {
    // '/apiv2/...'는 '/api'로 시작하지만 경로 구분자가 달라 잘라내면 안 된다.
    expect(await resolveUrl('/api', '/apiv2/backtest')).toBe('/api/apiv2/backtest')
  })

  it('타임아웃이 설정되어 있고 프로덕션 nginx의 proxy_read_timeout(180s)보다 길다 (P2-30)', async () => {
    // nginx.conf / nginx.prod.conf의 proxy_read_timeout 180s보다 조금 더
    // 길게 잡아, 프로덕션에서는 nginx의 504(실제 HTTP 응답)가 먼저 발생하고
    // axios 타임아웃은 dev 프록시(타임아웃 없음)나 nginx 자체가 응답하지
    // 못하는 경우의 최후 안전망 역할만 하도록 한다. 정지된 연결이 폼을
    // 영구히 막지 않도록 무한대는 아니어야 한다.
    vi.resetModules()
    const { apiClient, BACKTEST_REQUEST_TIMEOUT_MS } = await import('../client')
    const NGINX_PROXY_READ_TIMEOUT_MS = 180_000

    expect(apiClient.defaults.timeout).toBe(BACKTEST_REQUEST_TIMEOUT_MS)
    expect(apiClient.defaults.timeout).toBeGreaterThan(NGINX_PROXY_READ_TIMEOUT_MS)
    // 며칠씩 걸리는 정도의 값을 실수로 넣지 않았는지 확인 (여전히 유한하고 합리적인 상한).
    expect(apiClient.defaults.timeout).toBeLessThan(10 * 60 * 1000)
  })
})
