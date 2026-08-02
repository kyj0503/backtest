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

export const apiClient = axios.create({
  baseURL,
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
