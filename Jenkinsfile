pipeline {
    agent any

    options {
    skipDefaultCheckout(true)
    timestamps()
    disableConcurrentBuilds()
    }

  // NOTE: Credentials and Docker auth
  // - Ensure Docker registry credentials (GHCR) are stored in Jenkins Credentials (id: 'github-token')
  // - Avoid committing ~/.docker/config.json to the build agents. Use `withCredentials` to inject secrets at runtime.
  // - Limit access to agent filesystem and rotate GHCR tokens periodically.

    environment {
        GHCR_OWNER = 'kyj0503'
        BACKEND_PROD_IMAGE = 'backtest-backend'
        FRONTEND_PROD_IMAGE = 'backtest-frontend'
        DEPLOY_HOST = 'localhost'
        DEPLOY_USER = 'jenkins'
        DEPLOY_PATH_PROD = '/opt/backtest'
        DOCKER_COMPOSE_PROD_FILE = '${WORKSPACE}/compose/compose.prod.yml'
    // If true, integration API check failures will fail the build
    FAIL_ON_INTEGRATION_CHECK = 'true'
    // Retry/backoff parameters for flaky network ops
    NETWORK_RETRY_COUNT = '3'
    NETWORK_RETRY_BASE_DELAY = '5'
        // Extend Docker client timeouts to reduce transient failures
        DOCKER_CLIENT_TIMEOUT = '300'
        COMPOSE_HTTP_TIMEOUT  = '300'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Debug Environment') {
            steps {
                script {
                    echo "Debug Information:"
                    echo "BRANCH_NAME: ${env.BRANCH_NAME}"
                    echo "GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "BUILD_NUMBER: ${env.BUILD_NUMBER}"
                    echo "All env vars:"
          // capture jenkins UID/GID to run containers as the same user
          env.UID_J = sh(script: 'id -u', returnStdout: true).trim()
          env.GID_J = sh(script: 'id -g', returnStdout: true).trim()
          sh '''
            env | grep -E "(BRANCH|GIT)" | sort || true
            echo "UID_J=${UID_J} GID_J=${GID_J}"
          '''
                }
            }
        }

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

        stage('Collect JUnit Reports') {
            steps {
                script {
                    sh '''
                        mkdir -p reports/backend reports/frontend
                        # Ensure host-side npm cache directory exists and is owned by the Jenkins user
                        mkdir -p frontend/.npm || true
                        chown ${UID_J}:${GID_J} frontend/.npm || true

                        # Backend JUnit (run tests inside image to emit JUnit XML) as jenkins user
                        docker run --rm -u ${UID_J}:${GID_J} -v "$PWD/reports/backend:/reports" backtest-backend-test:${BUILD_NUMBER} \
                          sh -lc "pytest tests/unit/ -v --tb=short --junitxml=/reports/junit.xml"

                        # Frontend JUnit (run in Node 20 container using vitest.config.ts)
                        # Mount host-side npm cache into /app/.npm and set NPM_CONFIG_CACHE to avoid writing to root-owned /.npm
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


        stage('Build and Push PROD') {
            parallel {
                stage('Backend PROD') {
                    steps {
                        script {
                            withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                                def fullImageName = "ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                                echo "Building PROD backend image: ${fullImageName}"
                                // Ensure a usable buildx builder exists without noisy errors
                                sh '''
                                  if ! docker buildx inspect backtest-builder >/dev/null 2>&1; then
                                    docker buildx create --use --name backtest-builder || true
                                  else
                                    docker buildx use backtest-builder || true
                                  fi
                                '''
                                sh "docker pull ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:latest || true"
                                sh "cd backend && DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg IMAGE_TAG=${BUILD_NUMBER} --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:latest -t ${fullImageName} ."
                                // Robust GHCR login with retries (handles intermittent network timeouts)
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
                                // Push with retries to mitigate transient network hiccups
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
                                // Ensure a usable buildx builder exists without noisy errors
                                sh '''
                                  if ! docker buildx inspect backtest-builder >/dev/null 2>&1; then
                                    docker buildx create --use --name backtest-builder || true
                                  else
                                    docker buildx use backtest-builder || true
                                  fi
                                '''
                                sh "docker pull ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:latest || true"
                                sh "cd frontend && DOCKER_BUILDKIT=1 docker build --build-arg RUN_TESTS=false --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:latest -t ${fullImageName} ."
                                // Robust GHCR login with retries (handles intermittent network timeouts)
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
                                // Push with retries to mitigate transient network hiccups
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
                    // Optional API checks (non-blocking): direct backend and via frontend proxy chain
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

  post {
    success {
      echo 'Pipeline succeeded!'
    }
    failure {
      echo 'Pipeline failed! (see console log for details)'
    }
    always {
      sh 'docker system prune -f'
      cleanWs(deleteDirs: true, disableDeferredWipeout: true)
    }
  }
}
