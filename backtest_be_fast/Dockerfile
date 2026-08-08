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
# P2-22: requirements.txt(사람이 편집하는 범위 지정 입력)가 아니라
# requirements.lock.txt(완전 고정본)를 설치한다 — CI가 매번 다른 버전을
# 해석해 "로컬은 되는데 CI는 깨지는" 드리프트를 막는다. requirements.txt는
# 락 파일을 재생성할 때 쓰는 입력으로만 남는다.
COPY requirements.lock.txt .
# VENV 위치를 소스 밖(/opt/venv)에 두어 바인드 마운트로 덮어지지 않게 함
ENV VENV_DIR=/opt/venv
RUN python3 -m venv ${VENV_DIR}
ENV PATH="${VENV_DIR}/bin:$PATH"

# requirements 설치 (pip 캐시 마운트로 재다운로드 방지)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.lock.txt

# 품질 게이트
#
# builder에서 갈라져 나오며 테스트 의존성을 추가 설치한다. runtime이 builder에서
# (test를 거치지 않고) 직접 갈라져 나오므로 이 스테이지는 최종 이미지의 의존
# 경로에 없다. 따라서 `docker build`(타깃 미지정)로는 실행되지 않고, CI가
# `docker build --target test`로 명시적으로 호출한다.
# DB가 필요 없는 unit 마커만 돌린다 (tests/integration은 MySQL을 요구).
FROM builder AS test

COPY requirements-test.lock.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-test.lock.txt

COPY app ./app
COPY tests ./tests
COPY pytest.ini ./

RUN pytest tests/unit -q

# audit: 의존성 취약점 감사 (CI 전용)
#
# test와 마찬가지로 최종 이미지의 의존 경로 밖이라 `docker build`(타깃 미지정)
# 로는 실행되지 않는다. CI가 `--target audit`으로 호출한다. 락 파일만 있으면
# 되므로 builder가 아니라 클린 slim에서 시작한다 (네이티브 컴파일 불필요).
#
# 바인드 마운트(-v)가 아니라 빌드 컨텍스트로 파일을 받는 이유: Jenkins가
# 컨테이너 안에서 호스트 Docker 데몬에 붙어 sibling 컨테이너를 띄우는 구조라
# -v의 소스 경로가 호스트 기준으로 해석되어 파일을 찾지 못한다.
FROM python:3.11-slim AS audit

WORKDIR /app
COPY requirements.lock.txt .

# 업그레이드로 고칠 수 없고 이 앱에서 도달 불가능한 취약점 ID (공백 구분).
# 근거와 재검토 조건은 scripts/audit-deps.sh에 적혀 있다.
ARG PIP_AUDIT_IGNORE=""

RUN pip install -q pip-audit && \
    ignore_args=""; \
    for vuln in $PIP_AUDIT_IGNORE; do ignore_args="$ignore_args --ignore-vuln $vuln"; done; \
    pip-audit -r requirements.lock.txt $ignore_args

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
