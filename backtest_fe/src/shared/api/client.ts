import axios from 'axios';
import { getApiBaseUrl } from './base';

const baseURL = getApiBaseUrl();

export const apiClient = axios.create({
  baseURL,
});

export const extractErrorMessage = (err: unknown): string => {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string; error?: string } | undefined;
    return data?.message || data?.error || err.message || '요청 처리 중 오류가 발생했습니다.';
  }
  if (err instanceof Error) {
    return err.message;
  }
  return '요청 처리 중 알 수 없는 오류가 발생했습니다.';
};
