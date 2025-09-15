Started by GitHub push by kyj0503
Obtained Jenkinsfile from git https://github.com/capstone-backtest/backtest.git
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins
 in /var/lib/jenkins/workspace/Backtest
[Pipeline] {
[Pipeline] withEnv
[Pipeline] {
[Pipeline] timestamps
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Checkout)
[Pipeline] checkout
 The recommended git tool is: /usr/bin/git
 using credential github-token
 Cloning the remote Git repository
 Cloning repository https://github.com/capstone-backtest/backtest.git
  > /usr/bin/git init /var/lib/jenkins/workspace/Backtest # timeout=10
 Fetching upstream changes from https://github.com/capstone-backtest/backtest.git
  > /usr/bin/git --version # timeout=10
  > git --version # 'git version 2.43.0'
 using GIT_ASKPASS to set credentials GHCR Token (Username/Password type)
  > /usr/bin/git fetch --tags --force --progress -- https://github.com/capstone-backtest/backtest.git +refs/heads/*:refs/remotes/origin/* # timeout=10
  > /usr/bin/git config remote.origin.url https://github.com/capstone-backtest/backtest.git # timeout=10
  > /usr/bin/git config --add remote.origin.fetch +refs/heads/*:refs/remotes/origin/* # timeout=10
 Avoid second fetch
  > /usr/bin/git rev-parse refs/remotes/origin/main^{commit} # timeout=10
 Checking out Revision d441a77c0978d4f661ed76aacb13b564f3e63e5d (refs/remotes/origin/main)
  > /usr/bin/git config core.sparsecheckout # timeout=10
  > /usr/bin/git checkout -f d441a77c0978d4f661ed76aacb13b564f3e63e5d # timeout=10
 Commit message: "ci(jenkins): prevent ARD storms — disable concurrent builds, run containers as jenkins UID/GID, and disable deferred wipeout in cleanWs"
  > /usr/bin/git rev-list --no-walk 50cf3890d568f5aca6211253574fdbdf69bc6ac3 # timeout=10
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Debug Environment)
[Pipeline] script
[Pipeline] {
[Pipeline] echo
 Debug Information:
[Pipeline] echo
 BRANCH_NAME: null
[Pipeline] echo
 GIT_BRANCH: null
[Pipeline] echo
 BUILD_NUMBER: 142
[Pipeline] echo
 All env vars:
[Pipeline] sh
 + id -u
[Pipeline] sh
 + id -g
[Pipeline] sh
 + env
 + grep -E (BRANCH|GIT)
 + sort
 + echo UID_J=131 GID_J=134
 UID_J=131 GID_J=134
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Tests)
[Pipeline] parallel
[Pipeline] { (Branch: Frontend Tests)
[Pipeline] { (Branch: Backend Tests)
[Pipeline] stage
[Pipeline] { (Frontend Tests)
[Pipeline] stage
[Pipeline] { (Backend Tests)
[Pipeline] script
[Pipeline] {
[Pipeline] script
[Pipeline] {
[Pipeline] echo
 Running frontend tests...
[Pipeline] sh
[Pipeline] echo
 Running backend tests with controlled environment...
[Pipeline] sh
 + cd frontend
 + docker build --build-arg RUN_TESTS=true -t backtest-frontend-test:142 .
 + cd backend
 + docker build --build-arg RUN_TESTS=true -t backtest-backend-test:142 .
 #0 building with "default" instance using docker driver
 
 #1 [internal] load build definition from Dockerfile
 #1 transferring dockerfile: 983B done
 #1 DONE 0.0s
 
 #2 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
 #2 DONE 0.0s
 
 #3 [internal] load metadata for docker.io/library/node:20.8.1-alpine
 #0 building with "default" instance using docker driver
 
 #1 [internal] load build definition from Dockerfile
 #1 transferring dockerfile: 1.54kB done
 #1 DONE 0.0s
 
 #2 [internal] load metadata for docker.io/library/python:3.11-slim
 #2 DONE 0.9s
 
 #3 [internal] load .dockerignore
 #3 transferring context: 92B done
 #3 DONE 0.0s
 
 #4 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
 #4 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
 #4 DONE 0.0s
 
 #5 [internal] load build context
 #5 transferring context: 861.84kB 0.1s done
 #5 DONE 0.1s
 
 #6 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
 #6 CACHED
 
 #7 [ 7/13] RUN uv pip install --system -r requirements.txt
 #7 CACHED
 
 #8 [ 8/13] RUN uv pip install --system -r requirements-test.txt
 #8 CACHED
 
 #9 [11/13] COPY tests ./tests
 #9 CACHED
 
 #10 [12/13] COPY run_server.py .
 #10 CACHED
 
 #11 [ 5/13] COPY requirements-test.txt .
 #11 CACHED
 
 #12 [ 4/13] COPY requirements.txt .
 #12 CACHED
 
 #13 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
 #13 CACHED
 
 #14 [ 9/13] RUN uv pip install --system backtesting
 #14 CACHED
 
 #15 [10/13] COPY app ./app
 #15 CACHED
 
 #16 [ 2/13] WORKDIR /app
 #16 CACHED
 
 #17 [13/13] RUN if [ "true" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
 #17 CACHED
 
 #18 exporting to image
 #18 exporting layers done
 #18 writing image sha256:1ba01f03d4c37307467b353f5e1f334969c441f32b18d25d2e41913337db5a2a done
 #18 naming to docker.io/library/backtest-backend-test:142 done
 #18 DONE 0.0s
[Pipeline] echo
 Backend tests passed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
 #3 DONE 1.8s
 
 #4 [internal] load .dockerignore
 #4 transferring context: 2B done
 #4 DONE 0.0s
 
 #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
 #5 DONE 0.0s
 
 #6 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
 #6 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
 #6 DONE 0.0s
 
 #7 [internal] load build context
 #7 transferring context: 913.28kB 0.1s done
 #7 DONE 0.1s
 
 #8 [build 7/7] RUN npm run build
 #8 CACHED
 
 #9 [build 3/7] COPY package.json package-lock.json ./
 #9 CACHED
 
 #10 [build 4/7] RUN npm ci --no-audit --prefer-offline --no-fund
 #10 CACHED
 
 #11 [build 5/7] COPY . .
 #11 CACHED
 
 #12 [build 6/7] RUN if [ "true" = "true" ] ; then npm test -- --run ; fi
 #12 CACHED
 
 #13 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
 #13 CACHED
 
 #14 [build 2/7] WORKDIR /app
 #14 CACHED
 
 #15 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
 #15 CACHED
 
 #16 exporting to image
 #16 exporting layers done
 #16 writing image sha256:03593e5d697037e46892689aaf45fe32c3a0a82252c5c9740a9c578e60d4ea19 done
 #16 naming to docker.io/library/backtest-frontend-test:142 done
 #16 DONE 0.0s
[Pipeline] echo
 Frontend tests passed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // parallel
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Collect JUnit Reports)
[Pipeline] script
[Pipeline] {
[Pipeline] sh
 + mkdir -p reports/backend reports/frontend
 + docker run --rm -u 131:134 -v /var/lib/jenkins/workspace/Backtest/reports/backend:/reports backtest-backend-test:142 sh -lc pytest tests/unit/ -v --tb=short --junitxml=/reports/junit.xml
 /usr/local/lib/python3.11/site-packages/hypothesis/_settings.py:968: HypothesisWarning: The database setting is not configured, and the default location is unusable - falling back to an in-memory database for this session.  path=PosixPath('/app/.hypothesis/examples')
   value = getattr(self, name)
 /usr/local/lib/python3.11/site-packages/hypothesis/_settings.py:969: HypothesisWarning: The database setting is not configured, and the default location is unusable - falling back to an in-memory database for this session.  path=PosixPath('/app/.hypothesis/examples')
   if value != getattr(default, name):
 ============================= test session starts ==============================
 platform linux -- Python 3.11.13, pytest-7.4.3, pluggy-1.6.0 -- /usr/local/bin/python
 cachedir: .pytest_cache
 metadata: {'Python': '3.11.13', 'Platform': 'Linux-6.14.0-29-generic-x86_64-with-glibc2.41', 'Packages': {'pytest': '7.4.3', 'pluggy': '1.6.0'}, 'Plugins': {'mock': '3.15.0', 'metadata': '3.1.1', 'json-report': '1.5.0', 'xdist': '3.8.0', 'cov': '7.0.0', 'Faker': '37.6.0', 'hypothesis': '6.138.15', 'html': '4.1.1', 'asyncio': '0.21.1', 'anyio': '3.7.1'}}
 hypothesis profile 'default' -> database=InMemoryExampleDatabase({})
 rootdir: /app
 plugins: mock-3.15.0, metadata-3.1.1, json-report-1.5.0, xdist-3.8.0, cov-7.0.0, Faker-37.6.0, hypothesis-6.138.15, html-4.1.1, asyncio-0.21.1, anyio-3.7.1
 asyncio: mode=Mode.STRICT
 collecting ... collected 43 items
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_buy_and_hold_success PASSED [  2%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success PASSED [  4%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_rsi_strategy_success PASSED [  6%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_invalid_strategy PASSED [  9%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data PASSED [ 11%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_portfolio_backtest_success SKIPPED [ 13%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success PASSED [ 16%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_with_different_initial_cash PASSED [ 18%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark PASSED [ 20%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency PASSED [ 23%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact PASSED [ 25%]
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_different_time_periods PASSED [ 27%]
 tests/unit/test_cash_assets.py::TestCashAssets::test_cash_only_portfolio PASSED [ 30%]
 tests/unit/test_cash_assets.py::TestCashAssets::test_mixed_cash_and_stock_portfolio PASSED [ 32%]
 tests/unit/test_cash_assets.py::TestCashAssets::test_multiple_cash_entries PASSED [ 34%]
 tests/unit/test_cash_assets.py::TestCashAssets::test_cash_dca_investment PASSED [ 37%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_success PASSED [ 39%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_invalid_ticker PASSED [ 41%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_empty_result PASSED [ 44%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_date_validation PASSED [ 46%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_ticker_info_success PASSED [ 48%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_ticker_info_invalid_ticker PASSED [ 51%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_data_caching_behavior PASSED [ 53%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_multiple_tickers_data_fetching PASSED [ 55%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_decimal_precision_compliance PASSED [ 58%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_performance_benchmarks PASSED [ 60%]
 tests/unit/test_data_fetcher.py::TestDataFetcher::test_concurrent_data_fetching PASSED [ 62%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_get_all_strategies_success PASSED [ 65%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_get_strategy_info_success PASSED [ 67%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_get_strategy_info_not_found PASSED [ 69%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_sma_crossover_valid PASSED [ 72%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_sma_crossover_invalid PASSED [ 74%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_rsi_strategy_valid PASSED [ 76%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_rsi_strategy_invalid PASSED [ 79%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_buy_and_hold PASSED [ 81%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_bollinger_bands_valid PASSED [ 83%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_macd_strategy_valid PASSED [ 86%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_parameter_ranges_compliance PASSED [ 88%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_class_instantiation PASSED [ 90%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_default_parameters PASSED [ 93%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_registry_integrity PASSED [ 95%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_parameter_type_validation PASSED [ 97%]
 tests/unit/test_strategy_service.py::TestStrategyService::test_edge_case_parameter_values PASSED [100%]
 
 =============================== warnings summary ===============================
 ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:323: 11 warnings
   /usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:323: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
     warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
 
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
   /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'env'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
     warn(
 
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1062
   /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1062: PydanticDeprecatedSince20: `min_items` is deprecated and will be removed, use `min_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
     warn('`min_items` is deprecated and will be removed, use `min_length` instead', DeprecationWarning)
 
 ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1068
   /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1068: PydanticDeprecatedSince20: `max_items` is deprecated and will be removed, use `max_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
     warn('`max_items` is deprecated and will be removed, use `max_length` instead', DeprecationWarning)
 
 tests/unit/test_backtest_service.py:24
   /app/tests/unit/test_backtest_service.py:24: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
     pytestmark = pytest.mark.unit
 
 ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:298
   /usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:298: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.11/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
     warnings.warn(
 
 tests/unit/test_cash_assets.py:11
   /app/tests/unit/test_cash_assets.py:11: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
     pytestmark = pytest.mark.unit
 
 tests/unit/test_data_fetcher.py:23
   /app/tests/unit/test_data_fetcher.py:23: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
     pytestmark = pytest.mark.unit
 
 tests/unit/test_strategy_service.py:19
   /app/tests/unit/test_strategy_service.py:19: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
     pytestmark = pytest.mark.unit
 
 tests/unit/test_backtest_service.py: 14 warnings
   /app/app/services/backtest/backtest_engine.py:67: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
     result = bt.run()
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=85: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=96: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=100: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=115: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=136: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=159: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=196: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=210: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=230: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=244: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=245: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
 tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
 tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=255: Broker canceled the relative-sized order due to insufficient margin.
     warnings.warn(
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success
   /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:1545: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
     stats = self.run(**dict(zip(heatmap.index.names, best_params)))
 
 tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success
   /app/app/services/backtest/optimization_service.py:177: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
     final_stats = bt.run(**best_params)
 
 ../usr/local/lib/python3.11/site-packages/_pytest/cacheprovider.py:451
   /usr/local/lib/python3.11/site-packages/_pytest/cacheprovider.py:451: PytestCacheWarning: cache could not write path /app/.pytest_cache/v/cache/nodeids: [Errno 13] Permission denied: '/app/.pytest_cache/v/cache/nodeids'
     config.cache.set("cache/nodeids", sorted(self.cached_nodeids))
 
 ../usr/local/lib/python3.11/site-packages/_pytest/stepwise.py:56
   /usr/local/lib/python3.11/site-packages/_pytest/stepwise.py:56: PytestCacheWarning: cache could not write path /app/.pytest_cache/v/cache/stepwise: [Errno 13] Permission denied: '/app/.pytest_cache/v/cache/stepwise'
     session.config.cache.set(STEPWISE_CACHE_DIR, [])
 
 -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
 -------------------- generated xml file: /reports/junit.xml --------------------
 ================= 42 passed, 1 skipped, 129 warnings in 8.13s ==================
 + docker run --rm -u 131:134 -e CI=1 -e VITEST_JUNIT_FILE=/reports/junit.xml -v /var/lib/jenkins/workspace/Backtest/frontend:/app -v /var/lib/jenkins/workspace/Backtest/reports/frontend:/reports -w /app node:18-alpine sh -lc npm ci && npx vitest run
 npm warn EBADENGINE Unsupported engine {
 npm warn EBADENGINE   package: '@isaacs/balanced-match@4.0.1',
 npm warn EBADENGINE   required: { node: '20 || >=22' },
 npm warn EBADENGINE   current: { node: 'v18.20.8', npm: '10.8.2' }
 npm warn EBADENGINE }
 npm warn EBADENGINE Unsupported engine {
 npm warn EBADENGINE   package: '@isaacs/brace-expansion@5.0.0',
 npm warn EBADENGINE   required: { node: '20 || >=22' },
 npm warn EBADENGINE   current: { node: 'v18.20.8', npm: '10.8.2' }
 npm warn EBADENGINE }
 npm warn EBADENGINE Unsupported engine {
 npm warn EBADENGINE   package: 'minimatch@10.0.3',
 npm warn EBADENGINE   required: { node: '20 || >=22' },
 npm warn EBADENGINE   current: { node: 'v18.20.8', npm: '10.8.2' }
 npm warn EBADENGINE }
 npm warn EBADENGINE Unsupported engine {
 npm warn EBADENGINE   package: 'commander@14.0.1',
 npm warn EBADENGINE   required: { node: '>=20' },
 npm warn EBADENGINE   current: { node: 'v18.20.8', npm: '10.8.2' }
 npm warn EBADENGINE }
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/_node/compat.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/_node/hchacha.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/index.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/aes/noble.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/cjs/examples/shared/inMemoryEventStore.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/chacha/noble.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/esm/examples/shared/inMemoryEventStore.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/aes/node.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/cjs/examples/server/jsonResponseStreamableHttp.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, lstat '/app/node_modules/@hookform/resolvers/vine/src/__tests__'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@ecies/ciphers/dist/chacha/node.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/esm/examples/server/jsonResponseStreamableHttp.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, lstat '/app/node_modules/@hookform/resolvers/yup/src'
 npm warn cleanup Failed to remove some directories [
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules/date-fns',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/date-fns/fp'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/date-fns/fp'
 npm warn cleanup     }
 npm warn cleanup   ],
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules/date-fns-jalali',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/date-fns-jalali/fp'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/date-fns-jalali/fp'
 npm warn cleanup     }
 npm warn cleanup   ],
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/date-fns/fp'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/date-fns/fp'
 npm warn cleanup     }
 npm warn cleanup   ],
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules/@ecies',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/@ecies/ciphers/dist/chacha'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/@ecies/ciphers/dist/chacha'
 npm warn cleanup     }
 npm warn cleanup   ],
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules/lucide-react',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/lucide-react/dist/esm/icons'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/lucide-react/dist/esm/icons'
 npm warn cleanup     }
 npm warn cleanup   ],
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules/@hookform',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/@hookform/resolvers/vest/src/__tests__'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/@hookform/resolvers/vest/src/__tests__'
 npm warn cleanup     }
 npm warn cleanup   ],
 npm warn cleanup   [
 npm warn cleanup     '/app/node_modules/@modelcontextprotocol',
 npm warn cleanup     [Error: ENOTEMPTY: directory not empty, rmdir '/app/node_modules/@modelcontextprotocol/sdk/dist/cjs/server'] {
 npm warn cleanup       errno: -39,
 npm warn cleanup       code: 'ENOTEMPTY',
 npm warn cleanup       syscall: 'rmdir',
 npm warn cleanup       path: '/app/node_modules/@modelcontextprotocol/sdk/dist/cjs/server'
 npm warn cleanup     }
 npm warn cleanup   ]
 npm warn cleanup ]
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@hookform/resolvers/effect-ts/dist/effect-ts.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/esm/server/mcp.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, lstat '/app/node_modules/@hookform/resolvers/effect-ts/src'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/cjs/examples/server/mcpServerOutputSchema.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, open '/app/node_modules/@modelcontextprotocol/sdk/dist/esm/examples/server/mcpServerOutputSchema.d.ts'
 npm warn tar TAR_ENTRY_ERROR ENOENT: no such file or directory, lstat '/app/node_modules/@hookform/resolvers/effect-ts/src'
 npm error code EACCES
 npm error syscall mkdir
 npm error path /.npm
 npm error errno -13
 npm error
 npm error Your cache folder contains root-owned files, due to a bug in
 npm error previous versions of npm which has since been addressed.
 npm error
 npm error To permanently fix this problem, please run:
 npm error   sudo chown -R 131:134 "/.npm"
 npm error Log files were not written due to an error writing to the directory: /.npm/_logs
 npm error You can rerun the command with `--loglevel=verbose` to see the logs in your terminal
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Build and Push PROD)
Stage "Build and Push PROD" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] parallel
[Pipeline] { (Branch: Backend PROD)
[Pipeline] { (Branch: Frontend PROD)
[Pipeline] stage
[Pipeline] { (Backend PROD)
[Pipeline] stage
[Pipeline] { (Frontend PROD)
Stage "Backend PROD" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
Stage "Frontend PROD" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] // stage
[Pipeline] }
 Failed in branch Backend PROD
[Pipeline] }
 Failed in branch Frontend PROD
[Pipeline] // parallel
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Deploy to Production (Local))
Stage "Deploy to Production (Local)" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Integration Tests)
Stage "Integration Tests" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Declarative: Post Actions)
[Pipeline] sh
 + docker system prune -f
 Deleted build cache objects:
 sxwgresihuxv4z5sj4wkoqa76
 3u5gbj68ltq9je3smz2kszjjz
 xop7xqricnw8guej6u8866m2p
 o26m5it0n2yziavt0i4g9n8i2
 svez017e98txvv6h73oulep43
 rtfxlm6o7rq7ylhw3734okvos
 
 Total reclaimed space: 1.758MB
[Pipeline] cleanWs
 [WS-CLEANUP] Deleting project workspace...
 [WS-CLEANUP] Deferred wipeout is disabled by the job configuration...
 [WS-CLEANUP] done
[Pipeline] echo
 Pipeline failed! (see console log for details)
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // timestamps
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
ERROR: script returned exit code 243
Finished: FAILURE
