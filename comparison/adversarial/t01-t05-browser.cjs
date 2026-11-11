// Actual form submissions and downloaded CSV against the final fixture API.
const {chromium,expect}=require('@playwright/test');
const fs=require('node:fs');
const report='/reports';
const cases=JSON.parse(fs.readFileSync(report+'/http-cases.json','utf8'));
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});
 const outputs=[];
 try {
  for(const name of ['first_valid_bollinger_20_0','late_listing_cash','fractional_csv_quantity']) {
   const c=cases.find(c=>c.name===name),r=c.request;
   const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
   const page=await context.newPage();page.setDefaultTimeout(30000);
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(process.argv[2]+'/backtest');
   await page.locator('table').getByLabel('1번째 종목 심볼').fill(r.portfolio[0].symbol);
   await page.locator('table').getByLabel('1번째 종목 투자 금액').fill(String(r.portfolio[0].amount));
   await page.getByLabel('시작 날짜').fill(r.start_date);
   await page.getByLabel('종료 날짜').fill(r.end_date);
   await page.getByRole('spinbutton',{name:/거래 수수료/}).fill('0');
   if(name.startsWith('first_valid')) {
    await page.getByLabel('투자 전략',{exact:true}).click();
    await page.getByRole('option',{name:'볼린저 밴드',exact:true}).click();
    await page.getByLabel('이동평균 기간',{exact:true}).fill('20');
    await page.getByLabel('표준편차 배수',{exact:true}).fill('1');
   }
   if(name==='fractional_csv_quantity') {
    await page.getByRole('button',{name:'현금 추가',exact:true}).click();
    await page.locator('table').getByLabel('2번째 현금 자산 이름').fill('USD');
    await page.locator('table').getByLabel('2번째 종목 투자 금액').fill('100');
    await page.getByRole('combobox',{name:/리밸런싱 주기/}).click();
    await page.getByRole('option',{name:'매주',exact:true}).click();
   }
   for(let attempt=0;attempt<(name==='late_listing_cash'?2:1);attempt++) {
    const pending=['backtest','prices','exchange-rates','benchmarks','news'].map(path=>page.waitForResponse(res=>new URL(res.url()).pathname==='/api/v1/'+path));
    await page.getByRole('button',{name:'백테스트 실행',exact:true}).click();
    const responses=await Promise.all(pending);for(const response of responses)expect(response.status()).toBe(200);
    const data=(await responses[0].json()).data;
    const expected=name.startsWith('first_valid')?12375:name==='late_listing_cash'?10000:300;
    expect(data.portfolio_statistics.Final_Value).toBeCloseTo(expected,8);
    await page.getByRole('button',{name:'CSV 다운로드'}).waitFor();
    const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'CSV 다운로드'}).click();
    const download=await downloadEvent;const file=report+'/'+name+'-'+attempt+'-browser.csv';await download.saveAs(file);
    let exported;
    if(name==='fractional_csv_quantity') {
     const line=fs.readFileSync(file,'utf8').split('\n').find(l=>l.startsWith('2023-01-09,'+r.portfolio[0].symbol+','));
     const cells=line.split(',');expect(Number(cells[4])).toBeGreaterThan(0);expect(Number(cells[4])*Number(cells[5])).toBeCloseTo(50,8);
     expect(Number(cells[3])).toBe(50);exported=line;
    }
    expect(errors).toEqual([]);
    outputs.push({name,attempt:attempt+1,statuses:responses.map(r=>r.status()),finalValue:data.portfolio_statistics.Final_Value,exported,pageErrors:errors});
    fs.writeFileSync(report+'/t01-t05-browser.json',JSON.stringify(outputs,null,2));console.log(JSON.stringify(outputs.at(-1)));
   }
   await page.screenshot({path:report+'/'+name+'-browser.png',fullPage:true});await context.close();
  }
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
