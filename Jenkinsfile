pipeline {
    agent any

    // P3-08: 파이프라인 전체에 상한을 둔다. 이게 없으면 예를 들어 Deploy
    // 단계의 외부 스크립트나 Health Check의 curl이 멎어도 executor를
    // 무한정 붙잡는다. 45분은 BE/FE 이미지 빌드(네이티브 확장 컴파일 포함)
    // + push + health check 재시도(최대 ~50초)를 넉넉히 덮는 값이다 —
    // 정상 실행이 이 근처까지 걸리면 시간을 늘리되, 그 전에 왜 느려졌는지
    // 먼저 확인할 것.
    options {
        timeout(time: 45, unit: 'MINUTES')
    }

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
                    //
                    // P3-08 (junit 아카이빙): 의도적으로 붙이지 않았다. pytest/vitest가
                    // JUnit XML을 쓰게 하는 것 자체는 Dockerfile의 RUN 커맨드에 플래그를
                    // 추가하는 정도로 가능하지만, --output=type=cacheonly는 어떤 파일도
                    // 내보내지 않고, 테스트가 실패하면 그 RUN 레이어 자체가 실패해
                    // BuildKit이 이후 "결과만 복사하는 스테이지"에 도달하지 못한다 —
                    // 즉 정작 결과를 보고 싶은 실패 케이스에서 XML을 꺼낼 방법이 없다.
                    // 이를 해결하려면 테스트 실행을 Docker 빌드 레이어 밖으로 빼서
                    // (예: 이미지를 빌드한 뒤 별도로 `docker run`) exit code와 아티팩트를
                    // 각각 다루는 구조 변경이 필요한데, 이는 "품질 게이트가 여전히
                    // 실패를 막는다"를 깨뜨릴 위험이 있는 구조 변경이라 이번 범위에서는
                    // 보류했다 (b4-E-report.md 참고).
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
                    // P2-26: 지금까지는 태그 인자 없이 호출해 배포 스크립트가
                    // 사실상 :latest를 추적했다 — 롤백 지점이 없다는 뜻이다.
                    // ${env.BUILD_NUMBER}를 두 번째 인자로 넘겨 불변 태그로
                    // 배포하도록 바꾼다 (Build/Push 단계에서 이미
                    // ${beImageName}:${env.BUILD_NUMBER} / ${feImageName}:${env.BUILD_NUMBER}
                    // 로 push해 뒀으므로 이 태그는 항상 존재한다).
                    //
                    // 이 저장소 밖에 있는 /opt/home-server/scripts/deploy-app.sh는
                    // 이 리포에서 보이지도, 여기서 수정되지도 않는다 — "$2"(태그)를
                    // 읽어서 실제로 그 태그의 이미지를 pull/기동하도록 운영 쪽에서
                    // 별도로 갱신해야 이 변경이 의미가 있다 (필수 후속 조치, README/
                    // 배포 문서에도 기록할 것). 스크립트의 현재 인자 파싱 방식을
                    // 이 리포에서 확인할 수 없으므로, 여분의 위치 인자를 그냥
                    // 무시하는지 아니면 인자 개수를 엄격히 검사해 실패하는지도
                    // 알 수 없다 — 즉 스크립트를 갱신하기 전까지는 이 변경이
                    // 배포 자체를 깨뜨리지 않는다고 보장할 수 없다. 운영 쪽 갱신과
                    // 함께(또는 스테이징에서 먼저) 검증할 것.
                    sh """
                        /opt/home-server/scripts/deploy-app.sh backtest-be ${env.BUILD_NUMBER}
                        /opt/home-server/scripts/deploy-app.sh backtest-fe ${env.BUILD_NUMBER}
                        sleep 10
                        echo "✅ Backtest deployment completed!"
                    """
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
                        echo "❌ Health check failed after 10 attempts"
                        exit 1
                    '''
                }
            }
        }
    }

    post {
        always {
            // P3-08: GHCR 자격증명이 에이전트에 남아있지 않도록 항상 로그아웃한다
            // (Login GHCR 단계 전에 파이프라인이 실패해 애초에 로그인한 적이
            // 없어도 안전하게 지나가도록 `|| true`).
            sh 'docker logout ghcr.io || true'
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
