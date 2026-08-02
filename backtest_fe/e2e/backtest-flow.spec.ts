import { test, expect } from '@playwright/test';

/**
 * 스모크 테스트: 포트폴리오 백테스트 입력 → 실행 → 결과 또는 오류 표시 (P2-38)
 *
 * 이전에는 @playwright/test가 devDependencies에 있고 npm run test:e2e 스크립트도
 * 있었지만 playwright.config.*가 아예 없었고, 이 파일은 100% 주석 처리된 템플릿
 * (존재하지 않는 PDF 다운로드 버튼을 참조하는 등 실제로 실행 불가능한 코드)이었다.
 * 이 spec은 실제로 실행 가능한 최소 스모크 테스트로 그 자리를 대체한다.
 *
 * 검증 대상은 "백테스트 결과가 정확한가"가 아니라 "폼을 채우고 제출하면 앱이
 * 멈추거나 깨지지 않고 로딩을 거쳐 결과 또는 오류 중 하나로 반드시 도달하는가"
 * 다 - 실제 브라우저 + 살아있는 백엔드가 있어야만 드러나는 배선 문제(잘못된
 * 프록시 설정, 완전히 깨진 제출 경로 등)를 잡기 위한 것이다.
 *
 * 실행 전제조건 (playwright.config.ts에 webServer를 두지 않은 이유도 동일):
 * - `docker compose -f compose.dev.yaml up -d`로 개발 스택이 이미 떠 있어야
 *   한다 - FE http://localhost:5173, BE http://localhost:8000 (BE 상태는
 *   FE의 vite proxy가 /api/v1/backtest를 전달할 대상이므로 간접적으로만
 *   필요하다).
 * - 실행: `npm run test:e2e` (backtest_fe/ 안에서).
 *
 * CI Quality Gate(Jenkinsfile)에는 의도적으로 연결하지 않았다 - 그 게이트는
 * 브라우저도 살아있는 백엔드도 없는 `docker build --target test`이기 때문이다.
 */

test.describe('포트폴리오 백테스트 스모크 테스트', () => {
  test('입력 → 실행 → 결과 또는 오류 표시', async ({ page }) => {
    await page.goto('/backtest');

    // 초기 상태: 아직 아무것도 제출하지 않았으므로 안내 카드가 보여야 한다.
    await expect(page.getByText('나만의 투자 전략을 검증해보세요')).toBeVisible();

    // 포트폴리오 입력은 데스크톱 테이블과 모바일 카드 두 가지 반응형 레이아웃이
    // 동시에 DOM에 존재하고(CSS로만 숨김) 같은 aria-label을 공유하므로,
    // <table> 하위로 스코프를 좁혀 strict mode violation을 피한다.
    const desktopTable = page.locator('table');
    await desktopTable.getByLabel('1번째 종목 심볼').fill('AAPL');

    // 기본 날짜 범위(오늘 기준 1년 전~오늘)에 의존하지 않고, 실데이터가 확실히
    // 존재하는 고정 범위를 지정해 테스트를 결정론적으로 만든다.
    await page.getByLabel('시작 날짜').fill('2023-01-01');
    await page.getByLabel('종료 날짜').fill('2023-12-31');

    // 전략은 기본값(buy_hold_strategy, initialBacktestFormState 참고)을 그대로 쓴다.

    await page.getByRole('button', { name: '백테스트 실행', exact: true }).click();

    // 실행 단계: 로딩 카드가 뜨는지 확인한다 - 요청이 실제로 디스패치됐다는 증거.
    // 제출 버튼도 로딩 중에는 접근성 이름이 "백테스트 실행 중..."으로 바뀌므로
    // (disabled 상태), 로딩 카드의 heading으로 스코프를 좁혀 strict mode
    // violation을 피한다.
    const loadingHeading = page.getByRole('heading', { name: '백테스트 실행 중' });
    await expect(loadingHeading).toBeVisible({ timeout: 10_000 });

    // 종료 단계: 결과 또는 오류 중 하나가 반드시 나타나야 한다. 결과는
    // BacktestResults가 렌더링될 때만 나오는 "CSV 다운로드" 버튼으로,
    // 오류는 PortfolioPage의 Alert 제목으로 식별한다.
    const resultMarker = page.getByRole('button', { name: 'CSV 다운로드' });
    const errorMarker = page.getByText('오류가 발생했습니다');
    await expect(resultMarker.or(errorMarker)).toBeVisible({ timeout: 200_000 });

    // 어느 쪽으로 끝났든 로딩 상태는 종료돼 있어야 한다.
    await expect(loadingHeading).not.toBeVisible();
  });
});
