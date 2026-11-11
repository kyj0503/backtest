const { chromium } = require('@playwright/test');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true });
  try {
    for (const [index, url] of process.argv.slice(2).entries()) {
      const name = index === 0 ? 'python' : 'rust';
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      const page = await context.newPage();
      page.setDefaultTimeout(120000);
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url + '/backtest');
      await page.locator('table').getByLabel('1번째 종목 심볼').fill('AAPL');
      await page.getByLabel('시작 날짜').fill('2023-01-02');
      await page.getByLabel('종료 날짜').fill('2023-10-31');
      const paths = ['/backtest', '/prices', '/exchange-rates', '/benchmarks', '/news'];
      const pending = paths.map(path => page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1' + path, { timeout: 150000 }));
      await page.getByRole('button', { name: '백테스트 실행', exact: true }).click();
      const responses = await Promise.all(pending);
      const bodies = [];
      for (const response of responses) {
        const body = await response.json();
        if (response.status() !== 200 || body.status !== 'success') {
          throw new Error(`${name} ${response.url()}: ${response.status()} ${JSON.stringify(body)}`);
        }
        bodies.push(body);
      }
      await page.getByRole('button', { name: 'CSV 다운로드' }).waitFor({ state: 'visible' });
      if (errors.length) throw new Error(`${name}: ${errors.join(', ')}`);
      fs.writeFileSync(`/reports/${name}.json`, JSON.stringify({ request: responses[0].request().postDataJSON(), responses: bodies }, null, 2));
      await page.screenshot({ path: `/reports/${name}.png`, fullPage: true });
      console.log(JSON.stringify({ name, calculation: 'success', referenceRequests: 4, csvVisible: true, finalValue: bodies[0].data.portfolio_statistics.Final_Value }));
      await context.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
