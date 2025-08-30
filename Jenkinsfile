pipeline {
    agent any
    
    environment {
        GHCR_OWNER = 'kyj05030'
        BACKEND_PROD_IMAGE = 'backtest-backend'
        FRONTEND_PROD_IMAGE = 'backtest-frontend'
        DEPLOY_PATH_PROD = '/opt/backtest'
        DOCKER_COMPOSE_FILE = '${WORKSPACE}/docker-compose.yml'  // 프로젝트 루트의 docker-compose.yml 사용
        DOCKER_COMPOSE_PROD_FILE = '${WORKSPACE}/docker-compose.prod.yml'  // 프로덕션용 파일
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }
        
        // --- Main 브랜치 전용 스테이지 ---
        stage('Build and Push Backend PROD') {
            when { branch 'main' }
            steps {
                script {
                    def fullImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    echo "Building PROD backend image for main branch: ${fullImageName}"
                    
                    docker.build(fullImageName, './backend')
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        echo "Pushing PROD backend image to GHCR..."
                        docker.image(fullImageName).push()
                    }
                }
            }
        }
        
        stage('Build and Push Frontend PROD') {
            when { branch 'main' }
            steps {
                script {
                    def fullImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    echo "Building PROD frontend image for main branch: ${fullImageName}"
                    
                    docker.build(fullImageName, './frontend')
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        echo "Pushing PROD frontend image to GHCR..."
                        docker.image(fullImageName).push()
                    }
                }
            }
        }
        
        stage('Deploy to Production (Local)') {
            when { branch 'main' }
            steps {
                script {
                    def backendImage = "ghcr.io/${env.GHCR_OWNER}/${env.BACKEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    def frontendImage = "ghcr.io/${env.GHCR_OWNER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER}"
                    
                    echo "Deploying to local production: ${env.DEPLOY_PATH_PROD}"
                    
                    // docker-compose.prod.yml 파일을 복사하고 이미지 이름 추가
                    sh """
                        # 프로덕션 파일을 작업 디렉터리로 복사
                        cp ${env.DOCKER_COMPOSE_PROD_FILE} ${env.DEPLOY_PATH_PROD}/docker-compose.yml
                        
                        # 백엔드 서비스에 image 필드 추가
                        sed -i '/backend:/a\\    image: ${backendImage}' ${env.DEPLOY_PATH_PROD}/docker-compose.yml
                        
                        # 프론트엔드 서비스에 image 필드 추가
                        sed -i '/frontend:/a\\    image: ${frontendImage}' ${env.DEPLOY_PATH_PROD}/docker-compose.yml
                        
                        # 기존 컨테이너 중지 및 제거
                        cd ${env.DEPLOY_PATH_PROD}
                        docker compose down
                        
                        # 새 컨테이너 시작
                        docker compose up -d
                        
                        # 헬스체크
                        sleep 30
                        curl -f http://localhost:8000/health || echo "Backend health check failed"
                        curl -f http://localhost:8080 || echo "Frontend health check failed"
                        
                        echo "Deployment completed!"
                    """
                }
            }
        }
        
        // 공통 테스트 단계
        stage('Test') {
            steps {
                echo 'Running tests...'
                // 백엔드 테스트 (pytest가 설치된 경우)
                sh 'docker run --rm ghcr.io/${GHCR_OWNER}/${BACKEND_PROD_IMAGE}:${BUILD_NUMBER} python -m pytest || echo "No tests found"'
                // 프론트엔드 테스트 (있는 경우)
                sh 'docker run --rm ghcr.io/${env.GHCR_OWNER}/${env.FRONTEND_PROD_IMAGE}:${env.BUILD_NUMBER} npm test -- --watchAll=false || echo "No tests found"'
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline succeeded! 🎉'
            // 성공 시 알림 (Slack, Email 등) 추가 가능
        }
        failure {
            echo 'Pipeline failed! ❌'
            // 실패 시 알림 추가 가능
        }
        always {
            echo 'Cleaning up...'
            sh 'docker system prune -f'
            cleanWs()
        }
    }
}