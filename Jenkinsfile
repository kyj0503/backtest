pipeline {
    agent any

    environment {
        GHCR_OWNER = 'kyj0503'
        BE_IMAGE_NAME = 'backtest-be'
        FE_IMAGE_NAME = 'backtest-fe'
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
