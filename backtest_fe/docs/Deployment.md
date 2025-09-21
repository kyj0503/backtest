# 배포 가이드

## 개요

이 문서는 백테스트 프론트엔드 애플리케이션의 배포 과정을 설명합니다.

## 배포 환경

### 개발 환경 (Development)

```bash
# 개발 서버 실행
npm run dev

# 접속 URL
http://localhost:5173
```

**특징:**
- HMR (Hot Module Replacement) 지원
- 소스맵 포함
- 디버깅 정보 포함
- API 프록시 설정

### 스테이징 환경 (Staging)

```bash
# 스테이징 빌드
npm run build:staging

# 미리보기
npm run preview
```

**특징:**
- 프로덕션과 동일한 빌드
- 테스트 데이터 사용
- 모니터링 도구 포함

### 프로덕션 환경 (Production)

```bash
# 프로덕션 빌드
npm run build

# 정적 파일 서빙
npm run preview
```

**특징:**
- 최적화된 번들
- 소스맵 제거
- 성능 모니터링 활성화

## Docker 배포

### 1. Dockerfile

```dockerfile
# Multi-stage build
FROM node:18-alpine AS builder

WORKDIR /app

# 의존성 파일 복사
COPY package*.json ./
RUN npm ci --only=production

# 소스 코드 복사
COPY . .

# 빌드
RUN npm run build

# Production stage
FROM nginx:alpine

# 빌드된 파일 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2. Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped

  # 백엔드 서비스들과 연결
  networks:
    - backtest-network

networks:
  backtest-network:
    external: true
```

### 3. Docker 빌드 및 실행

```bash
# 이미지 빌드
docker build -t backtest-frontend:latest .

# 컨테이너 실행
docker run -d \
  --name backtest-frontend \
  -p 80:80 \
  --env-file .env.production \
  backtest-frontend:latest

# Docker Compose 사용
docker compose -f docker-compose.prod.yml up -d
```

## Nginx 설정

### 1. 기본 설정 (nginx.conf)

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # 로그 설정
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # 성능 최적화
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip 압축
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rss+xml
        application/vnd.geo+json
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        font/opentype
        image/bmp
        image/svg+xml
        image/x-icon
        text/cache-manifest
        text/css
        text/plain
        text/vcard
        text/vnd.rim.location.xloc
        text/vtt
        text/x-component
        text/x-cross-domain-policy;

    server {
        listen 80;
        server_name localhost;

        root /usr/share/nginx/html;
        index index.html;

        # SPA 라우팅 지원
        location / {
            try_files $uri $uri/ /index.html;
        }

        # 정적 자산 캐싱
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API 프록시
        location /api/ {
            proxy_pass http://backend:8080/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 보안 헤더
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy "strict-origin-when-cross-origin";
    }
}
```

### 2. HTTPS 설정

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    # SSL 최적화
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # HTTP에서 HTTPS로 리다이렉트
    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    }

    # 나머지 설정은 위와 동일
}
```

## CI/CD 파이프라인

### 1. GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run type check
      run: npm run type-check
    
    - name: Run linting
      run: npm run lint
    
    - name: Run tests
      run: npm run test:run
    
    - name: Build
      run: npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          yourusername/backtest-frontend:latest
          yourusername/backtest-frontend:${{ github.sha }}
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.PRIVATE_KEY }}
        script: |
          docker pull yourusername/backtest-frontend:latest
          docker stop backtest-frontend || true
          docker rm backtest-frontend || true
          docker run -d \
            --name backtest-frontend \
            -p 80:80 \
            --env-file /home/deploy/.env.production \
            yourusername/backtest-frontend:latest
```

### 2. Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'backtest-frontend'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'npm ci'
            }
        }
        
        stage('Run Tests') {
            parallel {
                stage('Type Check') {
                    steps {
                        sh 'npm run type-check'
                    }
                }
                stage('Lint') {
                    steps {
                        sh 'npm run lint'
                    }
                }
                stage('Unit Tests') {
                    steps {
                        sh 'npm run test:run'
                    }
                }
            }
        }
        
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
        
        stage('Docker Build') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push('latest')
                    }
                }
                
                sh '''
                    ssh deploy@production-server "
                        docker pull ${DOCKER_IMAGE}:latest &&
                        docker stop backtest-frontend || true &&
                        docker rm backtest-frontend || true &&
                        docker run -d --name backtest-frontend -p 80:80 ${DOCKER_IMAGE}:latest
                    "
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        failure {
            mail to: 'dev-team@company.com',
                 subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                 body: "Build failed. Check console output at ${env.BUILD_URL}"
        }
    }
}
```

## 환경 변수 관리

### 1. 환경별 설정 파일

```bash
# .env.development
VITE_API_URL=http://localhost:8080/api
VITE_ENVIRONMENT=development
VITE_DEBUG=true

# .env.staging
VITE_API_URL=https://staging-api.backtest.com/api
VITE_ENVIRONMENT=staging
VITE_DEBUG=false

# .env.production
VITE_API_URL=https://api.backtest.com/api
VITE_ENVIRONMENT=production
VITE_DEBUG=false
VITE_ANALYTICS_ID=GA_TRACKING_ID
```

### 2. 런타임 환경 변수

```typescript
// src/shared/config/index.ts
interface Config {
  apiUrl: string;
  environment: 'development' | 'staging' | 'production';
  debug: boolean;
  analyticsId?: string;
}

const config: Config = {
  apiUrl: import.meta.env.VITE_API_URL || '/api',
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  debug: import.meta.env.VITE_DEBUG === 'true',
  analyticsId: import.meta.env.VITE_ANALYTICS_ID,
};

export default config;
```

## 모니터링 및 로깅

### 1. 애플리케이션 모니터링

```typescript
// src/shared/utils/monitoring.ts
interface MetricData {
  name: string;
  value: number;
  tags?: Record<string, string>;
}

class MonitoringService {
  private static instance: MonitoringService;

  static getInstance(): MonitoringService {
    if (!MonitoringService.instance) {
      MonitoringService.instance = new MonitoringService();
    }
    return MonitoringService.instance;
  }

  // 성능 메트릭 수집
  trackPageLoad(page: string, loadTime: number) {
    this.sendMetric({
      name: 'page_load_time',
      value: loadTime,
      tags: { page }
    });
  }

  // 에러 추적
  trackError(error: Error, context?: Record<string, any>) {
    this.sendMetric({
      name: 'frontend_error',
      value: 1,
      tags: {
        error_type: error.name,
        error_message: error.message,
        ...context
      }
    });
  }

  // 사용자 액션 추적
  trackUserAction(action: string, data?: Record<string, any>) {
    this.sendMetric({
      name: 'user_action',
      value: 1,
      tags: { action, ...data }
    });
  }

  private sendMetric(data: MetricData) {
    if (config.environment === 'production') {
      // 프로덕션에서는 실제 모니터링 서비스로 전송
      fetch('/api/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).catch(console.error);
    }
  }
}

export const monitoring = MonitoringService.getInstance();
```

### 2. 에러 경계에서 모니터링

```typescript
// src/shared/components/ErrorBoundary.tsx
export class ErrorBoundary extends Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    monitoring.trackError(error, {
      component_stack: errorInfo.componentStack,
      error_boundary: 'global'
    });
  }
}
```

## 성능 최적화

### 1. 빌드 최적화

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // 벤더 청크 분리
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-slot', 'class-variance-authority'],
          utils: ['date-fns', 'clsx', 'tailwind-merge']
        }
      }
    },
    // 최적화 옵션
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
});
```

### 2. 캐싱 전략

```nginx
# Nginx 캐싱 설정
location ~* \.(js|css)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header ETag "";
}

location ~* \.(png|jpg|jpeg|gif|ico|svg)$ {
    expires 6M;
    add_header Cache-Control "public";
}

location /index.html {
    expires -1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

## 보안 설정

### 1. CSP (Content Security Policy)

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.backtest.com;
  font-src 'self';
">
```

### 2. 환경 변수 보안

```bash
# 민감한 정보는 별도 시스템에서 관리
export VITE_API_KEY=$(vault kv get -field=api_key secret/backtest/frontend)
export VITE_DATABASE_URL=$(aws ssm get-parameter --name "/backtest/db-url" --query "Parameter.Value" --output text)
```

## 롤백 전략

### 1. Blue-Green 배포

```bash
# Blue 환경 (현재 프로덕션)
docker run -d --name backtest-frontend-blue -p 80:80 backtest-frontend:v1.0.0

# Green 환경 (새 버전)
docker run -d --name backtest-frontend-green -p 8080:80 backtest-frontend:v1.1.0

# 트래픽 전환 (로드 밸런서 설정)
# 문제 발생 시 즉시 Blue로 롤백
```

### 2. 자동 롤백 스크립트

```bash
#!/bin/bash
# rollback.sh

CURRENT_VERSION=$(docker ps --format "table {{.Image}}" | grep backtest-frontend | head -1 | cut -d: -f2)
PREVIOUS_VERSION=$(docker images --format "table {{.Tag}}" | grep -v latest | grep -v $CURRENT_VERSION | head -1)

echo "Rolling back from $CURRENT_VERSION to $PREVIOUS_VERSION"

docker stop backtest-frontend
docker rm backtest-frontend
docker run -d --name backtest-frontend -p 80:80 backtest-frontend:$PREVIOUS_VERSION

echo "Rollback completed"
```

이 가이드를 통해 안전하고 효율적인 배포를 수행할 수 있습니다.