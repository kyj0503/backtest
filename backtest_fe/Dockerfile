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

# Stage 3: 의존성 취약점 감사 (CI 전용)
#
# test 스테이지와 마찬가지로 최종 이미지의 의존 경로 밖이라 `docker build`
# (타깃 미지정)로는 실행되지 않는다. CI가 `--target audit`으로 호출한다.
#
# 바인드 마운트(-v)가 아니라 빌드 컨텍스트로 파일을 받는 이유: Jenkins가
# 컨테이너 안에서 호스트 Docker 데몬에 붙어 sibling 컨테이너를 띄우는 구조라,
# -v의 소스 경로가 "Jenkins 컨테이너 안의 경로"가 아니라 "호스트 경로"로
# 해석되어 파일을 찾지 못한다. 빌드 컨텍스트는 데몬으로 스트리밍되므로
# 그 문제가 없다 (Quality Gate가 동작하는 것과 같은 이유).
FROM deps AS audit

# npm audit는 어드바이저리 단위 allowlist를 지원하지 않으므로 JSON을 걸러낸다.
COPY scripts/npm-audit-filter.js /filter.js

# 업그레이드로 고칠 수 없고 이 앱에서 도달 불가능한 어드바이저리 ID 목록.
# 근거와 재검토 조건은 scripts/audit-deps.sh에 적혀 있다.
ARG NPM_AUDIT_ALLOWLIST=""

# npm audit는 취약점이 있으면 비정상 종료하므로 `|| true`로 JSON을 확보한 뒤
# 필터가 판단한다. 필터가 종료 코드를 결정한다.
RUN npm audit --audit-level=high --json > /tmp/audit.json 2>/dev/null || true; \
    node /filter.js /tmp/audit.json "$NPM_AUDIT_ALLOWLIST"

# Stage 4: Build the React application
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
