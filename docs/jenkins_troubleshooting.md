# Jenkins 유휴 상태 CPU 폭주 문제 해결기: ARD와 workspace cleanup의 함정

> **환경**: Ubuntu Server + Jenkins 2.516.2 + Docker CI/CD 파이프라인  
> **증상**: 빌드 작업이 없는데도 Jenkins가 지속적으로 CPU 300%+ 사용  
> **해결 시간**: 약 2시간 (진단 + 해결)

## 🚨 문제 발생: "빌드도 안 하는데 왜 이렇게 느려?"

### 발견된 증상들
- **Jenkins 프로세스 CPU 사용률**: 327.3% (멀티 스레드로 폭주)
- **메모리 사용량**: 2.3GB (평소 대비 높음)
- **스왑 사용량**: 2.2GB 
- **Load Average**: 3.24 (지속적 높은 부하)
- **서버 반응성**: 현저히 느려짐

```bash
# htop 결과
jenkins   3903207 327.3 31.2 5867704 2459920 ?  Ssl  9월14 256:32.08 java -jar jenkins.war
```

### Jenkins UI에서 확인된 알림
```
There are resources Jenkins was not able to dispose automatically.
```

Jenkins 관리 페이지의 **Asynchronous resource disposer** 섹션에 8개의 실패한 워크스페이스 정리 작업이 누적되어 있었습니다.

## 🔍 문제 원인 분석: ARD 백로그 폭주의 정체

### 1. 핵심 원인: node_modules 파일 권한 충돌

에러 로그를 자세히 살펴보니 다음과 같은 패턴이 반복되고 있었습니다:

```java
java.nio.file.FileSystemException: /var/lib/jenkins/workspace/Backtest_ws-cleanup_1757924683550/frontend/node_modules/css-tree/README.md: 명령을 허용하지 않음
    at java.base/sun.nio.fs.UnixFileAttributeViews$Posix.setPermissions(UnixFileAttributeViews.java:299)
    at jenkins.util.io.PathRemover.makeWritable(PathRemover.java:280)
    at jenkins.util.io.PathRemover.makeRemovable(PathRemover.java:253)
    ...
jenkins.util.io.CompositeIOException: Unable to delete '/var/lib/jenkins/workspace/Backtest_ws-cleanup_1757924683550'. Tried 3 times (of a maximum of 3) waiting 0.1 sec between attempts. (Discarded 37142 additional exceptions)
```

**37,142개의 추가 예외가 버려졌다**는 것이 핵심입니다. 하나의 cleanup 디렉터리에서 수만 번의 삭제 실패가 발생하고 있었습니다.

### 2. 왜 node_modules 파일이 삭제되지 않았나?

Docker 컨테이너에서 생성된 `node_modules` 파일들이 권한 문제로 Jenkins가 삭제할 수 없는 상태였습니다:

1. **Docker 빌드 과정**에서 프론트엔드 의존성 설치
2. **컨테이너 내부**에서 생성된 파일들의 소유권/권한 문제
3. **Jenkins 사용자**가 해당 파일들을 삭제할 권한 부족
4. **ARD(Asynchronous Resource Disposer)**가 무한 재시도

### 3. ARD 동작 원리와 문제점

Jenkins의 ARD는 백그라운드에서 워크스페이스를 정리하는 컴포넌트입니다:

```groovy
// 문제가 되었던 설정 (기본값)
cleanWs() // disableDeferredWipeout=false (기본값)
```

이 설정은 워크스페이스 정리를 **비동기적으로 ARD에 위임**합니다. 삭제 실패 시 계속해서 재시도하면서 CPU를 잡아먹는 구조였습니다.

## 🔧 해결 과정: 단계별 문제 해결

### 1단계: 문제 상황 확인 및 진단

```bash
# Jenkins 프로세스 상태 확인
ssh kyj@192.168.0.6 "ps aux | grep jenkins | grep -v grep"

# cleanup 디렉터리 개수 확인  
ssh kyj@192.168.0.6 "ls -la /var/lib/jenkins/workspace/ | grep cleanup"
```

**결과**: 8개의 `_ws-cleanup_*` 디렉터리가 삭제되지 않은 채로 남아있음을 확인

### 2단계: Jenkins 서비스 일시 중단

```bash
ssh kyj@192.168.0.6 "echo 'wara0503' | sudo -S systemctl stop jenkins"
```

ARD의 무한 재시도를 중단시키기 위해 Jenkins를 먼저 정지했습니다.

### 3단계: 문제 디렉터리 강제 삭제

```bash
# 권한 변경 후 강제 삭제
ssh kyj@192.168.0.6 "echo 'wara0503' | sudo -S bash -c 'chmod -R 777 /var/lib/jenkins/workspace/*_ws-cleanup_* && rm -rf /var/lib/jenkins/workspace/*_ws-cleanup_*'"

# 삭제 확인
ssh kyj@192.168.0.6 "ls -la /var/lib/jenkins/workspace/ | grep cleanup || echo 'No cleanup directories found'"
```

**결과**: 모든 cleanup 디렉터리가 성공적으로 삭제됨

### 4단계: Jenkins 서비스 재시작

```bash
ssh kyj@192.168.0.6 "echo 'wara0503' | sudo -S systemctl start jenkins"
```

### 5단계: 해결 확인

```bash
# CPU 사용률 재확인
ssh kyj@192.168.0.6 "ps aux | grep jenkins | grep -v grep"
```

**결과**: 
- **Before**: `jenkins 3903207 327.3 31.2 ...` (327% CPU)
- **After**: `jenkins 514252 21.8 6.5 ...` (21.8% CPU)

**93% CPU 사용률 감소!** 🎉

## 🛡️ 재발 방지책: 근본 원인 해결

### 1. Jenkinsfile 최적화 (이미 적용되어 있던 설정들)

우리의 Jenkinsfile은 다행히 이미 올바른 설정들이 적용되어 있었습니다:

```groovy
pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
        timestamps()
        disableConcurrentBuilds()  // ✅ 동시 빌드 방지
    }
    
    // ...
    
    post {
        always {
            sh 'docker system prune -f'
            cleanWs(deleteDirs: true, disableDeferredWipeout: true)  // ✅ 동기식 정리
        }
    }
}
```

#### 핵심 설정 해설:

1. **`disableConcurrentBuilds()`**: 같은 프로젝트의 동시 빌드를 방지하여 워크스페이스 경합 상황을 제거
2. **`disableDeferredWipeout: true`**: ARD에 위임하지 않고 즉시 동기적으로 워크스페이스 정리
3. **Docker 컨테이너 권한 설정**: `-u ${UID_J}:${GID_J}` 옵션으로 Jenkins 사용자 권한으로 실행

### 2. Docker 권한 문제 해결

```groovy
stage('Debug Environment') {
    steps {
        script {
            // Jenkins 사용자 UID/GID 캡처
            env.UID_J = sh(script: 'id -u', returnStdout: true).trim()
            env.GID_J = sh(script: 'id -g', returnStdout: true).trim()
        }
    }
}

// Docker 실행 시 Jenkins 사용자 권한 사용
stage('Collect JUnit Reports') {
    steps {
        script {
            sh '''
                # Jenkins 사용자 권한으로 Docker 컨테이너 실행
                docker run --rm -u ${UID_J}:${GID_J} \
                  -v "$PWD/frontend:/app" \
                  node:20-alpine sh -c "npm ci && npx vitest run"
            '''
        }
    }
}
```

이렇게 하면 Docker 컨테이너에서 생성되는 파일들이 Jenkins 사용자 소유가 되어 권한 문제를 방지합니다.

## 📊 해결 결과 요약

| 지표 | 문제 발생 시 | 해결 후 | 개선율 |
|------|--------------|---------|--------|
| **CPU 사용률** | 327.3% | 21.8% | **93% 감소** |
| **메모리 사용량** | 2.3GB | 512MB | **78% 감소** |
| **ARD 백로그** | 8개 cleanup 디렉터리 | 0개 | **100% 해결** |
| **Load Average** | 3.24 (높음) | 정상 범위 | **완전 안정화** |
| **서버 응답성** | 매우 느림 | 정상 | **완전 회복** |

## 🔍 학습한 교훈들

### 1. ARD의 이중날검
- **장점**: 빌드 후 워크스페이스를 비동기적으로 정리하여 빌드 시간 단축
- **단점**: 권한 문제 발생 시 무한 재시도로 시스템 리소스 고갈

### 2. Docker와 호스트 파일시스템의 권한 문제
- Docker 컨테이너의 기본 사용자는 root (UID=0)
- 호스트에 마운트된 볼륨에서 파일 생성 시 권한 불일치 발생 가능
- **해결책**: `-u $(id -u):$(id -g)` 옵션으로 호스트 사용자 권한 사용

### 3. Jenkins 모니터링의 중요성
- "There are resources Jenkins was not able to dispose automatically" 알림을 즉시 확인해야 함
- ARD 백로그 누적은 시간이 지날수록 더 심각한 성능 문제로 발전

## 🛠️ 예방 및 모니터링 방안

### 1. 정기적 헬스체크 스크립트

```bash
#!/bin/bash
# jenkins_health_check.sh

echo "=== Jenkins Health Check ==="
echo "1. Jenkins Process Status:"
ps aux | grep jenkins | grep -v grep

echo -e "\n2. ARD Cleanup Directory Count:"
sudo find /var/lib/jenkins/workspace -maxdepth 1 -name '*_ws-cleanup_*' -type d | wc -l

echo -e "\n3. Workspace Disk Usage:"
sudo du -sh /var/lib/jenkins/workspace

echo -e "\n4. System Load:"
uptime

# 알림 조건 (cleanup 디렉터리 3개 이상 시)
CLEANUP_COUNT=$(sudo find /var/lib/jenkins/workspace -maxdepth 1 -name '*_ws-cleanup_*' -type d | wc -l)
if [ $CLEANUP_COUNT -gt 2 ]; then
    echo "WARNING: Too many cleanup directories ($CLEANUP_COUNT). Investigation needed."
fi
```

### 2. 예방적 정리 자동화

```bash
#!/bin/bash
# jenkins_maintenance.sh (cron으로 주간 실행)

echo "Starting Jenkins workspace maintenance..."

# 1일 이상 된 cleanup 디렉터리 제거
sudo find /var/lib/jenkins/workspace -name "*_ws-cleanup_*" -type d -mtime +1 -exec rm -rf {} \; 2>/dev/null || true

# 디스크 사용량 정리
docker system prune -f

echo "Maintenance completed."
```

### 3. Jenkins 플러그인 개선사항

현재 콘솔 로그에서 확인된 경고들도 함께 해결:

```
[Checks API] No suitable checks publisher found.
BRANCH_NAME: null
GIT_BRANCH: null
```

**해결 방법**:
1. **GitHub Checks API 플러그인** 설치
2. **Git 환경변수 개선**을 위한 Jenkinsfile 수정

```groovy
stage('Debug Environment') {
    steps {
        script {
            env.UID_J = sh(script: 'id -u', returnStdout: true).trim()
            env.GID_J = sh(script: 'id -g', returnStdout: true).trim()
            
            // Git 정보 개선
            env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
            env.GIT_BRANCH_NAME = sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim()
            
            sh '''
                echo "=== Build Information ==="
                echo "BUILD_NUMBER: ${BUILD_NUMBER}"
                echo "GIT_COMMIT: ${GIT_COMMIT}"
                echo "GIT_COMMIT_SHORT: ${GIT_COMMIT_SHORT}" 
                echo "GIT_BRANCH_NAME: ${GIT_BRANCH_NAME}"
                echo "UID_J=${UID_J} GID_J=${GID_J}"
            '''
        }
    }
}
```

## 🚨 긴급 상황 대응 플레이북

향후 유사한 문제 발생 시 빠른 해결을 위한 원클릭 명령어들:

### 즉시 진정 (Jenkins 중단 없이)
```bash
# 1. ARD 백로그 확인
ssh kyj@192.168.0.6 "ls -la /var/lib/jenkins/workspace/ | grep cleanup | wc -l"

# 2. 핫 클린업 (서비스 중단 없음)
ssh kyj@192.168.0.6 "sudo -u jenkins find /var/lib/jenkins/workspace -maxdepth 1 -name '*_ws-cleanup_*' -exec rm -rf {} \;"
```

### 완전 해결 (서비스 재시작 포함)
```bash
# 1. Jenkins 중단
ssh kyj@192.168.0.6 "sudo systemctl stop jenkins"

# 2. 강제 정리
ssh kyj@192.168.0.6 "sudo chmod -R 777 /var/lib/jenkins/workspace/*_ws-cleanup_* && sudo rm -rf /var/lib/jenkins/workspace/*_ws-cleanup_*"

# 3. Jenkins 재시작
ssh kyj@192.168.0.6 "sudo systemctl start jenkins"

# 4. 상태 확인
ssh kyj@192.168.0.6 "ps aux | grep jenkins | grep -v grep"
```

### Jenkins Script Console 백로그 클리어
```groovy
// Jenkins 관리 → Script Console에서 실행
import org.jenkinsci.plugins.resourcedisposer.AsyncResourceDisposer
def d = AsyncResourceDisposer.get()
println "ARD backlog before: " + d.getBacklog().size()
d.getBacklog().clear()
d.save()
println "ARD backlog after: " + d.getBacklog().size()
```

## 💡 결론 및 앞으로의 개선점

이번 사건을 통해 학습한 핵심 사항들:

### ✅ **즉시 적용된 해결책**
1. **문제 디렉터리 강제 삭제**: CPU 사용률 327% → 21.8%로 극적 개선
2. **ARD 백로그 완전 정리**: 8개 → 0개로 모든 백로그 해소
3. **시스템 안정화**: 메모리 사용량 78% 감소, Load Average 정상화

### 🔧 **이미 적용되어 있던 좋은 설정들**
- `disableConcurrentBuilds()`: 동시 빌드 방지
- `cleanWs(deleteDirs: true, disableDeferredWipeout: true)`: 동기식 정리
- Docker 컨테이너 권한 설정: `-u ${UID_J}:${GID_J}`

### 📈 **추가 개선 계획**
1. **모니터링 자동화**: 주간 헬스체크 스크립트 cron 등록
2. **예방적 정리**: 정기적인 workspace maintenance 자동화
3. **알림 시스템**: CPU/메모리 임계치 초과 시 즉시 알림
4. **문서화**: 이번 트러블슈팅 경험을 팀 지식베이스에 공유

### 🎯 **핵심 메시지**
> **"Jenkins ARD 백로그는 시한폭탄이다."**  
> 소수의 권한 문제가 시스템 전체를 마비시킬 수 있으므로, 정기적인 모니터링과 예방적 정리가 필수다.

이번 경험을 통해 Jenkins CI/CD 파이프라인의 안정성과 Docker 컨테이너 권한 관리의 중요성을 다시 한번 깨달았습니다. 무엇보다 **"There are resources Jenkins was not able to dispose automatically"** 알림을 절대 무시해서는 안 된다는 교훈을 얻었습니다.

---

**참고 자료**:
- [Jenkins Workspace Cleanup Plugin 문서](https://plugins.jenkins.io/ws-cleanup/)
- [Docker 사용자 권한 매핑 가이드](https://docs.docker.com/engine/security/userns-remap/)
- [Jenkins ARD (Asynchronous Resource Disposer) 이해하기](https://www.jenkins.io/doc/developer/plugin-development/pipeline-integration/#resource-management)