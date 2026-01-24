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
                checkout scm
                script {
                    echo "=== Git Information ==="
                    echo "GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "BRANCH_NAME: ${env.BRANCH_NAME}"
                }
            }
        }

        stage('Setup Buildx') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                script {
                    // Docker Buildx 설정 (멀티 아키텍처 빌드용)
                    sh '''
                        docker buildx create --name multiarch-builder --use --bootstrap || docker buildx use multiarch-builder
                        docker buildx inspect --bootstrap
                    '''
                    
                    // GHCR 로그인
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_TOKEN')]) {
                        sh 'echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin'
                    }
                }
            }
        }

        // --- Main 브랜치 전용 스테이지 ---
        stage('Build and Push Backend Multi-Arch Image') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                script {
                    def beImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BE_IMAGE_NAME}"
                    echo "Building multi-arch Backend image for main branch: ${beImageName}"
                    
                    // 멀티 아키텍처 빌드 및 푸시 (AMD64 + ARM64)
                    sh """
                        docker buildx build \
                            --platform linux/amd64,linux/arm64 \
                            --tag ${beImageName}:${env.BUILD_NUMBER} \
                            --tag ${beImageName}:latest \
                            --push \
                            ./backtest_be_fast
                    """
                }
            }
        }

        stage('Build and Push Frontend Multi-Arch Image') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                script {
                    def feImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FE_IMAGE_NAME}"
                    echo "Building multi-arch Frontend image for main branch: ${feImageName}"
                    
                    // 멀티 아키텍처 빌드 및 푸시 (AMD64 + ARM64)
                    sh """
                        docker buildx build \
                            --platform linux/amd64,linux/arm64 \
                            --tag ${feImageName}:${env.BUILD_NUMBER} \
                            --tag ${feImageName}:latest \
                            --push \
                            ./backtest_fe
                    """
                }
            }
        }

        // 배포는 home-server에서 담당
        stage('Trigger Deploy') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                build job: 'home-server-deploy', wait: false, propagate: false
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo '✅ Build and Push completed successfully!'
        }
        failure {
            echo '❌ Build failed!'
        }
    }
}
