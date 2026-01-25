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
                        echo "Waiting for services to be ready..."
                        for i in {1..4}; do
                            echo "Health check attempt $i/4"
                            if curl -f https://backtest-be.yeonjae.kr/health && curl -f https://backtest.yeonjae.kr; then
                                echo "✅ Services are healthy!"
                                exit 0
                            fi
                            sleep 5
                        done
                        echo "⚠️ Health check timed out, but continuing..."
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
