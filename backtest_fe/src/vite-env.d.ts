/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// 비표준 Chromium 메모리 계측 API (performance.memory).
// 표준이 아니므로 lib.dom에 없고, 지원하지 않는 브라우저에서는 undefined다.
interface PerformanceMemory {
  readonly usedJSHeapSize: number;
  readonly totalJSHeapSize: number;
  readonly jsHeapSizeLimit: number;
}

interface Performance {
  readonly memory?: PerformanceMemory;
}

// Vite의 define으로 주입되는 글로벌 변수들
declare const __APP_VERSION__: string;
declare const __BUILD_TIME__: string;
declare const __GIT_COMMIT__: string;
declare const __GIT_BRANCH__: string;
declare const __BUILD_NUMBER__: string;
