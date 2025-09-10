# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Python 의존성 먼저 설치 (uv 기반)
COPY requirements.txt .
# uv 설치 (Rust 기반, 공식 스크립트 사용) 및 PATH 반영
RUN curl -Ls https://astral.sh/uv/install.sh | sh \
    && cp /root/.local/bin/uv /usr/local/bin/uv
# requirements.txt 기반 패키지 설치
RUN uv pip install --system -r requirements.txt
# 백테스팅 라이브러리 별도 설치
RUN uv pip install --system backtesting

# 애플리케이션 코드 복사
COPY app ./app
COPY tests ./tests
COPY run_server.py .

# 빌드 인자들
ARG RUN_TESTS=false
ARG IMAGE_TAG=latest
ARG PYTEST_ADDOPTS=""

# 환경변수로 설정
ENV IMAGE_TAG=${IMAGE_TAG}
ENV IMAGE_NAME=backtest-backend

# 테스트 실행 (빌드 인자로 제어 가능)
RUN if [ "$RUN_TESTS" = "true" ] ; then python -m pytest tests/ -v --tb=short $PYTEST_ADDOPTS ; fi

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 