# Jenkins Workspace Cleanup 장애 사례

이 문서는 Jenkins가 유휴 상태에서도 높은 CPU를 소비했던 사례를 정리한 것입니다. 문제 재발 시 동일 절차를 참고하세요.

## 환경
- Ubuntu Server
- Jenkins 2.516.2
- Docker 기반 CI 파이프라인 (프론트/백엔드 이미지 빌드)

## 증상
- Jenkins Java 프로세스가 지속적으로 CPU 300% 이상 사용
- 메모리와 스왑 사용량이 평소 대비 크게 증가
- Jenkins UI에 `There are resources Jenkins was not able to dispose automatically.` 경고 표시
- `workspace/*_ws-cleanup_*` 디렉터리가 반복적으로 남음

## 원인 분석
1. Docker 컨테이너에서 생성된 `frontend/node_modules` 디렉터리의 권한이 Jenkins 사용자와 달라 삭제에 실패
2. `cleanWs()` 기본 설정(`disableDeferredWipeout=false`)으로 인해 Asynchronous Resource Disposer(ARD)가 권한 오류가 반복되는 워크스페이스를 계속 재시도
3. 하나의 cleanup 작업에서 수만 건의 삭제 예외가 발생하며 CPU를 소모

## 해결 절차
1. Jenkins 서비스를 일시 중단
2. 권한 문제로 남은 `_ws-cleanup_*` 디렉터리의 소유권과 권한을 Jenkins 사용자에 맞게 조정 후 삭제
3. Jenkins 서비스 재시작
4. CPU 사용률과 cleanup 디렉터리가 정상적으로 정리되었는지 확인

## 재발 방지
- Jenkins 파이프라인의 `cleanWs` 호출 시 `disableDeferredWipeout: true`를 설정하여 동기 삭제를 강제
- Docker 실행 시 `-u $(id -u):$(id -g)` 형태로 Jenkins 사용자 권한을 명시해 컨테이너가 생성하는 파일의 소유권을 맞춤
- 정기적으로 `workspace` 디렉터리를 점검하고 필요 시 수동 정리를 수행

필요한 경우 `docker system prune -f` 등 추가 정리 작업도 함께 수행합니다.
