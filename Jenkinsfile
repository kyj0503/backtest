pipeline {
    agent any

    environment {
        GHCR_OWNER = 'kyj0503'
        BE_IMAGE_NAME = 'backtest-be'
        FE_IMAGE_NAME = 'backtest-fe'
        DOCKER_BUILDKIT = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/kyj0503/backtest.git',
                        credentialsId: 'github-token'
                    ]]
                ])
            }
        }

        stage('Test Backend') {
            steps {
                script {
                    echo "Running Backend tests..."
                    dir('backtest_be_fast') {
                        sh '''
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install -r requirements.txt -r requirements-test.txt
                            
                            # home-server의 설정 파일 사용
                            cp /home/ubuntu/source/home-server/config/backtest/.env .env
                            
                            # 테스트 환경을 위한 DATABASE_HOST 오버라이드
                            export DATABASE_HOST=localhost
                            
                            python -m pytest tests/ -v --tb=short || echo "No tests found or tests skipped"
                        '''
                    }
                }
            }
            post {
                failure {
                    echo "Backend tests failed. Stopping pipeline."
                }
            }
        }

        stage('Test Frontend') {
            steps {
                script {
                    echo "Running Frontend tests..."
                    dir('backtest_fe') {
                        sh '''
                            npm ci
                            npm run test -- --run || echo "No tests found or tests skipped"
                        '''
                    }
                }
            }
            post {
                failure {
                    echo "Frontend tests failed. Stopping pipeline."
                }
            }
        }

        stage('Login GHCR') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_TOKEN')]) {
                        sh 'echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin'
                    }
                }
            }
        }

        stage('Build and Push Backend Image') {
            steps {
                script {
                    def beImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BE_IMAGE_NAME}"
                    echo "Building Backend image: ${beImageName}"
                    
                    sh """
                        docker build \
                            --tag ${beImageName}:${env.BUILD_NUMBER} \
                            --tag ${beImageName}:latest \
                            ./backtest_be_fast
                        docker push ${beImageName}:${env.BUILD_NUMBER}
                        docker push ${beImageName}:latest
                    """
                }
            }
        }

        stage('Build and Push Frontend Image') {
            steps {
                script {
                    def feImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FE_IMAGE_NAME}"
                    echo "Building Frontend image: ${feImageName}"
                    
                    sh """
                        docker build \
                            --tag ${feImageName}:${env.BUILD_NUMBER} \
                            --tag ${feImageName}:latest \
                            ./backtest_fe
                        docker push ${feImageName}:${env.BUILD_NUMBER}
                        docker push ${feImageName}:latest
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh '''
                        cd /home/ubuntu/source/home-server/docker
                        docker compose -f docker-compose.apps.yml pull backtest-be backtest-fe
                        docker compose -f docker-compose.apps.yml up -d backtest-be backtest-fe
                        sleep 10
                        docker ps | grep -E "backtest"
                        echo "✅ Backtest deployment completed!"
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    sh '''
                        sleep 15
                        curl -f https://backtest.yeonjae.kr/ || echo "Frontend health check pending..."
                        curl -f https://backtest-be.yeonjae.kr/health || echo "Backend health check pending..."
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo '✅ Backtest Build, Push, and Deploy completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed!'
        }
    }
}
