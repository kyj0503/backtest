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
00:10:13  The recommended git tool is: /usr/bin/git
00:10:13  using credential github-token
00:10:13  Cloning the remote Git repository
00:10:13  Cloning repository https://github.com/capstone-backtest/backtest.git
00:10:13   > /usr/bin/git init /var/lib/jenkins/workspace/Backtest # timeout=10
00:10:13  Fetching upstream changes from https://github.com/capstone-backtest/backtest.git
00:10:13   > /usr/bin/git --version # timeout=10
00:10:13   > git --version # 'git version 2.43.0'
00:10:13  using GIT_ASKPASS to set credentials GHCR Token (Username/Password type)
00:10:13   > /usr/bin/git fetch --tags --force --progress -- https://github.com/capstone-backtest/backtest.git +refs/heads/*:refs/remotes/origin/* # timeout=10
00:10:14   > /usr/bin/git config remote.origin.url https://github.com/capstone-backtest/backtest.git # timeout=10
00:10:14   > /usr/bin/git config --add remote.origin.fetch +refs/heads/*:refs/remotes/origin/* # timeout=10
00:10:14  Avoid second fetch
00:10:14   > /usr/bin/git rev-parse refs/remotes/origin/main^{commit} # timeout=10
00:10:14  Checking out Revision 0bfcde62630a7cbbcd82d10494df7514c7d16167 (refs/remotes/origin/main)
00:10:14   > /usr/bin/git config core.sparsecheckout # timeout=10
00:10:14   > /usr/bin/git checkout -f 0bfcde62630a7cbbcd82d10494df7514c7d16167 # timeout=10
00:10:14  Commit message: "ci(jenkins): Checks API 적용"
00:10:14   > /usr/bin/git rev-list --no-walk 6bf1f85dd26664370080e6ccc6e898ad3915523c # timeout=10
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Debug Environment)
[Pipeline] script
[Pipeline] {
[Pipeline] echo
00:10:14  Debug Information:
[Pipeline] sh
00:10:15  + git rev-parse --short HEAD
[Pipeline] sh
00:10:15  + git rev-parse --abbrev-ref HEAD
[Pipeline] echo
00:10:15  BRANCH_NAME: HEAD
[Pipeline] echo
00:10:15  GIT_BRANCH: HEAD
[Pipeline] echo
00:10:15  GIT_BRANCH_NAME: HEAD
[Pipeline] echo
00:10:15  GIT_COMMIT_SHORT: 0bfcde6
[Pipeline] echo
00:10:15  BUILD_NUMBER: 150
[Pipeline] echo
00:10:15  All env vars:
[Pipeline] sh
00:10:15  + id -u
[Pipeline] sh
00:10:16  + id -g
[Pipeline] sh
00:10:16  + env
00:10:16  + grep -E (BRANCH|GIT|BUILD)
00:10:16  + sort
00:10:16  BRANCH_NAME=HEAD
00:10:16  BUILD_DISPLAY_NAME=#150
00:10:16  BUILD_ID=150
00:10:16  BUILD_NUMBER=150
00:10:16  BUILD_TAG=jenkins-Backtest-150
00:10:16  BUILD_URL=https://jenkins.yeonjae.kr/job/Backtest/150/
00:10:16  GIT_BRANCH=HEAD
00:10:16  GIT_BRANCH_NAME=HEAD
00:10:16  GIT_COMMIT_SHORT=0bfcde6
00:10:16  + echo UID_J=131 GID_J=134
00:10:16  UID_J=131 GID_J=134
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
00:10:16  Running frontend tests...
[Pipeline] sh
[Pipeline] echo
00:10:16  Running backend tests with controlled environment...
[Pipeline] sh
00:10:16  + cd frontend
00:10:16  + docker build --build-arg RUN_TESTS=true -t backtest-frontend-test:150 .
00:10:16  #0 building with "default" instance using docker driver
00:10:16  
00:10:16  #1 [internal] load build definition from Dockerfile
00:10:16  + cd backend
00:10:16  + docker build --build-arg RUN_TESTS=true -t backtest-backend-test:150 .
00:10:17  #1 transferring dockerfile: 983B done
00:10:17  #1 DONE 0.0s
00:10:17  
00:10:17  #2 [internal] load metadata for docker.io/library/node:20.8.1-alpine
00:10:17  #0 building with "default" instance using docker driver
00:10:17  
00:10:17  #1 [internal] load build definition from Dockerfile
00:10:17  #1 transferring dockerfile: 1.54kB done
00:10:17  #1 DONE 0.0s
00:10:17  
00:10:17  #2 [internal] load metadata for docker.io/library/python:3.11-slim
00:10:18  #2 ...
00:10:18  
00:10:18  #3 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
00:10:18  #3 DONE 1.7s
00:10:18  
00:10:18  #2 [internal] load metadata for docker.io/library/node:20.8.1-alpine
00:10:18  #2 DONE 1.9s
00:10:18  
00:10:18  #3 [internal] load .dockerignore
00:10:18  #3 transferring context: 92B done
00:10:18  #3 DONE 0.0s
00:10:18  
00:10:18  #4 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
00:10:18  #4 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
00:10:18  #4 DONE 0.0s
00:10:18  
00:10:18  #5 [internal] load build context
00:10:18  #5 transferring context: 862.12kB 0.0s done
00:10:18  #5 DONE 0.1s
00:10:18  
00:10:18  #6 [ 4/13] COPY requirements.txt .
00:10:18  #6 CACHED
00:10:18  
00:10:18  #7 [12/13] COPY run_server.py .
00:10:18  #7 CACHED
00:10:18  
00:10:18  #8 [ 2/13] WORKDIR /app
00:10:18  #8 CACHED
00:10:18  
00:10:18  #9 [ 5/13] COPY requirements-test.txt .
00:10:18  #9 CACHED
00:10:18  
00:10:18  #10 [10/13] COPY app ./app
00:10:18  #10 CACHED
00:10:18  
00:10:18  #11 [11/13] COPY tests ./tests
00:10:18  #11 CACHED
00:10:18  
00:10:18  #12 [ 7/13] RUN uv pip install --system -r requirements.txt
00:10:18  #12 CACHED
00:10:18  
00:10:18  #13 [ 9/13] RUN uv pip install --system backtesting
00:10:18  #13 CACHED
00:10:18  
00:10:18  #14 [ 8/13] RUN uv pip install --system -r requirements-test.txt
00:10:18  #14 CACHED
00:10:18  
00:10:18  #15 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
00:10:18  #15 CACHED
00:10:18  
00:10:18  #16 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
00:10:18  #16 CACHED
00:10:18  
00:10:18  #17 [13/13] RUN if [ "true" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
00:10:18  #17 CACHED
00:10:18  
00:10:18  #18 exporting to image
00:10:18  #18 exporting layers done
00:10:18  #18 writing image sha256:83b98c4c07f546f2bc7010a59a5704827cab125fbf8d9fdaea5102a1cdf21555 done
00:10:18  #18 naming to docker.io/library/backtest-backend-test:150 done
00:10:18  #18 DONE 0.0s
[Pipeline] echo
00:10:19  Backend tests passed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
00:10:20  #2 DONE 3.0s
00:10:20  
00:10:20  #4 [internal] load .dockerignore
00:10:20  #4 transferring context: 2B done
00:10:20  #4 DONE 0.0s
00:10:20  
00:10:20  #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
00:10:20  #5 DONE 0.0s
00:10:20  
00:10:20  #6 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
00:10:20  #6 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
00:10:20  #6 DONE 0.0s
00:10:20  
00:10:20  #7 [internal] load build context
00:10:20  #7 transferring context: 917.94kB 0.0s done
00:10:20  #7 DONE 0.1s
00:10:20  
00:10:20  #8 [build 4/7] RUN npm ci --no-audit --prefer-offline --no-fund
00:10:20  #8 CACHED
00:10:20  
00:10:20  #9 [build 5/7] COPY . .
00:10:20  #9 CACHED
00:10:20  
00:10:20  #10 [build 2/7] WORKDIR /app
00:10:20  #10 CACHED
00:10:20  
00:10:20  #11 [build 3/7] COPY package.json package-lock.json ./
00:10:20  #11 CACHED
00:10:20  
00:10:20  #12 [build 6/7] RUN if [ "true" = "true" ] ; then npm test -- --run ; fi
00:10:20  #12 CACHED
00:10:20  
00:10:20  #13 [build 7/7] RUN npm run build
00:10:20  #13 CACHED
00:10:20  
00:10:20  #14 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
00:10:20  #14 CACHED
00:10:20  
00:10:20  #15 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
00:10:20  #15 CACHED
00:10:20  
00:10:20  #16 exporting to image
00:10:20  #16 exporting layers done
00:10:20  #16 writing image sha256:f2c3246c31c6dfb95da99d0d0257ed11abc0d6dc313d09718744125d326adbef done
00:10:20  #16 naming to docker.io/library/backtest-frontend-test:150 done
00:10:20  #16 DONE 0.0s
[Pipeline] echo
00:10:20  Frontend tests passed
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
00:10:20  + mkdir -p reports/backend reports/frontend
00:10:20  + mkdir -p frontend/.npm
00:10:20  + chown 131:134 frontend/.npm
00:10:20  + docker run --rm -u 131:134 -v /var/lib/jenkins/workspace/Backtest/reports/backend:/reports backtest-backend-test:150 sh -lc pytest tests/unit/ -v --tb=short --junitxml=/reports/junit.xml
00:10:21  /usr/local/lib/python3.11/site-packages/hypothesis/_settings.py:968: HypothesisWarning: The database setting is not configured, and the default location is unusable - falling back to an in-memory database for this session.  path=PosixPath('/app/.hypothesis/examples')
00:10:21    value = getattr(self, name)
00:10:21  /usr/local/lib/python3.11/site-packages/hypothesis/_settings.py:969: HypothesisWarning: The database setting is not configured, and the default location is unusable - falling back to an in-memory database for this session.  path=PosixPath('/app/.hypothesis/examples')
00:10:21    if value != getattr(default, name):
00:10:21  ============================= test session starts ==============================
00:10:21  platform linux -- Python 3.11.13, pytest-7.4.3, pluggy-1.6.0 -- /usr/local/bin/python
00:10:21  cachedir: .pytest_cache
00:10:21  metadata: {'Python': '3.11.13', 'Platform': 'Linux-6.14.0-29-generic-x86_64-with-glibc2.41', 'Packages': {'pytest': '7.4.3', 'pluggy': '1.6.0'}, 'Plugins': {'mock': '3.15.0', 'metadata': '3.1.1', 'json-report': '1.5.0', 'xdist': '3.8.0', 'cov': '7.0.0', 'Faker': '37.6.0', 'hypothesis': '6.138.15', 'html': '4.1.1', 'asyncio': '0.21.1', 'anyio': '3.7.1'}}
00:10:21  hypothesis profile 'default' -> database=InMemoryExampleDatabase({})
00:10:21  rootdir: /app
00:10:21  plugins: mock-3.15.0, metadata-3.1.1, json-report-1.5.0, xdist-3.8.0, cov-7.0.0, Faker-37.6.0, hypothesis-6.138.15, html-4.1.1, asyncio-0.21.1, anyio-3.7.1
00:10:21  asyncio: mode=Mode.STRICT
00:10:22  collecting ... collected 43 items
00:10:22  
00:10:22  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_buy_and_hold_success PASSED [  2%]
00:10:23  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success PASSED [  4%]
00:10:23  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_rsi_strategy_success PASSED [  6%]
00:10:23  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_invalid_strategy PASSED [  9%]
00:10:23  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data PASSED [ 11%]
00:10:23  tests/unit/test_backtest_service.py::TestBacktestService::test_run_portfolio_backtest_success SKIPPED [ 13%]
00:10:23  tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success PASSED [ 16%]
00:10:24  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_with_different_initial_cash PASSED [ 18%]
00:10:24  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark PASSED [ 20%]
00:10:24  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency PASSED [ 23%]
00:10:25  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact PASSED [ 25%]
00:10:26  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_different_time_periods PASSED [ 27%]
00:10:26  tests/unit/test_cash_assets.py::TestCashAssets::test_cash_only_portfolio PASSED [ 30%]
00:10:26  tests/unit/test_cash_assets.py::TestCashAssets::test_mixed_cash_and_stock_portfolio PASSED [ 32%]
00:10:26  tests/unit/test_cash_assets.py::TestCashAssets::test_multiple_cash_entries PASSED [ 34%]
00:10:26  tests/unit/test_cash_assets.py::TestCashAssets::test_cash_dca_investment PASSED [ 37%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_success PASSED [ 39%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_invalid_ticker PASSED [ 41%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_empty_result PASSED [ 44%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_stock_data_date_validation PASSED [ 46%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_ticker_info_success PASSED [ 48%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_get_ticker_info_invalid_ticker PASSED [ 51%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_data_caching_behavior PASSED [ 53%]
00:10:26  tests/unit/test_data_fetcher.py::TestDataFetcher::test_multiple_tickers_data_fetching PASSED [ 55%]
00:10:27  tests/unit/test_data_fetcher.py::TestDataFetcher::test_decimal_precision_compliance PASSED [ 58%]
00:10:27  tests/unit/test_data_fetcher.py::TestDataFetcher::test_performance_benchmarks PASSED [ 60%]
00:10:27  tests/unit/test_data_fetcher.py::TestDataFetcher::test_concurrent_data_fetching PASSED [ 62%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_get_all_strategies_success PASSED [ 65%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_get_strategy_info_success PASSED [ 67%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_get_strategy_info_not_found PASSED [ 69%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_sma_crossover_valid PASSED [ 72%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_sma_crossover_invalid PASSED [ 74%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_rsi_strategy_valid PASSED [ 76%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_rsi_strategy_invalid PASSED [ 79%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_buy_and_hold PASSED [ 81%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_bollinger_bands_valid PASSED [ 83%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_validate_strategy_params_macd_strategy_valid PASSED [ 86%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_parameter_ranges_compliance PASSED [ 88%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_class_instantiation PASSED [ 90%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_default_parameters PASSED [ 93%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_strategy_registry_integrity PASSED [ 95%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_parameter_type_validation PASSED [ 97%]
00:10:27  tests/unit/test_strategy_service.py::TestStrategyService::test_edge_case_parameter_values PASSED [100%]
00:10:27  
00:10:27  =============================== warnings summary ===============================
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:323: 11 warnings
00:10:27    /usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:323: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
00:10:27      warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
00:10:27  
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093
00:10:27    /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1093: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'env'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
00:10:27      warn(
00:10:27  
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1062
00:10:27    /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1062: PydanticDeprecatedSince20: `min_items` is deprecated and will be removed, use `min_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
00:10:27      warn('`min_items` is deprecated and will be removed, use `min_length` instead', DeprecationWarning)
00:10:27  
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/fields.py:1068
00:10:27    /usr/local/lib/python3.11/site-packages/pydantic/fields.py:1068: PydanticDeprecatedSince20: `max_items` is deprecated and will be removed, use `max_length` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
00:10:27      warn('`max_items` is deprecated and will be removed, use `max_length` instead', DeprecationWarning)
00:10:27  
00:10:27  tests/unit/test_backtest_service.py:24
00:10:27    /app/tests/unit/test_backtest_service.py:24: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
00:10:27      pytestmark = pytest.mark.unit
00:10:27  
00:10:27  ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:298
00:10:27    /usr/local/lib/python3.11/site-packages/pydantic/_internal/_generate_schema.py:298: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.11/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_cash_assets.py:11
00:10:27    /app/tests/unit/test_cash_assets.py:11: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
00:10:27      pytestmark = pytest.mark.unit
00:10:27  
00:10:27  tests/unit/test_data_fetcher.py:23
00:10:27    /app/tests/unit/test_data_fetcher.py:23: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
00:10:27      pytestmark = pytest.mark.unit
00:10:27  
00:10:27  tests/unit/test_strategy_service.py:19
00:10:27    /app/tests/unit/test_strategy_service.py:19: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
00:10:27      pytestmark = pytest.mark.unit
00:10:27  
00:10:27  tests/unit/test_backtest_service.py: 14 warnings
00:10:27    /app/app/services/backtest/backtest_engine.py:67: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
00:10:27      result = bt.run()
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=85: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=96: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=100: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=115: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=136: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=159: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=196: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=210: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=230: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=244: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=245: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_sma_crossover_success
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_run_backtest_insufficient_data
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_performance_benchmark
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_result_consistency
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_backtest_commission_impact
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:966: UserWarning: time=255: Broker canceled the relative-sized order due to insufficient margin.
00:10:27      warnings.warn(
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success
00:10:27    /usr/local/lib/python3.11/site-packages/backtesting/backtesting.py:1545: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
00:10:27      stats = self.run(**dict(zip(heatmap.index.names, best_params)))
00:10:27  
00:10:27  tests/unit/test_backtest_service.py::TestBacktestService::test_optimize_strategy_success
00:10:27    /app/app/services/backtest/optimization_service.py:177: UserWarning: Some trades remain open at the end of backtest. Use `Backtest(..., finalize_trades=True)` to close them and include them in stats.
00:10:27      final_stats = bt.run(**best_params)
00:10:27  
00:10:27  ../usr/local/lib/python3.11/site-packages/_pytest/cacheprovider.py:451
00:10:27    /usr/local/lib/python3.11/site-packages/_pytest/cacheprovider.py:451: PytestCacheWarning: cache could not write path /app/.pytest_cache/v/cache/nodeids: [Errno 13] Permission denied: '/app/.pytest_cache/v/cache/nodeids'
00:10:27      config.cache.set("cache/nodeids", sorted(self.cached_nodeids))
00:10:27  
00:10:27  ../usr/local/lib/python3.11/site-packages/_pytest/stepwise.py:56
00:10:27    /usr/local/lib/python3.11/site-packages/_pytest/stepwise.py:56: PytestCacheWarning: cache could not write path /app/.pytest_cache/v/cache/stepwise: [Errno 13] Permission denied: '/app/.pytest_cache/v/cache/stepwise'
00:10:27      session.config.cache.set(STEPWISE_CACHE_DIR, [])
00:10:27  
00:10:27  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
00:10:27  -------------------- generated xml file: /reports/junit.xml --------------------
00:10:27  ================= 42 passed, 1 skipped, 129 warnings in 6.11s ==================
00:10:27  + docker run --rm -u 131:134 -e CI=1 -e VITEST_JUNIT_FILE=/reports/junit.xml -e NPM_CONFIG_CACHE=/app/.npm -v /var/lib/jenkins/workspace/Backtest/frontend:/app -v /var/lib/jenkins/workspace/Backtest/frontend/.npm:/app/.npm -v /var/lib/jenkins/workspace/Backtest/reports/frontend:/reports -w /app node:20-alpine sh -lc npm ci --prefer-offline --no-audit && npx vitest run
00:10:35  npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
00:10:43  
00:10:43  added 790 packages in 14s
00:10:43  
00:10:43  199 packages are looking for funding
00:10:43    run `npm fund` for details
00:10:43  
00:10:43  [7m[1m[36m RUN [39m[22m[27m [36mv0.34.6[39m [90m/app[39m
00:10:43  
00:10:45   [32m✓[39m src/utils/__tests__/dateUtils.test.ts [2m ([22m[2m38 tests[22m[2m)[22m[90m 51[2mms[22m[39m
00:10:45   [32m✓[39m src/utils/__tests__/numberUtils.test.ts [2m ([22m[2m57 tests[22m[2m)[22m[90m 36[2mms[22m[39m
00:10:45  [90mstderr[2m | src/hooks/__tests__/useBacktestForm.test.ts[2m > [22m[2museBacktestForm[2m > [22m[2m초기 상태[2m > [22m[2m기본값으로 올바르게 초기화되어야 함[22m[39m
00:10:45  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:45  
00:10:45   [32m✓[39m src/hooks/__tests__/useBacktestForm.test.ts [2m ([22m[2m19 tests[22m[2m)[22m[90m 94[2mms[22m[39m
00:10:46   [32m✓[39m src/utils/formatters.test.ts [2m ([22m[2m20 tests[22m[2m)[22m[90m 18[2mms[22m[39m
00:10:47  [90mstderr[2m | src/components/common/__tests__/FormField.test.tsx[2m > [22m[2mFormField[2m > [22m[2m기본 렌더링[2m > [22m[2m라벨과 입력 필드가 올바르게 렌더링되어야 함[22m[39m
00:10:47  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:47  
00:10:47   [32m✓[39m src/services/__tests__/api.test.ts [2m ([22m[2m4 tests[22m [2m|[22m [33m1 skipped[39m[2m)[22m[90m 22[2mms[22m[39m
00:10:47   [32m✓[39m src/components/common/__tests__/FormField.test.tsx [2m ([22m[2m18 tests[22m[2m)[22m[33m 972[2mms[22m[39m
00:10:48  [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
00:10:48  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:48  
00:10:49  [90mstderr[2m | src/hooks/__tests__/useBacktest.test.ts[2m > [22m[2museBacktest[2m > [22m[2m성공 시 결과를 설정하고 isPortfolio를 올바르게 표시해야 함[22m[39m
00:10:49  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:49  
00:10:49   [32m✓[39m src/hooks/__tests__/useBacktest.test.ts [2m ([22m[2m3 tests[22m[2m)[22m[90m 50[2mms[22m[39m
00:10:49  [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2monSubmit에서 오류 발생 시 에러 메시지를 표시해야 함[22m[39m
00:10:49  백테스트 실행 중 오류: Error: 테스트 오류
00:10:49      at [90m/app/[39msrc/components/__tests__/UnifiedBacktestForm.test.tsx:58:48
00:10:49      at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:135:14
00:10:49      at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:58:26
00:10:49      at runTest [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:663:17[90m)[39m
00:10:49      at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
00:10:49      at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
00:10:49      at runFiles [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:834:5[90m)[39m
00:10:49      at startTests [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:843:3[90m)[39m
00:10:49      at [90mfile:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:103:7
00:10:49      at withEnv [90m(file:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:73:5[90m)[39m
00:10:49  
00:10:49   [32m✓[39m src/components/__tests__/UnifiedBacktestForm.test.tsx [2m ([22m[2m2 tests[22m[2m)[22m[33m 2039[2mms[22m[39m
00:10:50   [32m✓[39m src/components/__tests__/charts.smoke.test.tsx [2m ([22m[2m4 tests[22m[2m)[22m[90m 163[2mms[22m[39m
00:10:50  [90mstderr[2m | src/components/__tests__/charts.smoke.test.tsx[2m > [22m[2mChart components (smoke)[2m > [22m[2mEquityChart renders an SVG with minimal data[22m[39m
00:10:50  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:50  
00:10:50   [32m✓[39m src/components/ErrorBoundary.test.tsx [2m ([22m[2m3 tests[22m[2m)[22m[90m 158[2mms[22m[39m
00:10:50  [90mstderr[2m | src/components/ErrorBoundary.test.tsx[2m > [22m[2mErrorBoundary[2m > [22m[2m정상적인 컴포넌트를 렌더링해야 함[22m[39m
00:10:50  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:50  
00:10:52  [90mstderr[2m | src/components/__tests__/CommissionForm.test.tsx[2m > [22m[2mCommissionForm[2m > [22m[2m기본 렌더링이 올바르게 되어야 함[22m[39m
00:10:52  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:52  
00:10:52  [90mstderr[2m | src/components/__tests__/PortfolioForm.test.tsx[2m > [22m[2mPortfolioForm[2m > [22m[2m렌더링 및 주요 액션(addStock/addCash/removeStock) 트리거[22m[39m
00:10:52  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:52  
00:10:52   [32m✓[39m src/components/__tests__/PortfolioForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[33m 654[2mms[22m[39m
00:10:52   [32m✓[39m src/components/__tests__/CommissionForm.test.tsx [2m ([22m[2m3 tests[22m[2m)[22m[33m 434[2mms[22m[39m
00:10:52  [90mstderr[2m | src/components/__tests__/StrategyForm.test.tsx[2m > [22m[2mStrategyForm[2m > [22m[2msma_crossover 선택 시 파라미터 입력 필드를 표시하고 변경 이벤트를 전파[22m[39m
00:10:52  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:52  
00:10:52   [32m✓[39m src/components/__tests__/StrategyForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[33m 326[2mms[22m[39m
00:10:53  [90mstderr[2m | src/components/__tests__/DateRangeForm.test.tsx[2m > [22m[2mDateRangeForm[2m > [22m[2m시작/종료 날짜 변경 시 핸들러 호출[22m[39m
00:10:53  Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
00:10:53  
00:10:53   [32m✓[39m src/components/__tests__/DateRangeForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[90m 256[2mms[22m[39m
00:10:53  
00:10:53  [2m Test Files [22m [1m[32m14 passed[39m[22m[90m (14)[39m
00:10:53  [2m      Tests [22m [1m[32m173 passed[39m[22m[2m | [22m[33m1 skipped[39m[90m (174)[39m
00:10:53  [2m   Start at [22m 15:10:43
00:10:53  [2m   Duration [22m 10.58s[2m (transform 595ms, setup 1.24s, collect 6.60s, tests 5.27s, environment 10.29s, prepare 1.63s)[22m
00:10:53  
[Pipeline] junit
00:10:54  Recording test results
[Pipeline] archiveArtifacts
00:10:54  Archiving artifacts
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
00:10:54  Masking supported pattern matches of $GH_TOKEN
[Pipeline] withCredentials
00:10:54  Masking supported pattern matches of $GH_TOKEN
[Pipeline] {
[Pipeline] {
[Pipeline] echo
00:10:54  Building PROD backend image: ghcr.io/kyj0503/backtest-backend:150
[Pipeline] sh
[Pipeline] echo
00:10:54  Building PROD frontend image: ghcr.io/kyj0503/backtest-frontend:150
[Pipeline] sh
00:10:55  + docker buildx inspect backtest-builder
00:10:55  + docker buildx use backtest-builder
00:10:55  + docker buildx inspect backtest-builder
00:10:55  + docker buildx use backtest-builder
[Pipeline] sh
[Pipeline] sh
00:10:55  + docker pull ghcr.io/kyj0503/backtest-backend:latest
00:10:55  + docker pull ghcr.io/kyj0503/backtest-frontend:latest
00:10:56  latest: Pulling from kyj0503/backtest-frontend
00:10:56  Digest: sha256:6f72c079b1588dd4b25a71ca7e28f3b6c7fd3f990097402bfe14a3482408710c
00:10:56  Status: Image is up to date for ghcr.io/kyj0503/backtest-frontend:latest
00:10:56  ghcr.io/kyj0503/backtest-frontend:latest
[Pipeline] sh
00:10:56  + cd frontend
00:10:56  + DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/kyj0503/backtest-frontend:latest -t ghcr.io/kyj0503/backtest-frontend:150 .
00:10:56  latest: Pulling from kyj0503/backtest-backend
00:10:56  Digest: sha256:3cee1ec4f8cd30f11867eb4540ba25ea0fb1c602df4264cf2aae4a8b34c180c9
00:10:56  Status: Image is up to date for ghcr.io/kyj0503/backtest-backend:latest
00:10:56  ghcr.io/kyj0503/backtest-backend:latest
[Pipeline] sh
00:10:56  #0 building with "default" instance using docker driver
00:10:56  
00:10:56  #1 [internal] load build definition from Dockerfile
00:10:56  #1 transferring dockerfile: 983B done
00:10:56  #1 DONE 0.0s
00:10:56  
00:10:56  #2 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
00:10:56  #2 DONE 0.0s
00:10:56  
00:10:56  #3 [internal] load metadata for docker.io/library/node:20.8.1-alpine
00:10:57  + cd backend
00:10:57  + DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg IMAGE_TAG=150 --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/kyj0503/backtest-backend:latest -t ghcr.io/kyj0503/backtest-backend:150 .
00:10:57  #0 building with "default" instance using docker driver
00:10:57  
00:10:57  #1 [internal] load build definition from Dockerfile
00:10:57  #1 transferring dockerfile: 1.54kB done
00:10:57  #1 DONE 0.0s
00:10:57  
00:10:57  #2 [internal] load metadata for docker.io/library/python:3.11-slim
00:10:57  #3 DONE 0.8s
00:10:57  
00:10:57  #4 [internal] load .dockerignore
00:10:57  #4 transferring context: 2B done
00:10:57  #4 DONE 0.0s
00:10:57  
00:10:57  #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
00:10:57  #5 DONE 0.0s
00:10:57  
00:10:57  #6 importing cache manifest from ghcr.io/kyj0503/backtest-frontend:latest
00:10:57  #6 DONE 0.0s
00:10:57  
00:10:57  #7 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
00:10:57  #7 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
00:10:57  #7 DONE 0.0s
00:10:57  
00:10:57  #8 [internal] load build context
00:10:57  #2 DONE 0.7s
00:10:57  
00:10:57  #3 [internal] load .dockerignore
00:10:57  #3 transferring context: 92B done
00:10:57  #3 DONE 0.0s
00:10:57  
00:10:57  #4 importing cache manifest from ghcr.io/kyj0503/backtest-backend:latest
00:10:57  #4 DONE 0.0s
00:10:57  
00:10:57  #5 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
00:10:57  #5 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
00:10:57  #5 DONE 0.0s
00:10:57  
00:10:57  #6 [internal] load build context
00:10:57  #6 transferring context: 7.32kB done
00:10:57  #6 DONE 0.0s
00:10:57  
00:10:57  #7 [ 2/13] WORKDIR /app
00:10:57  #7 CACHED
00:10:57  
00:10:57  #8 [ 4/13] COPY requirements.txt .
00:10:57  #8 CACHED
00:10:57  
00:10:57  #9 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
00:10:57  #9 CACHED
00:10:57  
00:10:57  #10 [11/13] COPY tests ./tests
00:10:57  #10 CACHED
00:10:57  
00:10:57  #11 [ 9/13] RUN uv pip install --system backtesting
00:10:57  #11 CACHED
00:10:57  
00:10:57  #12 [10/13] COPY app ./app
00:10:57  #12 CACHED
00:10:57  
00:10:57  #13 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
00:10:57  #13 CACHED
00:10:57  
00:10:57  #14 [ 8/13] RUN uv pip install --system -r requirements-test.txt
00:10:57  #14 CACHED
00:10:57  
00:10:57  #15 [ 5/13] COPY requirements-test.txt .
00:10:57  #15 CACHED
00:10:57  
00:10:57  #16 [ 7/13] RUN uv pip install --system -r requirements.txt
00:10:57  #16 CACHED
00:10:57  
00:10:57  #17 [12/13] COPY run_server.py .
00:10:57  #17 CACHED
00:10:57  
00:10:57  #18 [13/13] RUN if [ "false" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
00:10:58  #18 DONE 0.2s
00:10:58  
00:10:58  #19 exporting to image
00:10:58  #19 exporting layers 0.0s done
00:10:58  #19 preparing layers for inline cache 0.0s done
00:10:58  #19 writing image sha256:db0241cbb05d12506fff3e1a3a62bbf0c726bc4f77c66fb76e723a2a055fb755 done
00:10:58  #19 naming to ghcr.io/kyj0503/backtest-backend:150 done
00:10:58  #19 DONE 0.1s
[Pipeline] sh
00:10:58  + set -eu
00:10:58  + export DOCKER_CLIENT_TIMEOUT=300
00:10:58  + export COMPOSE_HTTP_TIMEOUT=300
00:10:58  + curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/
00:10:58  + echo Warning: GHCR probe failed; continuing
00:10:58  Warning: GHCR probe failed; continuing
00:10:58  + docker logout ghcr.io
00:10:58  + ok=
00:10:58  + seq 1 3
00:10:58  + printf %s ****
00:10:58  + docker login ghcr.io -u kyj0503 --password-stdin
00:10:59  
00:10:59  WARNING! Your credentials are stored unencrypted in '/var/lib/jenkins/.docker/config.json'.
00:10:59  Configure a credential helper to remove this warning. See
00:10:59  https://docs.docker.com/go/credential-store/
00:10:59  
00:10:59  Login Succeeded
00:10:59  + ok=1
00:10:59  + break
00:10:59  + [ -z 1 ]
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh
00:10:59  + set -eu
00:10:59  + ok=
00:10:59  + seq 1 3
00:10:59  + docker push ghcr.io/kyj0503/backtest-backend:150
00:10:59  The push refers to repository [ghcr.io/kyj0503/backtest-backend]
00:11:00  d279a95f289c: Preparing
00:11:00  1786f360df95: Preparing
00:11:00  3e13088c1051: Preparing
00:11:00  6da07a6a0e8f: Preparing
00:11:00  52e5562c7273: Preparing
00:11:00  57d8b80cef4b: Preparing
00:11:00  4430cc1d395d: Preparing
00:11:00  bb3118717ab5: Preparing
00:11:00  22c144244ab5: Preparing
00:11:00  0f420d6c9384: Preparing
00:11:00  18c41aea3627: Preparing
00:11:00  3bbebd0b50d8: Preparing
00:11:00  8d441cbfbc35: Preparing
00:11:00  49dd736005c7: Preparing
00:11:00  135aac4d5c9a: Preparing
00:11:00  daf557c4f08e: Preparing
00:11:00  57d8b80cef4b: Waiting
00:11:00  4430cc1d395d: Waiting
00:11:00  bb3118717ab5: Waiting
00:11:00  22c144244ab5: Waiting
00:11:00  0f420d6c9384: Waiting
00:11:00  18c41aea3627: Waiting
00:11:00  3bbebd0b50d8: Waiting
00:11:00  8d441cbfbc35: Waiting
00:11:00  49dd736005c7: Waiting
00:11:00  135aac4d5c9a: Waiting
00:11:00  daf557c4f08e: Waiting
00:11:01  3e13088c1051: Layer already exists
00:11:01  1786f360df95: Layer already exists
00:11:01  52e5562c7273: Layer already exists
00:11:01  6da07a6a0e8f: Layer already exists
00:11:01  4430cc1d395d: Layer already exists
00:11:01  22c144244ab5: Layer already exists
00:11:01  bb3118717ab5: Layer already exists
00:11:01  57d8b80cef4b: Layer already exists
00:11:01  0f420d6c9384: Layer already exists
00:11:01  18c41aea3627: Layer already exists
00:11:01  8d441cbfbc35: Layer already exists
00:11:01  3bbebd0b50d8: Layer already exists
00:11:01  49dd736005c7: Layer already exists
00:11:01  135aac4d5c9a: Layer already exists
00:11:02  daf557c4f08e: Layer already exists
00:11:02  #8 transferring context: 462.83MB 5.0s
00:11:02  d279a95f289c: Pushed
00:11:03  #8 transferring context: 551.51MB 5.9s done
00:11:03  #8 DONE 6.0s
00:11:03  
00:11:03  #5 [build 1/7] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
00:11:03  #5 resolve docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5 0.0s done
00:11:03  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 0B / 2.34MB 0.1s
00:11:03  #5 sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5 1.43kB / 1.43kB done
00:11:03  #5 sha256:1ccb0c0ded3b21cee95fe6b6ce1ac23bd6680c8f152cbfb3047d5d9ea490b098 1.16kB / 1.16kB done
00:11:03  #5 sha256:cf2316e995eb236a3d42066d396685efb1333bd540aface0a9bfc4ff29ce030f 6.78kB / 6.78kB done
00:11:03  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 0B / 3.40MB 0.1s
00:11:03  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 0B / 49.81MB 0.1s
00:11:04  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 1.05MB / 3.40MB 1.1s
00:11:04  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 3.15MB / 49.81MB 1.1s
00:11:04  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 2.10MB / 3.40MB 1.3s
00:11:04  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 1.05MB / 2.34MB 1.4s
00:11:05  #5 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 2.34MB / 2.34MB 1.5s done
00:11:05  #5 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 3.40MB / 3.40MB 1.5s done
00:11:05  #5 extracting sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 0.1s done
00:11:05  #5 sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 0B / 452B 1.5s
00:11:05  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 6.29MB / 49.81MB 1.7s
00:11:05  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 10.49MB / 49.81MB 2.0s
00:11:05  #5 sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 452B / 452B 2.0s done
00:11:05  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 14.68MB / 49.81MB 2.4s
00:11:06  150: digest: sha256:9150ea50a5af69e0d257dc09b376bb7cce2a8f7dd42406de955e4fd255ce9402 size: 3667
00:11:06  + ok=1
00:11:06  + break
00:11:06  + [ -z 1 ]
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
00:11:06  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 18.87MB / 49.81MB 2.8s
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
00:11:07  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 22.02MB / 49.81MB 3.4s
00:11:07  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 25.17MB / 49.81MB 3.7s
00:11:07  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 28.31MB / 49.81MB 4.0s
00:11:07  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 32.51MB / 49.81MB 4.3s
00:11:08  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 35.65MB / 49.81MB 4.6s
00:11:08  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 39.85MB / 49.81MB 4.9s
00:11:09  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 44.04MB / 49.81MB 5.3s
00:11:09  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 47.19MB / 49.81MB 5.6s
00:11:09  #5 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 49.81MB / 49.81MB 5.8s done
00:11:09  #5 extracting sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 0.1s
00:11:10  #5 extracting sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 1.5s done
00:11:10  #5 extracting sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef
00:11:11  #5 extracting sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 0.1s done
00:11:11  #5 extracting sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 done
00:11:11  #5 DONE 7.6s
00:11:11  
00:11:11  #9 [build 2/7] WORKDIR /app
00:11:11  #9 DONE 0.3s
00:11:11  
00:11:11  #10 [build 3/7] COPY package.json package-lock.json ./
00:11:11  #10 DONE 0.1s
00:11:11  
00:11:11  #11 [build 4/7] RUN npm ci --no-audit --prefer-offline --no-fund
00:11:18  #11 6.277 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.277 (Use `node --trace-warnings ...` to show where the warning was created)
00:11:18  #11 6.279 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.279 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.279 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.279 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.279 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.280 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.280 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.281 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.281 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.281 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.282 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.282 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.282 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.283 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.283 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.284 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.284 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.284 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.285 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.285 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.285 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.286 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.286 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.286 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.287 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.287 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.287 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.288 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.288 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.288 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.288 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.289 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.289 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.289 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.290 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.290 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.290 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.290 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.291 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.291 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.291 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.292 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.292 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.292 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.292 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.293 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.293 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.293 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.294 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.294 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.294 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.294 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.295 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.295 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.295 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.296 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.296 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.297 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.297 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.297 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.298 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.298 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.298 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:18  #11 6.299 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
00:11:23  #11 11.84 npm WARN deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
00:11:31  #11 18.77 
00:11:31  #11 18.77 added 790 packages in 18s
00:11:31  #11 18.77 npm notice 
00:11:31  #11 18.77 npm notice New major version of npm available! 10.1.0 -> 11.6.0
00:11:31  #11 18.77 npm notice Changelog: <https://github.com/npm/cli/releases/tag/v11.6.0>
00:11:31  #11 18.77 npm notice Run `npm install -g npm@11.6.0` to update!
00:11:31  #11 18.77 npm notice 
00:11:31  #11 DONE 19.1s
00:11:31  
00:11:31  #12 [build 5/7] COPY . .
00:11:41  #12 DONE 9.7s
00:11:41  
00:11:41  #13 [build 6/7] RUN if [ "false" = "true" ] ; then npm test -- --run ; fi
00:11:41  #13 DONE 0.2s
00:11:41  
00:11:41  #14 [build 7/7] RUN npm run build
00:11:41  #14 0.534 
00:11:41  #14 0.534 > backtesting-frontend@1.0.0 build
00:11:41  #14 0.534 > tsc && vite build
00:11:41  #14 0.534 
00:11:49  #14 8.826 vite v4.5.14 building for production...
00:11:49  #14 8.907 transforming...
00:11:59  #14 17.18 ✓ 2651 modules transformed.
00:11:59  #14 17.50 Generated an empty chunk: "util-vendor".
00:11:59  #14 17.62 rendering chunks...
00:11:59  #14 17.75 [plugin:vite:reporter] 
00:11:59  #14 17.75 (!) /app/src/components/ExchangeRateChart.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
00:11:59  #14 17.75 
00:11:59  #14 17.75 [plugin:vite:reporter] 
00:11:59  #14 17.75 (!) /app/src/components/StockVolatilityNews.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
00:11:59  #14 17.75 
00:11:59  #14 17.80 computing gzip size...
00:11:59  #14 17.83 dist/index.html                                 1.06 kB │ gzip:   0.53 kB
00:11:59  #14 17.83 dist/assets/index-8e69c335.css                 71.17 kB │ gzip:  12.42 kB
00:11:59  #14 17.83 dist/assets/util-vendor-4ed993c7.js             0.00 kB │ gzip:   0.02 kB
00:11:59  #14 17.83 dist/assets/CustomTooltip-a385ef6e.js           0.42 kB │ gzip:   0.32 kB
00:11:59  #14 17.83 dist/assets/EquityChart-c3267435.js             1.55 kB │ gzip:   0.80 kB
00:11:59  #14 17.83 dist/assets/TradesChart-03c94393.js             1.64 kB │ gzip:   0.94 kB
00:11:59  #14 17.83 dist/assets/OHLCChart-40b525f4.js               1.90 kB │ gzip:   0.97 kB
00:11:59  #14 17.83 dist/assets/FinancialTermTooltip-ce90e474.js    1.94 kB │ gzip:   1.76 kB
00:11:59  #14 17.83 dist/assets/StatsSummary-44db21f6.js            2.29 kB │ gzip:   1.12 kB
00:11:59  #14 17.83 dist/assets/StockPriceChart-c525171c.js         2.38 kB │ gzip:   1.21 kB
00:11:59  #14 17.83 dist/assets/icon-vendor-c4a0e88b.js             2.51 kB │ gzip:   1.09 kB
00:11:59  #14 17.83 dist/assets/react-vendor-4413ae29.js          162.28 kB │ gzip:  52.95 kB
00:11:59  #14 17.83 dist/assets/index-2e2a7a35.js                 305.11 kB │ gzip:  90.93 kB
00:11:59  #14 17.83 dist/assets/chart-vendor-df37046f.js          407.43 kB │ gzip: 109.28 kB
00:11:59  #14 17.83 ✓ built in 9.00s
00:11:59  #14 DONE 17.9s
00:11:59  
00:11:59  #15 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
00:11:59  #15 CACHED
00:11:59  
00:11:59  #16 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
00:11:59  #16 CACHED
00:11:59  
00:11:59  #17 exporting to image
00:11:59  #17 exporting layers done
00:11:59  #17 preparing layers for inline cache done
00:11:59  #17 writing image sha256:48307f82a6c2817dfd2a8f0b78ed4747ce95450c6b805dd15bdfeb6cf6a23b1f done
00:11:59  #17 naming to ghcr.io/kyj0503/backtest-frontend:150 done
00:11:59  #17 DONE 0.0s
[Pipeline] sh
00:11:59  + set -eu
00:11:59  + export DOCKER_CLIENT_TIMEOUT=300
00:11:59  + export COMPOSE_HTTP_TIMEOUT=300
00:11:59  + curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/
00:11:59  + echo Warning: GHCR probe failed; continuing
00:11:59  Warning: GHCR probe failed; continuing
00:11:59  + docker logout ghcr.io
00:11:59  + ok=
00:11:59  + seq 1 3
00:11:59  + printf %s ****
00:11:59  + docker login ghcr.io -u kyj0503 --password-stdin
00:12:00  
00:12:00  WARNING! Your credentials are stored unencrypted in '/var/lib/jenkins/.docker/config.json'.
00:12:00  Configure a credential helper to remove this warning. See
00:12:00  https://docs.docker.com/go/credential-store/
00:12:00  
00:12:00  Login Succeeded
00:12:00  + ok=1
00:12:00  + break
00:12:00  + [ -z 1 ]
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh
00:12:01  + set -eu
00:12:01  + ok=
00:12:01  + seq 1 3
00:12:01  + docker push ghcr.io/kyj0503/backtest-frontend:150
00:12:01  The push refers to repository [ghcr.io/kyj0503/backtest-frontend]
00:12:01  c0d5d7d3ce48: Preparing
00:12:01  aa000d710c0b: Preparing
00:12:01  ce495f7b0b7d: Preparing
00:12:01  9c70f446fbe2: Preparing
00:12:01  5be225e16e44: Preparing
00:12:01  3d04ead9b400: Preparing
00:12:01  af5598fef05f: Preparing
00:12:01  8fbd5a835e5e: Preparing
00:12:01  75061be64847: Preparing
00:12:01  d4fc045c9e3a: Preparing
00:12:01  8fbd5a835e5e: Waiting
00:12:01  75061be64847: Waiting
00:12:01  3d04ead9b400: Waiting
00:12:01  d4fc045c9e3a: Waiting
00:12:01  af5598fef05f: Waiting
00:12:02  5be225e16e44: Layer already exists
00:12:02  ce495f7b0b7d: Layer already exists
00:12:02  c0d5d7d3ce48: Layer already exists
00:12:02  aa000d710c0b: Layer already exists
00:12:02  9c70f446fbe2: Layer already exists
00:12:02  8fbd5a835e5e: Layer already exists
00:12:02  3d04ead9b400: Layer already exists
00:12:02  75061be64847: Layer already exists
00:12:02  af5598fef05f: Layer already exists
00:12:02  d4fc045c9e3a: Layer already exists
00:12:05  150: digest: sha256:eb2dd5b504dff9eb986cd71a0ce71e6881dcab2abdc1b1a028e8fd547ef0d47d size: 2406
00:12:05  + ok=1
00:12:05  + break
00:12:05  + [ -z 1 ]
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
00:12:06  Masking supported pattern matches of $GH_TOKEN or $SSH_KEY
[Pipeline] {
[Pipeline] echo
00:12:06  Deploying to /opt/backtest on localhost as jenkins
[Pipeline] sh
00:12:06  + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost mkdir -p /opt/backtest
[Pipeline] sh
00:12:07  + scp -i **** -o StrictHostKeyChecking=no /var/lib/jenkins/workspace/Backtest/compose/compose.prod.yml jenkins@localhost:/opt/backtest/docker-compose.yml
[Pipeline] sh
00:12:07  + scp -i **** -o StrictHostKeyChecking=no ./scripts/remote_deploy.sh jenkins@localhost:/opt/backtest/remote_deploy.sh
[Pipeline] sh
00:12:08  + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost chmod +x /opt/backtest/remote_deploy.sh
[Pipeline] sh
00:12:08  + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost /opt/backtest/remote_deploy.sh ghcr.io/kyj0503/backtest-backend:150 ghcr.io/kyj0503/backtest-frontend:150 /opt/backtest
00:12:10  150: Pulling from kyj0503/backtest-backend
00:12:10  Digest: sha256:9150ea50a5af69e0d257dc09b376bb7cce2a8f7dd42406de955e4fd255ce9402
00:12:10  Status: Image is up to date for ghcr.io/kyj0503/backtest-backend:150
00:12:10  ghcr.io/kyj0503/backtest-backend:150
00:12:12  150: Pulling from kyj0503/backtest-frontend
00:12:12  Digest: sha256:eb2dd5b504dff9eb986cd71a0ce71e6881dcab2abdc1b1a028e8fd547ef0d47d
00:12:12  Status: Image is up to date for ghcr.io/kyj0503/backtest-frontend:150
00:12:12  ghcr.io/kyj0503/backtest-frontend:150
00:12:12  [2025-09-16 00:12:12] Starting deploy: backend=ghcr.io/kyj0503/backtest-backend:150 frontend=ghcr.io/kyj0503/backtest-frontend:150
00:12:12  Current docker-compose.yml configuration:
00:12:12  services:
00:12:12    backend:
00:12:12      image: ghcr.io/kyj0503/backtest-backend:150
00:12:12      ports:
00:12:12        - "8001:8000"
00:12:12      env_file:
00:12:12        - ./backend/.env
00:12:12      restart: unless-stopped
00:12:12  
00:12:12    frontend:
00:12:12      image: ghcr.io/kyj0503/backtest-frontend:150
00:12:12      ports:
00:12:12        - "8082:80"
00:12:12      depends_on:
00:12:12        - backend
00:12:12      restart: unless-stopped
00:12:12   Container backtest-backend-1  Recreate
00:12:13   Container backtest-backend-1  Recreated
00:12:13   Container backtest-frontend-1  Recreate
00:12:13   Container backtest-frontend-1  Recreated
00:12:13   Container backtest-backend-1  Starting
00:12:13   Container backtest-backend-1  Started
00:12:13   Container backtest-frontend-1  Starting
00:12:13   Container backtest-frontend-1  Started
00:12:13  [2025-09-16 00:12:12] Deploy succeeded
00:12:19    % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
00:12:19                                   Dload  Upload   Total   Spent    Left  Speed
00:12:19  
00:12:19    0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
00:12:19  100    79  100    79    0     0  46171      0 --:--:-- --:--:-- --:--:-{"status":"healthy","timestamp":"2025-09-15T15:12:18.715602","version":"1.0.0"}- 79000
00:12:19    % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
00:12:19                                   Dload  Upload   Total   Spent    Left  Speed
00:12:19  
00:12:19    0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0﻿<!doctype html>
00:12:19  <html lang="ko">
00:12:19    <head>
00:12:19      <meta charset="UTF-8" />
00:12:19      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
00:12:19      <title>라고할때살걸</title>
00:12:19      <link rel="preconnect" href="https://fonts.googleapis.com">
00:12:19      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
00:12:19      <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Lora:ital,wght@0,400..700;1,400..700&family=Fira+Code:wght@300..700&display=swap" rel="stylesheet">
00:12:19      <script type="module" crossorigin src="/assets/index-2e2a7a35.js"></script>
00:12:19      <link rel="modulepreload" crossorigin href="/assets/react-vendor-4413ae29.js">
00:12:19      <link rel="modulepreload" crossorigin href="/assets/icon-vendor-c4a0e88b.js">
00:12:19      <link rel="modulepreload" crossorigin href="/assets/chart-vendor-df37046f.js">
00:12:19      <link rel="stylesheet" href="/assets/index-8e69c335.css">
00:12:19    </head>
00:12:19    <body>
00:12:19      <div id="root"></div>
00:12:19      
00:12:19    </body>
00:12:19  </html>
00:12:19  
00:12:19  100  1074  100  1074    0     0   949k      0 --:--:-- --:--:-- --:--:-- 1048k
00:12:19  [2025-09-16 00:12:12] Deployment finished with status=success
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
00:12:19  Running integration tests against deployed environment...
[Pipeline] sh
00:12:19  + seq 1 30
00:12:19  + curl -fsS http://localhost:8001/health
00:12:19  + echo backend healthy
00:12:19  backend healthy
00:12:19  + break
00:12:19  + seq 1 30
00:12:19  + curl -fsS http://localhost:8082/
00:12:19  + echo frontend up
00:12:19  frontend up
00:12:19  + break
[Pipeline] sh
00:12:19  + cat
00:12:19  + command -v jq
00:12:19  + JQ=jq -e
00:12:19  + MAX_TRIES=3
00:12:19  + DELAY=5
00:12:19  + SUCCESS=0
00:12:19  + seq 1 3
00:12:19  + echo [integration] backend attempt 1/3
00:12:19  [integration] backend attempt 1/3
00:12:19  + curl -fsS -H Content-Type: application/json -d @/tmp/payload.json http://localhost:8001/api/v1/backtest/chart-data
00:12:19  + tee /tmp/resp.json
00:12:21  {"ticker":"AAPL","strategy":"buy_and_hold","start_date":"2023-01-03","end_date":"2023-01-20","ohlc_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","open":128.4682,"high":129.0796,"low":122.4432,"close":123.3307,"volume":112117500},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","open":125.1253,"high":126.8707,"low":123.3405,"close":124.6027,"volume":89113600},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","open":125.362,"high":125.9931,"low":123.025,"close":123.2814,"volume":80962700},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","open":124.2576,"high":128.4781,"low":123.1532,"close":127.8174,"volume":87754700},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","open":128.6556,"high":131.5547,"low":128.0836,"close":128.34,"volume":70790800},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","open":128.4485,"high":129.4346,"low":126.3382,"close":128.9119,"volume":63896200},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","open":129.4247,"high":131.6532,"low":128.6457,"close":131.6335,"volume":69458900},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","open":132.0181,"high":132.3928,"low":129.6121,"close":131.5547,"volume":71379600},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","open":130.1938,"high":133.0437,"low":129.829,"close":132.8859,"volume":57809700},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","open":132.9549,"high":135.3807,"low":132.2647,"close":134.0495,"volume":63646600},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","open":134.9172,"high":136.6823,"low":133.1521,"close":133.3296,"volume":69672800},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","open":132.2153,"high":134.3552,"low":131.9097,"close":133.3888,"volume":58280400},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","open":133.3986,"high":136.1005,"low":132.3534,"close":135.9526,"volume":80223600}],"equity_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","equity":10000.0,"return_pct":0.0,"drawdown_pct":0.0},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","equity":10103.13733725666,"return_pct":1.0313733725666019,"drawdown_pct":0.0},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","equity":9996.002617353182,"return_pct":-0.03997382646817593,"drawdown_pct":-1.0713471990347778},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","equity":10363.794253985423,"return_pct":3.637942539854233,"drawdown_pct":0.0},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","equity":10406.168131697948,"return_pct":4.061681316979482,"drawdown_pct":0.0},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","equity":10452.539392057291,"return_pct":4.525393920572918,"drawdown_pct":0.0},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","equity":10673.214374036635,"return_pct":6.7321437403663476,"drawdown_pct":0.0},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","equity":10666.825048426708,"return_pct":6.668250484267091,"drawdown_pct":-0.06389325609925667},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","equity":10774.762488172046,"return_pct":7.74762488172045,"drawdown_pct":0.0},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","equity":10869.110448574442,"return_pct":8.691104485744416,"drawdown_pct":0.0},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","equity":10810.738931993414,"return_pct":8.107389319934132,"drawdown_pct":-0.5837151658102844},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","equity":10815.53903448209,"return_pct":8.15539034482089,"drawdown_pct":-0.5357141409235258},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","equity":11023.41914867912,"return_pct":10.234191486791211,"drawdown_pct":0.0}],"trade_markers":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","price":123.3307,"type":"entry","side":"buy","size":1.0,"pnl_pct":null}],"indicators":[],"summary_stats":{"total_return_pct":8.168550548858402,"sharpe_ratio":3.471899564278569,"max_drawdown_pct":-1.8417907139589795,"total_trades":0,"win_rate_pct":0.0,"profit_factor":0.0,"final_equity":10816.85505488584,"volatility_pct":0.0,"annualized_return_pct":358.1787758348895,"sortino_ratio":40.744455681130425,"calmar_ratio":194.47311419274908}}+ cat /tmp/resp.json
00:12:21  + jq -e .ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)
00:12:21  + echo [integration] backend check passed
00:12:21  [integration] backend check passed
00:12:21  + SUCCESS=1
00:12:21  + break
00:12:21  + [ 1 -ne 1 ]
00:12:21  + SUCCESS=0
00:12:21  + seq 1 3
00:12:21  + echo [integration] frontend attempt 1/3
00:12:21  [integration] frontend attempt 1/3
00:12:21  + curl -fsS -H Content-Type: application/json -d @/tmp/payload.json http://localhost:8082/api/v1/backtest/chart-data
00:12:21  + tee /tmp/resp2.json
00:12:21  {"ticker":"AAPL","strategy":"buy_and_hold","start_date":"2023-01-03","end_date":"2023-01-20","ohlc_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","open":128.4682,"high":129.0796,"low":122.4432,"close":123.3307,"volume":112117500},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","open":125.1253,"high":126.8707,"low":123.3405,"close":124.6027,"volume":89113600},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","open":125.362,"high":125.9931,"low":123.025,"close":123.2814,"volume":80962700},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","open":124.2576,"high":128.4781,"low":123.1532,"close":127.8174,"volume":87754700},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","open":128.6556,"high":131.5547,"low":128.0836,"close":128.34,"volume":70790800},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","open":128.4485,"high":129.4346,"low":126.3382,"close":128.9119,"volume":63896200},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","open":129.4247,"high":131.6532,"low":128.6457,"close":131.6335,"volume":69458900},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","open":132.0181,"high":132.3928,"low":129.6121,"close":131.5547,"volume":71379600},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","open":130.1938,"high":133.0437,"low":129.829,"close":132.8859,"volume":57809700},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","open":132.9549,"high":135.3807,"low":132.2647,"close":134.0495,"volume":63646600},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","open":134.9172,"high":136.6823,"low":133.1521,"close":133.3296,"volume":69672800},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","open":132.2153,"high":134.3552,"low":131.9097,"close":133.3888,"volume":58280400},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","open":133.3986,"high":136.1005,"low":132.3534,"close":135.9526,"volume":80223600}],"equity_data":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","equity":10000.0,"return_pct":0.0,"drawdown_pct":0.0},{"timestamp":"2023-01-04T00:00:00","date":"2023-01-04","equity":10103.13733725666,"return_pct":1.0313733725666019,"drawdown_pct":0.0},{"timestamp":"2023-01-05T00:00:00","date":"2023-01-05","equity":9996.002617353182,"return_pct":-0.03997382646817593,"drawdown_pct":-1.0713471990347778},{"timestamp":"2023-01-06T00:00:00","date":"2023-01-06","equity":10363.794253985423,"return_pct":3.637942539854233,"drawdown_pct":0.0},{"timestamp":"2023-01-09T00:00:00","date":"2023-01-09","equity":10406.168131697948,"return_pct":4.061681316979482,"drawdown_pct":0.0},{"timestamp":"2023-01-10T00:00:00","date":"2023-01-10","equity":10452.539392057291,"return_pct":4.525393920572918,"drawdown_pct":0.0},{"timestamp":"2023-01-11T00:00:00","date":"2023-01-11","equity":10673.214374036635,"return_pct":6.7321437403663476,"drawdown_pct":0.0},{"timestamp":"2023-01-12T00:00:00","date":"2023-01-12","equity":10666.825048426708,"return_pct":6.668250484267091,"drawdown_pct":-0.06389325609925667},{"timestamp":"2023-01-13T00:00:00","date":"2023-01-13","equity":10774.762488172046,"return_pct":7.74762488172045,"drawdown_pct":0.0},{"timestamp":"2023-01-17T00:00:00","date":"2023-01-17","equity":10869.110448574442,"return_pct":8.691104485744416,"drawdown_pct":0.0},{"timestamp":"2023-01-18T00:00:00","date":"2023-01-18","equity":10810.738931993414,"return_pct":8.107389319934132,"drawdown_pct":-0.5837151658102844},{"timestamp":"2023-01-19T00:00:00","date":"2023-01-19","equity":10815.53903448209,"return_pct":8.15539034482089,"drawdown_pct":-0.5357141409235258},{"timestamp":"2023-01-20T00:00:00","date":"2023-01-20","equity":11023.41914867912,"return_pct":10.234191486791211,"drawdown_pct":0.0}],"trade_markers":[{"timestamp":"2023-01-03T00:00:00","date":"2023-01-03","price":123.3307,"type":"entry","side":"buy","size":1.0,"pnl_pct":null}],"indicators":[],"summary_stats":{"total_return_pct":8.168550548858402,"sharpe_ratio":3.471899564278569,"max_drawdown_pct":-1.8417907139589795,"total_trades":0,"win_rate_pct":0.0,"profit_factor":0.0,"final_equity":10816.85505488584,"volatility_pct":0.0,"annualized_return_pct":358.1787758348895,"sortino_ratio":40.744455681130425,"calmar_ratio":194.47311419274908}}+ cat /tmp/resp2.json
00:12:21  + jq -e .ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)
00:12:21  + echo [integration] frontend check passed
00:12:21  [integration] frontend check passed
00:12:21  + SUCCESS=1
00:12:21  + break
00:12:21  + [ 1 -ne 1 ]
[Pipeline] echo
00:12:21  Integration API checks (direct & via frontend) passed
[Pipeline] echo
00:12:21  Integration tests completed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Declarative: Post Actions)
[Pipeline] sh
00:12:22  + docker system prune -f
00:12:24  Deleted build cache objects:
00:12:24  y28fip0gy4jj3mt2uk1a68wum
00:12:24  dmu69h2l1rebstoqtwhwusr3c
00:12:24  gqhujltl4e6y1prny1khhm3fv
00:12:24  yq0vhmayv95hy9aoy6r882bwm
00:12:24  ek246m1211ycxymgzkzev0n1l
00:12:24  empkynnfshafa8ig9x8hi8ahi
00:12:24  xv2ssxgyy46oemii7qggvbumg
00:12:24  rbt59expr6072mchb5viv4euj
00:12:24  ijtct8qigv9zj5ybybkvxe5in
00:12:24  hcwd5zfqjkeacbuldxxjq8dtc
00:12:24  jte43xuztq6fwcmfdiwm9escp
00:12:24  m9u4dirhvxzy2po7huxgsjnfo
00:12:24  ogizimvir6bxi4ec9cw1xvznx
00:12:24  mtmjshugj5dkkc9sb5sbn8av6
00:12:24  a3i2dbmh8kavgju6rm2ekz8hk
00:12:24  7pcj34158rr9nfconcjzgp392
00:12:24  
00:12:24  Total reclaimed space: 1.647GB
[Pipeline] cleanWs
00:12:24  [WS-CLEANUP] Deleting project workspace...
00:12:24  [WS-CLEANUP] Deferred wipeout is disabled by the job configuration...
00:12:26  [WS-CLEANUP] done
[Pipeline] echo
00:12:26  Pipeline succeeded!
[Pipeline] script
[Pipeline] {
[Pipeline] withCredentials
00:12:26  Masking supported pattern matches of $GH_TOKEN
[Pipeline] {
[Pipeline] publishChecks
00:12:26  WARNING: Unknown parameter(s) found for class type 'io.jenkins.plugins.checks.steps.PublishChecksStep': output
[Pipeline] echo
00:12:26  publishChecks 호출 성공
[Pipeline] }
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // script
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
