# nginx-gateway DNS 캐싱으로 인한 502 Bad Gateway

- **발생일**: 2026-02-06
- **영향 범위**: OCI 서버 전역 (nginx-gateway 뒤의 모든 서비스)
- **상태**: 미해결 — home-server 리포지토리에서 nginx-gateway 설정 수정 필요

## 증상

backtest 서비스 배포(Jenkins CI/CD) 후 `https://backtest.yeonjae.kr` 접속 시 **502 Bad Gateway** 발생.
`backtest-be`, `backtest-fe` 컨테이너는 정상 구동 중(healthy).

## 근본 원인

```
browser → nginx-gateway (11일 전 시작, 구 IP 캐싱) → backtest-fe (재생성, 새 IP) = 502
```

nginx는 시작 시점에 `proxy_pass` upstream 호스트의 DNS를 resolve하고 **영구 캐싱**한다.
Jenkins 파이프라인이 `backtest-be`, `backtest-fe` 컨테이너만 재생성하면 Docker 내부 IP가 변경되지만,
`nginx-gateway`는 재시작하지 않으므로 구 IP로 계속 요청을 보내 502가 발생한다.

### 영향받는 서비스 (전역)

nginx-gateway 뒤의 **모든 서비스**가 재배포 시 동일한 문제 발생 가능:

| 서비스 | 컨테이너명 |
|---|---|
| backtest-fe | backtest-fe |
| backtest-be | backtest-be |
| jandi-plan | jandi-plan |
| jandi-ide | jandi-ide |
| jandi-band-py | jandi-band-py |
| jandi-band | jandi-band |

## 수동 즉시 복구

502 발생 시 아래 명령으로 복구 가능:

```bash
docker exec nginx-gateway nginx -s reload
```

`nginx -s reload`는 프로세스 재시작 없이 설정을 다시 로드하여 DNS를 재resolve한다.
기존 연결(다른 서비스)이 끊기지 않는 안전한 방식.

## 해결 방법

이 문제는 인프라 레벨이므로 각 프로젝트 Jenkinsfile이 아닌 **home-server 리포지토리**에서 해결해야 한다.
Jenkinsfile마다 `nginx -s reload`를 넣는 방식은 모든 프로젝트가 각각 알아서 추가해야 하므로 부적절.

nginx-gateway 설정에서 **동적 DNS resolution**을 활성화하면, 어떤 서비스를 재배포하든
nginx가 자동으로 새 IP를 resolve하여 502가 발생하지 않는다.

### 수정 대상

OCI 서버 `home-server` 리포지토리 내 nginx-gateway 설정 파일

**변경 전** (일반적인 패턴):
```nginx
upstream backtest-fe {
    server backtest-fe:80;
}

location / {
    proxy_pass http://backtest-fe;
}
```

**변경 후**:
```nginx
# Docker 내장 DNS를 resolver로 지정 (TTL 30초)
resolver 127.0.0.11 valid=30s ipv6=off;

location / {
    # 변수를 사용해야 nginx가 매 요청마다 DNS resolve 수행
    set $upstream_backtest_fe http://backtest-fe:80;
    proxy_pass $upstream_backtest_fe;
}
```

핵심 포인트:
1. `resolver 127.0.0.11` - Docker 내장 DNS 사용
2. `valid=30s` - DNS 캐시 TTL을 30초로 제한
3. `set $upstream` + `proxy_pass $variable` - 변수 사용 시에만 동적 resolve 동작
4. **모든 `proxy_pass` 블록**에 동일 패턴 적용 필요

### 확인 절차

1. OCI 서버에서 nginx-gateway 설정 파일 확인
2. 위 패턴으로 수정
3. `docker exec nginx-gateway nginx -t` 로 문법 검증
4. `docker exec nginx-gateway nginx -s reload` 로 적용
5. 아무 서비스 재배포하여 502 발생하지 않는지 확인

## 함께 발견된 문제: WSL2 Docker 유휴 CPU

같은 세션에서 발견한 별도 이슈. `compose.dev.yaml`의 `uvicorn --reload`가 WSL2 바인드 마운트에서
watchfiles 폴링 모드로 동작하여 유휴 시 CPU 25% 소모.

**해결**: `WATCHFILES_FORCE_POLLING=false` 환경변수 + `--reload-dir app` 추가 (CPU 0.2%로 감소).
해당 수정은 개발 환경(`compose.dev.yaml`)에만 적용되며 프로덕션에 영향 없음.
