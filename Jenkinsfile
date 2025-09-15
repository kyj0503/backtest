pipeline {
  // 파이프라인 최상위 설정
  // - agent any: 가능한 어떤 에이전트(node)에서든 실행
  // - options: 동시 빌드 방지, 타임스탬프 출력, 기본체크아웃 건너뛰기 등
  agent any

  options {
  // 기본 체크아웃을 수동으로 제어하여 불필요한 작업을 줄입니다.
  skipDefaultCheckout(true)
  // 로그 타임스탬프를 활성화하여 문제 조사 시 시간을 쉽게 추적합니다.
  timestamps()
  // 동일한 잡의 동시 실행을 막아 워크스페이스 충돌을 예방합니다.
  disableConcurrentBuilds()
  }

  // 자격증명 및 Docker 관련 주의사항
  // - GHCR 접근용 토큰은 Jenkins Credentials에 'github-token'으로 등록해 사용합니다.
  // - 에이전트의 ~/.docker/config.json을 커밋하지 말고 런타임에 credentials로 주입하세요.
  // - 빌드 에이전트의 파일시스템 접근을 제한하고 토큰은 주기적으로 교체하세요.

    environment {
        GHCR_OWNER = 'kyj0503'
        BACKEND_PROD_IMAGE = 'backtest-backend'
        FRONTEND_PROD_IMAGE = 'backtest-frontend'
        DEPLOY_HOST = 'localhost'
        DEPLOY_USER = 'jenkins'
        DEPLOY_PATH_PROD = '/opt/backtest'
        DOCKER_COMPOSE_PROD_FILE = '${WORKSPACE}/compose/compose.prod.yml'
  // 통합 검사 실패 시 빌드를 실패로 처리할지 여부
  FAIL_ON_INTEGRATION_CHECK = 'true'
  // 네트워크 불안정성에 대비한 재시도/백오프 파라미터
  NETWORK_RETRY_COUNT = '3'
  NETWORK_RETRY_BASE_DELAY = '5'
    // Docker 클라이언트 타임아웃을 늘려 일시적 실패를 완화
    DOCKER_CLIENT_TIMEOUT = '300'
    COMPOSE_HTTP_TIMEOUT  = '300'
    }

    stages {
    // 1) 소스 코드 체크아웃 단계
    //    - SCM(예: GitHub)에서 현재 레포를 체크아웃합니다.
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

  // 2) 빌드 환경 디버그 출력
  //    - Jenkins에서 사용 가능한 Git/빌드 환경 정보를 캡처하여 로그에 출력합니다.
  //    - UID/GID를 캡처해 도커 컨테이너 실행 시 권한 문제를 방지합니다.
  stage('Debug Environment') {
            steps {
                script {
                    echo "Debug Information:"
                    // Git 메타데이터를 캡처하여 BRANCH_NAME/GIT_BRANCH가 비어있을 때 대체값으로 사용
                    env.GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD || echo ''", returnStdout: true).trim()
                    env.GIT_BRANCH_NAME = sh(script: "git rev-parse --abbrev-ref HEAD || echo ''", returnStdout: true).trim()
                    // Jenkins 환경변수가 비어있으면 감지한 브랜치명을 대신 사용
                    if (!env.BRANCH_NAME || env.BRANCH_NAME == 'null') { env.BRANCH_NAME = env.GIT_BRANCH_NAME }
                    if (!env.GIT_BRANCH || env.GIT_BRANCH == 'null') { env.GIT_BRANCH = env.GIT_BRANCH_NAME }

                    echo "BRANCH_NAME: ${env.BRANCH_NAME}"
                    echo "GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "GIT_BRANCH_NAME: ${env.GIT_BRANCH_NAME}"
                    echo "GIT_COMMIT_SHORT: ${env.GIT_COMMIT_SHORT}"
                    echo "BUILD_NUMBER: ${env.BUILD_NUMBER}"
                    echo "All env vars:"
          // Jenkins의 UID/GID를 캡처하여 컨테이너를 동일 사용자 권한으로 실행
          env.UID_J = sh(script: 'id -u', returnStdout: true).trim()
          env.GID_J = sh(script: 'id -g', returnStdout: true).trim()
          sh '''
            env | grep -E "(BRANCH|GIT|BUILD)" | sort || true
            echo "UID_J=${UID_J} GID_J=${GID_J}"
          '''
          // Hypothesis DB 디렉터리(호스트)에 대한 안전한 생성/권한 설정
          // 여러 에이전트에서 동작할 수 있도록 Debug 단계에서 보장합니다.
          sh '''
            mkdir -p /var/lib/jenkins/.hypothesis/examples || true
            chown ${UID_J}:${GID_J} /var/lib/jenkins/.hypothesis /var/lib/jenkins/.hypothesis/examples || true
            chmod 700 /var/lib/jenkins/.hypothesis || true
          '''
                }
            }
        }

  // 3) 테스트 단계 (프론트엔드/백엔드 병렬 실행)
  //    - Docker 이미지 빌드 내에서 테스트를 실행하여 테스트 환경을 격리합니다.
  stage('Tests') {
            parallel {
                stage('Frontend Tests') {
                    steps {
                        script {
                            echo 'Running frontend tests...'
                            sh '''
                                cd frontend
                                docker build --build-arg RUN_TESTS=true \
                                    -t backtest-frontend-test:${BUILD_NUMBER} .
                            '''
                            echo "Frontend tests passed"
                        }
                    }
                }
                stage('Backend Tests') {
                    steps {
                        script {
                            echo 'Running backend tests with controlled environment...'
                            sh '''
                cd backend
                docker build --build-arg RUN_TESTS=true \
                  -t backtest-backend-test:${BUILD_NUMBER} .
                            '''
                            echo "Backend tests passed"
                        }
                    }
                }
            }
        }

  // 4) JUnit 리포트 수집
  //    - 각 테스트 결과를 JUnit XML로 수집하고 Jenkins에 보고합니다.
  //    - 프론트엔드의 경우 호스트의 npm 캐시를 마운트하여 권한 문제를 방지합니다.
  stage('Collect JUnit Reports') {
            steps {
                script {
                    sh '''
                        mkdir -p reports/backend reports/frontend
                        # 호스트측 npm 캐시 디렉터리가 존재하고 Jenkins 사용자가 소유하도록 보장
                        mkdir -p frontend/.npm || true
                        chown ${UID_J}:${GID_J} frontend/.npm || true

                        # 백엔드 JUnit: 이미지 내부에서 테스트를 실행해 JUnit XML을 생성 (Jenkins 사용자 권한)
                        # Hypothesis DB 호스트 디렉터리를 마운트하고 HYPOTHESIS_DATABASE 환경변수를 설정
                        docker run --rm -u ${UID_J}:${GID_J} \
                          -v /var/lib/jenkins/.hypothesis:/home/jenkins/.hypothesis \
                          -e HYPOTHESIS_DATABASE=/home/jenkins/.hypothesis/examples \
                          -v "$PWD/reports/backend:/reports" backtest-backend-test:${BUILD_NUMBER} \
                          sh -lc "pytest tests/unit/ -v --tb=short --junitxml=/reports/junit.xml"

                        # 프론트엔드 JUnit: Node 컨테이너에서 vitest를 실행
                        # 호스트의 npm 캐시를 /app/.npm에 마운트하고 NPM_CONFIG_CACHE를 설정해 루트 권한 문제 방지
                        docker run --rm -u ${UID_J}:${GID_J} \
                          -e CI=1 -e VITEST_JUNIT_FILE=/reports/junit.xml -e NPM_CONFIG_CACHE=/app/.npm \
                          -v "$PWD/frontend:/app" -v "$PWD/frontend/.npm:/app/.npm" -v "$PWD/reports/frontend:/reports" -w /app \
                          node:20-alpine sh -lc "npm ci --prefer-offline --no-audit && npx vitest run"
                    '''

                    junit allowEmptyResults: true, testResults: 'reports/**/junit.xml'
                    archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
                }
            }
        }


  // 5) 프로덕션 이미지 빌드 및 레지스트리로 푸시
  //    - 빌더(backtest-builder)를 사용해 BuildKit으로 빌드합니다.
  //    - GHCR에 로그인 후 이미지 푸시(재시도 로직 포함).
  stage('Build and Push PROD') {
            parallel {
                stage('Backend PROD') {
                    steps {
                        script {
                            withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                                def fullImageName = "ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                                echo "Building PROD backend image: ${fullImageName}"
                                // 빌드 중 불필요한 오류를 줄이기 위해 buildx 빌더 존재 여부 확인
                                sh '''
                                  if ! docker buildx inspect backtest-builder >/dev/null 2>&1; then
                                    docker buildx create --use --name backtest-builder || true
                                  else
                                    docker buildx use backtest-builder || true
                                  fi
                                '''
                                sh "docker pull ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:latest || true"
                                sh "cd backend && DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg IMAGE_TAG=${BUILD_NUMBER} --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:latest -t ${fullImageName} ."
                                // GHCR 로그인: 일시적 네트워크 실패를 고려한 재시도 로직
                                sh '''
                                  set -eu
                                  export DOCKER_CLIENT_TIMEOUT=${DOCKER_CLIENT_TIMEOUT:-300}
                                  export COMPOSE_HTTP_TIMEOUT=${COMPOSE_HTTP_TIMEOUT:-300}
                                  # Probe GHCR then login with retries using configured backoff
                                  curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/ >/dev/null 2>&1 || echo 'Warning: GHCR probe failed; continuing'
                                  docker logout ghcr.io >/dev/null 2>&1 || true
                                  ok=''
                                  for i in $(seq 1 ${NETWORK_RETRY_COUNT}); do
                                    if printf "%s" "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin; then
                                      ok=1; break
                                    fi
                                    echo "docker login to ghcr.io failed (attempt $i), retrying..."
                                    sleep $((i * ${NETWORK_RETRY_BASE_DELAY}))
                                  done
                                  if [ -z "$ok" ]; then
                                    echo 'ERROR: docker login to ghcr.io failed after retries' >&2
                                    exit 1
                                  fi
                                '''
                                // 네트워크 문제에 대비한 푸시 재시도 로직
                                withEnv(["FULL_IMAGE_NAME=${fullImageName}"]) {
                                  sh '''
                                    set -eu
                                    ok=''
                                    for i in $(seq 1 ${NETWORK_RETRY_COUNT}); do
                                      if docker push "$FULL_IMAGE_NAME"; then
                                        ok=1; break
                                      fi
                                      echo "docker push failed (attempt $i), retrying..."
                                      sleep $((i * ${NETWORK_RETRY_BASE_DELAY}))
                                    done
                                    if [ -z "$ok" ]; then
                                      echo 'ERROR: docker push failed after retries' >&2
                                      exit 1
                                    fi
                                  '''
                                }
                            }
                        }
                    }
                }
                stage('Frontend PROD') {
                    steps {
                        script {
                            withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                                def fullImageName = "ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                                echo "Building PROD frontend image: ${fullImageName}"
                                // 빌드 중 불필요한 오류를 줄이기 위해 buildx 빌더 존재 여부 확인
                                sh '''
                                  if ! docker buildx inspect backtest-builder >/dev/null 2>&1; then
                                    docker buildx create --use --name backtest-builder || true
                                  else
                                    docker buildx use backtest-builder || true
                                  fi
                                '''
                                sh "docker pull ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:latest || true"
                                sh "cd frontend && DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:latest -t ${fullImageName} ."
                                // GHCR 로그인: 일시적 네트워크 실패를 고려한 재시도 로직
                                sh '''
                                  set -eu
                                  export DOCKER_CLIENT_TIMEOUT=${DOCKER_CLIENT_TIMEOUT:-300}
                                  export COMPOSE_HTTP_TIMEOUT=${COMPOSE_HTTP_TIMEOUT:-300}
                                    # Probe GHCR then login with retries using configured backoff
                                    curl -fsSLI --connect-timeout 10 --max-time 20 https://ghcr.io/v2/ >/dev/null 2>&1 || echo 'Warning: GHCR probe failed; continuing'
                                    docker logout ghcr.io >/dev/null 2>&1 || true
                                    ok=''
                                    for i in $(seq 1 ${NETWORK_RETRY_COUNT}); do
                                      if printf "%s" "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin; then
                                        ok=1; break
                                      fi
                                      echo "docker login to ghcr.io failed (attempt $i), retrying..."
                                      sleep $((i * ${NETWORK_RETRY_BASE_DELAY}))
                                    done
                                    if [ -z "$ok" ]; then
                                      echo 'ERROR: docker login to ghcr.io failed after retries' >&2
                                      exit 1
                                    fi
                                '''
                                // 네트워크 문제에 대비한 푸시 재시도 로직
                                withEnv(["FULL_IMAGE_NAME=${fullImageName}"]) {
                                  sh '''
                                    set -eu
                                    ok=''
                                    for i in $(seq 1 ${NETWORK_RETRY_COUNT}); do
                                      if docker push "$FULL_IMAGE_NAME"; then
                                        ok=1; break
                                      fi
                                      echo "docker push failed (attempt $i), retrying..."
                                      sleep $((i * ${NETWORK_RETRY_BASE_DELAY}))
                                    done
                                    if [ -z "$ok" ]; then
                                      echo 'ERROR: docker push failed after retries' >&2
                                      exit 1
                                    fi
                                  '''
                                }
                            }
                        }
                    }
                }
            }
        }

  // 6) 배포 (로컬 목적지)
  //    - SSH로 원격 호스트에 도커 컴포즈 파일과 배포 스크립트를 전달하고 실행합니다.
  stage('Deploy to Production (Local)') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN'),
                        sshUserPrivateKey(credentialsId: 'home-ubuntu-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')
                    ]) {
                        def remoteUser = SSH_USER ?: env.DEPLOY_USER
                        def remote = "${remoteUser}@${env.DEPLOY_HOST}"
                        def backendImage = "ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                        def frontendImage = "ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"

                        echo "Deploying to ${env.DEPLOY_PATH_PROD} on ${env.DEPLOY_HOST} as ${remoteUser}"

                        sh "ssh -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${remote}\" \"mkdir -p ${env.DEPLOY_PATH_PROD}\""
                        sh "scp -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${env.DOCKER_COMPOSE_PROD_FILE}\" \"${remote}:${env.DEPLOY_PATH_PROD}/docker-compose.yml\""
                        sh "scp -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no ./scripts/remote_deploy.sh \"${remote}:${env.DEPLOY_PATH_PROD}/remote_deploy.sh\""
                        sh "ssh -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${remote}\" \"chmod +x ${env.DEPLOY_PATH_PROD}/remote_deploy.sh\""
                        sh "ssh -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${remote}\" \"${env.DEPLOY_PATH_PROD}/remote_deploy.sh ${backendImage} ${frontendImage} ${env.DEPLOY_PATH_PROD}\""
                    }
                }
            }
        }

  // 7) 통합 테스트
  //    - 배포된 서비스(백엔드/프론트엔드)에 대해 간단한 API 검증을 수행합니다.
  stage('Integration Tests') {
            steps {
                script {
                    echo 'Running integration tests against deployed environment...'
                    sh '''
                        # Poll until healthy
                        for i in $(seq 1 30); do
                          if curl -fsS http://localhost:8001/health >/dev/null; then echo "backend healthy"; break; fi
                          sleep 1;
                        done
                        for i in $(seq 1 30); do
                          if curl -fsS http://localhost:8082/ >/dev/null; then echo "frontend up"; break; fi
                          sleep 1;
                        done
                    '''
                    // 선택적 API 검사(비차단): 백엔드 직접호출 및 프론트엔드 프록시 체인을 통해 검사
                    try {
                        sh '''
                            cat > /tmp/payload.json <<'EOF'
                            {"ticker":"AAPL","start_date":"2023-01-03","end_date":"2023-01-20","initial_cash":10000,"strategy":"buy_and_hold","strategy_params":{}}
EOF
                            # Choose jq implementation (host or containerized)
                            if command -v jq >/dev/null 2>&1; then
                              JQ='jq -e'
                            else
                              JQ='docker run --rm -i ghcr.io/jqlang/jq jq -e'
                            fi

                            MAX_TRIES=3
                            DELAY=5

                            # Backend direct with retries
                            SUCCESS=0
                            for i in $(seq 1 $MAX_TRIES); do
                              echo "[integration] backend attempt $i/$MAX_TRIES"
                              curl -fsS -H 'Content-Type: application/json' -d @/tmp/payload.json http://localhost:8001/api/v1/backtest/chart-data | tee /tmp/resp.json || true
                              if cat /tmp/resp.json | $JQ '.ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)' >/dev/null 2>&1; then
                                echo "[integration] backend check passed"
                                SUCCESS=1; break
                              else
                                echo "[integration] backend check failed (dumping response)"
                                cat /tmp/resp.json || true
                                if [ $i -lt $MAX_TRIES ]; then sleep $DELAY; fi
                              fi
                            done
                            if [ $SUCCESS -ne 1 ]; then echo "[integration] backend checks failed after $MAX_TRIES attempts"; exit 1; fi

                            # Frontend proxy chain with retries
                            SUCCESS=0
                            for i in $(seq 1 $MAX_TRIES); do
                              echo "[integration] frontend attempt $i/$MAX_TRIES"
                              curl -fsS -H 'Content-Type: application/json' -d @/tmp/payload.json http://localhost:8082/api/v1/backtest/chart-data | tee /tmp/resp2.json || true
                              if cat /tmp/resp2.json | $JQ '.ticker=="AAPL" and (.ohlc_data|length)>0 and (.equity_data|length)>0 and (.summary_stats!=null)' >/dev/null 2>&1; then
                                echo "[integration] frontend check passed"
                                SUCCESS=1; break
                              else
                                echo "[integration] frontend check failed (dumping response)"
                                cat /tmp/resp2.json || true
                                if [ $i -lt $MAX_TRIES ]; then sleep $DELAY; fi
                              fi
                            done
                            if [ $SUCCESS -ne 1 ]; then echo "[integration] frontend checks failed after $MAX_TRIES attempts"; exit 1; fi
                        '''
            echo "Integration API checks (direct & via frontend) passed"
                    } catch (Exception e) {
            echo "Integration API check failed: ${e.getMessage()}"
                        // Dump and archive response snapshots for debugging
                        sh 'echo "--- /tmp/resp.json ---"; cat /tmp/resp.json || true'
                        sh 'echo "--- /tmp/resp2.json ---"; cat /tmp/resp2.json || true'
                        archiveArtifacts artifacts: '/tmp/resp*.json', allowEmptyArchive: true
                        if (env.FAIL_ON_INTEGRATION_CHECK == 'true') {
                          echo 'FAIL_ON_INTEGRATION_CHECK=true -> marking build as FAILURE'
                          currentBuild.result = 'FAILURE'
                          error('Integration API checks failed and FAIL_ON_INTEGRATION_CHECK is true')
                        } else {
                          echo "FAIL_ON_INTEGRATION_CHECK=false -> continuing pipeline despite API check failure"
                        }
                    }
                    echo "Integration tests completed"
                }
            }
        }
    }

  // 8) 파이프라인 종료 후 처리 (성공/실패/항상 실행할 작업)
  post {
    success {
      echo 'Pipeline succeeded!'
      // GitHub Checks에 결과를 게시하려고 시도합니다. 설치된 플러그인에 따라
      // publishChecks 또는 githubChecks 스텝을 시도하고, 없으면 실패해도 무시합니다.
      script {
        withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
          try {
            publishChecks name: 'Backtest CI', conclusion: 'SUCCESS', detailsURL: env.BUILD_URL,
                          output: [title: '빌드 성공', summary: "모든 단계 통과 — ${env.BUILD_URL}"]
            echo 'publishChecks 호출 성공'
          } catch (MissingMethodException | Exception e1) {
            echo "publishChecks 호출 실패: ${e1}. githubChecks로 시도합니다."
            try {
              githubChecks name: 'Backtest CI', status: 'COMPLETED', conclusion: 'SUCCESS', detailsURL: env.BUILD_URL,
                           output: [title: '빌드 성공', summary: "모든 단계 통과 — ${env.BUILD_URL}"]
              echo 'githubChecks 호출 성공'
            } catch (MissingMethodException | Exception e2) {
              echo "Checks 게시 스텝을 찾지 못했습니다 (publishChecks/githubChecks). 오류: ${e2}. 계속 진행합니다."
            }
          }
        }
      }
    }
    failure {
      echo 'Pipeline failed! (see console log for details)'
      script {
        withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
          try {
            publishChecks name: 'Backtest CI', conclusion: 'FAILURE', detailsURL: env.BUILD_URL,
                          output: [title: '빌드 실패', summary: "빌드 또는 테스트 실패 — 콘솔 로그 확인: ${env.BUILD_URL}"]
            echo 'publishChecks 호출 성공'
          } catch (MissingMethodException | Exception e1) {
            echo "publishChecks 호출 실패: ${e1}. githubChecks로 시도합니다."
            try {
              githubChecks name: 'Backtest CI', status: 'COMPLETED', conclusion: 'FAILURE', detailsURL: env.BUILD_URL,
                           output: [title: '빌드 실패', summary: "빌드 또는 테스트 실패 — 콘솔 로그 확인: ${env.BUILD_URL}"]
              echo 'githubChecks 호출 성공'
            } catch (MissingMethodException | Exception e2) {
              echo "Checks 게시 스텝을 찾지 못했습니다 (publishChecks/githubChecks). 오류: ${e2}. 계속 진행합니다."
            }
          }
        }
      }
    }
    always {
      sh 'docker system prune -f'
      cleanWs(deleteDirs: true, disableDeferredWipeout: true)
    }
  }
}
