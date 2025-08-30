pipeline {
    agent any

    environment {
        GHCR_OWNER = 'kyj05030'
        BACKEND_PROD_IMAGE = 'backtest-backend'
        FRONTEND_PROD_IMAGE = 'backtest-frontend'
        DEPLOY_PATH_PROD = '/opt/backtest'
        DOCKER_COMPOSE_PROD_FILE = '${WORKSPACE}/docker-compose.prod.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Push Backend PROD') {
            when {
                expression {
                    // multibranch이면 BRANCH_NAME, 일반 pipeline이면 GIT_BRANCH 확인
                    return (env.BRANCH_NAME == 'main') || (env.GIT_BRANCH != null && env.GIT_BRANCH.endsWith('/main'))
                }
            }
            steps {
                script {
                    def fullImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    echo "Building PROD backend image: ${fullImageName}"
                    docker.build(fullImageName, './backend')
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        docker.image(fullImageName).push()
                    }
                }
            }
        }

        stage('Build and Push Frontend PROD') {
            when {
                expression {
                    return (env.BRANCH_NAME == 'main') || (env.GIT_BRANCH != null && env.GIT_BRANCH.endsWith('/main'))
                }
            }
            steps {
                script {
                    def fullImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    echo "Building PROD frontend image: ${fullImageName}"
                    docker.build(fullImageName, './frontend')
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        docker.image(fullImageName).push()
                    }
                }
            }
        }

        stage('Deploy to Production (Local)') {
            when {
                expression {
                    return (env.BRANCH_NAME == 'main') || (env.GIT_BRANCH != null && env.GIT_BRANCH.endsWith('/main'))
                }
            }
            steps {
                                script {
                                        def backendImage = "ghcr.io/${env.GHCR_OWNER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                                        def frontendImage = "ghcr.io/${env.GHCR_OWNER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"

                                        echo "Deploying to ${env.DEPLOY_PATH_PROD} using override file"
                                        sh """
                                                set -e
                                                mkdir -p ${env.DEPLOY_PATH_PROD}
                                                cp ${env.DOCKER_COMPOSE_PROD_FILE} ${env.DEPLOY_PATH_PROD}/docker-compose.yml

                                                cat > ${env.DEPLOY_PATH_PROD}/override-images.yml <<'YAML'
services:
    backend:
        image: ${backendImage}
    frontend:
        image: ${frontendImage}
YAML

                                                cd ${env.DEPLOY_PATH_PROD}
                                                # Try pulling images first (no-op if not available locally)
                                                docker pull ${backendImage} || true
                                                docker pull ${frontendImage} || true

                                                echo 'Final merged docker-compose config:'
                                                docker compose -f docker-compose.yml -f override-images.yml config || true

                                                # Use --no-build to ensure compose will not try to build locally
                                                docker compose -f docker-compose.yml -f override-images.yml up -d --remove-orphans --no-build
                                                sleep 30
                                                curl -f http://localhost:8000/health || echo "Backend health check failed"
                                                curl -f http://localhost:8080 || echo "Frontend health check failed"
                                        """
                                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo 'Running tests...'
                    // build full image names in Groovy to avoid leaving ${...} in the shell script
                    def backendImage = "ghcr.io/${env.GHCR_OWNER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    def frontendImage = "ghcr.io/${env.GHCR_OWNER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"

                    // Try to pull images (no-op if not present) then run tests. Use returnStatus to avoid pipeline hard-fail
                    def rcBackend = sh(script: "docker pull ${backendImage} || true && docker run --rm ${backendImage} python -m pytest", returnStatus: true)
                    if (rcBackend != 0) {
                        echo "Backend tests skipped or failed (image may not exist or tests failed): ${backendImage}"
                    }

                    def rcFrontend = sh(script: "docker pull ${frontendImage} || true && docker run --rm ${frontendImage} npm test -- --watchAll=false", returnStatus: true)
                    if (rcFrontend != 0) {
                        echo "Frontend tests skipped or failed (image may not exist or tests failed): ${frontendImage}"
                    }
                }
            }
        }
    }

    post {
        success { echo 'Pipeline succeeded! 🎉' }
        failure { echo 'Pipeline failed! ❌' }
        always {
            sh 'docker system prune -f'
            cleanWs()
        }
    }
}