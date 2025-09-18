# Backtesting Frontend — Docker Compose

이 리포지토리는 Vite + React + TypeScript 기반 프론트엔드 애플리케이션입니다. 로컬에서 Docker Compose(`compose.yaml`)를 이용해 개발 또는 프로덕션 환경으로 실행할 수 있습니다.

## 요구 사항
- Docker (버전 20.x 권장)
- Docker Compose
- Node는 로컬에 없어도 되지만 이미 로컬에 있을 경우 권장 버전: Node >= 16

## 파일
- `compose.yaml` — 개발(`frontend-dev`)과 프로덕션(`frontend-prod`) 서비스를 정의합니다.
- `Dockerfile` — 프로덕션 빌드(멀티 스테이지) 및 Nginx 서빙 설정

## 실행 방법
### 개발 (핫 리로드)
이 모드는 컨테이너 내부에서 `npm install` 후 로컬 소스 바인드마운트로 실행합니다. 수정 시 Vite의 핫 리로드가 동작합니다.

```bash
cd /path/to/repo
# Compose 파일을 명시적으로 지정
docker compose -f compose.yaml up --build frontend-dev
```

브라우저에서: `http://localhost:5173`

### 프로덕션 (빌드 후 Nginx 서빙)
프로덕션 이미지를 빌드하고 Nginx로 정적 파일을 서빙합니다.

```bash
cd /path/to/repo
docker compose -f compose.yaml up --build frontend-prod
```

브라우저에서: `http://localhost:8080`

## 환경 변수
- `API_PROXY_TARGET` (옵션) — 개발 시 Vite의 `/api` 프록시가 포워딩할 백엔드 주소. 예: `http://host.docker.internal:8001` 또는 백엔드 컨테이너 이름.

예: Docker Compose 환경에 설정하려면 `compose.yaml`의 `environment` 블록에 추가하세요.

### 여러 리포지토리(백엔드)를 연결하는 권장 패턴 (외부 네트워크)
여러 레포지토리에서 독립적으로 Compose 파일을 유지하면서 컨테이너 간 통신을 하려면 외부 네트워크를 만들어 양쪽 Compose에서 공유하는 것이 안전합니다.

1. 네트워크 생성 (한 번만 실행):

```bash
docker network create backtest-network
```

2. 프론트엔드(`compose.yaml`)에서 외부 네트워크 사용 예시(이 리포지토리는 이미 설정됨):

```yaml
services:
	frontend-dev:
		...
		environment:
			- API_PROXY_TARGET=http://backend:8001
		networks:
			- backtest-net

networks:
	backtest-net:
		external: true
		name: backtest-network
```

3. 백엔드 레포지토리의 `compose.yaml`에서도 동일한 외부 네트워크를 선언:

```yaml
services:
	backend:
		image: my-backend:dev
		ports:
			- "8001:8001" # 호스트 접근이 필요하면 설정
		networks:
			- backtest-net

networks:
	backtest-net:
		external: true
		name: backtest-network
```

이제 프론트엔드 컨테이너에서 `http://backend:8001`로 백엔드에 접근할 수 있습니다. 개발 중 Vite 프록시(`API_PROXY_TARGET`)를 백엔드 서비스 이름으로 설정하면 CORS 문제를 줄일 수 있습니다.

## 추가 팁
- 개발 중 로컬 에디터에서 의존성 문제(타입 선언 등)가 보이면 로컬에서 `npm install`을 수행하거나 `package-lock.json`을 확인하세요.
- 이미지 캐시를 재사용하려면 불필요한 `--no-cache` 옵션은 피하세요.

문의 사항이나 추가 커스터마이징(예: `.env`통합, 서로 다른 포트, 백엔드 컨테이너 연결)을 원하시면 알려주세요.
