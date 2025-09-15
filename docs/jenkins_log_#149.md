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
23:37:36  The recommended git tool is: /usr/bin/git
23:37:36  using credential github-token
23:37:36  Cloning the remote Git repository
23:37:36  Cloning repository https://github.com/capstone-backtest/backtest.git
23:37:36   > /usr/bin/git init /var/lib/jenkins/workspace/Backtest # timeout=10
23:37:36  Fetching upstream changes from https://github.com/capstone-backtest/backtest.git
23:37:36   > /usr/bin/git --version # timeout=10
23:37:36   > git --version # 'git version 2.43.0'
23:37:36  using GIT_ASKPASS to set credentials GHCR Token (Username/Password type)
23:37:36   > /usr/bin/git fetch --tags --force --progress -- https://github.com/capstone-backtest/backtest.git +refs/heads/*:refs/remotes/origin/* # timeout=10
23:37:37   > /usr/bin/git config remote.origin.url https://github.com/capstone-backtest/backtest.git # timeout=10
23:37:37   > /usr/bin/git config --add remote.origin.fetch +refs/heads/*:refs/remotes/origin/* # timeout=10
23:37:37  Avoid second fetch
23:37:37   > /usr/bin/git rev-parse refs/remotes/origin/main^{commit} # timeout=10
23:37:37  Checking out Revision 6bf1f85dd26664370080e6ccc6e898ad3915523c (refs/remotes/origin/main)
23:37:37   > /usr/bin/git config core.sparsecheckout # timeout=10
23:37:37   > /usr/bin/git checkout -f 6bf1f85dd26664370080e6ccc6e898ad3915523c # timeout=10
23:37:37  Commit message: "fix(jenkins): Remove agent labels to resolve scheduling issues"
23:37:37   > /usr/bin/git rev-list --no-walk e2b7da57f89798c13fcfe1800a49f0df6ab61354 # timeout=10
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Debug Environment)
[Pipeline] script
[Pipeline] {
[Pipeline] echo
23:37:37  Debug Information:
[Pipeline] echo
23:37:37  BRANCH_NAME: null
[Pipeline] echo
23:37:37  GIT_BRANCH: null
[Pipeline] echo
23:37:37  BUILD_NUMBER: 149
[Pipeline] echo
23:37:37  All env vars:
[Pipeline] sh
23:37:38  + id -u
[Pipeline] sh
23:37:38  + id -g
[Pipeline] sh
23:37:38  + env
23:37:38  + grep -E (BRANCH|GIT)
23:37:38  + sort
23:37:38  + echo UID_J=131 GID_J=134
23:37:38  UID_J=131 GID_J=134
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
23:37:39  Running frontend tests...
[Pipeline] sh
[Pipeline] echo
23:37:39  Running backend tests with controlled environment...
[Pipeline] sh
23:37:39  + cd frontend
23:37:39  + docker build --build-arg RUN_TESTS=true -t backtest-frontend-test:149 .
23:37:39  + cd backend
23:37:39  + docker build --build-arg RUN_TESTS=true -t backtest-backend-test:149 .
23:37:39  #0 building with "default" instance using docker driver
23:37:39  
23:37:39  #1 [internal] load build definition from Dockerfile
23:37:39  #1 transferring dockerfile: 983B done
23:37:39  #1 DONE 0.0s
23:37:39  
23:37:39  #2 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
23:37:39  #0 building with "default" instance using docker driver
23:37:39  
23:37:39  #1 [internal] load build definition from Dockerfile
23:37:39  #1 transferring dockerfile: 1.54kB done
23:37:39  #1 DONE 0.0s
23:37:39  
23:37:39  #2 [internal] load metadata for docker.io/library/python:3.11-slim
23:37:41  #2 DONE 1.7s
23:37:41  
23:37:41  #3 [internal] load metadata for docker.io/library/node:20.8.1-alpine
23:37:41  #2 DONE 2.0s
23:37:41  
23:37:41  #3 [internal] load .dockerignore
23:37:41  #3 transferring context: 92B done
23:37:41  #3 DONE 0.0s
23:37:41  
23:37:41  #4 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
23:37:41  #4 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
23:37:41  #4 DONE 0.0s
23:37:41  
23:37:41  #5 [internal] load build context
23:37:41  #5 transferring context: 862.12kB 0.0s done
23:37:41  #5 DONE 0.1s
23:37:41  
23:37:41  #6 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
23:37:41  #6 CACHED
23:37:41  
23:37:41  #7 [ 2/13] WORKDIR /app
23:37:41  #7 CACHED
23:37:41  
23:37:41  #8 [11/13] COPY tests ./tests
23:37:41  #8 CACHED
23:37:41  
23:37:41  #9 [ 4/13] COPY requirements.txt .
23:37:41  #9 CACHED
23:37:41  
23:37:41  #10 [12/13] COPY run_server.py .
23:37:41  #10 CACHED
23:37:41  
23:37:41  #11 [ 5/13] COPY requirements-test.txt .
23:37:41  #11 CACHED
23:37:41  
23:37:41  #12 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
23:37:41  #12 CACHED
23:37:41  
23:37:41  #13 [ 8/13] RUN uv pip install --system -r requirements-test.txt
23:37:41  #13 CACHED
23:37:41  
23:37:41  #14 [ 7/13] RUN uv pip install --system -r requirements.txt
23:37:41  #14 CACHED
23:37:41  
23:37:41  #15 [ 9/13] RUN uv pip install --system backtesting
23:37:41  #15 CACHED
23:37:41  
23:37:41  #16 [10/13] COPY app ./app
23:37:41  #16 CACHED
23:37:41  
23:37:41  #17 [13/13] RUN if [ "true" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
23:37:41  #17 CACHED
23:37:41  
23:37:41  #18 exporting to image
23:37:41  #18 exporting layers done
23:37:41  #18 writing image sha256:36f4c7e61a84cab9d826a072c59277e28d6509ad58ee9845af35a0e086244873 done
23:37:41  #18 naming to docker.io/library/backtest-backend-test:149 done
23:37:41  #18 DONE 0.0s
[Pipeline] echo
23:37:41  Backend tests passed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
23:37:42  #3 DONE 3.0s
23:37:42  
23:37:42  #4 [internal] load .dockerignore
23:37:42  #4 transferring context: 2B done
23:37:42  #4 DONE 0.0s
23:37:42  
23:37:42  #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
23:37:42  #5 DONE 0.0s
23:37:42  
23:37:42  #6 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
23:37:42  #6 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
23:37:42  #6 DONE 0.0s
23:37:42  
23:37:42  #7 [internal] load build context
23:37:42  #7 transferring context: 917.94kB 0.0s done
23:37:42  #7 DONE 0.1s
23:37:42  
23:37:42  #8 [build 4/7] RUN npm ci --no-audit --prefer-offline --no-fund
23:37:42  #8 CACHED
23:37:42  
23:37:42  #9 [build 5/7] COPY . .
23:37:42  #9 CACHED
23:37:42  
23:37:42  #10 [build 6/7] RUN if [ "true" = "true" ] ; then npm test -- --run ; fi
23:37:42  #10 CACHED
23:37:42  
23:37:42  #11 [build 7/7] RUN npm run build
23:37:42  #11 CACHED
23:37:42  
23:37:42  #12 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
23:37:42  #12 CACHED
23:37:42  
23:37:42  #13 [build 3/7] COPY package.json package-lock.json ./
23:37:42  #13 CACHED
23:37:42  
23:37:42  #14 [build 2/7] WORKDIR /app
23:37:42  #14 CACHED
23:37:42  
23:37:42  #15 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
23:37:42  #15 CACHED
23:37:42  
23:37:42  #16 exporting to image
23:37:42  #16 exporting layers done
23:37:42  #16 writing image sha256:7d4ed8130143eab3d6bc94eeaf1017dcb600d53a23184fc54ea002d5127500c8 done
23:37:42  #16 naming to docker.io/library/backtest-frontend-test:149 done
23:37:42  #16 DONE 0.0s
[Pipeline] echo
23:37:42  Frontend tests passed
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
23:37:43  + mkdir -p reports/backend reports/frontend
23:37:43  + mkdir -p frontend/.npm
23:37:43  + chown 131:134 frontend/.npm
23:37:43  + docker run --rm -u 131:134 -v /var/lib/jenkins/workspace/Backtest/reports/backend:/reports backtest-backend-test:149 sh -lc pytest tests/unit/ -v --tb=short --junitxml=/reports/junit.xml
23:37:44  /usr/local/lib/python3.11/site-packages/hypothesis/_settings.py:968: HypothesisWarning: The database setting is not configured, and the default location is unusable - falling back to an in-memory database for this session.  path=PosixPath('/app/.hypothesis/examples')
23:37:44    value = getattr(self, name)
23:37:44  /usr/local/lib/python3.11/site-packages/hypothesis/_settings.py:969: HypothesisWarning: The database setting is not configured, and the default location is unusable - falling back to an in-memory database for this session.  path=PosixPath('/app/.hypothesis/examples')
23:37:44    if value != getattr(default, name):
23:37:44  ============================= test session starts ==============================
23:37:44  platform linux -- Python 3.11.13, pytest-7.4.3, pluggy-1.6.0 -- /usr/local/bin/python
23:37:44  cachedir: .pytest_cache
23:37:44  metadata: {'Python': '3.11.13', 'Platform': 'Linux-6.14.0-29-generic-x86_64-with-glibc2.41', 'Packages': {'pytest': '7.4.3', 'pluggy': '1.6.0'}, 'Plugins': {'mock': '3.15.0', 'metadata': '3.1.1', 'json-report': '1.5.0', 'xdist': '3.8.0', 'cov': '7.0.0', 'Faker': '37.6.0', 'hypothesis': '6.138.15', 'html': '4.1.1', 'asyncio': '0.21.1', 'anyio': '3.7.1'}}
23:37:44  hypothesis profile 'default' -> database=InMemoryExampleDatabase({})
23:37:44  rootdir: /app
23:37:44  plugins: mock-3.15.0, metadata-3.1.1, json-report-1.5.0, xdist-3.8.0, cov-7.0.0, Faker-37.6.0, hypothesis-6.138.15, html-4.1.1, asyncio-0.21.1, anyio-3.7.1
23:37:44  asyncio: mode=Mode.STRICT
23:37:45  collecting ... collected 43 items
23:37:45  
23:37:45  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_buy_and_hold_success PASSED [  2%]
23:37:45  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success PASSED [  4%]
23:37:45  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_rsi_strategy_success PASSED [  6%]
23:37:45  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_invalid_strategy PASSED [  9%]
23:37:46  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data PASSED [ 11%]
23:37:46  tests/unit/test_backtest_service.py::TestBacktestService::test_run_portfolio_backtest_success SKIPPED [ 13%]
23:37:46  tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success PASSED [ 16%]
23:37:46  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_with_different_initial_cash PASSED [ 18%]
23:37:47  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark PASSED [ 20%]
23:37:47  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency PASSED [ 23%]
23:37:48  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact PASSED [ 25%]
23:37:48  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_different_time_periods PASSED [ 27%]
23:37:48  tests/unit/test_cash_assets.py::TestCashAssets::test_cash_only_portfolio PASSED [ 30%]
23:37:48  tests/unit/test_cash_assets.py::TestCashAssets::test_mixed_cash_and_stock_portfolio PASSED [ 32%]
23:37:48  tests/unit/test_cash_assets.py::TestCashAssets::test_multiple_cash_entries PASSED [ 34%]
23:37:48  tests/unit/test_cash_assets.py::TestCashAssets::test_cash_dca_investment PASSED [ 37%]
23:37:48  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_success PASSED [ 39%]
23:37:48  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_invalid_ticker PASSED [ 41%]
23:37:48  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_empty_result PASSED [ 44%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_date_validation PASSED [ 46%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_ticker_info_success PASSED [ 48%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_ticker_info_invalid_ticker PASSED [ 51%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_data_caching_behavior PASSED [ 53%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_multiple_tickers_data_fetching PASSED [ 55%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_decimal_precision_compliance PASSED [ 58%]
23:37:49  tests/unit/test_data_fetcher.py::TestDataFetcher::test_performance_benchmarks PASSED [ 60%]
23:37:50  tests/unit/test_data_fetcher.py::TestDataFetcher::test_concurrent_data_fetching PASSED [ 62%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_get_all_strategies_success PASSED [ 65%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_get_strategy_info_success PASSED [ 67%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_get_strategy_info_not_found PASSED [ 69%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_sma_crossover_valid PASSED [ 72%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_sma_crossover_invalid PASSED [ 74%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_rsi_strategy_valid PASSED [ 76%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_rsi_strategy_invalid PASSED [ 79%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_buy_and_hold PASSED [ 81%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_bollinger_bands_valid PASSED [ 83%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_macd_strategy_valid PASSED [ 86%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_parameter_ranges_compliance PASSED [ 88%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_class_instantiation PASSED [ 90%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_default_parameters PASSED [ 93%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_registry_integrity PASSED [ 95%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_parameter_type_validation PASSED [ 97%]
23:37:50  tests/unit/test_strategy_service.py::TestStrategyService::test_edge_case_parameter_values PASSED [100%]
23:37:50  
23:37:50  =============================== warnings summary ===============================
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:323: 11 warnings
23:37:50    /usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:323: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
23:37:50      warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
23:37:50  
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
23:37:50    /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'env'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
23:37:50      warn(
23:37:50  
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1062
23:37:50    /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1062: PydanticDeprecatedSince20: `min_items` is deprecated and will be removed, use `min_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
23:37:50      warn('`min_items` is deprecated and will be removed, use `min_length` instead', DeprecationWarning)
23:37:50  
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1068
23:37:50    /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1068: PydanticDeprecatedSince20: `max_items` is deprecated and will be removed, use `max_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
23:37:50      warn('`max_items` is deprecated and will be removed, use `max_length` instead', DeprecationWarning)
23:37:50  
23:37:50  tests/unit/test_backtest_service.py:24
23:37:50    /app/tests/unit/test_backtest_service.py:24: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
23:37:50      pytestmark = pytest.mark.unit
23:37:50  
23:37:50  ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:298
23:37:50    /usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:298: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.11/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_cash_assets.py:11
23:37:50    /app/tests/unit/test_cash_assets.py:11: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
23:37:50      pytestmark = pytest.mark.unit
23:37:50  
23:37:50  tests/unit/test_data_fetcher.py:23
23:37:50    /app/tests/unit/test_data_fetcher.py:23: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
23:37:50      pytestmark = pytest.mark.unit
23:37:50  
23:37:50  tests/unit/test_strategy_service.py:19
23:37:50    /app/tests/unit/test_strategy_service.py:19: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
23:37:50      pytestmark = pytest.mark.unit
23:37:50  
23:37:50  tests/unit/test_backtest_service.py: 14 warnings
23:37:50    /app/app/services/backtest/backtest_engine.py:67: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
23:37:50      result = bt.run()
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=85: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=96: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=100: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=115: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=136: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=159: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=196: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=210: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=230: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=244: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=245: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=255: Broker canceled the relative-sized order due to insufficient margin.
23:37:50      warnings.warn(
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success
23:37:50    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:1545: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
23:37:50      stats = self.run(**dict(zip(heatmap.index.names, best_params)))
23:37:50  
23:37:50  tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success
23:37:50    /app/app/services/backtest/optimization_service.py:177: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
23:37:50      final_stats = bt.run(**best_params)
23:37:50  
23:37:50  ../usr/local/lib/python3.11/site-packages/_pytest/cacheprovider.py:451
23:37:50    /usr/local/lib/python3.11/site-packages/_pytest/cacheprovider.py:451: PytestCacheWarning: cache could not write path /app/.pytest_cache/v/cache/nodeids: [Errno 13] Permission denied: '/app/.pytest_cache/v/cache/nodeids'
23:37:50      config.cache.set("cache/nodeids", sorted(self.cached_nodeids))
23:37:50  
23:37:50  ../usr/local/lib/python3.11/site-packages/_pytest/stepwise.py:56
23:37:50    /usr/local/lib/python3.11/site-packages/_pytest/stepwise.py:56: PytestCacheWarning: cache could not write path /app/.pytest_cache/v/cache/stepwise: [Errno 13] Permission denied: '/app/.pytest_cache/v/cache/stepwise'
23:37:50      session.config.cache.set(STEPWISE_CACHE_DIR, [])
23:37:50  
23:37:50  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
23:37:50  -------------------- generated xml file: /reports/junit.xml --------------------
23:37:50  ================= 42 passed, 1 skipped, 129 warnings in 6.12s ==================
23:37:50  + docker run --rm -u 131:134 -e CI=1 -e VITEST_JUNIT_FILE=/reports/junit.xml -e NPM_CONFIG_CACHE=/app/.npm -v /var/lib/jenkins/workspace/Backtest/frontend:/app -v /var/lib/jenkins/workspace/Backtest/frontend/.npm:/app/.npm -v /var/lib/jenkins/workspace/Backtest/reports/frontend:/reports -w /app node:20-alpine sh -lc npm ci --prefer-offline --no-audit && npx vitest run
23:37:58  npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead

23:38:05  
23:38:05  added 790 packages in 14s
23:38:05  
23:38:05  199 packages are looking for funding
23:38:05    run `npm fund` for details

23:38:06  
23:38:06  [7m[1m[36m RUN [39m[22m[27m [36mv0.34.6[39m [90m/app[39m
23:38:06  

23:38:07   [32m✓[39m src/utils/__tests__/dateUtils.test.ts [2m ([22m[2m38 tests[22m[2m)[22m[90m 29[2mms[22m[39m
23:38:07   [32m✓[39m src/utils/__tests__/numberUtils.test.ts [2m ([22m[2m57 tests[22m[2m)[22m[90m 61[2mms[22m[39m
23:38:07  [90mstderr[2m | src/hooks/__tests__/useBacktestForm.test.ts[2m > [22m[2museBacktestForm[2m > [22m[2m초기 상태[2m > [22m[2m기본값으로 올바르게 초기화되어야 함[22m[39m
23:38:07  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:07  
23:38:07   [32m✓[39m src/hooks/__tests__/useBacktestForm.test.ts [2m ([22m[2m19 tests[22m[2m)[22m[90m 117[2mms[22m[39m

23:38:08   [32m✓[39m src/utils/formatters.test.ts [2m ([22m[2m20 tests[22m[2m)[22m[90m 20[2mms[22m[39m

23:38:10  [90mstderr[2m | src/components/common/__tests__/FormField.test.tsx[2m > [22m[2mFormField[2m > [22m[2m기본 렌더링[2m > [22m[2m라벨과 입력 필드가 올바르게 렌더링되어야 함[22m[39m
23:38:10  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:10  
23:38:10   [32m✓[39m src/services/__tests__/api.test.ts [2m ([22m[2m4 tests[22m [2m|[22m [33m1 skipped[39m[2m)[22m[90m 15[2mms[22m[39m
23:38:10   [32m✓[39m src/components/common/__tests__/FormField.test.tsx [2m ([22m[2m18 tests[22m[2m)[22m[33m 1057[2mms[22m[39m

23:38:11  [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
23:38:11  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:11  

23:38:12  [90mstderr[2m | src/hooks/__tests__/useBacktest.test.ts[2m > [22m[2museBacktest[2m > [22m[2m성공 시 결과를 설정하고 isPortfolio를 올바르게 표시해야 함[22m[39m
23:38:12  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:12  
23:38:12   [32m✓[39m src/hooks/__tests__/useBacktest.test.ts [2m ([22m[2m3 tests[22m[2m)[22m[90m 44[2mms[22m[39m
23:38:12  [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2monSubmit에서 오류 발생 시 에러 메시지를 표시해야 함[22m[39m
23:38:12  백테스트 실행 중 오류: Error: 테스트 오류
23:38:12      at [90m/app/[39msrc/components/__tests__/UnifiedBacktestForm.test.tsx:58:48
23:38:12      at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:135:14
23:38:12      at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:58:26
23:38:12      at runTest [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:663:17[90m)[39m
23:38:12      at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
23:38:12      at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
23:38:12      at runFiles [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:834:5[90m)[39m
23:38:12      at startTests [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:843:3[90m)[39m
23:38:12      at [90mfile:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:103:7
23:38:12      at withEnv [90m(file:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:73:5[90m)[39m
23:38:12  
23:38:12   [32m✓[39m src/components/__tests__/UnifiedBacktestForm.test.tsx [2m ([22m[2m2 tests[22m[2m)[22m[33m 2060[2mms[22m[39m

23:38:12   [32m✓[39m src/components/__tests__/charts.smoke.test.tsx [2m ([22m[2m4 tests[22m[2m)[22m[90m 151[2mms[22m[39m
23:38:12  [90mstderr[2m | src/components/__tests__/charts.smoke.test.tsx[2m > [22m[2mChart components (smoke)[2m > [22m[2mEquityChart renders an SVG with minimal data[22m[39m
23:38:12  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:12  
23:38:13  [90mstderr[2m | src/components/ErrorBoundary.test.tsx[2m > [22m[2mErrorBoundary[2m > [22m[2m정상적인 컴포넌트를 렌더링해야 함[22m[39m
23:38:13  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:13  
23:38:13   [32m✓[39m src/components/ErrorBoundary.test.tsx [2m ([22m[2m3 tests[22m[2m)[22m[90m 166[2mms[22m[39m

23:38:14  [90mstderr[2m | src/components/__tests__/PortfolioForm.test.tsx[2m > [22m[2mPortfolioForm[2m > [22m[2m렌더링 및 주요 액션(addStock/addCash/removeStock) 트리거[22m[39m
23:38:14  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:14  

23:38:15   [32m✓[39m src/components/__tests__/PortfolioForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[33m 742[2mms[22m[39m
23:38:15  [90mstderr[2m | src/components/__tests__/CommissionForm.test.tsx[2m > [22m[2mCommissionForm[2m > [22m[2m기본 렌더링이 올바르게 되어야 함[22m[39m
23:38:15  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:15  
23:38:15   [32m✓[39m src/components/__tests__/CommissionForm.test.tsx [2m ([22m[2m3 tests[22m[2m)[22m[33m 496[2mms[22m[39m
23:38:15  [90mstderr[2m | src/components/__tests__/StrategyForm.test.tsx[2m > [22m[2mStrategyForm[2m > [22m[2msma_crossover 선택 시 파라미터 입력 필드를 표시하고 변경 이벤트를 전파[22m[39m
23:38:15  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:15  
23:38:15   [32m✓[39m src/components/__tests__/StrategyForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[33m 308[2mms[22m[39m

23:38:16  [90mstderr[2m | src/components/__tests__/DateRangeForm.test.tsx[2m > [22m[2mDateRangeForm[2m > [22m[2m시작/종료 날짜 변경 시 핸들러 호출[22m[39m
23:38:16  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
23:38:16  
23:38:16   [32m✓[39m src/components/__tests__/DateRangeForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[90m 248[2mms[22m[39m
23:38:16  
23:38:16  [2m Test Files [22m [1m[32m14 passed[39m[22m[90m (14)[39m
23:38:16  [2m      Tests [22m [1m[32m173 passed[39m[22m[2m | [22m[33m1 skipped[39m[90m (174)[39m
23:38:16  [2m   Start at [22m 14:38:05
23:38:16  [2m   Duration [22m 10.79s[2m (transform 528ms, setup 1.35s, collect 6.55s, tests 5.51s, environment 10.63s, prepare 1.67s)[22m
23:38:16  

[Pipeline] junit
23:38:16  Recording test results
23:38:16  [Checks API] No suitable checks publisher found.
[Pipeline] archiveArtifacts
23:38:16  Archiving artifacts
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Build and Push PROD)
[Pipeline] parallel
[Pipeline] { (Branch: Backend PROD)
[Pipeline] { (Branch: Frontend PROD)
[Pipeline] stage
[Pipeline] { (Backend PROD)
[Pipeline] stage
[Pipeline] { (Frontend PROD)
[Pipeline] script
[Pipeline] {
[Pipeline] script
[Pipeline] {
[Pipeline] withCredentials
23:38:17  Masking supported pattern matches of $GH_TOKEN
[Pipeline] withCredentials
23:38:17  Masking supported pattern matches of $GH_TOKEN
[Pipeline] {
[Pipeline] {
[Pipeline] echo
23:38:17  Building PROD backend image: ghcr.io/kyj0503/backtest-backend:149
[Pipeline] sh
[Pipeline] echo
23:38:17  Building PROD frontend image: ghcr.io/kyj0503/backtest-frontend:149
[Pipeline] sh
23:38:17  + docker buildx inspect backtest-builder
23:38:17  + docker buildx use backtest-builder
[Pipeline] sh
23:38:17  + docker buildx inspect backtest-builder
23:38:17  + docker buildx use backtest-builder
[Pipeline] sh
23:38:17  + docker pull ghcr.io/kyj0503/backtest-backend:latest
23:38:17  + docker pull ghcr.io/kyj0503/backtest-frontend:latest

23:38:18  latest: Pulling from kyj0503/backtest-backend
23:38:18  Digest: sha256:3cee1ec4f8cd30f11867eb4540ba25ea0fb1c602df4264cf2aae4a8b34c180c9
23:38:18  Status: Image is up to date for ghcr.io/kyj0503/backtest-backend:latest
23:38:18  ghcr.io/kyj0503/backtest-backend:latest
[Pipeline] sh
23:38:18  + cd backend
23:38:18  + DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg IMAGE_TAG=149 --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/kyj0503/backtest-backend:latest -t ghcr.io/kyj0503/backtest-backend:149 .

23:38:19  #0 building with "default" instance using docker driver
23:38:19  
23:38:19  #1 [internal] load build definition from Dockerfile
23:38:19  #1 transferring dockerfile: 1.54kB done
23:38:19  #1 DONE 0.0s
23:38:19  
23:38:19  #2 [internal] load metadata for docker.io/library/python:3.11-slim
23:38:19  #2 DONE 0.8s

23:38:20  
23:38:20  #3 [internal] load .dockerignore
23:38:20  #3 transferring context: 92B done
23:38:20  #3 DONE 0.0s
23:38:20  
23:38:20  #4 importing cache manifest from ghcr.io/kyj0503/backtest-backend:latest
23:38:20  #4 DONE 0.0s
23:38:20  
23:38:20  #5 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
23:38:20  #5 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
23:38:20  #5 DONE 0.0s
23:38:20  
23:38:20  #6 [internal] load build context
23:38:20  #6 transferring context: 7.32kB 0.0s done
23:38:20  #6 DONE 0.0s
23:38:20  
23:38:20  #7 [ 4/13] COPY requirements.txt .
23:38:20  #7 CACHED
23:38:20  
23:38:20  #8 [ 7/13] RUN uv pip install --system -r requirements.txt
23:38:20  #8 CACHED
23:38:20  
23:38:20  #9 [ 9/13] RUN uv pip install --system backtesting
23:38:20  #9 CACHED
23:38:20  
23:38:20  #10 [10/13] COPY app ./app
23:38:20  #10 CACHED
23:38:20  
23:38:20  #11 [ 2/13] WORKDIR /app
23:38:20  #11 CACHED
23:38:20  
23:38:20  #12 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
23:38:20  #12 CACHED
23:38:20  
23:38:20  #13 [ 8/13] RUN uv pip install --system -r requirements-test.txt
23:38:20  #13 CACHED
23:38:20  
23:38:20  #14 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
23:38:20  #14 CACHED
23:38:20  
23:38:20  #15 [11/13] COPY tests ./tests
23:38:20  #15 CACHED
23:38:20  
23:38:20  #16 [ 5/13] COPY requirements-test.txt .
23:38:20  #16 CACHED
23:38:20  
23:38:20  #17 [12/13] COPY run_server.py .
23:38:20  #17 CACHED
23:38:20  
23:38:20  #18 [13/13] RUN if [ "false" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
23:38:20  #18 DONE 0.2s
23:38:20  
23:38:20  #19 exporting to image
23:38:20  #19 exporting layers 0.0s done
23:38:20  #19 preparing layers for inline cache done
23:38:20  #19 writing image sha256:49a88016859fb23f4b05c48027311bc9393ef9cd3a75e966bdce990a1fa70d7f done
23:38:20  #19 naming to ghcr.io/kyj0503/backtest-backend:149 done
23:38:20  #19 DONE 0.0s
[Pipeline] sh
23:38:20  + set -eu
23:38:20  + export DOCKER_CLIENT_TIMEOUT=300
23:38:20  + export COMPOSE_HTTP_TIMEOUT=300
23:38:20  + curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/
23:38:20  + echo Warning: GHCR probe failed; continuing
23:38:20  Warning: GHCR probe failed; continuing
23:38:20  + docker logout ghcr.io
23:38:20  + ok=
23:38:20  + seq 1 3
23:38:20  + printf %s ****
23:38:20  + docker login ghcr.io -u kyj0503 --password-stdin

23:38:23  latest: Pulling from kyj0503/backtest-frontend
23:38:23  Digest: sha256:6f72c079b1588dd4b25a71ca7e28f3b6c7fd3f990097402bfe14a3482408710c
23:38:23  Status: Image is up to date for ghcr.io/kyj0503/backtest-frontend:latest
23:38:23  ghcr.io/kyj0503/backtest-frontend:latest
23:38:23  
23:38:23  WARNING! Your credentials are stored unencrypted in '/var/lib/jenkins/.docker/config.json'.
23:38:23  Configure a credential helper to remove this warning. See
23:38:23  https://docs.docker.com/go/credential-store/
23:38:23  
23:38:23  Login Succeeded
23:38:23  + ok=1
23:38:23  + break
23:38:23  + [ -z 1 ]

[Pipeline] sh
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh
23:38:23  + cd frontend
23:38:23  + DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/kyj0503/backtest-frontend:latest -t ghcr.io/kyj0503/backtest-frontend:149 .
23:38:23  + set -eu
23:38:23  + ok=
23:38:23  + seq 1 3
23:38:23  + docker push ghcr.io/kyj0503/backtest-backend:149
23:38:23  The push refers to repository [ghcr.io/kyj0503/backtest-backend]
23:38:23  #0 building with "default" instance using docker driver
23:38:23  
23:38:23  #1 [internal] load build definition from Dockerfile
23:38:23  #1 transferring dockerfile: 983B done
23:38:23  #1 DONE 0.0s
23:38:23  
23:38:23  #2 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
23:38:23  #2 DONE 0.0s
23:38:23  
23:38:23  #3 [internal] load metadata for docker.io/library/node:20.8.1-alpine
23:38:23  1f3adeb0a84a: Preparing
23:38:23  1786f360df95: Preparing
23:38:23  3e13088c1051: Preparing
23:38:23  6da07a6a0e8f: Preparing
23:38:23  52e5562c7273: Preparing
23:38:23  57d8b80cef4b: Preparing
23:38:23  4430cc1d395d: Preparing
23:38:23  bb3118717ab5: Preparing
23:38:23  22c144244ab5: Preparing
23:38:23  0f420d6c9384: Preparing
23:38:23  18c41aea3627: Preparing
23:38:23  3bbebd0b50d8: Preparing
23:38:23  8d441cbfbc35: Preparing
23:38:23  49dd736005c7: Preparing
23:38:23  135aac4d5c9a: Preparing
23:38:23  daf557c4f08e: Preparing
23:38:23  57d8b80cef4b: Waiting
23:38:23  4430cc1d395d: Waiting
23:38:23  bb3118717ab5: Waiting
23:38:23  22c144244ab5: Waiting
23:38:23  0f420d6c9384: Waiting
23:38:23  18c41aea3627: Waiting
23:38:23  3bbebd0b50d8: Waiting
23:38:23  49dd736005c7: Waiting
23:38:23  8d441cbfbc35: Waiting
23:38:23  135aac4d5c9a: Waiting
23:38:23  daf557c4f08e: Waiting

23:38:24  #3 DONE 0.7s
23:38:24  
23:38:24  #4 [internal] load .dockerignore
23:38:24  #4 transferring context: 2B done
23:38:24  #4 DONE 0.0s
23:38:24  
23:38:24  #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
23:38:24  #5 DONE 0.0s
23:38:24  
23:38:24  #6 importing cache manifest from ghcr.io/kyj0503/backtest-frontend:latest
23:38:24  #6 DONE 0.0s
23:38:24  
23:38:24  #7 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
23:38:24  #7 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
23:38:24  #7 DONE 0.0s
23:38:24  
23:38:24  #8 [internal] load build context
23:38:24  6da07a6a0e8f: Layer already exists
23:38:24  1786f360df95: Layer already exists
23:38:24  52e5562c7273: Layer already exists
23:38:24  4430cc1d395d: Layer already exists
23:38:24  57d8b80cef4b: Layer already exists
23:38:24  22c144244ab5: Layer already exists
23:38:24  0f420d6c9384: Layer already exists
23:38:24  bb3118717ab5: Layer already exists

23:38:25  3bbebd0b50d8: Layer already exists
23:38:25  8d441cbfbc35: Layer already exists
23:38:25  49dd736005c7: Layer already exists
23:38:25  135aac4d5c9a: Layer already exists
23:38:25  18c41aea3627: Layer already exists
23:38:25  daf557c4f08e: Layer already exists

23:38:26  1f3adeb0a84a: Pushed
23:38:26  3e13088c1051: Layer already exists

23:38:29  #8 transferring context: 491.99MB 5.0s
23:38:29  149: digest: sha256:4f3374d803b76bf141c4994330ac61ebb639fa4bd43812110f1624eb1a81aede size: 3667
23:38:29  + ok=1
23:38:29  + break
23:38:29  + [ -z 1 ]
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
23:38:29  #8 transferring context: 551.51MB 5.7s done
23:38:29  #8 DONE 5.7s
23:38:29  
23:38:29  #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
23:38:29  #5 resolve docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5 0.0s done
23:38:29  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 0B / 2.34MB 0.1s
23:38:29  #5 sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5 1.43kB / 1.43kB done
23:38:29  #5 sha256:1ccb0c0ded3b21cee95fe6b6ce1ac23bd6680c8f152cbfb3047d5d9ea490b098 1.16kB / 1.16kB done
23:38:29  #5 sha256:cf2316e995eb236a3d42066d396685efb1333bd540aface0a9bfc4ff29ce030f 6.78kB / 6.78kB done
23:38:29  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 0B / 3.40MB 0.1s
23:38:29  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 0B / 49.81MB 0.1s

23:38:30  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 3.15MB / 49.81MB 0.9s
23:38:30  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 1.05MB / 3.40MB 1.0s

23:38:31  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 1.05MB / 2.34MB 1.3s
23:38:31  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 2.10MB / 3.40MB 1.3s
23:38:31  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 2.34MB / 2.34MB 1.4s
23:38:31  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 2.34MB / 2.34MB 1.4s done
23:38:31  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 3.15MB / 3.40MB 1.5s
23:38:31  #5 sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 0B / 452B 1.5s
23:38:31  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 3.40MB / 3.40MB 1.5s done
23:38:31  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 6.29MB / 49.81MB 1.6s
23:38:31  #5 extracting sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 0.1s done
23:38:31  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 10.49MB / 49.81MB 2.0s
23:38:31  #5 sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 452B / 452B 1.9s done
23:38:32  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 13.63MB / 49.81MB 2.2s

23:38:32  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 16.78MB / 49.81MB 2.5s
23:38:32  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 19.92MB / 49.81MB 2.8s
23:38:32  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 23.07MB / 49.81MB 3.0s
23:38:33  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 26.21MB / 49.81MB 3.3s

23:38:33  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 30.41MB / 49.81MB 3.7s
23:38:33  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 34.60MB / 49.81MB 4.0s

23:38:34  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 38.80MB / 49.81MB 4.4s
23:38:34  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 44.04MB / 49.81MB 4.8s

23:38:35  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 48.23MB / 49.81MB 5.2s
23:38:35  #5 extracting sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676
23:38:35  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 49.81MB / 49.81MB 5.3s done

23:38:36  #5 extracting sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 1.4s done
23:38:36  #5 extracting sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 0.1s done
23:38:36  #5 extracting sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 done
23:38:36  #5 DONE 7.1s
23:38:37  
23:38:37  #9 [build 2/7] WORKDIR /app
23:38:37  #9 DONE 0.2s

23:38:37  
23:38:37  #10 [build 3/7] COPY package.json package-lock.json ./
23:38:37  #10 DONE 0.1s
23:38:37  
23:38:37  #11 [build 4/7] RUN npm ci --no-audit --prefer-offline --no-fund

23:38:43  #11 6.410 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.410 (Use `node --trace-warnings ...` to show where the warning was created)
23:38:43  #11 6.410 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.411 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.411 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.411 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.412 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.412 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.413 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.413 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.413 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.414 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.414 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.415 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.415 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.415 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.416 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.416 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.416 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.417 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.417 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.417 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.418 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.418 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.418 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.419 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.419 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.419 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.420 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.420 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.420 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.421 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.421 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.421 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.422 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.422 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.422 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.422 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.423 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.423 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.423 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.424 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.424 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.424 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.424 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.425 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.425 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.425 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.425 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.426 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.426 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.426 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.427 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.427 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.427 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.427 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.428 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.428 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.428 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.429 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.429 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.429 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.430 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
23:38:43  #11 6.430 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit

23:38:49  #11 11.12 npm WARN deprecated node-domexception@1.0.0: Use your platform's native DOMException instead

23:38:57  #11 19.23 
23:38:57  #11 19.23 added 790 packages in 19s
23:38:57  #11 19.23 npm notice 
23:38:57  #11 19.23 npm notice New major version of npm available! 10.1.0 -> 11.6.0
23:38:57  #11 19.23 npm notice Changelog: <https://github.com/npm/cli/releases/tag/v11.6.0>
23:38:57  #11 19.23 npm notice Run `npm install -g npm@11.6.0` to update!
23:38:57  #11 19.23 npm notice 
23:38:57  #11 DONE 19.5s
23:38:57  
23:38:57  #12 [build 5/7] COPY . .

23:39:06  #12 DONE 9.2s
23:39:06  
23:39:06  #13 [build 6/7] RUN if [ "false" = "true" ] ; then npm test -- --run ; fi
23:39:06  #13 DONE 0.2s
23:39:06  
23:39:06  #14 [build 7/7] RUN npm run build
23:39:06  #14 0.546 
23:39:06  #14 0.546 > backtesting-frontend@1.0.0 build
23:39:06  #14 0.546 > tsc && vite build
23:39:06  #14 0.546 

23:39:14  #14 8.904 vite v4.5.14 building for production...
23:39:15  #14 8.985 transforming...

23:39:23  #14 17.23 ✓ 2651 modules transformed.

23:39:23  #14 17.55 Generated an empty chunk: "util-vendor".
23:39:23  #14 17.66 rendering chunks...
23:39:24  #14 17.75 [plugin:vite:reporter] 
23:39:24  #14 17.75 (!) /app/src/components/ExchangeRateChart.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
23:39:24  #14 17.75 
23:39:24  #14 17.75 [plugin:vite:reporter] 
23:39:24  #14 17.75 (!) /app/src/components/StockVolatilityNews.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
23:39:24  #14 17.75 
23:39:24  #14 17.82 computing gzip size...
23:39:24  #14 17.84 dist/index.html                                 1.06 kB │ gzip:   0.53 kB
23:39:24  #14 17.84 dist/assets/index-8e69c335.css                 71.17 kB │ gzip:  12.42 kB
23:39:24  #14 17.84 dist/assets/util-vendor-4ed993c7.js             0.00 kB │ gzip:   0.02 kB
23:39:24  #14 17.84 dist/assets/CustomTooltip-a385ef6e.js           0.42 kB │ gzip:   0.32 kB
23:39:24  #14 17.84 dist/assets/EquityChart-c3267435.js             1.55 kB │ gzip:   0.80 kB
23:39:24  #14 17.84 dist/assets/TradesChart-03c94393.js             1.64 kB │ gzip:   0.94 kB
23:39:24  #14 17.84 dist/assets/OHLCChart-40b525f4.js               1.90 kB │ gzip:   0.97 kB
23:39:24  #14 17.84 dist/assets/FinancialTermTooltip-ce90e474.js    1.94 kB │ gzip:   1.76 kB
23:39:24  #14 17.84 dist/assets/StatsSummary-44db21f6.js            2.29 kB │ gzip:   1.12 kB
23:39:24  #14 17.84 dist/assets/StockPriceChart-c525171c.js         2.38 kB │ gzip:   1.21 kB
23:39:24  #14 17.84 dist/assets/icon-vendor-c4a0e88b.js             2.51 kB │ gzip:   1.09 kB
23:39:24  #14 17.84 dist/assets/react-vendor-4413ae29.js          162.28 kB │ gzip:  52.95 kB
23:39:24  #14 17.84 dist/assets/index-2e2a7a35.js                 305.11 kB │ gzip:  90.93 kB
23:39:24  #14 17.84 dist/assets/chart-vendor-df37046f.js          407.43 kB │ gzip: 109.28 kB
23:39:24  #14 17.85 ✓ built in 8.94s
23:39:24  #14 DONE 17.9s

23:39:24  
23:39:24  #15 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
23:39:24  #15 CACHED
23:39:24  
23:39:24  #16 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
23:39:24  #16 CACHED
23:39:24  
23:39:24  #17 exporting to image
23:39:24  #17 exporting layers done
23:39:24  #17 preparing layers for inline cache done
23:39:24  #17 writing image sha256:3d8549f0e08ba8f0405e9cf4b527e40af9f3ca553535bd6c20e53a827cb19593 done
23:39:24  #17 naming to ghcr.io/kyj0503/backtest-frontend:149 done
23:39:24  #17 DONE 0.0s
[Pipeline] sh
23:39:25  + set -eu
23:39:25  + export DOCKER_CLIENT_TIMEOUT=300
23:39:25  + export COMPOSE_HTTP_TIMEOUT=300
23:39:25  + curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/
23:39:25  + echo Warning: GHCR probe failed; continuing
23:39:25  Warning: GHCR probe failed; continuing
23:39:25  + docker logout ghcr.io
23:39:25  + ok=
23:39:25  + seq 1 3
23:39:25  + printf %s ****
23:39:25  + docker login ghcr.io -u kyj0503 --password-stdin

23:39:26  
23:39:26  WARNING! Your credentials are stored unencrypted in '/var/lib/jenkins/.docker/config.json'.
23:39:26  Configure a credential helper to remove this warning. See
23:39:26  https://docs.docker.com/go/credential-store/
23:39:26  
23:39:26  Login Succeeded
23:39:26  + ok=1
23:39:26  + break
23:39:26  + [ -z 1 ]
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh

23:39:26  + set -eu
23:39:26  + ok=
23:39:26  + seq 1 3
23:39:26  + docker push ghcr.io/kyj0503/backtest-frontend:149
23:39:26  The push refers to repository [ghcr.io/kyj0503/backtest-frontend]
23:39:26  c0d5d7d3ce48: Preparing
23:39:26  aa000d710c0b: Preparing
23:39:26  ce495f7b0b7d: Preparing
23:39:26  9c70f446fbe2: Preparing
23:39:26  5be225e16e44: Preparing
23:39:26  3d04ead9b400: Preparing
23:39:26  af5598fef05f: Preparing
23:39:26  8fbd5a835e5e: Preparing
23:39:26  75061be64847: Preparing
23:39:26  d4fc045c9e3a: Preparing
23:39:26  3d04ead9b400: Waiting
23:39:26  af5598fef05f: Waiting
23:39:26  8fbd5a835e5e: Waiting
23:39:26  75061be64847: Waiting
23:39:26  d4fc045c9e3a: Waiting
23:39:27  ce495f7b0b7d: Layer already exists
23:39:27  5be225e16e44: Layer already exists
23:39:27  aa000d710c0b: Layer already exists
23:39:27  9c70f446fbe2: Layer already exists
23:39:27  c0d5d7d3ce48: Layer already exists

23:39:27  3d04ead9b400: Layer already exists
23:39:27  d4fc045c9e3a: Layer already exists
23:39:27  75061be64847: Layer already exists
23:39:27  8fbd5a835e5e: Layer already exists
23:39:27  af5598fef05f: Layer already exists

23:39:35  149: digest: sha256:fd5e413ceab98a7b301e5b0635ece43e1cc72ee5347f5f55f545a92e80682b62 size: 2406
23:39:35  + ok=1
23:39:35  + break
23:39:35  + [ -z 1 ]
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // parallel
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Deploy to Production (Local))
[Pipeline] script
[Pipeline] {
[Pipeline] withCredentials
23:39:36  Masking supported pattern matches of $GH_TOKEN or $SSH_KEY
[Pipeline] {
[Pipeline] echo
23:39:36  Deploying to /opt/backtest on localhost as jenkins
[Pipeline] sh
23:39:36  + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost mkdir -p /opt/backtest

[Pipeline] sh
23:39:37  + scp -i **** -o StrictHostKeyChecking=no /var/lib/jenkins/workspace/Backtest/compose/compose.prod.yml jenkins@localhost:/opt/backtest/docker-compose.yml
[Pipeline] sh

23:39:37  + scp -i **** -o StrictHostKeyChecking=no ./scripts/remote_deploy.sh jenkins@localhost:/opt/backtest/remote_deploy.sh
[Pipeline] sh
23:39:38  + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost chmod +x /opt/backtest/remote_deploy.sh
[Pipeline] sh

23:39:38  + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost /opt/backtest/remote_deploy.sh ghcr.io/kyj0503/backtest-backend:149 ghcr.io/kyj0503/backtest-frontend:149 /opt/backtest

23:39:40  149: Pulling from kyj0503/backtest-backend
23:39:40  Digest: sha256:4f3374d803b76bf141c4994330ac61ebb639fa4bd43812110f1624eb1a81aede
23:39:40  Status: Image is up to date for ghcr.io/kyj0503/backtest-backend:149
23:39:40  ghcr.io/kyj0503/backtest-backend:149
23:39:41  149: Pulling from kyj0503/backtest-frontend
23:39:41  Digest: sha256:fd5e413ceab98a7b301e5b0635ece43e1cc72ee5347f5f55f545a92e80682b62
23:39:41  Status: Image is up to date for ghcr.io/kyj0503/backtest-frontend:149
23:39:41  ghcr.io/kyj0503/backtest-frontend:149
23:39:41  [2025-09-15 23:39:41] Starting deploy: backend=ghcr.io/kyj0503/backtest-backend:149 frontend=ghcr.io/kyj0503/backtest-frontend:149
23:39:41  Current docker-compose.yml configuration:
23:39:41  services:
23:39:41    backend:
23:39:41      image: ghcr.io/kyj0503/backtest-backend:149
23:39:41      ports:
23:39:41        - "8001:8000"
23:39:41      env_file:
23:39:41        - ./backend/.env
23:39:41      restart: unless-stopped
23:39:41  
23:39:41    frontend:
23:39:41      image: ghcr.io/kyj0503/backtest-frontend:149
23:39:41      ports:
23:39:41        - "8082:80"
23:39:41      depends_on:
23:39:41        - backend
23:39:41      restart: unless-stopped

23:39:42   Container backtest-backend-1  Recreate
23:39:42   Container backtest-backend-1  Recreated
23:39:42   Container backtest-frontend-1  Recreate

23:39:43   Container backtest-frontend-1  Recreated
23:39:43   Container backtest-backend-1  Starting
23:39:43   Container backtest-backend-1  Started
23:39:43   Container backtest-frontend-1  Starting
23:39:43   Container backtest-frontend-1  Started
23:39:43  [2025-09-15 23:39:41] Deploy succeeded

23:39:48    % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
23:39:48                                   Dload  Upload   Total   Spent    Left  Speed
23:39:48  
23:39:48    0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
23:39:48  100    79  100    79    0     0  34184      0 --:--:-- --:--:-- --:--:-{"status":"healthy","timestamp":"2025-09-15T14:39:48.314053","version":"1.0.0"}- 39500
23:39:48    % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
23:39:48                                   Dload  Upload   Total   Spent    Left  Speed
23:39:48  
23:39:48    0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
23:39:48  100  1074  100  1074    0     0   287k      0 --:--:-- -﻿<!doctype html>
23:39:48  <html lang="ko">
23:39:48    <head>
23:39:48      <meta charset="UTF-8" />
23:39:48      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
23:39:48      <title>라고할때살걸</title>
23:39:48      <link rel="preconnect" href="https://fonts.googleapis.com">
23:39:48      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
23:39:48      <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Lora:ital,wght@0,400..700;1,400..700&family=Fira+Code:wght@300..700&display=swap" rel="stylesheet">
23:39:48      <script type="module" crossorigin src="/assets/index-2e2a7a35.js"></script>
23:39:48      <link rel="modulepreload" crossorigin href="/assets/react-vendor-4413ae29.js">
23:39:48      <link rel="modulepreload" crossorigin href="/assets/icon-vendor-c4a0e88b.js">
23:39:48      <link rel="modulepreload" crossorigin href="/assets/chart-vendor-df37046f.js">
23:39:48      <link rel="stylesheet" href="/assets/index-8e69c335.css">
23:39:48    </head>
23:39:48    <body>
23:39:48      <div id="root"></div>
23:39:48      
23:39:48    </body>
23:39:48  </html>
23:39:48  -:--:-- --:--:--  349k
23:39:48  [2025-09-15 23:39:41] Deployment finished with status=success
[Pipeline] }
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // script
[Pipeline] }

[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Integration Tests)
[Pipeline] script
[Pipeline] {
[Pipeline] echo
23:39:48  Running integration tests against deployed environment...
[Pipeline] sh
23:39:49  + seq 1 30
23:39:49  + curl -fsS http://localhost:8001/health
23:39:49  + echo backend healthy
23:39:49  backend healthy
23:39:49  + break
23:39:49  + seq 1 30
23:39:49  + curl -fsS http://localhost:8082/
23:39:49  + echo frontend up
23:39:49  frontend up
23:39:49  + break
[Pipeline] sh
23:39:49  + cat
23:39:49  + command -v jq
23:39:49  + JQ=jq -e
23:39:49  + MAX_TRIES=3
23:39:49  + DELAY=5
23:39:49  + SUCCESS=0
23:39:49  + seq 1 3
23:39:49  + echo [integration] backend attempt 1/3
23:39:49  [integration] backend attempt 1/3
23:39:49  + curl -fsS -H Content-Type: application/json -d @/tmp/payload.json http://localhost:8001/api/v1/backtest/chart-data
23:39:49  + tee /tmp/resp.json

23:39:51  {"ticker":"AAPL","strategy":"buy_and_hold","start_date":"2023-01-03","end_date":"2023-01-20","ohlc_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","open":128.4682,"high":129.0796,"low":122.4432,"close":123.3307,"volume":112117500},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","open":125.1253,"high":126.8707,"low":123.3405,"close":124.6027,"volume":89113600},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","open":125.362,"high":125.9931,"low":123.025,"close":123.2814,"volume":80962700},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","open":124.2576,"high":128.4781,"low":123.1532,"close":127.8174,"volume":87754700},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","open":128.6556,"high":131.5547,"low":128.0836,"close":128.34,"volume":70790800},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","open":128.4485,"high":129.4346,"low":126.3382,"close":128.9119,"volume":63896200},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","open":129.4247,"high":131.6532,"low":128.6457,"close":131.6335,"volume":69458900},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","open":132.0181,"high":132.3928,"low":129.6121,"close":131.5547,"volume":71379600},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","open":130.1938,"high":133.0437,"low":129.829,"close":132.8859,"volume":57809700},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","open":132.9549,"high":135.3807,"low":132.2647,"close":134.0495,"volume":63646600},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","open":134.9172,"high":136.6823,"low":133.1521,"close":133.3296,"volume":69672800},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","open":132.2153,"high":134.3552,"low":131.9097,"close":133.3888,"volume":58280400},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","open":133.3986,"high":136.1005,"low":132.3534,"close":135.9526,"volume":80223600}],"equity_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","equity":10000.0,"return_pct":0.0,"drawdown_pct":0.0},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","equity":10103.13733725666,"return_pct":1.0313733725666019,"drawdown_pct":0.0},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","equity":9996.002617353182,"return_pct":-0.03997382646817593,"drawdown_pct":-1.0713471990347778},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","equity":10363.794253985423,"return_pct":3.637942539854233,"drawdown_pct":0.0},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","equity":10406.168131697948,"return_pct":4.061681316979482,"drawdown_pct":0.0},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","equity":10452.539392057291,"return_pct":4.525393920572918,"drawdown_pct":0.0},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","equity":10673.214374036635,"return_pct":6.7321437403663476,"drawdown_pct":0.0},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","equity":10666.825048426708,"return_pct":6.668250484267091,"drawdown_pct":-0.06389325609925667},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","equity":10774.762488172046,"return_pct":7.74762488172045,"drawdown_pct":0.0},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","equity":10869.110448574442,"return_pct":8.691104485744416,"drawdown_pct":0.0},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","equity":10810.738931993414,"return_pct":8.107389319934132,"drawdown_pct":-0.5837151658102844},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","equity":10815.53903448209,"return_pct":8.15539034482089,"drawdown_pct":-0.5357141409235258},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","equity":11023.41914867912,"return_pct":10.234191486791211,"drawdown_pct":0.0}],"trade_markers":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","price":123.3307,"type":"entry","side":"buy","size":1.0,"pnl_pct":null}],"indicators":[],"summary_stats":{"total_return_pct":8.168520298768854,"sharpe_ratio":3.471876749490803,"max_drawdown_pct":-1.8417908279401263,"total_trades":0,"win_rate_pct":0.0,"profit_factor":0.0,"final_equity":10816.852029876885,"volatility_pct":0.0,"annualized_return_pct":358.1762920344951,"sortino_ratio":40.74408155306316,"calmar_ratio":194.47175357859845}}+ cat /tmp/resp.json
23:39:51  + jq -e .ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)
23:39:51  + echo [integration] backend check passed
23:39:51  [integration] backend check passed
23:39:51  + SUCCESS=1
23:39:51  + break
23:39:51  + [ 1 -ne 1 ]
23:39:51  + SUCCESS=0
23:39:51  + seq 1 3
23:39:51  + echo [integration] frontend attempt 1/3
23:39:51  [integration] frontend attempt 1/3
23:39:51  + curl -fsS -H Content-Type: application/json -d @/tmp/payload.json http://localhost:8082/api/v1/backtest/chart-data
23:39:51  + tee /tmp/resp2.json
23:39:51  {"ticker":"AAPL","strategy":"buy_and_hold","start_date":"2023-01-03","end_date":"2023-01-20","ohlc_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","open":128.4682,"high":129.0796,"low":122.4432,"close":123.3307,"volume":112117500},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","open":125.1253,"high":126.8707,"low":123.3405,"close":124.6027,"volume":89113600},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","open":125.362,"high":125.9931,"low":123.025,"close":123.2814,"volume":80962700},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","open":124.2576,"high":128.4781,"low":123.1532,"close":127.8174,"volume":87754700},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","open":128.6556,"high":131.5547,"low":128.0836,"close":128.34,"volume":70790800},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","open":128.4485,"high":129.4346,"low":126.3382,"close":128.9119,"volume":63896200},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","open":129.4247,"high":131.6532,"low":128.6457,"close":131.6335,"volume":69458900},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","open":132.0181,"high":132.3928,"low":129.6121,"close":131.5547,"volume":71379600},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","open":130.1938,"high":133.0437,"low":129.829,"close":132.8859,"volume":57809700},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","open":132.9549,"high":135.3807,"low":132.2647,"close":134.0495,"volume":63646600},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","open":134.9172,"high":136.6823,"low":133.1521,"close":133.3296,"volume":69672800},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","open":132.2153,"high":134.3552,"low":131.9097,"close":133.3888,"volume":58280400},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","open":133.3986,"high":136.1005,"low":132.3534,"close":135.9526,"volume":80223600}],"equity_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","equity":10000.0,"return_pct":0.0,"drawdown_pct":0.0},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","equity":10103.13733725666,"return_pct":1.0313733725666019,"drawdown_pct":0.0},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","equity":9996.002617353182,"return_pct":-0.03997382646817593,"drawdown_pct":-1.0713471990347778},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","equity":10363.794253985423,"return_pct":3.637942539854233,"drawdown_pct":0.0},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","equity":10406.168131697948,"return_pct":4.061681316979482,"drawdown_pct":0.0},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","equity":10452.539392057291,"return_pct":4.525393920572918,"drawdown_pct":0.0},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","equity":10673.214374036635,"return_pct":6.7321437403663476,"drawdown_pct":0.0},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","equity":10666.825048426708,"return_pct":6.668250484267091,"drawdown_pct":-0.06389325609925667},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","equity":10774.762488172046,"return_pct":7.74762488172045,"drawdown_pct":0.0},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","equity":10869.110448574442,"return_pct":8.691104485744416,"drawdown_pct":0.0},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","equity":10810.738931993414,"return_pct":8.107389319934132,"drawdown_pct":-0.5837151658102844},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","equity":10815.53903448209,"return_pct":8.15539034482089,"drawdown_pct":-0.5357141409235258},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","equity":11023.41914867912,"return_pct":10.234191486791211,"drawdown_pct":0.0}],"trade_markers":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","price":123.3307,"type":"entry","side":"buy","size":1.0,"pnl_pct":null}],"indicators":[],"summary_stats":{"total_return_pct":8.168520298768854,"sharpe_ratio":3.471876749490803,"max_drawdown_pct":-1.8417908279401263,"total_trades":0,"win_rate_pct":0.0,"profit_factor":0.0,"final_equity":10816.852029876885,"volatility_pct":0.0,"annualized_return_pct":358.1762920344951,"sortino_ratio":40.74408155306316,"calmar_ratio":194.47175357859845}}+ cat /tmp/resp2.json
23:39:51  + jq -e .ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)
23:39:51  + echo [integration] frontend check passed
23:39:51  [integration] frontend check passed
23:39:51  + SUCCESS=1
23:39:51  + break
23:39:51  + [ 1 -ne 1 ]
[Pipeline] echo
23:39:51  Integration API checks (direct & via frontend) passed
[Pipeline] echo
23:39:51  Integration tests completed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Declarative: Post Actions)
[Pipeline] sh

23:39:51  + docker system prune -f

23:39:54  Deleted build cache objects:
23:39:54  i92f9rlorzjy6mmq3c7rdcb5u
23:39:54  480f6do0ezadmn3ai377awcnu
23:39:54  229n9pnhvpgmtfkk6oysve3j2
23:39:54  joz4ztfdwqfpwqmu6y2lpralx
23:39:54  y9zt0ej873tlkgkp60eejviok
23:39:54  0b7lbklyqj8gye63ierlbxdk2
23:39:54  s358mp830iyzc3gfgabr99x6n
23:39:54  ip7jpe2gsniry7a2ojkqqwxbo
23:39:54  tmqm1gdw7vr9p66zm6r43su1n
23:39:54  wnc8vhd5f1pu89qsgvzgqqw6y
23:39:54  l03bh9cfq6f9sajim7wuemd5b
23:39:54  hlsg8um4290uf7ebcpokjhknp
23:39:54  jb4qhr5ov1kacqbhf8w29och5
23:39:54  ab4i20bxeyomfmz8r89fxgbpm
23:39:54  y2eejjmu6yrjmairlmxrdxk3y
23:39:54  mtv0cr5vusfxh4e7es94yywtg
23:39:54  
23:39:54  Total reclaimed space: 1.647GB
[Pipeline] cleanWs
23:39:54  [WS-CLEANUP] Deleting project workspace...
23:39:54  [WS-CLEANUP] Deferred wipeout is disabled by the job configuration...

23:39:55  [WS-CLEANUP] done
[Pipeline] echo
23:39:55  Pipeline succeeded!
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // timestamps
[Pipeline] }

[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
Finished: SUCCESS
