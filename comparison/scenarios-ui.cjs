// Real form interactions and CSV downloads against both running frontends.
const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const output = process.env.REPORT_DIR || '/reports/scenarios';
fs.mkdirSync(output + '/ui', { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true });
  const results = [];
  try {
    for (const [index, url] of process.argv.slice(2).entries()) {
      const server = process.env.SERVER_NAME || (index === 0 ? 'python' : 'rust');
      for (const scenario of [
        { name: 'usd_buy_hold', symbol: 'AAPL' },
        { name: 'krw_sma', symbol: '005930.KS', strategy: '단순이동평균 교차' },
        { name: 'monthly_dca', symbol: 'AAPL', dca: true },
        ...(process.env.INCLUDE_WEIGHT_DCA === '1' ? [{ name: 'weight_dca', symbol: 'AAPL', dca: true, weight: true }] : []),
      ]) {
        const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
        const page = await context.newPage();
        page.setDefaultTimeout(90000);
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(url + '/backtest');
        await page.locator('table').getByLabel('1번째 종목 심볼').fill(scenario.symbol);
        await page.getByLabel('시작 날짜').fill('2023-01-03');
        await page.getByLabel('종료 날짜').fill('2023-10-31');
        if (scenario.strategy) {
          await page.getByLabel('투자 전략', { exact: true }).click();
          await page.getByRole('option', { name: scenario.strategy, exact: true }).click();
        }
        if (scenario.dca) {
          await page.locator('table').getByLabel('1번째 종목 투자 금액').fill('500');
          await page.locator('table').getByRole('combobox').filter({ hasText: '일시불 투자' }).click();
          await page.getByRole('option', { name: '분할 매수 (DCA)', exact: true }).click();
        }
        if (scenario.weight) {
          await page.getByRole('button', { name: '비중 기준', exact: true }).click();
          await page.getByLabel('전체 투자금액($)', { exact: true }).fill('12000');
          await page.getByLabel('전체 투자금액($)', { exact: true }).fill('10000');
        }
        const paths = ['/backtest', '/prices', '/exchange-rates', '/benchmarks', '/news'];
        const pending = paths.map(path => page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1' + path));
        const started = performance.now();
        await page.getByRole('button', { name: '백테스트 실행', exact: true }).click();
        const responses = await Promise.all(pending);
        const bodies = await Promise.all(responses.map(r => r.json()));
        if (scenario.weight) {
          const request = responses[0].request().postDataJSON();
          if (request.portfolio[0].total_amount !== 10000 || request.portfolio[0].amount !== 1000 || bodies[0].data.portfolio_statistics.Initial_Value !== 10000) throw new Error('DCA budget was not conserved through the real form/API path');
        }
        await page.getByRole('button', { name: 'CSV 다운로드' }).waitFor({ state: 'visible' });
        const uiMs = performance.now() - started;
        const downloadEvent = page.waitForEvent('download');
        await page.getByRole('button', { name: 'CSV 다운로드' }).click();
        const download = await downloadEvent;
        await download.saveAs(`${output}/ui/${server}-${scenario.name}.csv`);
        await page.waitForFunction(() => document.querySelectorAll('.animate-spin').length === 0);
        await page.evaluate(() => document.fonts.ready);
        await page.screenshot({ path: `${output}/ui/${server}-${scenario.name}.png`, fullPage: true });
        const result = { server, scenario: scenario.name, request: responses[0].request().postDataJSON(), statuses: responses.map(r => r.status()), finalValue: bodies[0].data?.portfolio_statistics?.Final_Value, totalReturn: bodies[0].data?.portfolio_statistics?.Total_Return, uiMs, csvBytes: fs.statSync(`${output}/ui/${server}-${scenario.name}.csv`).size, pageErrors: errors };
        results.push(result);
        fs.writeFileSync(output + '/ui.json', JSON.stringify(results, null, 2));
        console.log(JSON.stringify(result));
        if (errors.length || result.statuses.some(s => s !== 200)) throw new Error('UI scenario failed');
        await context.close();
      }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
