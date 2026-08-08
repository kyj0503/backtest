import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { getApiBaseUrl } from './base';

const baseURL = getApiBaseUrl();

/**
 * baseURL에서 경로 부분만 추출한다.
 * '/api' -> '/api', 'https://host/api' -> '/api', '' -> ''
 */
const getBasePath = (base: string): string => {
  if (!base) return '';
  try {
    // 상대 경로도 처리할 수 있도록 더미 origin을 붙여 파싱한다.
    return new URL(base, 'http://placeholder.invalid').pathname.replace(/\/$/, '');
  } catch {
    return base.replace(/\/$/, '');
  }
};

const basePath = getBasePath(baseURL);

/**
 * 백테스트 요청 타임아웃(ms).
 *
 * 프로덕션 nginx(`nginx.conf`/`nginx.prod.conf`)의 `proxy_read_timeout`이
 * 180s로 설정되어 있다 — 백엔드가 그보다 오래 응답하지 않으면 nginx가 먼저
 * 504로 연결을 끊는다. axios 타임아웃을 180s보다 5초 더 길게 잡아서,
 * 프로덕션에서는 nginx의 504(실제 HTTP 응답이라 extractErrorMessage가 그대로
 * 처리)가 먼저 발생하도록 하고, axios 타임아웃 자체는 nginx가 없는 dev vite
 * 프록시(타임아웃 없음)나 nginx가 응답하지 못하는 상황을 위한 최후의
 * 안전망 역할만 하게 한다. 백테스트는 종목 수·기간에 따라 오래 걸릴 수
 * 있으므로 값 자체는 넉넉하게 잡는다 (P2-30) — 그래도 폼이 영구히 잠기지
 * 않도록 무한대는 아니다.
 */
export const BACKTEST_REQUEST_TIMEOUT_MS = 185_000;

export const apiClient = axios.create({
  baseURL,
  timeout: BACKTEST_REQUEST_TIMEOUT_MS,
  // fetch 어댑터로 고정한다. AbortController가 네이티브로 연결돼 취소
  // 처리가 단순하고, 이 앱은 진행률 이벤트(onUploadProgress 등) 같은
  // XHR 전용 기능을 쓰지 않는다.
  //
  // 주의: 기본 xhr 어댑터로 되돌리면 위 타임아웃·취소 테스트 3개가
  // 깨진다. 실제 브라우저의 XMLHttpRequest.timeout은 정상 동작하므로
  // 이는 프로덕션 제약이 아니라 테스트 환경(happy-dom + MSW)이 XHR의
  // timeout/abort를 충실히 구현하지 않는 데서 오는 제약이다.
  adapter: 'fetch',
});

/**
 * 경로 이중 접두사 방지.
 *
 * 서비스 레이어는 전체 경로(`/api/v1/...`)를 그대로 넘기는데,
 * VITE_API_BASE_URL이 `/api`로 설정되어 있으면 baseURL과 겹쳐
 * `/api/api/v1/backtest`가 만들어져 404가 난다.
 * 요청 경로가 이미 baseURL의 경로 부분으로 시작하면 그만큼 덜어낸다.
 */
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const url = config.url;
  if (basePath && url && url.startsWith(`${basePath}/`)) {
    config.url = url.slice(basePath.length);
  }
  return config;
});

/**
 * 진행 중인 백테스트 요청의 취소 브리지.
 *
 * BacktestService.executeBacktest(request)는 매개변수가 request 하나뿐인
 * 고정 시그니처라, 호출부(usePortfolioBacktest)가 AbortSignal을 직접 넘길
 * 방법이 없다. 대신 훅이 "지금 진행 중인 요청"의 signal을 여기 등록해두면,
 * 다음에 나가는 요청에 인터셉터가 자동으로 실어준다. 언마운트되거나 새
 * 제출이 이전 요청을 대체(supersede)할 때 훅이 컨트롤러의 abort()를
 * 호출해 실제로 취소한다 (P2-30).
 */
let activeRequestSignal: AbortSignal | undefined;

export const setActiveRequestSignal = (signal: AbortSignal | undefined): void => {
  activeRequestSignal = signal;
};

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (activeRequestSignal && !config.signal) {
    config.signal = activeRequestSignal;
  }
  return config;
});

/**
 * axios 에러(또는 임의의 값)에서 사용자에게 보여줄 메시지를 추출한다.
 *
 * FastAPI는 에러를 `detail` 필드로 응답한다 (`message` / `error` 키가 아님):
 *   - 문자열 형태: { "detail": "포트폴리오 구성이 올바르지 않습니다." }
 *   - Pydantic 검증 에러 배열 형태(422):
 *     { "detail": [{ "loc": [...], "msg": "...", "type": "..." }, ...] }
 *
 * usePortfolioBacktest(페이지 레벨 Alert)와 PortfolioBacktestForm(입력 오류
 * 모달) 양쪽에서 이 함수를 공유해, 백엔드가 실제로 보내는 형식과 무관하게
 * 항상 같은 방식으로 실제 메시지를 노출한다.
 */
export const extractErrorMessage = (err: unknown): string => {
  if (axios.isAxiosError(err)) {
    const responseData = err.response?.data as { detail?: unknown } | undefined;
    const detail = responseData?.detail;

    if (Array.isArray(detail)) {
      // FastAPI/Pydantic 422 응답: [{ loc, msg, type }, ...]
      const messages = detail.map((item: unknown) => {
        if (typeof item === 'object' && item !== null && 'msg' in item && item.msg) {
          return String(item.msg);
        }
        return JSON.stringify(item);
      });
      return messages.join('\n');
    }

    if (typeof detail === 'string' && detail) {
      return detail;
    }

    return err.message || '요청 처리 중 오류가 발생했습니다.';
  }
  if (err instanceof Error) {
    return err.message;
  }
  return '요청 처리 중 알 수 없는 오류가 발생했습니다.';
};
