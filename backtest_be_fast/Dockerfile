# syntax=docker/dockerfile:1
# Python 3.11 슬림 이미지 사용
#
# 3-스테이지 구성:
#   builder  - 컴파일 툴체인(gcc/g++/cargo/rustc 등) + venv 생성 + requirements.txt만 설치.
#              최종 이미지에는 포함되지 않는다.
#   test     - builder에서 갈라져 나와 requirements-test.txt를 추가 설치하고 pytest를 실행.
#              품질 게이트 전용 (아래 설명 참고).
#   runtime  - 클린 python:3.11-slim 위에 /opt/venv만 복사. 컴파일러도, 테스트
#              의존성도 없다. non-root 사용자로 실행된다.
FROM python:3.11-slim AS builder

WORKDIR /app

# 빌드(컴파일)에만 필요한 시스템 패키지. runtime 스테이지에는 설치하지 않는다.
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
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

# 품질 게이트
#
# builder에서 갈라져 나오며 테스트 의존성을 추가 설치한다. runtime이 builder에서
# (test를 거치지 않고) 직접 갈라져 나오므로 이 스테이지는 최종 이미지의 의존
# 경로에 없다. 따라서 `docker build`(타깃 미지정)로는 실행되지 않고, CI가
# `docker build --target test`로 명시적으로 호출한다.
# DB가 필요 없는 unit 마커만 돌린다 (tests/integration은 MySQL을 요구).
FROM builder AS test

COPY requirements-test.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-test.txt

COPY app ./app
COPY tests ./tests
COPY pytest.ini ./

RUN pytest tests/unit -q

# runtime: 실제 배포 이미지 (마지막 스테이지 = 기본 빌드 타깃)
#
# builder의 컴파일러/헤더, test의 pytest 등 테스트 의존성은 여기 포함되지 않는다.
# 클린한 python:3.11-slim 위에 venv(/opt/venv)만 복사하고 non-root 사용자로 실행한다.
FROM python:3.11-slim AS runtime

WORKDIR /app

# HEALTHCHECK가 curl로 /health를 조회하므로 런타임에도 필요하다 (빌드 툴체인은 불필요).
# non-root 실행을 위한 시스템 계정도 함께 생성한다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home app

ENV VENV_DIR=/opt/venv
ENV PATH="${VENV_DIR}/bin:$PATH"
# builder에서 만든 venv만 가져온다 (컴파일러/헤더/캐시는 제외). app 사용자 소유로 복사.
COPY --from=builder --chown=app:app /opt/venv /opt/venv

# 애플리케이션 코드 복사 (app 사용자 소유)
COPY --chown=app:app app ./app
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app run_server.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 빌드 인자 및 메타데이터
ARG IMAGE_TAG=latest

# 환경변수로 설정
ENV IMAGE_TAG=${IMAGE_TAG}
ENV IMAGE_NAME=backtest-backend

# 포트 노출
EXPOSE 8000

# Prometheus Multiprocess Mode 설정 (world-writable 대신 app 소유 + 0755)
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
RUN mkdir -p ${PROMETHEUS_MULTIPROC_DIR} \
    && chown app:app ${PROMETHEUS_MULTIPROC_DIR} \
    && chmod 0755 ${PROMETHEUS_MULTIPROC_DIR}

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# non-root로 실행 (entrypoint/CMD 모두 이 사용자로 실행됨)
USER app

# 서버 실행
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
