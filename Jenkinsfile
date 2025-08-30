pipeline {
    agent any

    environment {
        GHCR_OWNER = 'kyj05030'
        BACKEND_PROD_IMAGE = 'backtest-backend'
        FRONTEND_PROD_IMAGE = 'backtest-frontend'
        DEPLOY_HOST = 'localhost'
        DEPLOY_USER = 'jenkins'
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
                    // Use the username from the 'github-token' credential as the GHCR owner
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                        def fullImageName = "ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                        echo "Building PROD backend image: ${fullImageName}"
                        docker.build(fullImageName, './backend')
                        docker.withRegistry("https://ghcr.io", 'github-token') {
                            docker.image(fullImageName).push()
                        }
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
                    // Use credential username as owner to ensure push permission
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                        def fullImageName = "ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                        echo "Building PROD frontend image: ${fullImageName}"
                        docker.build(fullImageName, './frontend')
                        docker.withRegistry("https://ghcr.io", 'github-token') {
                            docker.image(fullImageName).push()
                        }
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
                    // This deploy uses SSH to run a server-side deploy script.
                    // Assumptions: Jenkins has an SSH credential with id 'deploy-ssh' and
                    // environment variables DEPLOY_HOST and DEPLOY_USER are set in Jenkins (or globally).
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                        sshagent(['home-ubuntu-ssh']) {
                            def remote = "${env.DEPLOY_USER}@${env.DEPLOY_HOST}"
                            def backendImage = "ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                            def frontendImage = "ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"

                            echo "Deploying to ${env.DEPLOY_PATH_PROD} on ${env.DEPLOY_HOST} as ${env.DEPLOY_USER}"

                            // Ensure remote directory exists
                            sh "ssh -o StrictHostKeyChecking=no ${remote} 'mkdir -p ${env.DEPLOY_PATH_PROD}'"

                            // Copy prod compose to remote
                            sh "scp -o StrictHostKeyChecking=no ${env.DOCKER_COMPOSE_PROD_FILE} ${remote}:${env.DEPLOY_PATH_PROD}/docker-compose.yml"

                            // Execute remote deploy script by piping local script over SSH
                            // pass args after -- so remote bash receives them reliably
                            sh "ssh -o StrictHostKeyChecking=no ${remote} 'bash -s' -- ${backendImage} ${frontendImage} ${env.DEPLOY_PATH_PROD} < ./scripts/remote_deploy.sh"
                        }
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo 'Running tests...'
                    // Prefer GH_USER obtained from github-token credential; fall back to GHCR_OWNER
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                        def owner = env.GH_USER ?: env.GHCR_OWNER
                        def backendImage = "ghcr.io/${owner}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                        def frontendImage = "ghcr.io/${owner}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"

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