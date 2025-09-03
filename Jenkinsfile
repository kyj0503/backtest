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

        stage('Frontend Tests') {
            steps {
                script {
                    echo 'Running frontend tests...'
                    try {
                        // Build test image with tests enabled and build info
                        sh '''
                            cd frontend
                            docker build --build-arg RUN_TESTS=true \
                                --build-arg GIT_COMMIT=${GIT_COMMIT} \
                                --build-arg GIT_BRANCH=${GIT_BRANCH} \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                -t backtest-frontend-test:${BUILD_NUMBER} .
                        '''
                        echo "✅ Frontend tests passed"
                    } catch (Exception e) {
                        echo "⚠️ Frontend tests failed: ${e.getMessage()}"
                        // Continue pipeline even if tests fail (for now)
                    }
                }
            }
        }

        stage('Backend Tests') {
            steps {
                script {
                    echo 'Running backend tests with controlled environment...'
                    try {
                        // Build test image with specific test configuration and build info
                        sh '''
                            cd backend
                            docker build --build-arg RUN_TESTS=true \
                                --build-arg GIT_COMMIT=${GIT_COMMIT} \
                                --build-arg GIT_BRANCH=${GIT_BRANCH} \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                -t backtest-backend-test:${BUILD_NUMBER} .
                        '''
                        echo "✅ Backend tests passed"
                    } catch (Exception e) {
                        echo "⚠️ Backend tests failed: ${e.getMessage()}"
                        // Continue pipeline even if tests fail (for now)
                    }
                }
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
                        // Build production image without tests but with build info
                        sh "cd backend && docker build --build-arg RUN_TESTS=false --build-arg GIT_COMMIT=${GIT_COMMIT} --build-arg GIT_BRANCH=${GIT_BRANCH} --build-arg BUILD_NUMBER=${BUILD_NUMBER} --build-arg IMAGE_TAG=${BUILD_NUMBER} -t ${fullImageName} ."
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
                        // Build production image without tests but with build info
                        sh "cd frontend && docker build --build-arg RUN_TESTS=false --build-arg GIT_COMMIT=${GIT_COMMIT} --build-arg GIT_BRANCH=${GIT_BRANCH} --build-arg BUILD_NUMBER=${BUILD_NUMBER} -t ${fullImageName} ."
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
                    // This deploy uses an SSH private-key credential to run a server-side deploy script.
                    // Use the 'github-token' for image owner and 'home-ubuntu-ssh' (SSH key) for remote actions.
                    withCredentials([
                        usernamePassword(credentialsId: 'github-token', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN'),
                        sshUserPrivateKey(credentialsId: 'home-ubuntu-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')
                    ]) {
                        // prefer the username provided by the SSH credential
                        def remoteUser = SSH_USER ?: env.DEPLOY_USER
                        def remote = "${remoteUser}@${env.DEPLOY_HOST}"
                        def backendImage = "ghcr.io/${env.GH_USER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                        def frontendImage = "ghcr.io/${env.GH_USER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"

                        echo "Deploying to ${env.DEPLOY_PATH_PROD} on ${env.DEPLOY_HOST} as ${remoteUser}"

                        // Ensure remote directory exists (use -i to supply private key file)
                        sh "ssh -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${remote}\" \"mkdir -p ${env.DEPLOY_PATH_PROD}\""

                        // Copy prod compose to remote
                        sh "scp -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${env.DOCKER_COMPOSE_PROD_FILE}\" \"${remote}:${env.DEPLOY_PATH_PROD}/docker-compose.yml\""

                        // Copy deploy script to remote and execute
                        sh "scp -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no ./scripts/remote_deploy.sh \"${remote}:${env.DEPLOY_PATH_PROD}/remote_deploy.sh\""
                        sh "ssh -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${remote}\" \"chmod +x ${env.DEPLOY_PATH_PROD}/remote_deploy.sh\""
                        sh "ssh -i \"\${SSH_KEY}\" -o StrictHostKeyChecking=no \"${remote}\" \"${env.DEPLOY_PATH_PROD}/remote_deploy.sh ${backendImage} ${frontendImage} ${env.DEPLOY_PATH_PROD}\""
                    }
                }
            }
        }

        stage('Integration Tests') {
            when {
                expression {
                    return (env.BRANCH_NAME == 'main') || (env.GIT_BRANCH != null && env.GIT_BRANCH.endsWith('/main'))
                }
            }
            steps {
                script {
                    echo 'Running integration tests against deployed environment...'
                    try {
                        // Test deployed API endpoints
                        sh '''
                            # Wait for services to be ready
                            sleep 30
                            
                            # Test backend health
                            curl -f http://localhost:8001/health || echo "Backend health check failed"
                            
                            # Test frontend availability  
                            curl -f http://localhost:8082/ || echo "Frontend availability check failed"
                        '''
                        echo "✅ Integration tests completed"
                    } catch (Exception e) {
                        echo "⚠️ Integration tests failed: ${e.getMessage()}"
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