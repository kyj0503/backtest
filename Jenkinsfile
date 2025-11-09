pipeline {
    agent any

    environment {
        // 프로젝트 설정
        PROJECT_NAME = 'backtest'
        DEPLOY_DIR = '/home/jenkins/backtest'

        // Docker 설정
        COMPOSE_FILE = 'compose.yaml'
        COMPOSE_PROJECT_NAME = 'backtest-prod'

        // 알림 설정 (선택사항)
        SLACK_CHANNEL = '#deployments'
    }

    options {
        // 빌드 기록 보관 설정
        buildDiscarder(logRotator(numToKeepStr: '10'))

        // 타임아웃 설정 (15분)
        timeout(time: 15, unit: 'MINUTES')

        // 동시 빌드 방지
        disableConcurrentBuilds()
    }

    stages {
        stage('Preparation') {
            steps {
                script {
                    echo "=========================================="
                    echo "프로젝트: ${PROJECT_NAME}"
                    echo "브랜치: ${env.GIT_BRANCH}"
                    echo "빌드 번호: ${env.BUILD_NUMBER}"
                    echo "=========================================="
                }
            }
        }

        stage('Checkout') {
            steps {
                echo '소스 코드 체크아웃...'
                checkout scm

                script {
                    // Git 정보 출력
                    sh 'git log -1 --pretty=format:"%h - %an: %s"'
                }
            }
        }

        stage('Environment Check') {
            steps {
                echo '환경 검증 중...'
                sh '''
                    echo "Docker 버전:"
                    docker --version

                    echo "Docker Compose 버전:"
                    docker compose version

                    echo ".env 파일 확인:"
                    if [ -f .env ]; then
                        echo ".env 파일이 존재합니다."
                    else
                        echo "경고: .env 파일이 없습니다!"
                        exit 1
                    fi
                '''
            }
        }

        stage('Stop Old Containers') {
            steps {
                echo '기존 컨테이너 중지 및 제거...'
                sh '''
                    docker compose -f ${COMPOSE_FILE} down || true

                    # 고아 컨테이너 정리
                    docker ps -a | grep ${PROJECT_NAME} | awk '{print $1}' | xargs -r docker rm -f || true
                '''
            }
        }

        stage('Build Images') {
            steps {
                echo 'Docker 이미지 빌드...'
                sh '''
                    # 빌드 캐시를 사용하여 이미지 빌드
                    docker compose -f ${COMPOSE_FILE} build --no-cache

                    # 빌드된 이미지 확인
                    echo "빌드된 이미지 목록:"
                    docker images | grep ${PROJECT_NAME}
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo '새 컨테이너 배포...'
                sh '''
                    # 컨테이너 시작
                    docker compose -f ${COMPOSE_FILE} up -d

                    # 컨테이너 상태 확인
                    echo "실행 중인 컨테이너:"
                    docker compose -f ${COMPOSE_FILE} ps
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo '서비스 상태 확인...'
                script {
                    // Backend 헬스체크 (최대 60초 대기)
                    def backendHealthy = false
                    for (int i = 0; i < 12; i++) {
                        try {
                            sh 'curl -f http://localhost:8000/api/v1/health || exit 1'
                            backendHealthy = true
                            echo 'Backend 서비스가 정상 작동 중입니다.'
                            break
                        } catch (Exception e) {
                            echo "Backend 헬스체크 대기 중... (${(i+1)*5}초)"
                            sleep(5)
                        }
                    }

                    if (!backendHealthy) {
                        error 'Backend 서비스가 정상적으로 시작되지 않았습니다!'
                    }

                    // Frontend 헬스체크 (포트 확인)
                    sh 'curl -f http://localhost:5173 || exit 1'
                    echo 'Frontend 서비스가 정상 작동 중입니다.'
                }
            }
        }

        stage('Cleanup') {
            steps {
                echo '사용하지 않는 Docker 리소스 정리...'
                sh '''
                    # Dangling 이미지 제거
                    docker image prune -f

                    # 사용하지 않는 볼륨 제거 (주의: 데이터 손실 가능)
                    # docker volume prune -f

                    echo "현재 디스크 사용량:"
                    df -h
                '''
            }
        }
    }

    post {
        success {
            echo '=========================================='
            echo '배포 성공!'
            echo '=========================================='

            script {
                // 서비스 URL 출력
                sh '''
                    echo "서비스 접속 정보:"
                    echo "- Frontend: http://$(hostname -I | awk '{print $1}'):5173"
                    echo "- Backend API: http://$(hostname -I | awk '{print $1}'):8000"
                    echo "- API Docs: http://$(hostname -I | awk '{print $1}'):8000/api/v1/docs"
                '''
            }

            // Slack 알림 (선택사항 - Slack 플러그인 설치 필요)
            // slackSend(
            //     channel: env.SLACK_CHANNEL,
            //     color: 'good',
            //     message: "배포 성공: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            // )
        }

        failure {
            echo '=========================================='
            echo '배포 실패!'
            echo '=========================================='

            script {
                // 실패 시 로그 출력
                sh '''
                    echo "컨테이너 로그:"
                    docker compose -f ${COMPOSE_FILE} logs --tail=50 || true
                '''
            }

            // Slack 알림 (선택사항)
            // slackSend(
            //     channel: env.SLACK_CHANNEL,
            //     color: 'danger',
            //     message: "배포 실패: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            // )
        }

        always {
            echo '파이프라인 종료'

            // 워크스페이스 정리 (선택사항)
            // cleanWs()
        }
    }
}
