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
 Checking out Revision b9d8210f9bcca5ae7efb84fb9bcb8c158e08759c (refs/remotes/origin/main)
  > /usr/bin/git config core.sparsecheckout # timeout=10
  > /usr/bin/git checkout -f b9d8210f9bcca5ae7efb84fb9bcb8c158e08759c # timeout=10
 Commit message: "chore(frontend): bump Docker Node base to node:20-alpine to satisfy package engines"
  > /usr/bin/git rev-list --no-walk 107b7ffbbee5add6f6f81bdf417107342d08a485 # timeout=10
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
 BUILD_NUMBER: 137
[Pipeline] echo
 All env vars:
[Pipeline] sh
 + env
 + grep -E (BRANCH|GIT)
 + sort
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
 + docker build --build-arg RUN_TESTS=true -t backtest-frontend-test:137 .
 + cd backend
 + docker build --build-arg RUN_TESTS=true -t backtest-backend-test:137 .
 #0 building with "default" instance using docker driver
 
 #1 [internal] load build definition from Dockerfile
 #1 transferring dockerfile: 740B done
 #1 DONE 0.0s
 
 #2 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
 #2 DONE 0.0s
 
 #3 [internal] load metadata for docker.io/library/node:20.8.1-alpine
 #0 building with "default" instance using docker driver
 
 #1 [internal] load build definition from Dockerfile
 #1 transferring dockerfile: 1.54kB done
 #1 DONE 0.0s
 
 #2 [internal] load metadata for docker.io/library/python:3.11-slim
 #2 DONE 1.6s
 
 #3 [internal] load .dockerignore
 #3 transferring context: 92B done
 #3 DONE 0.0s
 
 #4 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
 #4 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
 #4 DONE 0.0s
 
 #5 [internal] load build context
 #5 transferring context: 861.84kB 0.0s done
 #5 DONE 0.1s
 
 #6 [ 2/13] WORKDIR /app
 #6 CACHED
 
 #7 [11/13] COPY tests ./tests
 #7 CACHED
 
 #8 [ 5/13] COPY requirements-test.txt .
 #8 CACHED
 
 #9 [ 7/13] RUN uv pip install --system -r requirements.txt
 #9 CACHED
 
 #10 [ 4/13] COPY requirements.txt .
 #10 CACHED
 
 #11 [ 9/13] RUN uv pip install --system backtesting
 #11 CACHED
 
 #12 [12/13] COPY run_server.py .
 #12 CACHED
 
 #13 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
 #13 CACHED
 
 #14 [ 8/13] RUN uv pip install --system -r requirements-test.txt
 #14 CACHED
 
 #15 [10/13] COPY app ./app
 #15 CACHED
 
 #16 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
 #16 CACHED
 
 #17 [13/13] RUN if [ "true" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
 #17 CACHED
 
 #18 exporting to image
 #18 exporting layers done
 #18 writing image sha256:b50b9c5da324cab7f81928795b45e6dbcc92137f6c375dac0381725368cc510d done
 #18 naming to docker.io/library/backtest-backend-test:137 done
 #18 DONE 0.0s
[Pipeline] echo
 Backend tests passed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
 #3 DONE 2.4s
 
 #4 [internal] load .dockerignore
 #4 transferring context: 2B done
 #4 DONE 0.0s
 
 #5 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
 #5 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
 #5 DONE 0.0s
 
 #6 [internal] load build context
 #6 transferring context: 912.66kB 0.0s done
 #6 DONE 0.1s
 
 #7 [build 1/8] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
 #7 resolve docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5 0.0s done
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 0B / 49.81MB 0.2s
 #7 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 0B / 2.34MB 0.2s
 #7 sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5 1.43kB / 1.43kB done
 #7 sha256:1ccb0c0ded3b21cee95fe6b6ce1ac23bd6680c8f152cbfb3047d5d9ea490b098 1.16kB / 1.16kB done
 #7 sha256:cf2316e995eb236a3d42066d396685efb1333bd540aface0a9bfc4ff29ce030f 6.78kB / 6.78kB done
 #7 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 0B / 3.40MB 0.2s
 #7 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 1.05MB / 3.40MB 0.7s
 #7 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 2.10MB / 3.40MB 0.8s
 #7 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 3.15MB / 3.40MB 0.9s
 #7 extracting sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa
 #7 sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 3.40MB / 3.40MB 1.0s done
 #7 extracting sha256:96526aa774ef0126ad0fe9e9a95764c5fc37f409ab9e97021e7b4775d82bf6fa 0.1s done
 #7 sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 0B / 452B 1.1s
 #7 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 1.05MB / 2.34MB 1.2s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 4.19MB / 49.81MB 1.4s
 #7 sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 2.34MB / 2.34MB 1.3s done
 #7 sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 452B / 452B 1.5s done
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 7.34MB / 49.81MB 1.7s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 10.49MB / 49.81MB 2.0s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 15.73MB / 49.81MB 2.4s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 19.92MB / 49.81MB 2.8s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 24.12MB / 49.81MB 3.2s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 28.31MB / 49.81MB 3.5s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 32.51MB / 49.81MB 4.0s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 35.65MB / 49.81MB 4.3s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 38.80MB / 49.81MB 4.7s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 41.94MB / 49.81MB 5.1s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 45.09MB / 49.81MB 5.4s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 49.81MB / 49.81MB 5.9s
 #7 sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 49.81MB / 49.81MB 5.9s done
 #7 extracting sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 0.1s
 #7 extracting sha256:8b8b60d56fb87c6d10ba362d45c153e8de47dcbe6463f9cc5343b11bae00f676 1.4s done
 #7 extracting sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef
 #7 extracting sha256:97f8dfa93eef338011688eb86e78e5fb5f6feab4c24c3ca31a7853e832e0bcef 0.0s done
 #7 extracting sha256:aaa59b7b85b65010878890781e909cb3345c930a9942bbf8b319825c2a670236 done
 #7 DONE 7.6s
 
 #8 [build 2/8] WORKDIR /app
 #8 DONE 0.2s
 
 #9 [build 3/8] COPY package.json ./
 #9 DONE 0.0s
 
 #10 [build 4/8] COPY package-lock.json ./
 #10 DONE 0.0s
 
 #11 [build 5/8] RUN npm ci
 #11 5.628 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.628 (Use `node --trace-warnings ...` to show where the warning was created)
 #11 5.628 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.629 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.629 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.629 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.630 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.630 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.630 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.631 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.631 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.632 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.632 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.632 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.633 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.633 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.633 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.634 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.634 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.634 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.635 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.635 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.635 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.636 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.636 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.636 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.636 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.637 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.637 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.637 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.638 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 5.638 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #11 10.16 npm WARN deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
 #11 18.65 
 #11 18.65 added 790 packages, and audited 791 packages in 18s
 #11 18.65 
 #11 18.65 199 packages are looking for funding
 #11 18.65   run `npm fund` for details
 #11 18.66 
 #11 18.66 5 vulnerabilities (1 low, 2 moderate, 1 high, 1 critical)
 #11 18.66 
 #11 18.66 To address issues that do not require attention, run:
 #11 18.66   npm audit fix
 #11 18.66 
 #11 18.66 To address all issues (including breaking changes), run:
 #11 18.66   npm audit fix --force
 #11 18.66 
 #11 18.66 Run `npm audit` for details.
 #11 18.66 npm notice 
 #11 18.66 npm notice New major version of npm available! 10.1.0 -> 11.6.0
 #11 18.66 npm notice Changelog: <https://github.com/npm/cli/releases/tag/v11.6.0>
 #11 18.66 npm notice Run `npm install -g npm@11.6.0` to update!
 #11 18.66 npm notice 
 #11 DONE 19.0s
 
 #12 [build 6/8] COPY . .
 #12 DONE 0.1s
 
 #13 [build 7/8] RUN if [ "true" = "true" ] ; then npm test -- --run ; fi
 #13 0.541 
 #13 0.541 > backtesting-frontend@1.0.0 test
 #13 0.541 > vitest --run
 #13 0.541 
 #13 0.935 
 #13 0.935  RUN  v0.34.6 /app
 #13 0.935 
 #13 2.643  ✓ src/utils/__tests__/dateUtils.test.ts  (38 tests) 40ms
 #13 2.657  ✓ src/utils/__tests__/numberUtils.test.ts  (57 tests) 32ms
 #13 2.984  ✓ src/hooks/__tests__/useBacktestForm.test.ts  (19 tests) 92ms
 #13 2.984 stderr | src/hooks/__tests__/useBacktestForm.test.ts > useBacktestForm > 초기 상태 > 기본값으로 올바르게 초기화되어야 함
 #13 2.984 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 2.984 
 #13 3.948  ✓ src/utils/formatters.test.ts  (20 tests) 16ms
 #13 5.032 stderr | src/components/common/__tests__/FormField.test.tsx > FormField > 기본 렌더링 > 라벨과 입력 필드가 올바르게 렌더링되어야 함
 #13 5.032 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 5.032 
 #13 5.406  ✓ src/services/__tests__/api.test.ts  (4 tests | 1 skipped) 23ms
 #13 5.525  ✓ src/components/common/__tests__/FormField.test.tsx  (18 tests) 1009ms
 #13 5.804 stderr | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > 사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함
 #13 5.804 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 5.804 
 #13 6.051 stderr | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > 사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함
 #13 6.051 Warning: An update to BacktestForm inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
 #13 6.051     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at div
 #13 6.051     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
 #13 6.051     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
 #13 6.051     at div
 #13 6.051     at div
 #13 6.051     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.051     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.051     at div
 #13 6.051     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.051     at div
 #13 6.051     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.051     at div
 #13 6.051     at form
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:81:57
 #13 6.051     at div
 #13 6.051     at /app/src/components/ui/card.tsx:7:50
 #13 6.051     at div
 #13 6.051     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.051 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.051 
 #13 6.051 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.051 
 #13 6.051 act(() => {
 #13 6.051   /* fire events that update state */
 #13 6.051 });
 #13 6.051 /* assert on the output */
 #13 6.051 
 #13 6.051 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.051     at /app/src/components/ui/select.tsx:169:56
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.051     at div
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.051     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.051     at SelectPortal
 #13 6.051     at /app/src/components/ui/select.tsx:96:59
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.051     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.051     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.052 
 #13 6.052 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.052 
 #13 6.052 act(() => {
 #13 6.052   /* fire events that update state */
 #13 6.052 });
 #13 6.052 /* assert on the output */
 #13 6.052 
 #13 6.052 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.052     at /app/src/components/ui/select.tsx:169:56
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.052     at SelectPortal
 #13 6.052     at /app/src/components/ui/select.tsx:96:59
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.052 
 #13 6.052 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.052 
 #13 6.052 act(() => {
 #13 6.052   /* fire events that update state */
 #13 6.052 });
 #13 6.052 /* assert on the output */
 #13 6.052 
 #13 6.052 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.052 
 #13 6.052 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.052 
 #13 6.052 act(() => {
 #13 6.052   /* fire events that update state */
 #13 6.052 });
 #13 6.052 /* assert on the output */
 #13 6.052 
 #13 6.052 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.052     at /app/src/components/ui/select.tsx:169:56
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.052     at SelectPortal
 #13 6.052     at /app/src/components/ui/select.tsx:96:59
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.052 
 #13 6.052 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.052 
 #13 6.052 act(() => {
 #13 6.052   /* fire events that update state */
 #13 6.052 });
 #13 6.052 /* assert on the output */
 #13 6.052 
 #13 6.052 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.052     at /app/src/components/ui/select.tsx:169:56
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.052     at SelectPortal
 #13 6.052     at /app/src/components/ui/select.tsx:96:59
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.052 
 #13 6.052 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.052 
 #13 6.052 act(() => {
 #13 6.052   /* fire events that update state */
 #13 6.052 });
 #13 6.052 /* assert on the output */
 #13 6.052 
 #13 6.052 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.052     at /app/src/components/ui/select.tsx:169:56
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.052     at SelectPortal
 #13 6.052     at /app/src/components/ui/select.tsx:96:59
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.052 
 #13 6.052 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.052 
 #13 6.052 act(() => {
 #13 6.052   /* fire events that update state */
 #13 6.052 });
 #13 6.052 /* assert on the output */
 #13 6.052 
 #13 6.052 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.052     at /app/src/components/ui/select.tsx:169:56
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.052     at div
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.052     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.052     at SelectPortal
 #13 6.052     at /app/src/components/ui/select.tsx:96:59
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.052     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.052     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.052     at div
 #13 6.052     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.052     at div
 #13 6.052     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.052     at div
 #13 6.052     at form
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:81:57
 #13 6.052     at div
 #13 6.052     at /app/src/components/ui/card.tsx:7:50
 #13 6.052     at div
 #13 6.052     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.052 
 #13 6.234 stderr | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > 사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함
 #13 6.234 Warning: An update to BacktestForm inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
 #13 6.234     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at div
 #13 6.234     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
 #13 6.234     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at div
 #13 6.234     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to Select inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 #13 6.234 
 #13 6.234 When testing, code that causes React state updates should be wrapped into act(...):
 #13 6.234 
 #13 6.234 act(() => {
 #13 6.234   /* fire events that update state */
 #13 6.234 });
 #13 6.234 /* assert on the output */
 #13 6.234 
 #13 6.234 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
 #13 6.234     at /app/src/components/ui/select.tsx:169:56
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
 #13 6.234     at div
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
 #13 6.234     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
 #13 6.234     at SelectPortal
 #13 6.234     at /app/src/components/ui/select.tsx:96:59
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
 #13 6.234     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
 #13 6.234     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
 #13 6.234     at div
 #13 6.234     at FormField (/app/src/components/common/FormField.tsx:12:3)
 #13 6.234     at div
 #13 6.234     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
 #13 6.234     at div
 #13 6.234     at form
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:81:57
 #13 6.234     at div
 #13 6.234     at /app/src/components/ui/card.tsx:7:50
 #13 6.234     at div
 #13 6.234     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 #13 6.234 
 #13 6.484 stderr | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > 사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함
 #13 6.484 <empty line>
 #13 6.484 stdout | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > 사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함
 #13 6.484 Portfolio data being sent: [
 #13 6.484   {
 #13 6.484     symbol: [32m'AAPL'[39m,
 #13 6.484     amount: [33m10000[39m,
 #13 6.484     weight: [90mundefined[39m,
 #13 6.484     investment_type: [32m'lump_sum'[39m,
 #13 6.484     dca_periods: [33m12[39m,
 #13 6.484     asset_type: [32m'stock'[39m
 #13 6.484   }
 #13 6.484 ]
 #13 6.484 Strategy params being sent: {}
 #13 6.484 
 #13 6.979 stdout | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > onSubmit에서 오류 발생 시 에러 메시지를 표시해야 함
 #13 6.979 Portfolio data being sent: [
 #13 6.979   {
 #13 6.979     symbol: [32m'AAPL'[39m,
 #13 6.979     amount: [33m10000[39m,
 #13 6.979     weight: [90mundefined[39m,
 #13 6.979     investment_type: [32m'lump_sum'[39m,
 #13 6.979     dca_periods: [33m12[39m,
 #13 6.979     asset_type: [32m'stock'[39m
 #13 6.979   }
 #13 6.979 ]
 #13 6.979 Strategy params being sent: {}
 #13 6.979 
 #13 6.980 stderr | src/components/__tests__/UnifiedBacktestForm.test.tsx > BacktestForm (integration) > onSubmit에서 오류 발생 시 에러 메시지를 표시해야 함
 #13 6.980 백테스트 실행 중 오류: Error: 테스트 오류
 #13 6.980     at [90m/app/[39msrc/components/__tests__/UnifiedBacktestForm.test.tsx:63:48
 #13 6.980     at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:135:14
 #13 6.980     at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:58:26
 #13 6.980     at runTest [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:663:17[90m)[39m
 #13 6.980     at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
 #13 6.980     at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
 #13 6.980     at runFiles [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:834:5[90m)[39m
 #13 6.980     at startTests [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:843:3[90m)[39m
 #13 6.980     at [90mfile:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:103:7
 #13 6.980     at withEnv [90m(file:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:73:5[90m)[39m
 #13 6.980 
 #13 7.055  ✓ src/components/__tests__/UnifiedBacktestForm.test.tsx  (2 tests) 1826ms
 #13 7.126 stderr | src/hooks/__tests__/useBacktest.test.ts > useBacktest > 성공 시 결과를 설정하고 isPortfolio를 올바르게 표시해야 함
 #13 7.126 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 7.126 
 #13 7.132  ✓ src/hooks/__tests__/useBacktest.test.ts  (3 tests) 45ms
 #13 7.815  ✓ src/components/__tests__/charts.smoke.test.tsx  (4 tests) 132ms
 #13 7.816 stderr | src/components/__tests__/charts.smoke.test.tsx > Chart components (smoke) > EquityChart renders an SVG with minimal data
 #13 7.816 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 7.816 
 #13 7.817 stderr | src/components/__tests__/charts.smoke.test.tsx > Chart components (smoke) > StockPriceChart renders with one stock dataset
 #13 7.817 The width(0) and height(0) of chart should be greater than 0,
 #13 7.817        please check the style of container, or the props width(100%) and height(100%),
 #13 7.817        or add a minWidth(0) or minHeight(undefined) or use aspect(undefined) to control the
 #13 7.817        height and width.
 #13 7.817 
 #13 8.665 stderr | src/components/ErrorBoundary.test.tsx > ErrorBoundary > 정상적인 컴포넌트를 렌더링해야 함
 #13 8.665 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 8.665 
 #13 8.666  ✓ src/components/ErrorBoundary.test.tsx  (3 tests) 180ms
 #13 9.377 stderr | src/components/__tests__/PortfolioForm.test.tsx > PortfolioForm > 렌더링 및 주요 액션(addStock/addCash/removeStock) 트리거
 #13 9.377 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 9.377 
 #13 9.630  ✓ src/components/__tests__/PortfolioForm.test.tsx  (1 test) 731ms
 #13 9.917 stderr | src/components/__tests__/CommissionForm.test.tsx > CommissionForm > 기본 렌더링이 올바르게 되어야 함
 #13 9.917 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 9.917 
 #13 10.15  ✓ src/components/__tests__/CommissionForm.test.tsx  (3 tests) 457ms
 #13 10.81 stderr | src/components/__tests__/StrategyForm.test.tsx > StrategyForm > sma_crossover 선택 시 파라미터 입력 필드를 표시하고 변경 이벤트를 전파
 #13 10.81 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 10.81 
 #13 10.84  ✓ src/components/__tests__/StrategyForm.test.tsx  (1 test) 326ms
 #13 11.26 stderr | src/components/__tests__/DateRangeForm.test.tsx > DateRangeForm > 시작/종료 날짜 변경 시 핸들러 호출
 #13 11.26 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 #13 11.26 
 #13 11.49  ✓ src/components/__tests__/DateRangeForm.test.tsx  (1 test) 295ms
 #13 11.51 
 #13 11.51  Test Files  14 passed (14)
 #13 11.51       Tests  173 passed | 1 skipped (174)
 #13 11.51    Start at  07:17:16
 #13 11.51    Duration  10.57s (transform 653ms, setup 1.44s, collect 6.24s, tests 5.20s, environment 11.28s, prepare 2.22s)
 #13 11.51 
 #13 DONE 11.6s
 
 #14 [build 8/8] RUN npm run build
 #14 0.519 
 #14 0.519 > backtesting-frontend@1.0.0 build
 #14 0.519 > tsc && vite build
 #14 0.519 
 #14 8.773 vite v4.5.14 building for production...
 #14 8.804 transforming...
 #14 19.56 ✓ 2650 modules transformed.
 #14 19.87 Generated an empty chunk: "util-vendor".
 #14 19.98 rendering chunks...
 #14 20.09 [plugin:vite:reporter] 
 #14 20.09 (!) /app/src/components/ExchangeRateChart.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
 #14 20.09 
 #14 20.09 [plugin:vite:reporter] 
 #14 20.09 (!) /app/src/components/StockVolatilityNews.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
 #14 20.09 
 #14 20.17 computing gzip size...
 #14 20.19 dist/index.html                                 1.06 kB │ gzip:   0.53 kB
 #14 20.20 dist/assets/index-00d4056a.css                 71.20 kB │ gzip:  12.43 kB
 #14 20.20 dist/assets/util-vendor-4ed993c7.js             0.00 kB │ gzip:   0.02 kB
 #14 20.20 dist/assets/CustomTooltip-2818ce66.js           0.42 kB │ gzip:   0.32 kB
 #14 20.20 dist/assets/TradesChart-0d9b2ddf.js             1.45 kB │ gzip:   0.88 kB
 #14 20.20 dist/assets/EquityChart-2dd224cb.js             1.52 kB │ gzip:   0.81 kB
 #14 20.20 dist/assets/OHLCChart-c8cd9c21.js               1.90 kB │ gzip:   0.97 kB
 #14 20.20 dist/assets/FinancialTermTooltip-197e12f5.js    1.94 kB │ gzip:   1.76 kB
 #14 20.20 dist/assets/StatsSummary-26ad3f7e.js            2.30 kB │ gzip:   1.12 kB
 #14 20.20 dist/assets/StockPriceChart-a2ab127f.js         2.38 kB │ gzip:   1.21 kB
 #14 20.20 dist/assets/icon-vendor-c4a0e88b.js             2.51 kB │ gzip:   1.09 kB
 #14 20.20 dist/assets/react-vendor-4413ae29.js          162.28 kB │ gzip:  52.95 kB
 #14 20.20 dist/assets/index-41a7606f.js                 305.66 kB │ gzip:  90.74 kB
 #14 20.20 dist/assets/chart-vendor-df37046f.js          407.43 kB │ gzip: 109.28 kB
 #14 20.20 ✓ built in 11.42s
 #14 DONE 20.3s
 
 #15 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
 #15 CACHED
 
 #16 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
 #16 CACHED
 
 #17 exporting to image
 #17 exporting layers done
 #17 writing image sha256:c027ed93e875544c1d42b815d629638bfb1afde4747b0b7112d36bb823bcc580 done
 #17 naming to docker.io/library/backtest-frontend-test:137 done
 #17 DONE 0.0s
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
 + docker run --rm -v /var/lib/jenkins/workspace/Backtest/reports/backend:/reports backtest-backend-test:137 sh -lc pytest tests/unit/ -v --tb=short --junitxml=/reports/junit.xml
 ============================= test session starts ==============================
 platform linux -- Python 3.11.13, pytest-7.4.3, pluggy-1.6.0 -- /usr/local/bin/python
 cachedir: .pytest_cache
 metadata: {'Python': '3.11.13', 'Platform': 'Linux-6.14.0-29-generic-x86_64-with-glibc2.41', 'Packages': {'pytest': '7.4.3', 'pluggy': '1.6.0'}, 'Plugins': {'mock': '3.15.0', 'metadata': '3.1.1', 'json-report': '1.5.0', 'xdist': '3.8.0', 'cov': '7.0.0', 'Faker': '37.6.0', 'hypothesis': '6.138.15', 'html': '4.1.1', 'asyncio': '0.21.1', 'anyio': '3.7.1'}}
 hypothesis profile 'default'
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
 
 -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
 -------------------- generated xml file: /reports/junit.xml --------------------
 ================= 42 passed, 1 skipped, 127 warnings in 6.18s ==================
 + docker run --rm -e CI=1 -e VITEST_JUNIT_FILE=/reports/junit.xml -v /var/lib/jenkins/workspace/Backtest/frontend:/app -v /var/lib/jenkins/workspace/Backtest/reports/frontend:/reports -w /app node:18-alpine sh -lc npm ci && npx vitest run
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
 npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
 
 added 790 packages, and audited 791 packages in 16s
 
 199 packages are looking for funding
   run `npm fund` for details
 
 5 vulnerabilities (1 low, 2 moderate, 1 high, 1 critical)
 
 To address issues that do not require attention, run:
   npm audit fix
 
 To address all issues (including breaking changes), run:
   npm audit fix --force
 
 Run `npm audit` for details.
 
 [7m[1m[36m RUN [39m[22m[27m [36mv0.34.6[39m [90m/app[39m
 
  [32m✓[39m src/utils/__tests__/dateUtils.test.ts [2m ([22m[2m38 tests[22m[2m)[22m[90m 34[2mms[22m[39m
  [32m✓[39m src/utils/__tests__/numberUtils.test.ts [2m ([22m[2m57 tests[22m[2m)[22m[90m 28[2mms[22m[39m
  [32m✓[39m src/hooks/__tests__/useBacktestForm.test.ts [2m ([22m[2m19 tests[22m[2m)[22m[90m 80[2mms[22m[39m
 [90mstderr[2m | src/hooks/__tests__/useBacktestForm.test.ts[2m > [22m[2museBacktestForm[2m > [22m[2m초기 상태[2m > [22m[2m기본값으로 올바르게 초기화되어야 함[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/utils/formatters.test.ts [2m ([22m[2m20 tests[22m[2m)[22m[90m 19[2mms[22m[39m
 [90mstderr[2m | src/components/common/__tests__/FormField.test.tsx[2m > [22m[2mFormField[2m > [22m[2m기본 렌더링[2m > [22m[2m라벨과 입력 필드가 올바르게 렌더링되어야 함[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/services/__tests__/api.test.ts [2m ([22m[2m4 tests[22m [2m|[22m [33m1 skipped[39m[2m)[22m[90m 19[2mms[22m[39m
  [32m✓[39m src/components/common/__tests__/FormField.test.tsx [2m ([22m[2m18 tests[22m[2m)[22m[33m 1019[2mms[22m[39m
 [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
 [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
 Warning: An update to BacktestForm inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
     at div
     at div
     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
     at div
     at div
     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 
 [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
 Warning: An update to BacktestForm inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
     at div
     at div
     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Tooltip inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Tooltip (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:73:5)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at TooltipProvider (file:///app/node_modules/@radix-ui/react-tooltip/dist/index.mjs:29:5)
     at Tooltip (/app/src/components/common/Tooltip.tsx:6:3)
     at div
     at div
     at PortfolioForm (/app/src/components/PortfolioForm.tsx:14:3)
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at StrategyForm (/app/src/components/StrategyForm.tsx:8:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to Select inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 Warning: An update to SelectItemText inside a test was not wrapped in act(...).
 
 When testing, code that causes React state updates should be wrapped into act(...):
 
 act(() => {
   /* fire events that update state */
 });
 /* assert on the output */
 
 This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:901:13
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:39:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:800:7
     at /app/src/components/ui/select.tsx:169:56
     at div
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:711:13
     at div
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:27:15
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:256:58
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:33:13
     at file:///app/node_modules/@radix-ui/react-slot/dist/index.mjs:9:13
     at file:///app/node_modules/@radix-ui/react-primitive/dist/index.mjs:28:13
     at file:///app/node_modules/@radix-ui/react-portal/dist/index.mjs:11:22
     at SelectPortal
     at /app/src/components/ui/select.tsx:96:59
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at CollectionProvider (file:///app/node_modules/@radix-ui/react-collection/dist/index.mjs:17:13)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Provider (file:///app/node_modules/@radix-ui/react-context/dist/index.mjs:27:15)
     at Popper (file:///app/node_modules/@radix-ui/react-popper/dist/index.mjs:30:11)
     at Select (file:///app/node_modules/@radix-ui/react-select/dist/index.mjs:42:5)
     at div
     at FormField (/app/src/components/common/FormField.tsx:12:3)
     at div
     at CommissionForm (/app/src/components/CommissionForm.tsx:6:3)
     at div
     at form
     at div
     at /app/src/components/ui/card.tsx:81:57
     at div
     at /app/src/components/ui/card.tsx:7:50
     at div
     at BacktestForm (/app/src/components/BacktestForm.tsx:27:25)
 
 [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
 <empty line>
 [90mstdout[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2m사용자 입력을 변환해 onSubmit에 올바른 요청을 전달해야 함[22m[39m
 Portfolio data being sent: [
   {
     symbol: [32m'AAPL'[39m,
     amount: [33m10000[39m,
     weight: [90mundefined[39m,
     investment_type: [32m'lump_sum'[39m,
     dca_periods: [33m12[39m,
     asset_type: [32m'stock'[39m
   }
 ]
 Strategy params being sent: {}
 
 [90mstderr[2m | src/hooks/__tests__/useBacktest.test.ts[2m > [22m[2museBacktest[2m > [22m[2m성공 시 결과를 설정하고 isPortfolio를 올바르게 표시해야 함[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/hooks/__tests__/useBacktest.test.ts [2m ([22m[2m3 tests[22m[2m)[22m[90m 51[2mms[22m[39m
 [90mstdout[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2monSubmit에서 오류 발생 시 에러 메시지를 표시해야 함[22m[39m
 Portfolio data being sent: [
   {
     symbol: [32m'AAPL'[39m,
     amount: [33m10000[39m,
     weight: [90mundefined[39m,
     investment_type: [32m'lump_sum'[39m,
     dca_periods: [33m12[39m,
     asset_type: [32m'stock'[39m
   }
 ]
 Strategy params being sent: {}
 
 [90mstderr[2m | src/components/__tests__/UnifiedBacktestForm.test.tsx[2m > [22m[2mBacktestForm (integration)[2m > [22m[2monSubmit에서 오류 발생 시 에러 메시지를 표시해야 함[22m[39m
 백테스트 실행 중 오류: Error: 테스트 오류
     at [90m/app/[39msrc/components/__tests__/UnifiedBacktestForm.test.tsx:63:48
     at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:135:14
     at [90mfile:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:58:26
     at runTest [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:663:17[90m)[39m
     at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
     at runSuite [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:782:15[90m)[39m
     at runFiles [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:834:5[90m)[39m
     at startTests [90m(file:///app/[39mnode_modules/[4m@vitest[24m/runner/dist/index.js:843:3[90m)[39m
     at [90mfile:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:103:7
     at withEnv [90m(file:///app/[39mnode_modules/[4mvitest[24m/dist/entry.js:73:5[90m)[39m
 
  [32m✓[39m src/components/__tests__/UnifiedBacktestForm.test.tsx [2m ([22m[2m2 tests[22m[2m)[22m[33m 1733[2mms[22m[39m
 [90mstderr[2m | src/components/__tests__/charts.smoke.test.tsx[2m > [22m[2mChart components (smoke)[2m > [22m[2mEquityChart renders an SVG with minimal data[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
 [90mstderr[2m | src/components/__tests__/charts.smoke.test.tsx[2m > [22m[2mChart components (smoke)[2m > [22m[2mStockPriceChart renders with one stock dataset[22m[39m
 The width(0) and height(0) of chart should be greater than 0,
        please check the style of container, or the props width(100%) and height(100%),
        or add a minWidth(0) or minHeight(undefined) or use aspect(undefined) to control the
        height and width.
 
  [32m✓[39m src/components/__tests__/charts.smoke.test.tsx [2m ([22m[2m4 tests[22m[2m)[22m[90m 143[2mms[22m[39m
  [32m✓[39m src/components/ErrorBoundary.test.tsx [2m ([22m[2m3 tests[22m[2m)[22m[90m 160[2mms[22m[39m
 [90mstderr[2m | src/components/ErrorBoundary.test.tsx[2m > [22m[2mErrorBoundary[2m > [22m[2m정상적인 컴포넌트를 렌더링해야 함[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
 [90mstderr[2m | src/components/__tests__/PortfolioForm.test.tsx[2m > [22m[2mPortfolioForm[2m > [22m[2m렌더링 및 주요 액션(addStock/addCash/removeStock) 트리거[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/components/__tests__/PortfolioForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[33m 686[2mms[22m[39m
 [90mstderr[2m | src/components/__tests__/CommissionForm.test.tsx[2m > [22m[2mCommissionForm[2m > [22m[2m기본 렌더링이 올바르게 되어야 함[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/components/__tests__/CommissionForm.test.tsx [2m ([22m[2m3 tests[22m[2m)[22m[33m 443[2mms[22m[39m
 [90mstderr[2m | src/components/__tests__/StrategyForm.test.tsx[2m > [22m[2mStrategyForm[2m > [22m[2msma_crossover 선택 시 파라미터 입력 필드를 표시하고 변경 이벤트를 전파[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/components/__tests__/StrategyForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[90m 296[2mms[22m[39m
 [90mstderr[2m | src/components/__tests__/DateRangeForm.test.tsx[2m > [22m[2mDateRangeForm[2m > [22m[2m시작/종료 날짜 변경 시 핸들러 호출[22m[39m
 Warning: `ReactDOMTestUtils.act` is deprecated in favor of `React.act`. Import `act` from `react` instead of `react-dom/test-utils`. See https://react.dev/warnings/react-dom-test-utils for more info.
 
  [32m✓[39m src/components/__tests__/DateRangeForm.test.tsx [2m ([22m[2m1 test[22m[2m)[22m[90m 265[2mms[22m[39m
 
 [2m Test Files [22m [1m[32m14 passed[39m[22m[90m (14)[39m
 [2m      Tests [22m [1m[32m173 passed[39m[22m[2m | [22m[33m1 skipped[39m[90m (174)[39m
 [2m   Start at [22m 07:18:13
 [2m   Duration [22m 9.98s[2m (transform 726ms, setup 1.21s, collect 6.11s, tests 4.98s, environment 10.42s, prepare 2.05s)[22m
 
[Pipeline] junit
 Recording test results
 [Checks API] No suitable checks publisher found.
[Pipeline] archiveArtifacts
 Archiving artifacts
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
 Masking supported pattern matches of $GH_TOKEN
[Pipeline] withCredentials
 Masking supported pattern matches of $GH_TOKEN
[Pipeline] {
[Pipeline] {
[Pipeline] echo
 Building PROD backend image: ghcr.io/kyj0503/backtest-backend:137
[Pipeline] sh
[Pipeline] echo
 Building PROD frontend image: ghcr.io/kyj0503/backtest-frontend:137
[Pipeline] sh
 + docker buildx inspect backtest-builder
 + docker buildx use backtest-builder
[Pipeline] sh
 + docker buildx inspect backtest-builder
 + docker buildx use backtest-builder
[Pipeline] sh
 + docker pull ghcr.io/kyj0503/backtest-backend:latest
 + docker pull ghcr.io/kyj0503/backtest-frontend:latest
 latest: Pulling from kyj0503/backtest-backend
 Digest: sha256:3cee1ec4f8cd30f11867eb4540ba25ea0fb1c602df4264cf2aae4a8b34c180c9
 Status: Image is up to date for ghcr.io/kyj0503/backtest-backend:latest
 ghcr.io/kyj0503/backtest-backend:latest
[Pipeline] sh
 + cd backend
 + DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg IMAGE_TAG=137 --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/kyj0503/backtest-backend:latest -t ghcr.io/kyj0503/backtest-backend:137 .
 latest: Pulling from kyj0503/backtest-frontend
 Digest: sha256:6f72c079b1588dd4b25a71ca7e28f3b6c7fd3f990097402bfe14a3482408710c
 Status: Image is up to date for ghcr.io/kyj0503/backtest-frontend:latest
 ghcr.io/kyj0503/backtest-frontend:latest
[Pipeline] sh
 #0 building with "default" instance using docker driver
 
 #1 [internal] load build definition from Dockerfile
 #1 transferring dockerfile: 1.54kB done
 #1 DONE 0.0s
 
 #2 [internal] load metadata for docker.io/library/python:3.11-slim
 + cd frontend
 + DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/kyj0503/backtest-frontend:latest -t ghcr.io/kyj0503/backtest-frontend:137 .
 #0 building with "default" instance using docker driver
 
 #1 [internal] load build definition from Dockerfile
 #1 transferring dockerfile: 740B done
 #1 DONE 0.0s
 
 #2 [internal] load metadata for docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
 #2 DONE 0.0s
 
 #3 [internal] load metadata for docker.io/library/node:20.8.1-alpine
 #2 DONE 0.7s
 
 #3 [internal] load .dockerignore
 #3 transferring context: 92B done
 #3 DONE 0.0s
 
 #4 importing cache manifest from ghcr.io/kyj0503/backtest-backend:latest
 #4 DONE 0.0s
 
 #5 [ 1/13] FROM docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228
 #5 resolve docker.io/library/python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228 0.0s done
 #5 DONE 0.0s
 
 #6 [internal] load build context
 #6 transferring context: 7.32kB 0.0s done
 #6 DONE 0.0s
 
 #7 [ 5/13] COPY requirements-test.txt .
 #7 CACHED
 
 #8 [ 4/13] COPY requirements.txt .
 #8 CACHED
 
 #9 [ 7/13] RUN uv pip install --system -r requirements.txt
 #9 CACHED
 
 #10 [ 9/13] RUN uv pip install --system backtesting
 #10 CACHED
 
 #11 [ 3/13] RUN apt-get update && apt-get install -y     gcc     g++     curl     && rm -rf /var/lib/apt/lists/*
 #11 CACHED
 
 #12 [10/13] COPY app ./app
 #12 CACHED
 
 #13 [ 6/13] RUN curl -Ls https://astral.sh/uv/install.sh | sh     && cp /root/.local/bin/uv /usr/local/bin/uv
 #13 CACHED
 
 #14 [11/13] COPY tests ./tests
 #14 CACHED
 
 #15 [ 2/13] WORKDIR /app
 #15 CACHED
 
 #16 [ 8/13] RUN uv pip install --system -r requirements-test.txt
 #16 CACHED
 
 #17 [12/13] COPY run_server.py .
 #17 CACHED
 
 #18 [13/13] RUN if [ "false" = "true" ] ; then python -m pytest tests/unit/ -v --tb=short ; fi
 #18 DONE 0.2s
 
 #19 exporting to image
 #19 exporting layers 0.0s done
 #19 preparing layers for inline cache 0.0s done
 #19 writing image sha256:fa772247640d2a3962071aef203b59a04f0aa0085580b80ad65750f83f490e10 done
 #19 naming to ghcr.io/kyj0503/backtest-backend:137 done
 #19 DONE 0.1s
[Pipeline] sh
 #3 DONE 0.7s
 
 #4 [internal] load .dockerignore
 #4 transferring context: 2B done
 #4 DONE 0.0s
 
 #5 [build 1/8] FROM docker.io/library/node:20.8.1-alpine@sha256:002b6ee25b63b81dc4e47c9378ffe20915c3fa0e98e834c46584438468b1d0b5
 #5 DONE 0.0s
 
 #6 importing cache manifest from ghcr.io/kyj0503/backtest-frontend:latest
 #6 DONE 0.0s
 
 #7 [stage-1 1/3] FROM docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7
 #7 resolve docker.io/library/nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7 0.0s done
 #7 DONE 0.0s
 
 #8 [internal] load build context
 + set -eu
 + export DOCKER_CLIENT_TIMEOUT=300
 + export COMPOSE_HTTP_TIMEOUT=300
 + curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/
 + echo Warning: GHCR probe failed; continuing
 Warning: GHCR probe failed; continuing
 + docker logout ghcr.io
 + ok=
 + printf %s ****
 + docker login ghcr.io -u kyj0503 --password-stdin
 
 WARNING! Your credentials are stored unencrypted in '/var/lib/jenkins/.docker/config.json'.
 Configure a credential helper to remove this warning. See
 https://docs.docker.com/go/credential-store/
 
 Login Succeeded
 + ok=1
 + break
 + [ -z 1 ]
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh
 + set -eu
 + ok=
 + docker push ghcr.io/kyj0503/backtest-backend:137
 The push refers to repository [ghcr.io/kyj0503/backtest-backend]
 354f993f6e88: Preparing
 1ffe847b372a: Preparing
 24ef036f4442: Preparing
 00c68896aae7: Preparing
 52e5562c7273: Preparing
 57d8b80cef4b: Preparing
 4430cc1d395d: Preparing
 bb3118717ab5: Preparing
 22c144244ab5: Preparing
 0f420d6c9384: Preparing
 18c41aea3627: Preparing
 3bbebd0b50d8: Preparing
 8d441cbfbc35: Preparing
 49dd736005c7: Preparing
 135aac4d5c9a: Preparing
 daf557c4f08e: Preparing
 0f420d6c9384: Waiting
 18c41aea3627: Waiting
 3bbebd0b50d8: Waiting
 8d441cbfbc35: Waiting
 49dd736005c7: Waiting
 135aac4d5c9a: Waiting
 daf557c4f08e: Waiting
 57d8b80cef4b: Waiting
 4430cc1d395d: Waiting
 bb3118717ab5: Waiting
 22c144244ab5: Waiting
 1ffe847b372a: Layer already exists
 24ef036f4442: Layer already exists
 52e5562c7273: Layer already exists
 4430cc1d395d: Layer already exists
 00c68896aae7: Layer already exists
 0f420d6c9384: Layer already exists
 22c144244ab5: Layer already exists
 18c41aea3627: Layer already exists
 3bbebd0b50d8: Layer already exists
 8d441cbfbc35: Layer already exists
 bb3118717ab5: Layer already exists
 49dd736005c7: Layer already exists
 135aac4d5c9a: Layer already exists
 daf557c4f08e: Layer already exists
 57d8b80cef4b: Layer already exists
 354f993f6e88: Pushed
 #8 transferring context: 365.84MB 4.3s done
 #8 DONE 4.4s
 
 #9 [build 3/8] COPY package.json ./
 #9 CACHED
 
 #10 [build 2/8] WORKDIR /app
 #10 CACHED
 
 #11 [build 4/8] COPY package-lock.json ./
 #11 CACHED
 
 #12 [build 5/8] RUN npm ci
 137: digest: sha256:41582248e5a06d0636d52d44429d930ada2bae2057cdc0675d70e2dfde66de76 size: 3667
 + ok=1
 + break
 + [ -z 1 ]
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
 #12 5.924 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.924 (Use `node --trace-warnings ...` to show where the warning was created)
 #12 5.925 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.925 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.926 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.926 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.927 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.927 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.928 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.928 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.929 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.929 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.930 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.930 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.931 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.931 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.932 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.932 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.932 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.933 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.933 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.934 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.934 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.935 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.935 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.935 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.936 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.936 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.937 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.937 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.937 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.938 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.938 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.939 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.939 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.939 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.940 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.940 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.941 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.941 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.941 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.942 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.942 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.942 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.943 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.943 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.944 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.944 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.944 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.945 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.945 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.945 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.946 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.946 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.946 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.947 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.947 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 5.948 (node:1) MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [TLSSocket]. Use emitter.setMaxListeners() to increase limit
 #12 11.75 npm WARN deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
 #12 20.36 
 #12 20.36 added 790 packages, and audited 791 packages in 20s
 #12 20.36 
 #12 20.36 199 packages are looking for funding
 #12 20.36   run `npm fund` for details
 #12 20.38 
 #12 20.38 5 vulnerabilities (1 low, 2 moderate, 1 high, 1 critical)
 #12 20.38 
 #12 20.38 To address issues that do not require attention, run:
 #12 20.38   npm audit fix
 #12 20.38 
 #12 20.38 To address all issues (including breaking changes), run:
 #12 20.38   npm audit fix --force
 #12 20.38 
 #12 20.38 Run `npm audit` for details.
 #12 20.38 npm notice 
 #12 20.38 npm notice New major version of npm available! 10.1.0 -> 11.6.0
 #12 20.38 npm notice Changelog: <https://github.com/npm/cli/releases/tag/v11.6.0>
 #12 20.38 npm notice Run `npm install -g npm@11.6.0` to update!
 #12 20.38 npm notice 
 #12 DONE 20.7s
 
 #13 [build 6/8] COPY . .
 #13 DONE 10.3s
 
 #14 [build 7/8] RUN if [ "false" = "true" ] ; then npm test -- --run ; fi
 #14 DONE 0.2s
 
 #15 [build 8/8] RUN npm run build
 #15 0.531 
 #15 0.531 > backtesting-frontend@1.0.0 build
 #15 0.531 > tsc && vite build
 #15 0.531 
 #15 8.793 vite v4.5.14 building for production...
 #15 8.827 transforming...
 #15 17.25 ✓ 2650 modules transformed.
 #15 17.58 Generated an empty chunk: "util-vendor".
 #15 17.69 rendering chunks...
 #15 17.81 [plugin:vite:reporter] 
 #15 17.81 (!) /app/src/components/ExchangeRateChart.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
 #15 17.81 
 #15 17.81 [plugin:vite:reporter] 
 #15 17.81 (!) /app/src/components/StockVolatilityNews.tsx is dynamically imported by /app/src/components/lazy/LazyChartComponents.tsx but also statically imported by /app/src/components/results/AdditionalFeatures.tsx, dynamic import will not move module into another chunk.
 #15 17.81 
 #15 17.88 computing gzip size...
 #15 17.90 dist/index.html                                 1.06 kB │ gzip:   0.53 kB
 #15 17.90 dist/assets/index-00d4056a.css                 71.20 kB │ gzip:  12.43 kB
 #15 17.90 dist/assets/util-vendor-4ed993c7.js             0.00 kB │ gzip:   0.02 kB
 #15 17.90 dist/assets/CustomTooltip-2818ce66.js           0.42 kB │ gzip:   0.32 kB
 #15 17.90 dist/assets/TradesChart-0d9b2ddf.js             1.45 kB │ gzip:   0.88 kB
 #15 17.90 dist/assets/EquityChart-2dd224cb.js             1.52 kB │ gzip:   0.81 kB
 #15 17.90 dist/assets/OHLCChart-c8cd9c21.js               1.90 kB │ gzip:   0.97 kB
 #15 17.90 dist/assets/FinancialTermTooltip-197e12f5.js    1.94 kB │ gzip:   1.76 kB
 #15 17.90 dist/assets/StatsSummary-26ad3f7e.js            2.30 kB │ gzip:   1.12 kB
 #15 17.90 dist/assets/StockPriceChart-a2ab127f.js         2.38 kB │ gzip:   1.21 kB
 #15 17.90 dist/assets/icon-vendor-c4a0e88b.js             2.51 kB │ gzip:   1.09 kB
 #15 17.90 dist/assets/react-vendor-4413ae29.js          162.28 kB │ gzip:  52.95 kB
 #15 17.90 dist/assets/index-41a7606f.js                 305.66 kB │ gzip:  90.74 kB
 #15 17.90 dist/assets/chart-vendor-df37046f.js          407.43 kB │ gzip: 109.28 kB
 #15 17.90 ✓ built in 9.11s
 #15 DONE 18.0s
 
 #16 [stage-1 2/3] COPY --from=build /app/dist /usr/share/nginx/html
 #16 CACHED
 
 #17 [stage-1 3/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
 #17 CACHED
 
 #18 exporting to image
 #18 exporting layers done
 #18 preparing layers for inline cache done
 #18 writing image sha256:84e7aef2f14ef2869b7612579c3fb56c1456ea323794b4e7f5bfb47dcd707679 done
 #18 naming to ghcr.io/kyj0503/backtest-frontend:137 done
 #18 DONE 0.0s
[Pipeline] sh
 + set -eu
 + export DOCKER_CLIENT_TIMEOUT=300
 + export COMPOSE_HTTP_TIMEOUT=300
 + curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/
 + echo Warning: GHCR probe failed; continuing
 Warning: GHCR probe failed; continuing
 + docker logout ghcr.io
 + ok=
 + printf %s ****
 + docker login ghcr.io -u kyj0503 --password-stdin
 
 WARNING! Your credentials are stored unencrypted in '/var/lib/jenkins/.docker/config.json'.
 Configure a credential helper to remove this warning. See
 https://docs.docker.com/go/credential-store/
 
 Login Succeeded
 + ok=1
 + break
 + [ -z 1 ]
[Pipeline] withEnv
[Pipeline] {
[Pipeline] sh
 + set -eu
 + ok=
 + docker push ghcr.io/kyj0503/backtest-frontend:137
 The push refers to repository [ghcr.io/kyj0503/backtest-frontend]
 658a3b4a616b: Preparing
 e6b46105d51f: Preparing
 ce495f7b0b7d: Preparing
 9c70f446fbe2: Preparing
 5be225e16e44: Preparing
 3d04ead9b400: Preparing
 af5598fef05f: Preparing
 8fbd5a835e5e: Preparing
 75061be64847: Preparing
 d4fc045c9e3a: Preparing
 3d04ead9b400: Waiting
 af5598fef05f: Waiting
 8fbd5a835e5e: Waiting
 75061be64847: Waiting
 d4fc045c9e3a: Waiting
 658a3b4a616b: Layer already exists
 e6b46105d51f: Layer already exists
 ce495f7b0b7d: Layer already exists
 9c70f446fbe2: Layer already exists
 5be225e16e44: Layer already exists
 af5598fef05f: Layer already exists
 3d04ead9b400: Layer already exists
 8fbd5a835e5e: Layer already exists
 75061be64847: Layer already exists
 d4fc045c9e3a: Layer already exists
 137: digest: sha256:02608074a489839d662394a63ce7f204ba7dc88b6f06c08c50dc8ea8f1bf0e83 size: 2406
 + ok=1
 + break
 + [ -z 1 ]
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
 Masking supported pattern matches of $GH_TOKEN or $SSH_KEY
[Pipeline] {
[Pipeline] echo
 Deploying to /opt/backtest on localhost as jenkins
[Pipeline] sh
 + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost mkdir -p /opt/backtest
[Pipeline] sh
 + scp -i **** -o StrictHostKeyChecking=no /var/lib/jenkins/workspace/Backtest/compose/compose.prod.yml jenkins@localhost:/opt/backtest/docker-compose.yml
[Pipeline] sh
 + scp -i **** -o StrictHostKeyChecking=no ./scripts/remote_deploy.sh jenkins@localhost:/opt/backtest/remote_deploy.sh
[Pipeline] sh
 + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost chmod +x /opt/backtest/remote_deploy.sh
[Pipeline] sh
 + ssh -i **** -o StrictHostKeyChecking=no jenkins@localhost /opt/backtest/remote_deploy.sh ghcr.io/kyj0503/backtest-backend:137 ghcr.io/kyj0503/backtest-frontend:137 /opt/backtest
 137: Pulling from kyj0503/backtest-backend
 Digest: sha256:41582248e5a06d0636d52d44429d930ada2bae2057cdc0675d70e2dfde66de76
 Status: Image is up to date for ghcr.io/kyj0503/backtest-backend:137
 ghcr.io/kyj0503/backtest-backend:137
 137: Pulling from kyj0503/backtest-frontend
 Digest: sha256:02608074a489839d662394a63ce7f204ba7dc88b6f06c08c50dc8ea8f1bf0e83
 Status: Image is up to date for ghcr.io/kyj0503/backtest-frontend:137
 ghcr.io/kyj0503/backtest-frontend:137
 [2025-09-15 16:19:34] Starting deploy: backend=ghcr.io/kyj0503/backtest-backend:137 frontend=ghcr.io/kyj0503/backtest-frontend:137
 Current docker-compose.yml configuration:
 services:
   backend:
     image: ghcr.io/kyj0503/backtest-backend:137
     ports:
       - "8001:8000"
     env_file:
       - ./backend/.env
     restart: unless-stopped
 
   frontend:
     image: ghcr.io/kyj0503/backtest-frontend:137
     ports:
       - "8082:80"
     depends_on:
       - backend
     restart: unless-stopped
  Container backtest-backend-1  Recreate
  Container backtest-backend-1  Recreated
  Container backtest-frontend-1  Recreate
  Container backtest-frontend-1  Recreated
  Container backtest-backend-1  Starting
  Container backtest-backend-1  Started
  Container backtest-frontend-1  Starting
  Container backtest-frontend-1  Started
 [2025-09-15 16:19:34] Deploy succeeded
   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                  Dload  Upload   Total   Spent    Left  Speed
 
   0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
   0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
 curl: (56) Recv failure: 상대편이 연결을 끊음
 Backend health check failed
   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                  Dload  Upload   Total   Spent    Left  Speed
 
   0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0﻿<!doctype html>
 <html lang="ko">
   <head>
     <meta charset="UTF-8" />
     <meta name="viewport" content="width=device-width, initial-scale=1.0" />
     <title>라고할때살걸</title>
     <link rel="preconnect" href="https://fonts.googleapis.com">
     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
     <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Lora:ital,wght@0,400..700;1,400..700&family=Fira+Code:wght@300..700&display=swap" rel="stylesheet">
     <script type="module" crossorigin src="/assets/index-41a7606f.js"></script>
     <link rel="modulepreload" crossorigin href="/assets/react-vendor-4413ae29.js">
     <link rel="modulepreload" crossorigin href="/assets/icon-vendor-c4a0e88b.js">
     <link rel="modulepreload" crossorigin href="/assets/chart-vendor-df37046f.js">
     <link rel="stylesheet" href="/assets/index-00d4056a.css">
   </head>
   <body>
     <div id="root"></div>
     
   </body>
 </html>
 
 100  1074  100  1074    0     0   882k      0 --:--:-- --:--:-- --:--:-- 1048k
 [2025-09-15 16:19:34] Deployment finished with status=success
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
 Running integration tests against deployed environment...
[Pipeline] sh
 + seq 1 30
 + curl -fsS http://localhost:8001/health
 curl: (56) Recv failure: 상대편이 연결을 끊음
 + sleep 1
 + curl -fsS http://localhost:8001/health
 + echo backend healthy
 backend healthy
 + break
 + seq 1 30
 + curl -fsS http://localhost:8082/
 + echo frontend up
 frontend up
 + break
[Pipeline] sh
 + cat
 + command -v jq
 + JQ=jq -e
 + curl -fsS -H Content-Type: application/json -d @/tmp/payload.json http://localhost:8001/api/v1/backtest/chart-data
 + tee /tmp/resp.json
 + cat /tmp/resp.json
 + jq -e .ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)
 + cat /tmp/resp.json
 + jq -e .summary_stats.total_trades>=0 and (.summary_stats.win_rate_pct>=0 and .summary_stats.win_rate_pct<=100) and .summary_stats.max_drawdown_pct>=0
[Pipeline] echo
 Integration API check failed (non-blocking): script returned exit code 1
[Pipeline] echo
 Continuing pipeline as successful despite API check failure
[Pipeline] echo
 Integration tests completed
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Declarative: Post Actions)
[Pipeline] sh
 + docker system prune -f
 Deleted build cache objects:
 oz26o55bgzyr6woawzgk6dw0n
 zvy7gqhnnk7oqv6fu9fodabai
 88k0wfkbbd300hojcc6uiiety
 1ugio0sbqwc9vqyqh4ca80ve8
 mmozmy85qrh4rwr6cp3m9lqu6
 k04gdfme9lea4n4op0lrhzavq
 4a44ubo7fi7dx6k864c61638y
 1fcglvyt9wgjiqxim5e2yywly
 ss9xrcfmbtcvpd9x8drhwfkj3
 tlsf8vwyj9npxqkzdc1m4fx37
 iepmcsyk9bnyr7pkn7je6t4uk
 k6kut64ghc1yzy1fmnqyuqxmf
 u7xurtx95sswdirne6ykzvho4
 lasd643unylhq0f1ct688wixm
 tm029riqu0ji90viirba0c1fi
 1x9fttz5yhki7k9qwk1c1yxhn
 a6ks9fo145vpaank3e49nmsux
 9bbstmets8zgo55zy7j3g06lo
 twpl3oefh8rilbnewh93tavw2
 k4kro2xv4vvpapauen80r1190
 r1gshcyxfmoc4u12dzuwj8c4r
 
 Total reclaimed space: 1.466GB
[Pipeline] cleanWs
 [WS-CLEANUP] Deleting project workspace...
 [WS-CLEANUP] Deferred wipeout is used...
 [WS-CLEANUP] done
[Pipeline] echo
 Pipeline succeeded!
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