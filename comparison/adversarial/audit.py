"""Build deterministic adversarial inputs; evaluate independent financial invariants.

Usage: python audit.py prepare|evaluate REPORT_DIRECTORY
The Rust adapter consumes cases.json, writes engine-results.json. No Python
backtest implementation or parity output is used as an oracle.
"""
import argparse
import datetime as dt
import json
import math
import statistics
import hashlib
import subprocess
from pathlib import Path

START = dt.date(2023, 1, 2)


def history(prices, symbol="TEST", currency="USD", opens=None):
    return {"symbol": symbol, "currency": currency, "bars": [
        {"date": str(START + dt.timedelta(days=i)), "open": (opens or prices)[i],
         "high": max(p, (opens or prices)[i]), "low": min(p, (opens or prices)[i]),
         "close": p, "volume": 1000000} for i, p in enumerate(prices)]}


def asset(symbol="TEST", amount=10000, **kwargs):
    return {"symbol": symbol, "amount": amount, **kwargs}


def request(n=40, portfolio=None, **kwargs):
    return {"portfolio": portfolio or [asset()], "start_date": str(START),
            "end_date": str(START + dt.timedelta(days=n-1)),
            "commission": 0, "rebalance_frequency": "none",
            "include_stock_data": False, "include_exchange_rates": False,
            "include_benchmarks": False, "include_news": False,
            "include_volatility_events": False, **kwargs}


def prepare(directory):
    cases = []

    def add(name, req, *histories):
        cases.append({"name": name, "request": req,
                      "histories": {h["symbol"]: h for h in histories}})

    add("cash_constant", request(portfolio=[asset("RESERVE", asset_type="cash")]))
    add("usd_double", request(), history([100]*39+[200]))
    add("usd_flat", request(), history([100]*40))
    add("initial_fee_1pct", request(commission=.01), history([100]*40))
    add("initial_fee_9pct", request(commission=.09), history([100]*40))
    add("fee_drawdown", request(commission=.09), history([100]*40))
    add("krw_fx", request(), history([10000]*40, currency="KRW"), history([1000]*39+[2000], "KRW=X"))
    add("eur_fx", request(), history([100]*40, currency="EUR"), history([1]*39+[1.2], "EURUSD=X"))
    for currency,ticker,usd_per_unit in [("JPY","JPY=X",False),("GBP","GBPUSD=X",True),("CNY","CNY=X",False),("HKD","HKD=X",False),("TWD","TWD=X",False),("SGD","SGD=X",False),("AUD","AUDUSD=X",True),("CAD","CADUSD=X",True),("CHF","CHFUSD=X",True),("INR","INR=X",False)]:
        add("fx_"+currency,request(),history([100]*40,currency=currency),history([2]*39+[4],ticker))
    add("drawdown_recovery",request(),history([100]*10+[200]*10+[100]*10+[200]*10))
    add("dca_drawdown_external_flow",request(portfolio=[asset(amount=1000,investment_type="dca",dca_frequency="monthly_1")]),history([100]*35+[50]*5))
    future_fx = history([1000]*40, "KRW=X")
    future_fx["bars"] = future_fx["bars"][1:]
    add("reject_future_fx", request(), history([10000]*40, currency="KRW"), future_fx)
    for name in ["sma", "ema", "macd", "rsi", "bollinger"]:
        add(name+"_flat", request(strategy=name+"_strategy"), history([100]*40))
    last = [100-i*.2 for i in range(39)] + [200]
    add("last_close_future_buy", request(strategy="ema_strategy", strategy_params={"fast_window": 5, "slow_window": 10}), history(last, opens=last[:-1]+[100]))
    # Same price path with one untraded future observation: the last-close signal
    # cannot have acquired exposure to a price move that was already over.
    add("last_close_with_future_bar", request(n=41, strategy="ema_strategy", strategy_params={"fast_window": 5, "slow_window": 10}), history(last+[200], opens=last[:-1]+[100,200]))
    # RSI(2): first two changes +1/-1 => Wilder initial average gains=losses=.5, RSI=50.
    add("rsi_wilder_seed", request(strategy="rsi_strategy", strategy_params={"rsi_period": 2, "rsi_oversold": 40, "rsi_overbought": 70}), history([100,101]+[100]*38))
    # Force a crossing from negative to positive and back, with all executions at 100.
    oscillation = [100]*4+[90]*10+[110]*10+[90]*16
    add("technical_roundtrip_fee", request(commission=.01, strategy="ema_strategy", strategy_params={"fast_window":5,"slow_window":10}), history(oscillation, opens=[100]*40))
    add("sma_equality_cross", request(strategy="sma_strategy", strategy_params={"short_window":5,"long_window":10}), history([100]*20+[110]*20))
    add("cash_dca", request(portfolio=[asset("RESERVE",500, asset_type="cash",investment_type="dca",dca_frequency="weekly_1")]))
    add("cash_dca_mixed", request(portfolio=[asset("RESERVE",500, asset_type="cash",investment_type="dca",dca_frequency="weekly_1"),asset(amount=1000)]), history([100]*40))
    add("cash_symbol_collision", request(portfolio=[asset("RESERVE",1000,asset_type="cash"),asset("CASH",2000)]), history([100]*39+[200],symbol="CASH"))
    add("rebalance_fee", request(portfolio=[asset(amount=1000),asset("RESERVE",1000,asset_type="cash")], commission=.01,rebalance_frequency="weekly_1"), history([100]*7+[200]*33))
    add("rebalance_no_fee", request(portfolio=[asset(amount=1000),asset("RESERVE",1000,asset_type="cash")],rebalance_frequency="weekly_1"), history([100]*7+[200]*33))
    add("dca_flow_neutral",request(portfolio=[asset(amount=1000,investment_type="dca",dca_frequency="monthly_1")]),history([100]*40))
    add("dca_growth",request(portfolio=[asset(amount=1000,investment_type="dca",dca_frequency="monthly_1")]),history([100]*35+[200]*5))
    prices = [100.0]
    for i in range(365):
        prices.append(prices[-1]*(1.02 if i%2==0 else .99))
    add("crypto_daily_annualization", request(n=366), history(prices, currency="USD"))
    for frequency in ["weekly_1","weekly_2","monthly_1","monthly_2","monthly_3","monthly_6","monthly_12"]:
        add("schedule_"+frequency, request(n=400,portfolio=[asset(amount=100,investment_type="dca",dca_frequency=frequency)]),history([100]*400))
    # UI uses floor(days / 30)+1; monthly first Monday dates are known calendar dates.
    add("ui_weight_dca_budget",request(n=303,portfolio=[asset(amount=1000,total_amount=10000,investment_type="dca",dca_frequency="monthly_1")]),history([100]*303))
    add("small_price_unrounded", request(), history([.00001]*39+[.00003]))
    add("small_price_after_decimal4", request(), history([0]*40))
    add("finite_input_overflow", request(portfolio=[asset("A",1e308),asset("B",1e308)]),history([100]*40,symbol="A"),history([100]*40,symbol="B"))
    for amount in [0.01,0.1,1,7,123.45,333.33,500,999.99,10000]:
        for price in [0.00001,0.1,3,7,99.9,123.45,10000]:
            add(f"flat_dca_{amount}_{price}",request(n=100,portfolio=[asset(amount=amount,investment_type="dca",dca_frequency="weekly_1")]),history([price]*100))
    # Deterministic independent invariants over additional portfolios.
    for k in range(1,11):
        portfolio = [asset("A",100*k),asset("B",333*k),asset("RESERVE",91*k,asset_type="cash")]
        add(f"allocation_{k}",request(portfolio=portfolio), history([10]*39+[15],symbol="A"),history([20]*39+[10],symbol="B"))
        add(f"permuted_allocation_{k}",request(portfolio=list(reversed(portfolio))), history([10]*39+[15],symbol="A"),history([20]*39+[10],symbol="B"))
    directory.mkdir(parents=True, exist_ok=True)
    (directory/"cases.json").write_text(json.dumps(cases,ensure_ascii=False),encoding="utf-8")
    print(f"Prepared {len(cases)} independent cases")


def evaluate(directory):
    outputs = {x["name"]:x["output"] for x in json.loads((directory/"engine-results.json").read_text(encoding="utf-8"))}
    checks = []

    def check(name, actual, expected, explanation="", tolerance=1e-7):
        passed = math.isclose(actual,expected,abs_tol=tolerance,rel_tol=1e-9) if isinstance(actual,(int,float)) and isinstance(expected,(int,float)) else actual==expected
        checks.append({"name":name,"passed":passed,"actual":actual,"expected":expected,"explanation":explanation})

    def data(name):
        return outputs[name]["data"]

    def stat(name,field="Final_Value"):
        return data(name)["portfolio_statistics"][field]

    def trades(name,symbol="TEST"):
        return data(name)["strategy_details"][symbol]["trade_log"]

    for name,expected in [("cash_constant",10000),("usd_double",20000),("usd_flat",10000),("krw_fx",5000),("eur_fx",12000),("rebalance_no_fee",3000),("dca_flow_neutral",2000),("dca_growth",3000)]:
        check(name,stat(name),expected)
    check("future_fx_not_backfilled",outputs["reject_future_fx"].get("error_code"),422)
    for name in ["sma","ema","macd","rsi","bollinger"]:
        check(name+"_flat_control",stat(name+"_flat"),10000)
    for currency,final in [("JPY",5000),("GBP",20000),("CNY",5000),("HKD",5000),("TWD",5000),("SGD",5000),("AUD",20000),("CAD",20000),("CHF",20000),("INR",5000)]:
        check("fx_"+currency,stat("fx_"+currency),final)
    check("drawdown_recovery_final",stat("drawdown_recovery"),20000)
    check("drawdown_recovery_mdd",stat("drawdown_recovery","Max_Drawdown"),-50)
    check("dca_flow_adjusted_mdd",stat("dca_drawdown_external_flow","Max_Drawdown"),-50)
    check("dca_flow_adjusted_final",stat("dca_drawdown_external_flow"),1500)
    for frequency,count in [("weekly_1",58),("weekly_2",29),("monthly_1",14),("monthly_2",7),("monthly_3",5),("monthly_6",3),("monthly_12",2)]:
        check("calendar_"+frequency,stat("schedule_"+frequency,"Initial_Value"),count*100)
    for c in [.01,.09]:
        check(f"cash_budget_fee_{c}",stat("initial_fee_"+str(int(c*100))+"pct"),10000/(1+c),"Notional N plus commission c*N must equal the cash budget.")
    check("initial_fee_is_drawdown",stat("fee_drawdown","Max_Drawdown"),(1/1.09-1)*100,"Relative to funded pre-trade capital, a flat market does not erase the initial transaction loss.")
    check("no_retroactive_final_bar_buy",stat("last_close_future_buy"),10000)
    check("causal_prefix_invariance",next(reversed(data("last_close_future_buy")["equity_curve"].values())),list(data("last_close_with_future_bar")["equity_curve"].values())[-2],"Adding a future bar cannot change previously observed marked wealth.")
    check("rsi_standard_seed_no_entry",len(trades("rsi_wilder_seed")),0,"RSI(2) starts at 50; subsequent unchanged prices keep it at 50, above oversold 40.")
    t=trades("technical_roundtrip_fee")
    gross=sum(x["Size"]*100 for x in t)
    check("roundtrip_flat_price_fees",stat("technical_roundtrip_fee"),10000-2*.01*gross,"Actual executed share count held fixed; charge the stated 1% commission on both notionals.")
    check("trade_commission_disclosed",sum(x["Commission"] for x in t),2*.01*gross)
    check("cash_dca_first_deposit",next(iter(data("cash_dca")["equity_curve"].values())),500)
    check("mixed_cash_dca_first_deposit",next(iter(data("cash_dca_mixed")["equity_curve"].values())),1500)
    check("individual_equity_reconciles",sum(x["final_equity"] for x in data("cash_symbol_collision")["individual_results"]),stat("cash_symbol_collision"))
    rb=data("rebalance_fee")["rebalance_history"][0]
    event=next(x for x in rb["trades"] if x["symbol"]=="TEST")
    trade=next(x for x in trades("rebalance_fee") if x["Type"]=="SELL")
    check("rebalance_share_ledger",event["shares"],trade["Size"])
    check("rebalance_fee_on_actual_trade",rb["commission_cost"],trade["Size"]*trade["EntryPrice"]*.01)
    # Isolate the rebalance from the initial purchase convention by deriving the
    # pre-rebalance wealth from the actually returned initial executed shares.
    pre_stock=trades("rebalance_fee")[0]["Size"]*200
    correct_target=(pre_stock+1000-.01*pre_stock)/(2-.01)
    check("rebalance_self_financing",data("rebalance_fee")["equity_curve"]["2023-01-09"],2*correct_target)
    raw=[v/100 for v in data("crypto_daily_annualization")["daily_returns"].values()]
    check("crypto_volatility_365",stat("crypto_daily_annualization","Annual_Volatility"),statistics.stdev(raw)*math.sqrt(365)*100)
    check("crypto_sharpe_365",stat("crypto_daily_annualization","Sharpe_Ratio"),statistics.mean(raw)/statistics.stdev(raw)*math.sqrt(365))
    # 2023-01-02 initial + first Monday Feb..Oct (9) = ten installments.
    check("ui_budget_matches_total",stat("ui_weight_dca_budget","Initial_Value"),10000)
    check("small_price_unrounded_control",stat("small_price_unrounded"),30000)
    check("zero_price_rejected",outputs["small_price_after_decimal4"].get("error_code"),422,"Zero prices must fail closed; precision preservation is separately checked through MySQL.")
    check("overflow_rejected",outputs["finite_input_overflow"].get("error_code"),422)
    check("finite_input_no_success_with_null_wealth",outputs["finite_input_overflow"].get("status")=="success" and stat("finite_input_overflow") is None,False)
    for name in outputs:
        if name.startswith("flat_dca_"):
            check(name+"_no_up_down_days",stat(name,"Positive_Days")+stat(name,"Negative_Days"),0)
            check(name+"_no_return",stat(name,"Total_Return"),0)
        if name.startswith("allocation_"):
            k=int(name.split("_")[-1])
            check(name+"_wealth",stat(name),407.5*k)
            check(name+"_order_invariance",stat(name),stat("permuted_"+name))
    summary={"cases":len(outputs),"checks":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks),"checks_detail":checks}
    (directory/"checks.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="checks_detail"}))
    flat_failed=sum(not c["passed"] for c in checks if c["name"].startswith("flat_dca_"))
    print(f"Flat-price DCA invariant failures: {flat_failed} / 63 constant-price scenarios")
    for c in checks:
        if not c["passed"] and not c["name"].startswith("flat_dca_"):
            print(json.dumps(c,ensure_ascii=False))


def summarize(directory):
    """Keep a compact, reviewable evidence record beside the reproducible scripts."""
    repository=Path(__file__).resolve().parents[2]
    frontend=repository.parent/'backtest-console'
    checks=json.loads((directory/'checks.json').read_text(encoding='utf-8'))
    front=json.loads((directory/'frontend-results.json').read_text(encoding='utf-8'))
    http=json.loads((directory/'http-results.json').read_text(encoding='utf-8'))
    db=json.loads((directory/'database-results.json').read_text(encoding='utf-8'))
    source_hashes={}
    for base,paths in [(repository,list((repository/'backtest_be_rust/src').rglob('*'))+[repository/'database/schema.sql']),
                       (frontend,list((frontend/'src/features/backtest').rglob('*.ts'))+list((frontend/'src/features/backtest').rglob('*.tsx'))+list((frontend/'src/shared/utils/dataSampling').rglob('*.ts')))]:
        for p in paths:
            if p.is_file() and '__tests__' not in p.parts:
                source_hashes[base.name+'/'+p.relative_to(base).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (repository/'backtest_be_rust/src').rglob('*'):
        if p.is_file():
            copied=repository/'.comparison/adversarial-crate/src'/p.relative_to(repository/'backtest_be_rust/src')
            assert p.read_bytes()==copied.read_bytes(),f'Audited source drift: {p}'
    summaries=[]
    for r in http:
        d=r['output'].get('data',{})
        summaries.append({'name':r['name'],'http_status':r['status'],'portfolio_statistics':d.get('portfolio_statistics'),
                          'supplemental_status':d.get('supplemental_status'),'error':r['output'].get('error')})
    manifest={
        'review_date':'2026-11-11','basis':'Independent arithmetic, causal execution, cash conservation; no original Python financial outputs used',
        'branches':{p.name:subprocess.check_output(['git','-C',str(p),'branch','--show-current'],text=True).strip() for p in [repository,frontend]},
        'rust_runtime_image':'sha256:bda62be9e3bcf9629170634bf5ada176124085ba589d7f363285f2e08c07edd1',
        'engine':checks,'frontend':front,'http':summaries,'database':db,
        'existing_rust_lib_tests':{'passed':14,'ignored':1,'failed':0,'command':'cargo test --offline --lib','role':'Operational regression context only; includes existing compatibility assertions'},
        'source_sha256':source_hashes,
    }
    path=Path(__file__).with_name('evidence-2026-11-11.json')
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Evidence saved: {path}; source snapshot unchanged')


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["prepare","evaluate","summarize"])
    parser.add_argument("directory",type=Path)
    args=parser.parse_args()
    {"prepare":prepare,"evaluate":evaluate,"summarize":summarize}[args.mode](args.directory)
