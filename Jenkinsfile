pipeline {
    agent any

    environment {
        GHCR_OWNER = 'kyj0503'
        BE_IMAGE_NAME = 'backtest-be'
        FE_IMAGE_NAME = 'backtest-fe'
        DEPLOY_PATH = '/opt/backtest'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    echo "=== Git Information ==="
                    echo "GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "BRANCH_NAME: ${env.BRANCH_NAME}"
                    sh 'git branch -a'
                    sh 'git status'
                }
            }
        }

        // --- Main 브랜치 전용 스테이지 ---
        stage('Build and Push Backend Image') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                script {
                    def beImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BE_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    def beImageLatest = "ghcr.io/${env.GHCR_OWNER}/${env.BE_IMAGE_NAME}:latest"
                    echo "Building Backend image for main branch: ${beImageName}"
                    
                    docker.build(beImageName, './backtest_be_fast')
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        echo "Pushing Backend image to GHCR..."
                        docker.image(beImageName).push()
                        docker.image(beImageName).push('latest')
                    }
                }
            }
        }

        stage('Build and Push Frontend Image') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                script {
                    def feImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FE_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    def feImageLatest = "ghcr.io/${env.GHCR_OWNER}/${env.FE_IMAGE_NAME}:latest"
                    echo "Building Frontend image for main branch: ${feImageName}"
                    
                    docker.build(feImageName, './backtest_fe')
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        echo "Pushing Frontend image to GHCR..."
                        docker.image(feImageName).push()
                        docker.image(feImageName).push('latest')
                    }
                }
            }
        }

        stage('Deploy to Production (Local)') {
            when {
                expression { 
                    return env.GIT_BRANCH == 'origin/main' || 
                           env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH?.contains('main')
                }
            }
            steps {
                script {
                    def beImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BE_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    def feImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FE_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    echo "Deploying to local on-premise server"
                    
                    // Docker Registry 인증된 상태에서 배포 실행
                    docker.withRegistry("https://ghcr.io", 'github-token') {
                        sh """
                            cd ${env.DEPLOY_PATH}
                            git pull origin main || true
                            chmod +x deploy.sh
                            bash deploy.sh ${beImageName} ${feImageName}
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
