// Run in the existing console build image with the current source mounted at /src.
const fs = require('node:fs');
const ts = require('/app/node_modules/typescript');
const Module = require('node:module');
const options = {module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true};
require.extensions['.ts'] = (m,f) => m._compile(ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:options}).outputText,f);
const stockChartFile='/src/src/features/backtest/components/StockPriceChart.tsx';
const stockChart=ts.createSourceFile(stockChartFile,fs.readFileSync(stockChartFile,'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
const printer=ts.createPrinter();
const fragments={};
function visit(node){
  if(ts.isVariableDeclaration(node)&&ts.isIdentifier(node.name)&&['findClosestAggregationDate','chartDataWithSignals'].includes(node.name.text)){
    const expression=node.name.text==='chartDataWithSignals'?node.initializer.arguments[0]:node.initializer;
    fragments[node.name.text]=printer.printNode(ts.EmitHint.Expression,expression,stockChart);
  }
  ts.forEachChild(node,visit);
}
visit(stockChart);
if(Object.keys(fragments).length!==2)throw new Error('Chart source layout changed; audit adapter must be reviewed');
const source = `
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { recalcAmountsByWeight } from '/src/src/features/backtest/model/backtestFormReducer';
import { calculateDcaPeriods } from '/src/src/features/backtest/utils/calculateDcaPeriods';
import { aggregateReturns } from '/src/src/shared/utils/dataSampling/returnAggregation';
import { generateTextReport, generateCSVReport } from '/src/src/features/backtest/services/reportGenerator';
const stock={symbol:'TEST',amount:0,weight:100,investmentType:'dca',dcaFrequency:'monthly_1',assetType:'stock'};
const weightResult=recalcAmountsByWeight([stock],10000,'2023-01-02','2023-10-31');
const all=[];
for(let i=0;i<21;i++){
  const d=new Date(Date.UTC(2023,0,2+i));
  all.push({date:d.toISOString().slice(0,10),return_pct:d.getUTCDay()===0||d.getUTCDay()===6?0:1});
}
const business=all.filter(p=>new Date(p.date).getUTCDay()!==0&&new Date(p.date).getUTCDay()!==6);
const selectedSymbol='TEST',aggregationType='daily';
const selectedStockData={symbol:'TEST',data:[{date:'2023-01-03',price:100},{date:'2023-01-04',price:110}]};
const tradeLogs={TEST:[{EntryTime:'2023-01-03T00:00:00',ExitTime:'2023-01-04T00:00:00',EntryPrice:100,ExitPrice:110,Size:1}]};
const findClosestAggregationDate=${fragments.findClosestAggregationDate};
const signals=(${fragments.chartDataWithSignals})();
const outcomes=JSON.parse(fs.readFileSync('/reports/engine-results.json','utf8'));
const valid=outcomes.find(x=>x.name==='dca_growth').output.data;
const overflow=outcomes.find(x=>x.name==='finite_input_overflow').output;
const csvFinalRow=generateCSVReport(valid,true).split(String.fromCharCode(10)).find(line=>line.startsWith('최종 자산가치,'));
const exportResults={textIncludesFinal:generateTextReport(valid,true).includes('3000.00'),csvFinalRow,csvFinalRowColumns:(csvFinalRow.match(/(?:"(?:[^"]|"")*"|[^,]+)(?:,|$)/g)||[]).length};
assert.equal(overflow.error_code,422);
assert.equal(weightResult[0].totalAmount,10000);
assert.equal(weightResult[0].amount,1000);
assert.equal(exportResults.csvFinalRowColumns,2);
assert.equal(signals[0].buySignal,100);
assert.equal(signals[1].sellSignal,110);
assert.equal(signals[1].buySignal,undefined);
assert.deepEqual(aggregateReturns(business,'weekly'),aggregateReturns(all,'weekly'));
const result={dca:{periods:calculateDcaPeriods('2023-01-02','2023-10-31','monthly_1'),weightResult},weekly:{stock:aggregateReturns(business,'weekly'),benchmark:aggregateReturns(all,'weekly')},signals,exportResults};
process.stdout.write(JSON.stringify(result));
`;
const compiled=ts.transpileModule(source,{compilerOptions:options}).outputText;
const m=new Module('/reports/frontend-probe.cjs',module);
const chunks=[];
const write=process.stdout.write;
process.stdout.write=(s)=>{chunks.push(String(s));return true;};
try {m._compile(compiled,'/reports/frontend-probe.cjs');} finally {process.stdout.write=write;}
const result=chunks.join('');
fs.writeFileSync('/reports/frontend-results.json',result);
process.stdout.write(result+'\n');
