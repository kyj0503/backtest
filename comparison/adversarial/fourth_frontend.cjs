// Real report function, actual engine ledger: precision loss in fractional units.
const fs=require('node:fs'),ts=require('/app/node_modules/typescript'),Module=require('node:module');
const opts={module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true};
for(const ext of ['.ts','.tsx'])require.extensions[ext]=(m,f)=>m._compile(ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:opts}).outputText,f);
const resolve=Module._resolveFilename;
Module._resolveFilename=function(name,parent,...args){return resolve.call(this,name.startsWith('@/')?'/src/src/'+name.slice(2):name,parent,...args);};
const {generateCSVReport}=require('/src/src/features/backtest/services/reportGenerator.ts');
const cases=JSON.parse(fs.readFileSync('/reports/engine-results.json','utf8'));
const d=cases.find(c=>c.name==='fractional_csv_quantity').output.data;
const csv=generateCSVReport(d,true);
fs.writeFileSync('/reports/fractional-quantity.csv',csv);
const rows=[];
for(const event of d.rebalance_history)for(const trade of event.trades){
 if(trade.symbol!=='HIGH')continue;
 const line=csv.split('\n').find(l=>l.startsWith(event.date+',HIGH,'));
 const cells=line.split(',');
 rows.push({date:event.date,trade,csv:line,exportedQuantity:Number(cells[4]),exportedNotional:Number(cells[3]),reconstructedNotional:Number(cells[4])*Number(cells[5])});
}
fs.writeFileSync('/reports/fourth-frontend-results.json',JSON.stringify(rows,null,2));
console.log(JSON.stringify(rows));
