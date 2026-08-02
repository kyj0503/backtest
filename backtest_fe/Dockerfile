# syntax=docker/dockerfile:1
# Stage 1: Install dependencies (build/test 공통 기반)
FROM node:20.19.0-alpine AS deps

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
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# When the container starts, Nginx will serve the files from /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
