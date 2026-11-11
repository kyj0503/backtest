//! Yahoo adapter probes use the library's own deserializer and quote validation.
use backtest_server::{data::parse_chart, engine, model::{BacktestRequest, Histories}};
use chrono::{Duration, NaiveDate};
use serde_json::{json,Value};
use tokio_util::sync::CancellationToken;
fn main(){
 let dir=std::env::args().nth(1).unwrap();
 let start=NaiveDate::from_ymd_opt(2023,1,2).unwrap();
 let meta=yahoo_finance_api::YMetaData{symbol:"TEST".into(),currency:Some("USD".into()),exchange_timezone_name:"UTC".into(),..Default::default()};
 let mut meta=serde_json::to_value(meta).unwrap();meta.as_object_mut().unwrap().remove("tradingPeriods");
 let times:Vec<_>=(0..40).map(|i|(start+Duration::days(i)).and_hms_opt(0,0,0).unwrap().and_utc().timestamp()).collect();
 let base=json!({"chart":{"error":null,"result":[{"meta":meta,"timestamp":times,"indicators":{"quote":[{"open":vec![100.;40],"high":vec![100.;40],"low":vec![100.;40],"close":vec![100.;40],"volume":vec![1000;40]}],"adjclose":[{"adjclose":vec![50.;40]}]}}]}});
 let mut outputs=vec![];
 for name in ["adjusted_control","missing_adjustment_last","missing_adjustment_middle","zero_close","open_outside_range","execution_control","invalid_open_execution"] {
  let mut v=base.clone();
  match name {
   "missing_adjustment_last"=>v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][39]=Value::Null,
   "missing_adjustment_middle"=>v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][20]=Value::Null,
   "zero_close"=>v["chart"]["result"][0]["indicators"]["quote"][0]["close"][20]=json!(0.),
   "open_outside_range"=>v["chart"]["result"][0]["indicators"]["quote"][0]["open"][20]=json!(1000.),
   _=>{}
  }
  let execution=name.ends_with("execution") || name=="execution_control";
  if execution {
   v["chart"]["result"][0]["indicators"]["quote"][0]["open"][5]=json!(80.);
   v["chart"]["result"][0]["indicators"]["quote"][0]["close"][5]=json!(80.);
   v["chart"]["result"][0]["indicators"]["quote"][0]["low"][5]=json!(80.);
   v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][5]=json!(40.);
   v["chart"]["result"][0]["indicators"]["quote"][0]["open"][6]=json!(if name=="execution_control" {80.}else{1.});
   v["chart"]["result"][0]["indicators"]["quote"][0]["low"][6]=json!(80.);
  }
  let response=yahoo_finance_api::YResponse::from_json(v.clone()).unwrap();
  let quotes=response.quotes();
  let h=parse_chart("TEST",serde_json::to_value(response).unwrap());
  let output=match h {
   Ok(h)=>{
    let mut request:BacktestRequest=serde_json::from_value(json!({"portfolio":[{"symbol":"TEST","amount":10000}],"start_date":start,"end_date":start+Duration::days(39),"commission":0,"rebalance_frequency":"none"})).unwrap();
    if execution {request.strategy="bollinger_strategy".into();request.strategy_params=serde_json::from_value(json!({"period":5,"std_dev":1})).unwrap();}
    let data=Histories::from([("TEST".into(),h.clone())]);
    json!({"history":h,"engine":engine::run(&request,&data,&CancellationToken::new()).unwrap()})
   },Err(e)=>json!({"error_code":e.0,"error":e.1})
  };
  outputs.push(json!({"name":name,"library_quotes_ok":quotes.is_ok(),"input":v,"output":output}));
 }
 std::fs::write(format!("{dir}/provider-results.json"),serde_json::to_vec_pretty(&outputs).unwrap()).unwrap();
 for c in outputs {println!("{} quotes_ok={} final={} MDD={} bars={}",c["name"],c["library_quotes_ok"],c["output"]["engine"]["data"]["portfolio_statistics"]["Final_Value"],c["output"]["engine"]["data"]["portfolio_statistics"]["Max_Drawdown"],c["output"]["history"]["bars"].as_array().map_or(0,Vec::len));}
}
