// Real form, local Vite bundle, SVG markers and CSV downloads; no API mocks.
const {chromium, expect}=require('@playwright/test');
const fs=require('node:fs');
const report=process.env.REPORT_DIR||'/reports';
const cases=JSON.parse(fs.readFileSync(report+'/http-cases.json','utf8'));
(async()=>{
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});
  const outcomes=[];
  try {
    for(const name of ['initial_fee','weekend_cash_weights','front_loaded_gain_monthly','open_close_gap','weekly_backdated_open']) {
      const scenario=cases.find(c=>c.name===name), r=scenario.request;
      const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
      const page=await context.newPage();page.setDefaultTimeout(30000);
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.goto(process.argv[2]+'/backtest');
      await page.locator('table').getByLabel('1번째 종목 심볼').fill(name==='open_close_gap'?'BROWSERGAP':r.portfolio[0].symbol);
      await page.getByLabel('시작 날짜').fill(r.start_date);
      await page.getByLabel('종료 날짜').fill(r.end_date);
      await page.getByRole('spinbutton',{name:/거래 수수료/}).fill(String(r.commission*100));
      if(r.strategy){
        await page.getByLabel('투자 전략',{exact:true}).click();
        await page.getByRole('option',{name:'RSI 전략',exact:true}).click();
        await page.getByLabel('RSI 계산 기간',{exact:true}).fill('5');
      }
      const pending=['backtest','prices','exchange-rates','benchmarks','news'].map(path=>page.waitForResponse(res=>new URL(res.url()).pathname==='/api/v1/'+path));
      await page.getByRole('button',{name:'백테스트 실행',exact:true}).click();
      const responses=await Promise.all(pending);
      for(const res of responses)expect(res.status()).toBe(200);
      const body=await responses[0].json();
      await expect(page.getByRole('note')).toContainText('수정주가 기반 소수 단위');
      await page.getByRole('button',{name:'CSV 다운로드'}).waitFor();
      let marker;
      if(r.strategy){
        const buy=page.locator('.recharts-scatter-symbol path[fill="#ef4444"]');
        await expect(buy).toHaveCount(1);
        await buy.hover();
        const date=name==='open_close_gap'?'2023-01-08':'2023-01-11';
        const price=name==='open_close_gap'?'97':'98';
        const tip=page.locator('.recharts-tooltip-wrapper').filter({hasText:'날짜: '+date});
        await expect(tip).toBeVisible();
        await expect(tip).toContainText(price);
        marker={date,price,tooltip:await tip.innerText()};
      }
      const event=page.waitForEvent('download');
      await page.getByRole('button',{name:'CSV 다운로드'}).click();
      const download=await event;await download.saveAs(report+'/'+name+'-browser.csv');
      const csv=fs.readFileSync(report+'/'+name+'-browser.csv','utf8');
      if(name==='weekend_cash_weights')expect(csv).toContain('2023-01-01,100.00%');
      if(name==='initial_fee')expect(body.data.portfolio_statistics.Final_Value).toBeCloseTo(10000/1.01,7);
      if(name==='front_loaded_gain_monthly')expect(body.data.portfolio_statistics.Final_Value).toBeCloseTo(12000,7);
      await page.screenshot({path:report+'/'+name+'-browser.png',fullPage:true});
      expect(errors).toEqual([]);
      outcomes.push({name,statuses:responses.map(r=>r.status()),finalValue:body.data.portfolio_statistics.Final_Value,marker,csvBytes:Buffer.byteLength(csv),pageErrors:errors});
      fs.writeFileSync(report+'/browser.json',JSON.stringify(outcomes,null,2));
      console.log(JSON.stringify(outcomes.at(-1)));await context.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
