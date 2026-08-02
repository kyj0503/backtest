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

        stage('Quality Gate') {
            steps {
                script {
                    // 각 Dockerfile의 test 스테이지를 돌린다.
                    // - FE: lint / type-check / type-check:test / vitest
                    // - BE: pytest tests/unit (DB 불필요)
                    // 실패하면 이미지 빌드와 배포에 도달하지 못한다.
                    //
                    // test 스테이지는 최종 이미지의 의존 경로에 없으므로 --target으로
                    // 명시해야 실행된다. 결과 이미지는 사용하지 않으므로 cacheonly로
                    // export를 생략한다. deps/base 레이어 캐시는 뒤이은 이미지
                    // 빌드가 재사용하므로 의존성 설치가 두 번 돌지 않는다.
                    parallel(
                        'Frontend': {
                            sh 'docker build --target test --output=type=cacheonly ./backtest_fe'
                        },
                        'Backend': {
                            sh 'docker build --target test --output=type=cacheonly ./backtest_be_fast'
                        }
                    )
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
                        /opt/home-server/scripts/deploy-app.sh backtest-be
                        /opt/home-server/scripts/deploy-app.sh backtest-fe
                        sleep 10
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
                        for i in 1 2 3 4 5 6 7 8 9 10; do
                            echo "Health check attempt $i/10"
                            BE_OK=false
                            FE_OK=false
                            if curl -sf https://backtest-be.yeonjae.kr/health > /dev/null 2>&1; then
                                BE_OK=true
                            fi
                            if curl -sf https://backtest.yeonjae.kr > /dev/null 2>&1; then
                                FE_OK=true
                            fi
                            echo "  BE=$BE_OK, FE=$FE_OK"
                            if [ "$BE_OK" = true ] && [ "$FE_OK" = true ]; then
                                echo "✅ All services are healthy!"
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
