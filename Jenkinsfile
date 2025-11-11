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
            }
        }

        // --- Main 브랜치 전용 스테이지 ---
        stage('Build and Push Backend Image') {
            when { branch 'main' }
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
            when { branch 'main' }
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
            when { branch 'main' }
            steps {
                script {
                    def beImageName = "ghcr.io/${env.GHCR_OWNER}/${env.BE_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    def feImageName = "ghcr.io/${env.GHCR_OWNER}/${env.FE_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    echo "Deploying to local on-premise server"
                    sh """
                        bash ${env.DEPLOY_PATH}/deploy.sh ${beImageName} ${feImageName}
                    """
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
