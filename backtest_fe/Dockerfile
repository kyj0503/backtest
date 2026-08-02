# syntax=docker/dockerfile:1
# Stage 1: Install dependencies (build/test 공통 기반)
# P3-05: node:20.19.0-alpine은 Node 20.19.0 고정 태그로 이미 EOL(2026-04-30)이
# 지났다. package.json의 engines.node(">=20.0.0")는 22에도 그대로 만족되므로
# package.json은 건드리지 않았다.
FROM node:22-alpine AS deps

WORKDIR /app

# Copy only package manifests first to leverage Docker layer caching
COPY package*.json ./

# Install dependencies (npm 캐시 마운트로 재다운로드 방지)
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then \
			npm ci --no-audit --prefer-offline --no-fund; \
		else \
			npm install --no-audit --prefer-offline --no-fund; \
		fi

# Stage 2: 품질 게이트
#
# 최종 이미지의 의존 경로에 없으므로 `docker build`(타깃 미지정)로는 실행되지
# 않는다. CI가 `docker build --target test`로 명시적으로 호출한다.
# deps 레이어를 재사용하므로 npm ci가 다시 돌지 않는다.
FROM deps AS test

COPY . .

# 개별 RUN으로 분리해 어느 단계에서 깨졌는지 로그에서 바로 보이게 한다.
RUN npm run lint
RUN npm run type-check
RUN npm run type-check:test
RUN npm run test:run

# Stage 3: Build the React application
FROM deps AS build

# Copy rest of sources
COPY . .

# Build production assets
RUN npm run build

# Stage 4: Serve the application with Nginx
# P3-05: stable-alpine은 부동 태그라 재빌드마다 다른 nginx/Alpine 버전을 받을 수
# 있다. 이 락은 이 작업 시점에 stable-alpine이 가리키던 것과 동일한 이미지다
# (다이제스트 sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46로
# 확인) — 버전을 바꾸지 않고 태그만 고정했다.
FROM nginx:1.30.4-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# When the container starts, Nginx will serve the files from /usr/share/nginx/html
EXPOSE 80

# P3-04: nginx.prod.conf가 서빙하는 /health를 그대로 찌른다 (BE Dockerfile의
# HEALTHCHECK와 동일한 스타일). nginx:alpine 이미지에 curl이 포함되어 있음을
# 확인했다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
