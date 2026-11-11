// Executes the actual reducer, validator, extractor, and chart callbacks.
const fs=require('node:fs'), ts=require('/app/node_modules/typescript'), Module=require('node:module');
const src=process.env.AUDIT_FE_SOURCE||'/src';
const reportDir=process.env.AUDIT_RESULT_DIR||'/reports';
const opts={module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true};
require.extensions['.ts']=(m,f)=>m._compile(ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:opts}).outputText,f);
const resolve=Module._resolveFilename;
Module._resolveFilename=function(name,parent,...args){return resolve.call(this,name.startsWith('@/')?src+'/src/'+name.slice(2):name,parent,...args);};
const feature=src+'/src/features/backtest/';
const {recalcAmountsByWeight,backtestFormReducer,backtestFormHelpers}=require(feature+'model/backtestFormReducer.ts');
const {initialBacktestFormState}=require(feature+'model/types/backtest-form-types.ts');
const {validateBacktestForm}=require(feature+'hooks/useFormValidation.ts');
const {extractTradeLogs}=require(feature+'utils/chartDataTransform.ts');
const {calculateDcaPeriods}=require(feature+'utils/calculateDcaPeriods.ts');
const stock=(symbol,weight)=>({symbol,weight,amount:10000,assetType:'stock',investmentType:'lump_sum',dcaFrequency:'monthly_1'});
const makeState=portfolio=>({...initialBacktestFormState,portfolioInputMode:'weight',portfolio,totalInvestment:10000,
  dates:{startDate:'2023-01-02',endDate:'2023-02-10'},settings:{...initialBacktestFormState.settings,commission:0,rebalanceFrequency:'none'},
  strategy:{selectedStrategy:'buy_hold_strategy',strategyParams:{}}});
const allocations={};
for(const weights of [[95,10],[10,95],[50,45],[45,50]]){
  const p=recalcAmountsByWeight([stock('A',weights[0]),stock('B',weights[1])],10000,'2023-01-02','2023-02-10');
  allocations[weights.join('+')]={portfolio:p,validation:validateBacktestForm(makeState(p))};
}
let added=makeState(recalcAmountsByWeight([stock('A',100)],10000));
added=backtestFormReducer(added,{type:'ADD_STOCK',payload:backtestFormHelpers.addStock()});
added=backtestFormReducer(added,{type:'UPDATE_STOCK',payload:{index:1,field:'symbol',value:'B'}});
let removed=makeState(recalcAmountsByWeight([stock('A',5),stock('B',95)],10000));
removed=backtestFormReducer(removed,{type:'REMOVE_STOCK',payload:0});
const outcomes=JSON.parse(fs.readFileSync(reportDir+'/engine-results.json','utf8'));
const opened=outcomes.find(x=>x.name==='open_position').output.data;
const tradeLogs=extractTradeLogs(opened.strategy_details);
const selectedSymbol='TEST', aggregationType='daily';
const cases=JSON.parse(fs.readFileSync(reportDir+'/cases.json','utf8'));
const selectedStockData={symbol:'TEST',data:cases.find(x=>x.name==='open_position').histories.TEST.bars.map(b=>({date:b.date,price:b.close}))};
const file=feature+'components/StockPriceChart.tsx';
const tree=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
const printer=ts.createPrinter(),parts={};
function visit(n){
 if(ts.isVariableDeclaration(n)&&ts.isIdentifier(n.name)&&['findClosestAggregationDate','chartDataWithSignals','tradeCount'].includes(n.name.text)){
   parts[n.name.text]=printer.printNode(ts.EmitHint.Expression,n.name.text==='findClosestAggregationDate'?n.initializer:n.initializer.arguments[0],tree);
 }
 ts.forEachChild(n,visit);
}
visit(tree);
const transpile=s=>ts.transpileModule(s,{compilerOptions:opts}).outputText;
const findClosestAggregationDate=eval(transpile('('+parts.findClosestAggregationDate+')'));
const signals=eval(transpile('('+parts.chartDataWithSignals+')'))();
const counts=eval(transpile('('+parts.tradeCount+')'))();
const cashOutcome=outcomes.find(x=>x.name==='cash_weight_chart').output.data;
const weightFile=feature+'components/results/WeightHistoryChart.tsx';
const weightTree=ts.createSourceFile(weightFile,fs.readFileSync(weightFile,'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
let weightExpression;
function weightVisit(n){
  if(ts.isVariableDeclaration(n)&&ts.isIdentifier(n.name)&&n.name.text==='chartData')weightExpression=printer.printNode(ts.EmitHint.Expression,n.initializer.arguments[0],weightTree);
  ts.forEachChild(n,weightVisit);
}
weightVisit(weightTree);
const symbols=Array.from(new Set(cashOutcome.portfolio_composition.map(a=>a.symbol)));
const weightHistory=cashOutcome.weight_history;
const weightChart=eval(transpile('('+weightExpression+')'))();
const permutation=[stock('A',95),stock('B',10)];
const result={allocations,addStock:{portfolio:added.portfolio,validation:validateBacktestForm(added),total:added.portfolio.reduce((s,a)=>s+(a.totalAmount??a.amount),0)},
 removeStock:{portfolio:removed.portfolio,validation:validateBacktestForm(removed),total:removed.portfolio.reduce((s,a)=>s+(a.totalAmount??a.amount),0)},
 openPosition:{apiPositions:opened.strategy_details.TEST.open_positions,logs:tradeLogs,chartCounts:counts,buyMarkers:signals.filter(p=>p.buySignal!==undefined).length},
 cashWeights:{composition:cashOutcome.portfolio_composition,raw:weightHistory[0],rendered:weightChart[0]},
 orderPermutation:[permutation,[...permutation].reverse()].map(p=>recalcAmountsByWeight(p,10000,'2023-01-02','2023-02-10')),
 monthly2Periods:calculateDcaPeriods('2023-01-30','2023-03-29','monthly_2')};
fs.writeFileSync(reportDir+'/frontend-results.json',JSON.stringify(result,null,2));
process.stdout.write(JSON.stringify(result,null,2)+'\n');
