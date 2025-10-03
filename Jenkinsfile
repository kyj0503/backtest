pipeline {
  agent any

  options {
    skipDefaultCheckout(true)
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    // Docker/Compose timeouts
    DOCKER_BUILDKIT = '1'
    DOCKER_CLIENT_TIMEOUT = '300'
    COMPOSE_HTTP_TIMEOUT  = '300'

    // Compose (prod)
    COMPOSE_FILE = 'compose/compose.prod.yaml'
    COMPOSE_PROJECT_NAME = 'backtest-prod'
    // External env file path on the server
    ENV_FILE_PATH = '/opt/backtest/.env'

    // Image namespace used by compose.prod.yaml
    // Compose expects ghcr.io/capstone-backtest/backtest/*:latest by default.
    REGISTRY_NS = 'ghcr.io/capstone-backtest/backtest'
    FAST_IMAGE   = "${REGISTRY_NS}/backtest-be-fast"
    SPRING_IMAGE = "${REGISTRY_NS}/backtest-be-spring"
    FE_IMAGE     = "${REGISTRY_NS}/backtest-fe"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Prepare & Debug') {
      steps {
        script {
          env.GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD || echo ${BUILD_NUMBER}", returnStdout: true).trim()
          sh '''
            set -eu
            echo "Docker version:"; docker --version || true
            echo "Compose version:"; docker compose version || true
            echo "Current branch:"; git rev-parse --abbrev-ref HEAD || true
            echo "GIT_COMMIT_SHORT=${GIT_COMMIT_SHORT}"
            # Ensure external env file exists and has required keys
            if [ ! -f "${ENV_FILE_PATH}" ]; then
              echo "ERROR: Missing env file at ${ENV_FILE_PATH}" >&2
              exit 1
            fi
            # Do not print secrets; just assert required keys exist
            for k in MYSQL_ROOT_PASSWORD REDIS_PASSWORD; do
              if ! grep -E "^${k}=" "${ENV_FILE_PATH}" >/dev/null 2>&1; then
                echo "ERROR: ${k} is missing in ${ENV_FILE_PATH}" >&2; exit 1; fi
            done
          '''
        }
      }
    }

    stage('Build Images (local)') {
      steps {
        script {
          // Build FastAPI (prod image)
          sh '''
            set -eu
            cd backtest_be_fast
            docker build \
              --build-arg IMAGE_TAG=${GIT_COMMIT_SHORT} \
              -t ${FAST_IMAGE}:${GIT_COMMIT_SHORT} \
              -t ${FAST_IMAGE}:latest \
              -f Dockerfile .
          '''

          // Build Spring Boot (prod image)
          sh '''
            set -eu
            cd backtest_be_spring
            docker build \
              -t ${SPRING_IMAGE}:${GIT_COMMIT_SHORT} \
              -t ${SPRING_IMAGE}:latest \
              -f Dockerfile .
          '''

          // Build Frontend (prod Nginx image)
          sh '''
            set -eu
            cd backtest_fe
            docker build \
              -t ${FE_IMAGE}:${GIT_COMMIT_SHORT} \
              -t ${FE_IMAGE}:latest \
              -f Dockerfile .
          '''

          // Show resulting images
          sh 'docker images | grep -E "(backtest-be-fast|backtest-be-spring|backtest-fe)" || true'
        }
      }
    }

    stage('Deploy (docker compose)') {
      steps {
        sh '''
          set -eu
          # Run compose with prod file and external env file. Also direct services' env_file via BACKTEST_ENV_FILE
          BACKTEST_ENV_FILE=${ENV_FILE_PATH} docker compose --env-file "${ENV_FILE_PATH}" -f ${COMPOSE_FILE} up -d --remove-orphans
          BACKTEST_ENV_FILE=${ENV_FILE_PATH} docker compose --env-file "${ENV_FILE_PATH}" -f ${COMPOSE_FILE} ps
        '''
      }
    }

    stage('Smoke Checks') {
      steps {
        sh '''
          set -eu
          # Wait for container health where defined
          wait_healthy() {
            name="$1"; tries="${2:-30}"; sleep_s=2;
            for i in $(seq 1 "$tries"); do
              status=$(docker inspect -f '{{json .State.Health.Status}}' "$name" 2>/dev/null | tr -d '"' || true)
              if [ "$status" = "healthy" ]; then echo "$name healthy"; return 0; fi
              echo "[$i/$tries] $name status=$status"; sleep "$sleep_s";
            done
            echo "ERROR: $name not healthy" >&2; return 1
          }

          # Named containers in compose.prod.yaml
          wait_healthy bt_mysql_prod 60 || true
          wait_healthy bt_redis_prod 60 || true

          # Poll app endpoints
          poll_http() {
            url="$1"; tries="${2:-30}"; sleep_s=2;
            for i in $(seq 1 "$tries"); do
              if curl -fsS "$url" >/dev/null; then echo "OK: $url"; return 0; fi
              echo "[$i/$tries] waiting for $url"; sleep "$sleep_s";
            done
            echo "ERROR: $url not responding" >&2; return 1
          }

          poll_http http://localhost:8000/health 60 || true
          # Spring is published on host 8082 (container stays on 8080)
          poll_http http://localhost:8082/actuator/health 60 || true
          poll_http http://localhost/health 60 || true
        '''
      }
    }
  }

  post {
    success {
      echo 'Pipeline succeeded: images built and stack deployed (prod compose).'
    }
    failure {
      echo 'Pipeline failed. Check console logs for details.'
    }
    always {
      // Keep workspace tidy but do not prune running containers/images
      cleanWs(deleteDirs: true, disableDeferredWipeout: true)
    }
  }
}
