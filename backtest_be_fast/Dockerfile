# syntax=docker/dockerfile:1
# Python 3.11 슬림 이미지 사용
# base: 의존성까지만 설치한 공통 기반 (test / runtime이 공유)
FROM python:3.11-slim AS base

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    python3-venv \
    python3-dev \
    libssl-dev \
    libffi-dev \
    cargo \
    rustc \
    && rm -rf /var/lib/apt/lists/*


# Python 의존성 설치 (uv 기반 유지)
COPY requirements.txt .
# VENV 위치를 소스 밖(/opt/venv)에 두어 바인드 마운트로 덮어지지 않게 함
ENV VENV_DIR=/opt/venv
RUN python3 -m venv ${VENV_DIR}
ENV PATH="${VENV_DIR}/bin:$PATH"

# requirements 설치 (pip 캐시 마운트로 재다운로드 방지)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 테스트 의존성 설치
COPY requirements-test.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-test.txt

# 품질 게이트
#
# runtime이 base에서 갈라져 나오므로 이 스테이지는 최종 이미지의 의존 경로에
# 없다. 따라서 `docker build`(타깃 미지정)로는 실행되지 않고, CI가
# `docker build --target test`로 명시적으로 호출한다.
# DB가 필요 없는 unit 마커만 돌린다 (tests/integration은 MySQL을 요구).
FROM base AS test

COPY app ./app
COPY tests ./tests
COPY pytest.ini ./

RUN pytest tests/unit -q

# runtime: 실제 배포 이미지 (마지막 스테이지 = 기본 빌드 타깃)
FROM base AS runtime

# 애플리케이션 코드 복사
COPY app ./app
COPY scripts ./scripts
COPY run_server.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 빌드 인자 및 메타데이터
ARG IMAGE_TAG=latest

# 환경변수로 설정
ENV IMAGE_TAG=${IMAGE_TAG}
ENV IMAGE_NAME=backtest-backend

# 포트 노출
EXPOSE 8000

# Prometheus Multiprocess Mode 설정
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
RUN mkdir -p ${PROMETHEUS_MULTIPROC_DIR} && chmod 777 ${PROMETHEUS_MULTIPROC_DIR}

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 서버 실행
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
