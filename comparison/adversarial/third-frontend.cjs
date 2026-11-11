// Calls current application functions and extracts actual chart callbacks.
const fs=require('node:fs'), ts=require('/app/node_modules/typescript'), Module=require('node:module');
const src='/src', reportDir='/reports', opts={module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true};
const transpile=s=>ts.transpileModule(s,{compilerOptions:opts}).outputText;
for(const ext of ['.ts','.tsx'])require.extensions[ext]=(m,f)=>m._compile(transpile(fs.readFileSync(f,'utf8')),f);
const resolve=Module._resolveFilename;
Module._resolveFilename=function(name,parent,...args){return resolve.call(this,name.startsWith('@/')?src+'/src/'+name.slice(2):name,parent,...args);};
const feature=src+'/src/features/backtest/';
const {buildPortfolioEquitySeries,sampleByDateRange}=require(feature+'hooks/charts/chartSeriesBuilders.ts');
const {smartSampleByPeriod}=require(src+'/src/shared/utils/dataSampling/index.ts');
const {extractTradeLogs}=require(feature+'utils/chartDataTransform.ts');
const {generateCSVReport}=require(feature+'services/reportGenerator.ts');
function callbacks(file,names){
 const tree=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX),printer=ts.createPrinter(),parts={};
 function visit(n){if(ts.isVariableDeclaration(n)&&ts.isIdentifier(n.name)&&names.includes(n.name.text))parts[n.name.text]=printer.printNode(ts.EmitHint.Expression,ts.isCallExpression(n.initializer)?n.initializer.arguments[0]:n.initializer,tree);ts.forEachChild(n,visit);}visit(tree);return parts;
}
const norm=callbacks(feature+'components/results/BenchmarkIndexChart.tsx',['normalizedPortfolio']);
let portfolioEquityData;
const normalizePortfolio=eval(transpile('('+norm.normalizedPortfolio+')'));
const stockParts=callbacks(feature+'components/StockPriceChart.tsx',['findClosestAggregationDate','chartDataWithSignals','tradeCount']);
const findClosestAggregationDate=eval(transpile('('+stockParts.findClosestAggregationDate+')'));
let selectedStockData,selectedSymbol='TEST',tradeLogs,aggregationType;
const chartSignals=eval(transpile('('+stockParts.chartDataWithSignals+')'));
const countTrades=eval(transpile('('+stockParts.tradeCount+')'));
const outcomes=JSON.parse(fs.readFileSync(reportDir+'/engine-results.json','utf8'));
const inputs=JSON.parse(fs.readFileSync(reportDir+'/cases.json','utf8'));
const normalized=[],markers=[];
for(const c of outcomes){
 const d=c.output.data;if(!d)continue;
 const input=inputs.find(v=>v.name===c.name),{start_date:start,end_date:end}=input.request;
 aggregationType=smartSampleByPeriod([{date:start}],start,end).aggregationType;
 portfolioEquityData=buildPortfolioEquitySeries(d,start,end,aggregationType);
 const chart=normalizePortfolio();
 normalized.push({name:c.name,aggregation:aggregationType,apiTWR:d.portfolio_statistics.Time_Weighted_Return,firstBucket:portfolioEquityData[0],lastIndex:chart.at(-1).normalized});
 if(input.histories.TEST && d.strategy_details.TEST){
   selectedStockData={symbol:'TEST',data:sampleByDateRange(input.histories.TEST.bars.map(b=>({date:b.date,price:b.close})),start,end)};
   tradeLogs=extractTradeLogs(d.strategy_details);
   markers.push({name:c.name,aggregation:aggregationType,entries:tradeLogs.TEST,chartCounts:countTrades(),points:chartSignals().filter(p=>p.buySignal!==undefined||p.sellSignal!==undefined)});
 }
}
const csvReports={};
for(const name of ['rebalance_csv_fees','weekend_cash_weights','late_initial_weights']){
  const d=outcomes.find(c=>c.name===name).output.data;
  const csv=generateCSVReport(d,true);
  fs.writeFileSync(reportDir+'/'+name+'.csv',csv);
  csvReports[name]={rebalanceHistory:d.rebalance_history,csv};
}
const result={normalized,markers,csvReports};
fs.writeFileSync(reportDir+'/frontend-results.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
